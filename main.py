import argparse
import logging
import sys
from pathlib import Path

import requests
import toml
from nico_download.configs import Config
from nico_download.downloader import DownloadManager, fetch_video_id, make_filename
from nico_download.exceptions import FileExistsError
from nico_download.logger import add_file_handler, get_logger, set_verbosity
from omegaconf import OmegaConf

config_schema = OmegaConf.structured(Config)
logger = get_logger("nico_download.main")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="./config.toml",
        help="config json path, see passwd.json.example",
    )
    parser.add_argument(
        "--logfile",
        type=str,
        default="./download.log",
        help="config json path, see passwd.json.example",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="download action will not be actually performed",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="set log level to DEBUG",
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite the mp4 file if existing."
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.logfile is not None:
        add_file_handler(args.logfile)
    set_verbosity(log_level)

    with open(args.config, "r", encoding="utf-8") as f:
        config_dict = toml.load(f)
    config = OmegaConf.merge(config_schema, OmegaConf.create(config_dict))

    manager = DownloadManager(
        uid=config.uid,
        passwd=config.passwd,
        session_cookie=config.session_cookie,
    )
    global_limit = config.limit
    failed_queries: list[str] = []
    failed: list[str] = []
    for query in config.queries:
        try:
            results = fetch_video_id(
                query=query.query,
                targets=query.target,
                max_videos=query.limit or global_limit,
                offset=query.offset,
            )
        except Exception as e:
            # Log it and go on to the next query. A network error (e.g. the host
            # is offline) is clear from its message, so skip its long traceback.
            logger.error(
                f"Failed to search videos for query '{query.query}': {e}",
                exc_info=not isinstance(e, requests.RequestException),
            )
            failed_queries.append(query.query)
            continue
        savedir = Path(config.saveroot)
        if len(query.subdir) > 0:
            savedir = savedir / query.subdir

        for movie_id, title in results:
            save_path = savedir / make_filename(title, movie_id)
            try:
                manager.download_video(
                    movie_id,
                    save_path,
                    args.overwrite,
                    args.dry_run,
                    config.skip_on_fail,
                )
            except FileExistsError:
                # Already logged in DownloadManager.
                pass
            except OSError:
                logger.exception(f"OSError on {save_path}, skip {movie_id}")
                failed.append(f"{movie_id} ({title})")
            except RuntimeError:
                # One failed video must not abort the remaining queries.
                # The failure is already logged in DownloadManager.
                failed.append(f"{movie_id} ({title})")

    if failed_queries:
        logger.error(
            f"Failed to search {len(failed_queries)} query(ies): {failed_queries}"
        )
    if failed:
        logger.error(f"Failed to download {len(failed)} video(s): {failed}")
    if failed_queries or failed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # An uncaught traceback only goes to stderr, which is not kept under
        # cron, so write it to the log file as well.
        logger.exception("Unexpected error")
        sys.exit(1)
