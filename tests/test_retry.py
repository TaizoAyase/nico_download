from pathlib import Path

import pytest
from nico_download import downloader
from nico_download.downloader import DownloadManager


def _manager(max_retries: int = 2) -> DownloadManager:
    return DownloadManager(
        session_cookie="dummy", max_retries=max_retries, retry_interval=0
    )


def test_retry_then_success(monkeypatch, tmp_path):
    calls = []

    def fake_execute(*args):
        calls.append(args)
        if len(calls) < 2:
            raise KeyError("video")
        Path(args[args.index("-o") + 1]).touch()

    monkeypatch.setattr(downloader.nndownload, "execute", fake_execute)
    save_path = tmp_path / "out.mp4"
    assert _manager().download_video("so1", save_path) == save_path
    assert len(calls) == 2
    assert save_path.exists()


def test_give_up_after_retries(monkeypatch, tmp_path):
    calls = []

    def fake_execute(*args):
        calls.append(args)
        raise KeyError("video")

    monkeypatch.setattr(downloader.nndownload, "execute", fake_execute)
    save_path = tmp_path / "out.mp4"
    with pytest.raises(RuntimeError):
        _manager(max_retries=2).download_video("so1", save_path)
    assert len(calls) == 3


def test_system_exit_becomes_runtime_error(monkeypatch, tmp_path):
    calls = []

    def fake_execute(*args):
        calls.append(args)
        raise SystemExit(2)

    monkeypatch.setattr(downloader.nndownload, "execute", fake_execute)
    save_path = tmp_path / "out.mp4"
    with pytest.raises(RuntimeError):
        _manager(max_retries=2).download_video("so1", save_path)
    assert len(calls) == 3


def test_keyboard_interrupt_exits_without_retry(monkeypatch, tmp_path):
    calls = []

    def fake_execute(*args):
        calls.append(args)
        raise KeyboardInterrupt

    monkeypatch.setattr(downloader.nndownload, "execute", fake_execute)
    save_path = tmp_path / "out.mp4"
    save_path.write_bytes(b"completed")
    with pytest.raises(SystemExit) as excinfo:
        _manager(max_retries=2).download_video("so1", save_path, overwrite=True)
    assert excinfo.value.code == 0
    assert len(calls) == 1
    assert save_path.read_bytes() == b"completed"


def test_skip_on_fail(monkeypatch, tmp_path):
    def fake_execute(*args):
        raise KeyError("video")

    monkeypatch.setattr(downloader.nndownload, "execute", fake_execute)
    save_path = tmp_path / "out.mp4"
    ret = _manager(max_retries=0).download_video("so1", save_path, skip_on_fail=True)
    assert ret == save_path
    assert not save_path.exists()
