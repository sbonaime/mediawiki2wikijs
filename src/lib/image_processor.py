"""Image processor for MediaWiki to Wiki.js migration tool.

This module handles image downloading, renaming, and processing.
"""

import requests
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import urlparse

from ..models import ImageAsset, DownloadStatus
from .logger import setup_logger, CSVErrorLogger


class ImageProcessor:
    """Handles image download and renaming operations."""

    def __init__(self, error_logger: Optional[CSVErrorLogger] = None):
        """Initialize image processor.

        Args:
            error_logger: CSV error logger for recording failures
        """
        self.logger = setup_logger(__name__)
        self.error_logger = error_logger
        self.timeout = 30  # Request timeout in seconds

    def download_image(self, image: ImageAsset, destination: str) -> bool:
        """Download image from URL to local file.

        Args:
            image: ImageAsset with URL to download
            destination: Local file path to save image

        Returns:
            True if download succeeds, False otherwise
        """
        try:
            self.logger.debug(f"Downloading image: {image.original_filename}")

            # Make HTTP GET request
            response = requests.get(
                image.url,
                timeout=self.timeout,
                stream=True
            )
            response.raise_for_status()

            # Create parent directory if needed
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Get actual file size
            file_size = dest_path.stat().st_size

            # Update image metadata
            image.mark_downloaded(
                local_path=str(dest_path),
                size_bytes=file_size,
                content_type=response.headers.get('Content-Type', '')
            )

            self.logger.debug(f"Successfully downloaded: {image.original_filename} ({file_size} bytes)")
            return True

        except requests.exceptions.Timeout:
            error_msg = f"Download timeout after {self.timeout}s"
            self.logger.error(f"Failed to download {image.original_filename}: {error_msg}")
            image.mark_failed(error_msg)

            if self.error_logger:
                self.error_logger.log_image_error(
                    image.url,
                    'download_timeout',
                    error_msg
                )

            return False

        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            self.logger.error(f"Failed to download {image.original_filename}: {error_msg}")
            image.mark_failed(error_msg)

            if self.error_logger:
                self.error_logger.log_image_error(
                    image.url,
                    'download_failed',
                    error_msg
                )

            return False

        except IOError as e:
            error_msg = f"File write error: {str(e)}"
            self.logger.error(f"Failed to save {image.original_filename}: {error_msg}")
            image.mark_failed(error_msg)

            if self.error_logger:
                self.error_logger.log_image_error(
                    image.url,
                    'file_write_error',
                    error_msg
                )

            return False

    def rename_images(self, images: list, page_slug: str) -> None:
        """Rename images based on page slug with sequential numbering.

        Args:
            images: List of ImageAsset objects
            page_slug: Page slug for naming pattern (e.g., "getting-started")
        """
        for idx, image in enumerate(images, start=1):
            # Get file extension
            original = image.original_filename
            ext = Path(original).suffix

            # Generate new filename: page-slug-image-001.ext
            new_filename = f"{page_slug}-image-{idx:03d}{ext}"
            image.renamed_filename = new_filename

            self.logger.debug(f"Renamed: {original} -> {new_filename}")

    def generate_page_slug(self, page_title: str) -> str:
        """Generate URL-safe slug from page title.

        Args:
            page_title: Original page title

        Returns:
            URL-safe slug (lowercase, hyphen-separated)
        """
        # Convert to lowercase
        slug = page_title.lower()

        # Replace spaces with hyphens
        slug = slug.replace(' ', '-')

        # Remove or replace special characters
        safe_chars = 'abcdefghijklmnopqrstuvwxyz0123456789-_'
        slug = ''.join(c if c in safe_chars else '-' for c in slug)

        # Remove consecutive hyphens
        while '--' in slug:
            slug = slug.replace('--', '-')

        # Remove leading/trailing hyphens
        slug = slug.strip('-')

        # Limit length
        max_length = 200
        if len(slug) > max_length:
            slug = slug[:max_length].rstrip('-')

        return slug or 'page'  # Fallback if slug is empty
