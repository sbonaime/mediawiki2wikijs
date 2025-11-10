"""ImageAsset model for MediaWiki to Wiki.js migration tool.

This module defines the ImageAsset dataclass representing an image file
associated with wiki pages.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DownloadStatus(Enum):
    """Image download/upload status states."""
    PENDING = "pending"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    UPLOADED = "uploaded"


@dataclass
class ImageAsset:
    """Represents an image file associated with wiki pages.

    Attributes:
        original_filename: Filename in MediaWiki
        url: Full URL to download image from MediaWiki
        page_references: List of page titles that reference this image
        download_status: Current status (pending, downloaded, failed, uploaded)
        renamed_filename: New filename based on page name (e.g., "PageName-image-001.png")
        local_path: Local filesystem path after download
        content_type: MIME type (e.g., "image/png", "image/jpeg")
        size_bytes: File size in bytes
        error_message: Error details if download_status is "failed"
        wikijs_url: URL in Wiki.js after upload
    """

    original_filename: str
    url: str
    page_references: List[str]
    download_status: DownloadStatus = DownloadStatus.PENDING
    renamed_filename: Optional[str] = None
    local_path: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    wikijs_url: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.original_filename:
            raise ValueError("Image filename cannot be empty")
        if not self.url:
            raise ValueError("Image URL cannot be empty")
        if not self.page_references:
            raise ValueError("Image must be referenced by at least one page")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("Image size must be positive")

        # Convert string status to enum if needed
        if isinstance(self.download_status, str):
            self.download_status = DownloadStatus(self.download_status)

    def is_pending(self) -> bool:
        """Check if image download is pending."""
        return self.download_status == DownloadStatus.PENDING

    def is_downloaded(self) -> bool:
        """Check if image has been downloaded."""
        return self.download_status == DownloadStatus.DOWNLOADED

    def is_failed(self) -> bool:
        """Check if image download failed."""
        return self.download_status == DownloadStatus.FAILED

    def is_uploaded(self) -> bool:
        """Check if image has been uploaded to Wiki.js."""
        return self.download_status == DownloadStatus.UPLOADED

    def mark_downloaded(self, local_path: str, size_bytes: int, content_type: str):
        """Mark image as successfully downloaded."""
        self.download_status = DownloadStatus.DOWNLOADED
        self.local_path = local_path
        self.size_bytes = size_bytes
        self.content_type = content_type

    def mark_failed(self, error_message: str):
        """Mark image download as failed."""
        self.download_status = DownloadStatus.FAILED
        self.error_message = error_message

    def mark_uploaded(self, wikijs_url: str):
        """Mark image as uploaded to Wiki.js."""
        self.download_status = DownloadStatus.UPLOADED
        self.wikijs_url = wikijs_url
