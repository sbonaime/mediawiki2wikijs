"""Logging utilities for MediaWiki to Wiki.js migration tool.

This module provides structured logging configuration and CSV error log writer.
"""

import logging
import csv
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(name: str, level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """Configure and return a logger with specified settings.

    Args:
        name: Logger name (typically __name__ of calling module)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Format: [2025-11-10 12:34:56] INFO: Message
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class CSVErrorLogger:
    """CSV error log writer for corrupted documents.

    Writes errors to CSV file with columns: timestamp, page_id, page_title, error_type, error_message
    """

    def __init__(self, csv_file: str):
        """Initialize CSV error logger.

        Args:
            csv_file: Path to CSV file (e.g., "export_errors.csv")
        """
        self.csv_file = Path(csv_file)
        self.csv_file.parent.mkdir(parents=True, exist_ok=True)

        # Create file with header if it doesn't exist
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'page_id', 'page_title', 'error_type', 'error_message'])

    def log_error(self, page_id: str, page_title: str, error_type: str, error_message: str):
        """Log an error to CSV file.

        Args:
            page_id: Page ID that encountered error
            page_title: Page title for reference
            error_type: Type of error (e.g., "parse_error", "network_error", "download_failed")
            error_message: Detailed error message
        """
        timestamp = datetime.now().isoformat()

        with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, page_id, page_title, error_type, error_message])

    def log_image_error(self, image_url: str, error_type: str, error_message: str):
        """Log an image download error to CSV file.

        Args:
            image_url: Image URL that failed
            error_type: Type of error (e.g., "download_failed", "timeout")
            error_message: Detailed error message
        """
        self.log_error(
            page_id='N/A',
            page_title=image_url,
            error_type=error_type,
            error_message=error_message
        )


def get_progress_logger(name: str, level: str = 'INFO') -> logging.Logger:
    """Get a logger configured for progress reporting.

    Args:
        name: Logger name
        level: Log level

    Returns:
        Logger configured for progress messages
    """
    return setup_logger(name, level)
