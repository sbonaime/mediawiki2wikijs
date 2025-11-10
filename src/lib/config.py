"""Configuration management for MediaWiki to Wiki.js migration tool.

This module loads environment variables from .env file and provides
configuration values to other modules.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for migration tool.

    Loads settings from .env file and provides typed access to configuration values.
    """

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            env_file: Path to .env file (defaults to .env in current directory)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # Load from .env in current directory

        # MediaWiki configuration
        self.mediawiki_url = self._get_required('MEDIAWIKI_URL')
        self.mediawiki_username = self._get_required('MEDIAWIKI_USERNAME')
        self.mediawiki_password = self._get_required('MEDIAWIKI_PASSWORD')

        # Wiki.js configuration
        self.wikijs_url = self._get_required('WIKIJS_URL')
        self.wikijs_api_key = self._get_required('WIKIJS_API_KEY')

        # Optional settings with defaults
        self.export_dir = self._get_optional('EXPORT_DIR', './export_output')
        self.checkpoint_frequency = int(self._get_optional('CHECKPOINT_FREQUENCY', '10'))
        self.max_link_depth = int(self._get_optional('MAX_LINK_DEPTH', '-1'))
        self.log_level = self._get_optional('LOG_LEVEL', 'INFO')

        # Validate export directory path
        self.export_dir_path = Path(self.export_dir)

    def _get_required(self, key: str) -> str:
        """Get required environment variable.

        Args:
            key: Environment variable name

        Returns:
            Environment variable value

        Raises:
            ValueError: If required variable is not set
        """
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set. "
                           f"Please check your .env file.")
        return value

    def _get_optional(self, key: str, default: str) -> str:
        """Get optional environment variable with default.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def validate(self):
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        # Validate URLs
        if not self.mediawiki_url.startswith(('http://', 'https://')):
            raise ValueError("MEDIAWIKI_URL must start with http:// or https://")
        if not self.wikijs_url.startswith(('http://', 'https://')):
            raise ValueError("WIKIJS_URL must start with http:// or https://")

        # Validate numeric values
        if self.checkpoint_frequency < 1:
            raise ValueError("CHECKPOINT_FREQUENCY must be at least 1")

        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary (for checkpoint snapshots).

        Returns:
            Dictionary of configuration values (excludes sensitive data)
        """
        return {
            'mediawiki_url': self.mediawiki_url,
            'wikijs_url': self.wikijs_url,
            'export_dir': self.export_dir,
            'checkpoint_frequency': self.checkpoint_frequency,
            'max_link_depth': self.max_link_depth,
            'log_level': self.log_level
        }


def load_config(env_file: Optional[str] = None) -> Config:
    """Load and validate configuration.

    Args:
        env_file: Path to .env file (optional)

    Returns:
        Validated Config object

    Raises:
        ValueError: If configuration is invalid or required values missing
    """
    config = Config(env_file)
    config.validate()
    return config
