import argparse
import logging
from pathlib import Path

import toml
from omegaconf import OmegaConf

from nico_download.configs import Config
from nico_download.downloader import DownloadManager, fetch_video_id
from nico_download.exceptions import FileExistsError
from nico_download.logger import add_file_handler, set_verbosity

config_schema = OmegaConf.structured(Config)


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

    with open(args.config, "r") as f:
        config_dict = toml.load(f)
    config = OmegaConf.merge(config_schema, OmegaConf.create(config_dict))

    manager = DownloadManager(uid=config.uid, passwd=config.passwd)
    global_limit = config.limit
    for query in config.queries:
        results = fetch_video_id(
            query=query.query,
            targets=query.target,
            max_videos=query.limit or global_limit,
            offset=query.offset,
        )
        savedir = Path(config.saveroot)
        if len(query["subdir"]) > 0:
            savedir = savedir / query["subdir"]

        for movie_id, title in results:
            save_path = savedir / f"{title}.mp4"
            try:
                manager.download_video(
                    movie_id, save_path, args.overwrite, args.dry_run
                )
            except FileExistsError as e:
                print(e)
            except OSError as e:
                print(f"OSError: {str(e)}")
                print(f"skip {movie_id}, {title}")


if __name__ == "__main__":
    main()
