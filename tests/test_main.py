import json
from pathlib import Path

import pytest
from nico_download.main import DownloadManager, fetch_video_id


@pytest.fixture
def nico_config():
    here = Path(__file__).parent
    with open(here / "../passwd.json", "r") as f:
        config = json.load(f)
    return config


def test_fetch_video_id():
    config = {"query": "仮装大賞 高坂海美", "targets": "title"}
    return_list = fetch_video_id(**config)
    assert isinstance(return_list, list)
    assert len(return_list) == 1
    data = return_list[0]
    assert isinstance(data, tuple)
    assert len(data) == 2
    assert data[0] == "sm37998381"
    assert data[1] == "仮装大賞 高坂海美"


@pytest.mark.parametrize(
    "overwrite_flag",
    (True, pytest.param(False, marks=pytest.mark.xfail(raises=RuntimeError))),
)
@pytest.mark.parametrize("video_id", ["sm37701231", "so24277772"])
def test_download_movie(tmp_path, video_id, overwrite_flag, nico_config):
    manager = DownloadManager(uid=nico_config["uid"], passwd=nico_config["passwd"])
    target_path = tmp_path / "tmp.mp4"

    # make dummy file to overwrite
    Path.touch(target_path)
    ret_path = manager.download_video(
        video_id=video_id, save_path=target_path, overwrite=overwrite_flag
    )
    assert target_path.exists()
    assert ret_path == target_path
