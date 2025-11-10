"""Storage manager for MediaWiki to Wiki.js migration tool.

This module handles filesystem operations for hierarchical directory structure,
including namespace directories, page markdown files, images, and checkpoint management.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..models import WikiPage, ImageAsset, Checkpoint


class StorageManager:
    """Manages local filesystem storage for exported wiki content.

    Handles creation of hierarchical directory structure:
    export_output/
    ├── [namespace]/
    │   ├── [category]/
    │   │   └── page-title.md
    │   └── images/
    │       └── page-name-image-001.png
    └── .checkpoint
    """

    def __init__(self, base_dir: str):
        """Initialize storage manager.

        Args:
            base_dir: Base directory for export output (e.g., "./export_output")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_namespace_dir(self, namespace: str) -> Path:
        """Create directory for a namespace.

        Args:
            namespace: Namespace name (e.g., "Main", "User", "Help")

        Returns:
            Path to created namespace directory
        """
        namespace_dir = self.base_dir / namespace
        namespace_dir.mkdir(parents=True, exist_ok=True)
        return namespace_dir

    def create_images_dir(self, namespace: str) -> Path:
        """Create images directory within a namespace.

        Args:
            namespace: Namespace name

        Returns:
            Path to images directory
        """
        images_dir = self.base_dir / namespace / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir

    def save_page_markdown(self, page: WikiPage, namespace: str) -> str:
        """Save page content as markdown file.

        Args:
            page: WikiPage object with content
            namespace: Namespace for directory organization

        Returns:
            Relative path to saved file
        """
        namespace_dir = self.create_namespace_dir(namespace)

        # Sanitize filename (remove special characters, limit length)
        safe_filename = self._sanitize_filename(page.title) + ".md"
        file_path = namespace_dir / safe_filename

        # Write markdown content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(page.content)

        # Return relative path
        relative_path = file_path.relative_to(self.base_dir)
        return str(relative_path)

    def save_image(self, image: ImageAsset, namespace: str, content: bytes) -> str:
        """Save image file to images directory.

        Args:
            image: ImageAsset object
            namespace: Namespace for directory organization
            content: Binary image content

        Returns:
            Path to saved image file
        """
        images_dir = self.create_images_dir(namespace)

        # Use renamed filename if available, otherwise original
        filename = image.renamed_filename or image.original_filename
        file_path = images_dir / filename

        # Write binary content
        with open(file_path, 'wb') as f:
            f.write(content)

        return str(file_path)

    def load_export_metadata(self) -> Optional[Dict]:
        """Load export metadata from JSON file.

        Returns:
            Dictionary of export metadata, or None if file doesn't exist
        """
        metadata_file = self.base_dir / "export_metadata.json"
        if not metadata_file.exists():
            return None

        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_export_metadata(self, metadata: Dict):
        """Save export metadata to JSON file.

        Args:
            metadata: Dictionary containing export metadata
        """
        metadata_file = self.base_dir / "export_metadata.json"

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to .checkpoint file in base directory.

        Args:
            checkpoint: Checkpoint object to save
        """
        checkpoint_file = self.base_dir / ".checkpoint"
        checkpoint.save(str(checkpoint_file))

    def load_checkpoint(self) -> Optional[Checkpoint]:
        """Load checkpoint from .checkpoint file.

        Returns:
            Checkpoint object if file exists, None otherwise
        """
        checkpoint_file = self.base_dir / ".checkpoint"
        if not checkpoint_file.exists():
            return None

        return Checkpoint.load(str(checkpoint_file))

    def delete_checkpoint(self):
        """Delete checkpoint file."""
        checkpoint_file = self.base_dir / ".checkpoint"
        if checkpoint_file.exists():
            checkpoint_file.unlink()

    def list_pages(self, namespace: Optional[str] = None) -> List[Path]:
        """List all markdown pages in storage.

        Args:
            namespace: Optional namespace to filter by

        Returns:
            List of paths to markdown files
        """
        if namespace:
            search_dir = self.base_dir / namespace
            if not search_dir.exists():
                return []
            return list(search_dir.glob("*.md"))
        else:
            return list(self.base_dir.glob("*/*.md"))

    def list_images(self, namespace: Optional[str] = None) -> List[Path]:
        """List all images in storage.

        Args:
            namespace: Optional namespace to filter by

        Returns:
            List of paths to image files
        """
        if namespace:
            images_dir = self.base_dir / namespace / "images"
            if not images_dir.exists():
                return []
            return list(images_dir.glob("*"))
        else:
            return list(self.base_dir.glob("*/images/*"))

    def get_base_path(self) -> Path:
        """Get base directory path.

        Returns:
            Path object for base directory
        """
        return self.base_dir

    def clear_export(self):
        """Delete all exported content (WARNING: destructive operation)."""
        if self.base_dir.exists():
            shutil.rmtree(self.base_dir)
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for filesystem
        """
        # Replace problematic characters
        replacements = {
            '/': '-',
            '\\': '-',
            ':': '-',
            '*': '-',
            '?': '-',
            '"': '',
            '<': '-',
            '>': '-',
            '|': '-'
        }

        sanitized = filename
        for old, new in replacements.items():
            sanitized = sanitized.replace(old, new)

        # Limit length (leave room for extension)
        max_length = 255 - 10
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized
