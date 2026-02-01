"""Logging configuration for stream2mediaserver.

This module provides a centralized logging configuration for the entire application.
It supports both file and console logging with different log levels.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from ..config import config


def setup_logger(
    name: str = "stream2mediaserver",
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Set up and configure a logger instance.

    Args:
        name: The name of the logger instance
        level: The logging level (defaults to config.log_config.level)
        log_file: Optional path to a log file

    Returns:
        A configured logger instance
    """
    logger = logging.getLogger(name)

    # Use configuration defaults if not specified
    level = level or config.log_config.level
    log_file = log_file or config.log_config.file

    logger.setLevel(getattr(logging, level.upper()))

    if not logger.handlers:
        formatter = logging.Formatter(config.log_config.format)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(str(log_file))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        logger.propagate = False

    return logger


# Create default logger instance
logger = setup_logger()
