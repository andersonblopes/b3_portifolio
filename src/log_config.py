"""Central logging configuration for the app.

Writes rotating log files under `logs/` at the project root, alongside
console output, so troubleshooting doesn't depend on capturing the
terminal that ran `make run`.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

_configured = False


def setup_logging(level=logging.INFO):
    """Configure root logger once per process (idempotent).

    Streamlit reruns the script on every interaction, so this guards
    against re-adding handlers (which would duplicate every log line).
    """
    global _configured
    if _configured:
        return

    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(level)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True
