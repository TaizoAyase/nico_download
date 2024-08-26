import logging
import logging.handlers
import threading
from typing import Optional

import colorlog

_lock: threading.Lock = threading.Lock()
_default_handler: Optional[logging.Handler] = None
_file_handler: Optional[logging.Handler] = None


def create_default_formatter() -> colorlog.ColoredFormatter:
    return colorlog.ColoredFormatter(
        "%(log_color)s[%(levelname)1.1s %(asctime)s]%(reset)s %(message)s"
    )


def _get_library_name() -> str:
    return __name__.split(".")[0]


def _get_library_root_logger() -> logging.Logger:
    return logging.getLogger(_get_library_name())


def _configure_library_root_logger() -> None:
    global _default_handler

    with _lock:
        if _default_handler:
            # This library has already configured the library root logger.
            return
        _default_handler = logging.StreamHandler()  # Set sys.stderr as stream.
        _default_handler.setFormatter(create_default_formatter())

        # Apply our default configuration to the library root logger.
        library_root_logger: logging.Logger = _get_library_root_logger()
        library_root_logger.addHandler(_default_handler)
        library_root_logger.setLevel(logging.INFO)
        library_root_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    _configure_library_root_logger()
    return logging.getLogger(name)


def add_file_handler(filename: str, max_bytes=1_000_000, max_counts=10) -> None:
    global _file_handler

    with _lock:
        if _file_handler:
            return
        _file_handler = logging.handlers.RotatingFileHandler(
            filename, maxBytes=max_bytes, backupCount=max_counts
        )
        _file_handler.setFormatter(create_default_formatter())
        logger = _get_library_root_logger()
        logger.addHandler(_file_handler)


def get_verbosity() -> int:
    _configure_library_root_logger()
    return _get_library_root_logger().getEffectiveLevel()


def set_verbosity(verbosity: int) -> None:
    _configure_library_root_logger()
    _get_library_root_logger().setLevel(verbosity)


def disable_default_handler() -> None:
    _configure_library_root_logger()

    assert _default_handler is not None
    _get_library_root_logger().removeHandler(_default_handler)


def enable_default_handler() -> None:
    _configure_library_root_logger()

    assert _default_handler is not None
    _get_library_root_logger().addHandler(_default_handler)
