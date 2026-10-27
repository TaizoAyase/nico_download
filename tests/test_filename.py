import pytest
from nico_download.downloader import MAX_FILENAME_BYTES, PART_SUFFIX, make_filename

VIDEO_ID = "dummy_video_id"


def _part_name(filename: str) -> str:
    # The name nndownload writes to while downloading.
    return filename.removesuffix(".mp4") + f"{PART_SUFFIX}.mp4"


def test_short_title_is_kept():
    assert make_filename("タイトル", VIDEO_ID) == "タイトル.mp4"


def test_title_at_limit_is_kept():
    title = "a" * (MAX_FILENAME_BYTES - len(f"{PART_SUFFIX}.mp4"))
    assert make_filename(title, VIDEO_ID) == f"{title}.mp4"


@pytest.mark.parametrize("char", ["a", "あ", "🎵"])
def test_long_title_is_truncated(tmp_path, char):
    title = char * MAX_FILENAME_BYTES
    filename = make_filename(title, VIDEO_ID)

    assert len(_part_name(filename).encode()) <= MAX_FILENAME_BYTES
    assert filename.endswith(f" ({VIDEO_ID}).mp4")
    head = filename.removesuffix(f" ({VIDEO_ID}).mp4")
    assert head and title.startswith(head)
    # Both names can be created on the file system.
    (tmp_path / filename).touch()
    (tmp_path / _part_name(filename)).touch()


def test_titles_differing_after_cut_get_different_names():
    prefix = "あ" * MAX_FILENAME_BYTES
    assert make_filename(f"{prefix}1", "dummy_id_1") != make_filename(
        f"{prefix}2", "dummy_id_2"
    )
