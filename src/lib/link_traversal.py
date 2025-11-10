"""Link traversal module for MediaWiki to Wiki.js migration tool.

This module implements BFS (Breadth-First Search) link traversal
with configurable depth limiting.
"""

from collections import deque
from typing import Set, List, Dict, Optional

from ..models import LinkReference, LinkType
from .logger import setup_logger


class LinkTraversal:
    """Manages BFS traversal of wiki page links with depth tracking."""

    def __init__(self, max_depth: int = -1):
        """Initialize link traversal manager.

        Args:
            max_depth: Maximum link depth to follow (-1 = unlimited)
        """
        self.max_depth = max_depth
        self.visited_pages: Set[str] = set()
        self.link_references: List[LinkReference] = []
        self.logger = setup_logger(__name__)

    def should_follow_link(self, page_title: str, current_depth: int) -> bool:
        """Check if a link should be followed.

        Args:
            page_title: Title of linked page
            current_depth: Current traversal depth

        Returns:
            True if link should be followed, False otherwise
        """
        # Check if already visited
        if page_title in self.visited_pages:
            return False

        # Check depth limit
        if self.max_depth >= 0 and current_depth >= self.max_depth:
            return False

        return True

    def add_link(self, source_page: str, target_page: str, link_type: LinkType, depth: int, anchor_text: Optional[str] = None):
        """Add a link reference to the collection.

        Args:
            source_page: Title of page containing the link
            target_page: Title of page being linked to
            link_type: Type of link (internal, category, redirect)
            depth: Link depth from starting page
            anchor_text: Display text of the link
        """
        link_ref = LinkReference(
            source_page=source_page,
            target_page=target_page,
            link_type=link_type,
            depth=depth,
            anchor_text=anchor_text
        )

        self.link_references.append(link_ref)

    def mark_visited(self, page_title: str):
        """Mark a page as visited.

        Args:
            page_title: Page title to mark
        """
        self.visited_pages.add(page_title)

    def get_pages_to_process(self, start_page: str, get_links_callback) -> List[Dict]:
        """Perform BFS traversal to collect pages to process.

        Args:
            start_page: Starting page title
            get_links_callback: Function to get links from a page
                               Should accept (page_title) and return List[str]

        Returns:
            List of dictionaries with 'title' and 'depth' for each page
        """
        self.logger.info(f"Starting BFS traversal from: {start_page}")
        if self.max_depth >= 0:
            self.logger.info(f"Maximum link depth: {self.max_depth}")
        else:
            self.logger.info("Maximum link depth: unlimited")

        # Queue of (page_title, depth) tuples
        queue = deque([(start_page, 0)])
        self.mark_visited(start_page)

        pages_to_process = [{'title': start_page, 'depth': 0}]

        while queue:
            current_page, current_depth = queue.popleft()

            # Check if we should continue traversing
            next_depth = current_depth + 1
            if self.max_depth >= 0 and next_depth > self.max_depth:
                continue

            # Get links from current page
            try:
                links = get_links_callback(current_page)
            except Exception as e:
                self.logger.error(f"Error getting links from '{current_page}': {e}")
                continue

            # Process each link
            for link in links:
                if self.should_follow_link(link, next_depth):
                    # Add to queue for processing
                    queue.append((link, next_depth))
                    self.mark_visited(link)
                    pages_to_process.append({'title': link, 'depth': next_depth})

                    # Record link reference
                    self.add_link(
                        source_page=current_page,
                        target_page=link,
                        link_type=LinkType.INTERNAL,
                        depth=next_depth
                    )

            self.logger.debug(f"Processed '{current_page}' at depth {current_depth}, found {len(links)} links")

        self.logger.info(f"BFS traversal complete. Found {len(pages_to_process)} pages to process")
        return pages_to_process

    def get_link_references(self) -> List[LinkReference]:
        """Get all collected link references.

        Returns:
            List of LinkReference objects
        """
        return self.link_references

    def get_visited_pages(self) -> Set[str]:
        """Get set of all visited page titles.

        Returns:
            Set of page titles that were visited
        """
        return self.visited_pages

    def reset(self):
        """Reset traversal state for a new traversal."""
        self.visited_pages.clear()
        self.link_references.clear()
