"""Application file logging for beta diagnosis."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from empirum_services.app_paths import app_data_dir

_LOG = logging.getLogger("emp_packagex3")


def default_log_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(*, debug: bool = False, log_dir: Path | None = None) -> Path:
    """Configure the app logger. Repeated calls switch level AND log directory."""
    directory = Path(log_dir) if log_dir else default_log_dir()
    directory.mkdir(parents=True, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO
    _LOG.setLevel(level)
    _LOG.propagate = False
    wanted_logfile = directory / "emp-packagex3.log"

    has_current = any(
        isinstance(h, RotatingFileHandler)
        and getattr(h, "stream", None) is not None
        and Path(h.baseFilename).resolve() == wanted_logfile.resolve()
        for h in _LOG.handlers
    )
    if not has_current:
        # Drop stale file handlers so a log_dir change takes effect immediately.
        for handler in [h for h in _LOG.handlers if isinstance(h, RotatingFileHandler)]:
            handler.close()
            _LOG.removeHandler(handler)

        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = RotatingFileHandler(
            wanted_logfile,
            maxBytes=2_000_000,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(fmt)
        file_handler.setLevel(level)
        _LOG.addHandler(file_handler)
        _LOG.info("Logging started (debug=%s) dir=%s", debug, directory)

    has_console = any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler)
        for h in _LOG.handlers
    )
    if not has_console:
        console: logging.Handler = logging.StreamHandler(sys.stderr)
        console.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _LOG.addHandler(console)
    for h in _LOG.handlers:
        if isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler):
            h.setLevel(logging.DEBUG if debug else logging.WARNING)
    return directory


def get_logger(name: str = "emp_packagex3") -> logging.Logger:
    return logging.getLogger(name)
