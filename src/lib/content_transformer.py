"""Content transformer for MediaWiki to Wiki.js migration tool.

This module handles content transformation including wikitext to markdown conversion,
link transformation, image reference updates, and category mapping.
"""

import re
import pypandoc
from pathlib import Path
from typing import List, Optional, Dict

from ..models import WikiPage
from .logger import setup_logger


class ContentTransformer:
    """Transforms MediaWiki content to Wiki.js compatible format."""

    def __init__(self, error_callback=None):
        """Initialize content transformer.

        Args:
            error_callback: Optional callback for logging errors (page_title, error_type, message)
        """
        self.logger = setup_logger(__name__)
        self.error_callback = error_callback

        # Check if Pandoc is available
        try:
            pypandoc.get_pandoc_version()
            self.logger.info("Pandoc is available for content conversion")
        except OSError:
            self.logger.error("Pandoc is not installed. Install it from https://pandoc.org/installing.html")
            raise RuntimeError("Pandoc is required but not installed")

    def convert_wikitext_to_markdown(self, wikitext: str, page_title: str = "") -> Optional[str]:
        """Convert MediaWiki wikitext to Markdown format.

        Args:
            wikitext: MediaWiki formatted content
            page_title: Page title for error logging

        Returns:
            Markdown formatted content, or None if conversion fails
        """
        if not wikitext:
            return ""

        try:
            # Convert using pypandoc
            markdown = pypandoc.convert_text(
                wikitext,
                'markdown',
                format='mediawiki',
                extra_args=['--wrap=none']  # Don't wrap lines
            )

            return markdown

        except Exception as e:
            error_msg = f"Pandoc conversion failed: {str(e)}"
            self.logger.error(f"Failed to convert page '{page_title}': {error_msg}")

            if self.error_callback:
                self.error_callback(page_title, 'pandoc_conversion_failed', error_msg)

            return None

    def transform_internal_links(self, content: str) -> str:
        """Transform MediaWiki internal links to Wiki.js format.

        Converts:
        - [[Page Name]] -> [Page Name](/page-name)
        - [[Page Name|Display Text]] -> [Display Text](/page-name)

        Args:
            content: Markdown content with MediaWiki-style links

        Returns:
            Content with Wiki.js formatted links
        """
        # Pattern for [[target|text]] or [[target]]
        pattern = r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

        def replace_link(match):
            target = match.group(1).strip()
            text = match.group(2).strip() if match.group(2) else target

            # Convert target to URL-safe path
            path = self.normalize_page_title(target)

            return f"[{text}](/{path})"

        transformed = re.sub(pattern, replace_link, content)
        return transformed

    def normalize_page_title(self, title: str) -> str:
        """Create URL-safe path from page title.

        Args:
            title: Original page title

        Returns:
            URL-safe path (lowercase, hyphen-separated, no special chars)
        """
        # Convert to lowercase
        normalized = title.lower()

        # Replace spaces and underscores with hyphens
        normalized = normalized.replace(' ', '-').replace('_', '-')

        # Remove or replace special characters (keep alphanumeric and hyphens)
        safe_chars = 'abcdefghijklmnopqrstuvwxyz0123456789-'
        normalized = ''.join(c if c in safe_chars else '-' for c in normalized)

        # Remove consecutive hyphens
        while '--' in normalized:
            normalized = normalized.replace('--', '-')

        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')

        # Limit length to 200 characters
        if len(normalized) > 200:
            normalized = normalized[:200].rstrip('-')

        return normalized or 'page'

    def update_image_references(
        self,
        content: str,
        image_mapping: Dict[str, str]
    ) -> str:
        """Update image references with renamed filenames.

        Converts MediaWiki image syntax to markdown and updates filenames:
        - [[File:Logo.png]] -> ![Logo.png](renamed-logo.png)
        - [[Image:Logo.png|thumb|Caption]] -> ![Caption](renamed-logo.png)

        Args:
            content: Markdown content
            image_mapping: Dict mapping original filename to renamed filename

        Returns:
            Content with updated image references
        """
        # Pattern for MediaWiki image syntax (may still be present after conversion)
        mw_pattern = r'\[\[(?:File|Image):([^\]|]+)(?:\|[^\]]+)?\]\]'

        def replace_mw_image(match):
            original = match.group(1).strip()
            renamed = image_mapping.get(original, original)
            alt_text = Path(original).stem  # Use filename without extension as alt
            return f"![{alt_text}]({renamed})"

        content = re.sub(mw_pattern, replace_mw_image, content)

        # Also update standard markdown image references
        md_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

        def replace_md_image(match):
            alt_text = match.group(1)
            original = match.group(2).strip()

            # Extract just the filename if it's a path
            original_filename = Path(original).name

            # Check if we have a mapping for this image
            renamed = image_mapping.get(original_filename, original)

            return f"![{alt_text}]({renamed})"

        content = re.sub(md_pattern, replace_md_image, content)

        return content

    def map_categories_to_tags(self, categories: List[str]) -> List[str]:
        """Convert MediaWiki categories to Wiki.js tags.

        Args:
            categories: List of category names (without "Category:" prefix)

        Returns:
            List of tag strings (lowercase, hyphen-separated)
        """
        tags = []

        for category in categories:
            # Normalize category name to tag format
            tag = self.normalize_page_title(category)
            tags.append(tag)

        return tags

    def transform_page(
        self,
        page: WikiPage,
        image_mapping: Optional[Dict[str, str]] = None
    ) -> bool:
        """Transform a WikiPage from MediaWiki format to Wiki.js format.

        This is the main transformation method that:
        1. Converts wikitext to markdown
        2. Transforms internal links
        3. Updates image references
        4. Maps categories to tags

        Args:
            page: WikiPage object to transform (modified in-place)
            image_mapping: Optional dict mapping original to renamed image filenames

        Returns:
            True if transformation succeeds, False otherwise
        """
        try:
            # Step 1: Convert wikitext to markdown
            markdown = self.convert_wikitext_to_markdown(page.content, page.title)

            if markdown is None:
                return False

            # Step 2: Transform internal links
            markdown = self.transform_internal_links(markdown)

            # Step 3: Update image references if mapping provided
            if image_mapping:
                markdown = self.update_image_references(markdown, image_mapping)

            # Update page content
            page.content = markdown

            # Step 4: Map categories to tags (stored in categories field)
            if page.categories:
                page.categories = self.map_categories_to_tags(page.categories)

            # Step 5: Generate normalized path for Wiki.js
            page.path = self.normalize_page_title(page.title)

            self.logger.debug(f"Successfully transformed page: {page.title}")
            return True

        except Exception as e:
            error_msg = f"Transformation failed: {str(e)}"
            self.logger.error(f"Failed to transform page '{page.title}': {error_msg}")

            if self.error_callback:
                self.error_callback(page.title, 'transformation_failed', error_msg)

            return False

    def transform_batch(
        self,
        pages: List[WikiPage],
        image_mapping: Optional[Dict[str, str]] = None
    ) -> tuple[int, int]:
        """Transform multiple pages in batch.

        Args:
            pages: List of WikiPage objects to transform
            image_mapping: Optional dict mapping original to renamed image filenames

        Returns:
            Tuple of (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0

        for page in pages:
            if self.transform_page(page, image_mapping):
                success_count += 1
            else:
                failure_count += 1

        self.logger.info(f"Batch transformation complete: {success_count} succeeded, {failure_count} failed")
        return success_count, failure_count
