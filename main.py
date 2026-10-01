import argparse
import logging
import sys
from pathlib import Path

import toml
from nico_download.configs import Config
from nico_download.downloader import DownloadManager, fetch_video_id
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
    failed: list[str] = []
    for query in config.queries:
        results = fetch_video_id(
            query=query.query,
            targets=query.target,
            max_videos=query.limit or global_limit,
            offset=query.offset,
        )
        savedir = Path(config.saveroot)
        if len(query.subdir) > 0:
            savedir = savedir / query.subdir

        for movie_id, title in results:
            save_path = savedir / f"{title}.mp4"
            try:
                manager.download_video(
                    movie_id,
                    save_path,
                    args.overwrite,
                    args.dry_run,
                    config.skip_on_fail,
                )
            except FileExistsError as e:
                print(e)
            except OSError as e:
                print(f"OSError: {str(e)}")
                print(f"skip {movie_id}, {title}")
            except RuntimeError:
                # One failed video must not abort the remaining queries.
                # The failure is already logged in DownloadManager.
                failed.append(f"{movie_id} ({title})")

    if failed:
        logger.error(f"Failed to download {len(failed)} video(s): {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
