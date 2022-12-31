import json
import sys
from pathlib import Path
from typing import List, Tuple

import nndownload
import requests
from nndownload.nndownload import (
    BACKOFF_FACTOR,
    LOGIN_URL,
    RETRY_ATTEMPTS,
    AuthenticationException,
)
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from nico_download.exceptions import FileExistsError
from nico_download.logger import get_logger

ENDPOINT_URL = "https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search"

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

    def __init__(self, uid: str, passwd: str):
        self._uid = uid
        self._passwd = passwd
        self.__cookie = None

    @property
    def _cookie(self):
        if self.__cookie is None:
            session = _login(self._uid, self._passwd)
            self.__cookie = session.cookies.get_dict()["user_session"]
        return self.__cookie

    def download_video(
        self,
        video_id: str,
        save_path: Path,
        overwrite: bool = False,
        dry_run: bool = False,
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

        try:
            logger.info(f"Start download from {url}.")
            nndownload.execute(
                "--username",
                self._uid,
                "--password",
                self._passwd,
                "--session-cookie",
                self._cookie,
                "-o",
                str(save_path),
                url,
            )
        except KeyboardInterrupt:
            logger.critical("KeyboardInterrupt stopped!")
            save_path.unlink()
            logger.critical(f"Intermediate file {save_path} is removed.")
            sys.exit(0)
        except Exception as e:
            logger.exception("Something wrong happened in nndownload.execute()")
            raise RuntimeError(str(e))
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
