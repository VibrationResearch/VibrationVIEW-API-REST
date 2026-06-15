# ============================================================================
# FILE: tests/test_logging_config.py
# ============================================================================

"""
Tests for logging configuration

Verify that the application uses an absolute log directory, configures
RotatingFileHandler with the expected defaults, and respects overrides.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from config import Config


class TestLoggingConfig:
    def test_vv_log_dir_is_absolute(self):
        """VV_LOG_DIR resolves to an absolute path"""
        assert os.path.isabs(Config.VV_LOG_DIR)

    def test_rotating_file_handler_used(self, app):
        """Application configures a RotatingFileHandler on the root logger"""
        handlers = logging.root.handlers
        rotating = [h for h in handlers if isinstance(h, RotatingFileHandler)]
        assert len(rotating) >= 1, "Expected at least one RotatingFileHandler"

    def test_rotating_handler_max_bytes(self, app):
        """RotatingFileHandler maxBytes matches config"""
        for h in logging.root.handlers:
            if isinstance(h, RotatingFileHandler):
                assert h.maxBytes == app.config["VV_LOG_MAX_BYTES"]
                break
        else:
            assert False, "No RotatingFileHandler found"

    def test_rotating_handler_backup_count(self, app):
        """RotatingFileHandler backupCount matches config"""
        for h in logging.root.handlers:
            if isinstance(h, RotatingFileHandler):
                assert h.backupCount == app.config["VV_LOG_BACKUP_COUNT"]
                break
        else:
            assert False, "No RotatingFileHandler found"

    def test_log_file_in_configured_directory(self, app):
        """Log file is created inside VV_LOG_DIR"""
        log_dir = app.config["VV_LOG_DIR"]
        for h in logging.root.handlers:
            if isinstance(h, RotatingFileHandler):
                log_path = os.path.abspath(h.baseFilename)
                assert log_path.startswith(log_dir)
                break
        else:
            assert False, "No RotatingFileHandler found"
