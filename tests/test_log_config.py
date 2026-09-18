import logging

import src.log_config as log_config


def test_setup_logging_creates_log_dir_and_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.log"
    monkeypatch.setattr(log_config, "LOG_DIR", str(log_dir))
    monkeypatch.setattr(log_config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(log_config, "_configured", False)

    root = logging.getLogger()
    prior_handlers = list(root.handlers)
    try:
        log_config.setup_logging(level=logging.DEBUG)

        assert log_dir.is_dir()
        assert root.level == logging.DEBUG
        assert len(root.handlers) == len(prior_handlers) + 2
        assert log_config._configured is True
    finally:
        for h in list(root.handlers):
            if h not in prior_handlers:
                root.removeHandler(h)
                h.close()


def test_setup_logging_is_idempotent(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "app.log"
    monkeypatch.setattr(log_config, "LOG_DIR", str(log_dir))
    monkeypatch.setattr(log_config, "LOG_FILE", str(log_file))
    monkeypatch.setattr(log_config, "_configured", False)

    root = logging.getLogger()
    prior_handlers = list(root.handlers)
    try:
        log_config.setup_logging()
        handlers_after_first = len(root.handlers)

        # Second call must be a no-op (guards against duplicate handlers
        # on every Streamlit rerun).
        log_config.setup_logging()

        assert len(root.handlers) == handlers_after_first
    finally:
        for h in list(root.handlers):
            if h not in prior_handlers:
                root.removeHandler(h)
                h.close()
