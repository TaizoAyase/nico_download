import json
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import nndownload
import requests
from nico_download.exceptions import FileExistsError
from nico_download.logger import get_logger
from nndownload.nndownload import (
    BACKOFF_FACTOR,
    LOGIN_URL,
    RETRY_ATTEMPTS,
    AuthenticationException,
)
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

ENDPOINT_URL = (
    "https://snapshot.search.nicovideo.jp/api/v2/snapshot/video/contents/search"
)

logger = get_logger(__name__)


def _login(username: str, password: str) -> requests.Session:
    session = requests.session()

    retry = Retry(
        total=RETRY_ATTEMPTS,
        read=RETRY_ATTEMPTS,
        connect=RETRY_ATTEMPTS,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {"User-Agent": f"{nndownload}/{nndownload.nndownload.__version__}"}
    )
    logger.info("Logging in...")
    login_post = {"mail_tel": username, "password": password}
    login_request = session.post(LOGIN_URL, data=login_post)
    login_request.raise_for_status()
    if not session.cookies.get_dict().get("user_session", None):
        logger.info("Failed to login.")
        raise AuthenticationException(
            "Failed to login. Please verify your account email/telephone and password"
        )
    logger.info("Logged in.")
    return session


class DownloadManager(object):
    movie_url_prefix = "https://www.nicovideo.jp/watch/"

    def __init__(
        self,
        uid: Optional[str] = None,
        passwd: Optional[str] = None,
        session_cookie: Optional[str] = None,
        max_retries: int = 2,
        retry_interval: float = 30.0,
    ):
        if session_cookie is None and not (uid and passwd):
            raise ValueError(
                "Either session_cookie or both uid and passwd must be set. "
                "Note: password login is currently broken on the niconico side; "
                "see README for how to obtain a session cookie."
            )
        self._uid = uid
        self._passwd = passwd
        self.__cookie = session_cookie
        self._max_retries = max_retries
        self._retry_interval = retry_interval

    @property
    def _cookie(self):
        if self.__cookie is None:
            # Password login stopped working after the niconico login system
            # was replaced with a Turnstile-protected SPA; supply
            # session_cookie in config.toml instead.
            session = _login(self._uid, self._passwd)
            self.__cookie = session.cookies.get_dict()["user_session"]
        return self.__cookie

    def download_video(
        self,
        video_id: str,
        save_path: Path,
        overwrite: bool = False,
        dry_run: bool = False,
        skip_on_fail: bool = False,
    ) -> Path:
        url = self.movie_url_prefix + str(video_id)
        if dry_run:
            logger.info(f"DRYRUN: Download from url: {url} to {save_path}")
            return save_path

        logger.debug(f"Start download from {url}, save to {save_path}")
        if save_path.exists():
            if not overwrite:
                mes = f"{save_path} already exists."
                logger.error(mes)
                raise FileExistsError(mes)
            else:
                logger.warning(
                    f"File {save_path} already exists, but overwrite flag is set."
                )
                logger.warning("Continue to download.")

        auth_args = []
        if self._uid and self._passwd:
            auth_args += ["--username", self._uid, "--password", self._passwd]
        for attempt in range(self._max_retries + 1):
            try:
                logger.info(f"Start download from {url}.")
                nndownload.execute(
                    *auth_args,
                    "--session-cookie",
                    self._cookie,
                    "-o",
                    str(save_path),
                    url,
                )
                break
            except KeyboardInterrupt:
                logger.critical("KeyboardInterrupt stopped!")
                save_path.unlink(missing_ok=True)
                logger.critical(f"Intermediate file {save_path} is removed.")
                sys.exit(0)
            except (Exception, SystemExit) as e:
                # nndownload.execute() parses its arguments with argparse,
                # which raises SystemExit on invalid arguments.
                logger.exception("Something wrong happened in nndownload.execute()")
                if attempt < self._max_retries:
                    logger.warning(
                        f"Retry downloading {url} in {self._retry_interval} sec "
                        f"({attempt + 1}/{self._max_retries})."
                    )
                    time.sleep(self._retry_interval)
                    continue
                if not skip_on_fail:
                    raise RuntimeError(str(e))
                logger.warning(f"skip_on_fail flag enabled. Skip for {save_path}")
                return save_path
        logger.info(f"Successfully download to {save_path}.")
        return save_path


def fetch_video_id(
    query: str, targets: str, max_videos: int = 100, offset: int = 0
) -> List[Tuple[str, str]]:
    query_dict = {
        "q": query,
        "targets": targets,
        "fields": "contentId,title",
        "_sort": "-startTime",
        "_limit": str(max_videos),
        "_offset": str(offset),
    }
    logger.debug(f"{query_dict=}")
    res = requests.get(ENDPOINT_URL, query_dict)

    response_dict = json.loads(res.text)
    logger.debug(f"{response_dict=}")
    return_value: List[Tuple[str, str]] = []
    for data in response_dict["data"]:
        movie_id = data["contentId"]
        title = data["title"]
        return_value.append((movie_id, title))
    logger.debug(f"{return_value=}")
    return return_value
