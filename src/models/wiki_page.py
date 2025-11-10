"""WikiPage model for MediaWiki to Wiki.js migration tool.

This module defines the WikiPage dataclass representing a single wiki page
with all its content, metadata, and relationships.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class WikiPage:
    """Represents a single wiki page with content and metadata.

    Attributes:
        id: MediaWiki page ID (unique identifier)
        title: Page title as it appears in MediaWiki
        namespace: MediaWiki namespace (e.g., "Main", "User", "Help")
        content: Raw page content (wikitext for export, markdown after transformation)
        categories: List of category names the page belongs to
        links: List of page titles this page links to
        images: List of image filenames referenced in the page
        url: Full URL to the page in MediaWiki
        created_at: Page creation timestamp
        modified_at: Last modification timestamp
        author: Last contributor username
        revision_id: MediaWiki revision ID
        path: Local filesystem path (relative) after export
        wikijs_id: Wiki.js page ID after import
    """

    id: str
    title: str
    namespace: str
    content: str
    url: str
    categories: List[str] = field(default_factory=list)
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    author: Optional[str] = None
    revision_id: Optional[str] = None
    path: Optional[str] = None
    wikijs_id: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.title:
            raise ValueError("Page title cannot be empty")
        if not self.url:
            raise ValueError("Page URL cannot be empty")
        if self.content is None:
            raise ValueError("Page content cannot be None (use empty string for empty pages)")

    def is_exported(self) -> bool:
        """Check if page has been exported from MediaWiki."""
        return bool(self.content and self.id)

    def is_transformed(self) -> bool:
        """Check if page content has been transformed to markdown."""
        # Heuristic: markdown has been converted if path is set
        return bool(self.path)

    def is_imported(self) -> bool:
        """Check if page has been imported to Wiki.js."""
        return bool(self.wikijs_id)
