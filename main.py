import argparse
import logging
from pathlib import Path

import toml

from nico_download.downloader import DownloadManager, fetch_video_id
from nico_download.exceptions import FileExistsError
from nico_download.logger import set_verbosity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=str,
        default="./config.toml",
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
    set_verbosity(log_level)

    with open(args.config, "r") as f:
        config = toml.load(f)

    manager = DownloadManager(uid=config["uid"], passwd=config["passwd"])
    limit = config["limit"]
    for query in config["queries"]:
        results = fetch_video_id(
            query=query["query"], targets=query["target"], max_videos=limit
        )
        savedir = Path(config["saveroot"])
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


if __name__ == "__main__":
    main()
