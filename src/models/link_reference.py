"""LinkReference model for MediaWiki to Wiki.js migration tool.

This module defines the LinkReference dataclass representing a link
from one page to another within the wiki.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LinkType(Enum):
    """Type of wiki link."""
    INTERNAL = "internal"      # Regular wiki page link
    CATEGORY = "category"      # Category membership link
    REDIRECT = "redirect"      # Page redirect


@dataclass
class LinkReference:
    """Represents a link from one page to another.

    Used for BFS traversal during export and link transformation during import.

    Attributes:
        source_page: Title of the page containing the link
        target_page: Title of the page being linked to
        link_type: Type of link (internal, category, redirect)
        depth: Link depth from starting page (for depth limiting)
        anchor_text: Display text of the link (if different from target)
    """

    source_page: str
    target_page: str
    link_type: LinkType
    depth: int
    anchor_text: Optional[str] = None

    def __post_init__(self):
        """Validate required fields."""
        if not self.source_page:
            raise ValueError("Source page cannot be empty")
        if not self.target_page:
            raise ValueError("Target page cannot be empty")
        if self.depth < 0:
            raise ValueError("Link depth must be non-negative")

        # Convert string type to enum if needed
        if isinstance(self.link_type, str):
            self.link_type = LinkType(self.link_type)

    def is_internal(self) -> bool:
        """Check if this is an internal page link."""
        return self.link_type == LinkType.INTERNAL

    def is_category(self) -> bool:
        """Check if this is a category link."""
        return self.link_type == LinkType.CATEGORY

    def is_redirect(self) -> bool:
        """Check if this is a redirect link."""
        return self.link_type == LinkType.REDIRECT
