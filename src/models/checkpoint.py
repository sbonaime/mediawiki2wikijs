"""Checkpoint model for MediaWiki to Wiki.js migration tool.

This module defines the Checkpoint dataclass for storing progress state
to enable resumable operations.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Set, Optional


@dataclass
class Checkpoint:
    """Stores progress state for resumable export/import operations.

    Attributes:
        version: Checkpoint format version (e.g., "1.0")
        operation: "export" or "import"
        timestamp: When checkpoint was created
        pages_processed: Count of pages completed
        images_processed: Count of images completed
        completed_pages: Set of page IDs already processed
        config: Configuration snapshot (URL, depth, etc.)
        current_namespace: Namespace currently being processed
        current_page: Page currently being processed
    """

    version: str
    operation: str
    timestamp: datetime
    pages_processed: int
    images_processed: int
    completed_pages: Set[str]
    config: Dict
    current_namespace: Optional[str] = None
    current_page: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if self.operation not in ("export", "import"):
            raise ValueError("Operation must be 'export' or 'import'")
        if len(self.completed_pages) != self.pages_processed:
            raise ValueError("pages_processed must match length of completed_pages")

    def should_skip(self, page_id: str) -> bool:
        """Check if a page has already been processed.

        Args:
            page_id: MediaWiki page ID to check

        Returns:
            True if page should be skipped (already processed)
        """
        return page_id in self.completed_pages

    def mark_page_processed(self, page_id: str):
        """Mark a page as processed.

        Args:
            page_id: MediaWiki page ID that was processed
        """
        if page_id not in self.completed_pages:
            self.completed_pages.add(page_id)
            self.pages_processed = len(self.completed_pages)
            self.timestamp = datetime.now()

    def mark_image_processed(self):
        """Increment the count of processed images."""
        self.images_processed += 1
        self.timestamp = datetime.now()

    def save(self, filepath: str):
        """Serialize checkpoint to JSON file.

        Args:
            filepath: Path to save checkpoint file (e.g., ".checkpoint")
        """
        checkpoint_data = {
            "version": self.version,
            "operation": self.operation,
            "timestamp": self.timestamp.isoformat(),
            "pages_processed": self.pages_processed,
            "images_processed": self.images_processed,
            "current_namespace": self.current_namespace,
            "current_page": self.current_page,
            "completed_pages": list(self.completed_pages),  # Convert set to list for JSON
            "config": self.config
        }

        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> 'Checkpoint':
        """Deserialize checkpoint from JSON file.

        Args:
            filepath: Path to checkpoint file to load

        Returns:
            Checkpoint object loaded from file

        Raises:
            FileNotFoundError: If checkpoint file doesn't exist
            json.JSONDecodeError: If checkpoint file is corrupted
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert ISO timestamp back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        # Convert list back to set
        data['completed_pages'] = set(data['completed_pages'])

        return cls(**data)

    @classmethod
    def create_new(cls, operation: str, config: Dict) -> 'Checkpoint':
        """Create a new checkpoint for a fresh operation.

        Args:
            operation: "export" or "import"
            config: Configuration snapshot

        Returns:
            New Checkpoint object with initial state
        """
        return cls(
            version="1.0",
            operation=operation,
            timestamp=datetime.now(),
            pages_processed=0,
            images_processed=0,
            completed_pages=set(),
            config=config
        )
