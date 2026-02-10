"""MediaWiki API client for MediaWiki to Wiki.js migration tool.

This module provides a wrapper around mwclient for MediaWiki API interactions,
including authentication, page listing, content retrieval, and image downloads.
"""

import mwclient
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse

from ..models import WikiPage, ImageAsset, LinkReference, LinkType, DownloadStatus
from .auth_manager import MediaWikiAuthManager
from .logger import setup_logger


class MediaWikiClient:
    """Client for interacting with MediaWiki API.

    Wraps mwclient library with authentication management and
    support for MediaWiki 1.13.5+.
    """

    def __init__(self, url: str, username: str = '', password: str = '', timeout_seconds: int = 300, verify_ssl: bool = True):
        """Initialize MediaWiki client.

        Args:
            url: MediaWiki site URL (e.g., "https://wiki.example.com")
            username: Bot or admin username (optional, for private wikis)
            password: User password (optional, for private wikis)
            timeout_seconds: Authentication timeout threshold (default: 300 = 5 minutes)
            verify_ssl: Verify SSL certificates (default: True, set to False for self-signed certs)
        """
        self.url = url
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.auth_manager = MediaWikiAuthManager(timeout_seconds)
        self.site: Optional[mwclient.Site] = None
        self.logger = setup_logger(__name__)
        self.is_authenticated = False

        # Parse URL to get host and path
        parsed = urlparse(url)
        self.host = parsed.netloc
        self.path = parsed.path.rstrip('/') + '/'
        self.scheme = parsed.scheme

    def login(self) -> bool:
        """Authenticate with MediaWiki API.

        Returns:
            True if connection succeeds, False otherwise
        """
        try:
            self.logger.info(f"Connecting to MediaWiki at {self.url}")
            
            # Prepare connection options for SSL if needed
            ssl_adapter = None
            connection_options = {}
            if not self.verify_ssl:
                self.logger.warning("SSL certificate verification is DISABLED")
                # Disable SSL warnings
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                import ssl
                from requests.adapters import HTTPAdapter
                from urllib3.util.ssl_ import create_urllib3_context
                
                # Create custom SSL adapter that allows legacy TLS and disables verification
                class LegacySSLAdapter(HTTPAdapter):
                    def init_poolmanager(self, *args, **kwargs):
                        # Create a very permissive SSL context
                        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                        context.check_hostname = False
                        context.verify_mode = ssl.CERT_NONE
                        # Set very permissive ciphers including weak/legacy ones
                        context.set_ciphers('DEFAULT:@SECLEVEL=0')
                        kwargs['ssl_context'] = context
                        return super().init_poolmanager(*args, **kwargs)
                
                ssl_adapter = LegacySSLAdapter()
                # Pass verify=False to disable SSL verification in requests
                connection_options['verify'] = False

            # Create site connection without initializing (do_init=False)
            self.site = mwclient.Site(
                self.host,
                path=self.path,
                scheme=self.scheme,
                connection_options=connection_options if connection_options else None,
                do_init=False,  # Don't connect yet
                force_login=False  # Don't force version check
            )
            
            # If we have a custom SSL adapter, mount it before initializing
            if ssl_adapter:
                self.site.connection.mount('https://', ssl_adapter)
            
            # Now initialize the connection (may fail on old MediaWiki versions)
            try:
                self.site.site_init()
            except mwclient.errors.MediaWikiVersionError as e:
                # Handle old MediaWiki versions (< 1.16)
                self.logger.warning(f"MediaWiki version check failed: {e}")
                self.logger.warning("Attempting to connect anyway (legacy version support)")
                # Manually set version to bypass check
                self.site.initialized = True

            # Login with credentials if provided
            if self.username and self.password:
                self.logger.info(f"Logging in as user: {self.username}")
                self.site.login(self.username, self.password)
                self.auth_manager.store_session(self.site)
                self.is_authenticated = True
                self.logger.info("Successfully authenticated with MediaWiki")
            else:
                self.logger.info("Connecting anonymously (no credentials provided)")
                self.is_authenticated = False

            return True

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            self.auth_manager.clear_session()
            return False

    def ensure_authenticated(self):
        """Check authentication status and reconnect if needed.

        Raises:
            RuntimeError: If reconnection fails
        """
        if self.is_authenticated and self.auth_manager.is_timed_out():
            self.logger.warning("Authentication timeout detected, reconnecting...")
            if not self.login():
                raise RuntimeError("Failed to reconnect to MediaWiki")

        # Update last request time if authenticated
        if self.is_authenticated:
            self.auth_manager.mark_request()

    def list_all_pages(self, namespaces: Optional[List[int]] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve list of all pages from specified namespaces.

        Args:
            namespaces: List of namespace IDs to query (default: [0] for Main)
            limit: Maximum number of pages to retrieve (default: unlimited)

        Returns:
            List of page dictionaries with 'pageid', 'title', 'ns' fields
        """
        self.ensure_authenticated()

        if namespaces is None:
            namespaces = [0]  # Default to Main namespace

        self.logger.info(f"Listing pages from namespaces: {namespaces}")

        pages = []
        for ns in namespaces:
            self.logger.debug(f"Querying namespace {ns}")

            # Use allpages query
            for page in self.site.allpages(namespace=ns):
                pages.append({
                    'pageid': page.pageid,
                    'title': page.name,
                    'ns': ns
                })

                if limit and len(pages) >= limit:
                    break

            if limit and len(pages) >= limit:
                break

        self.logger.info(f"Found {len(pages)} pages")
        return pages

    def get_page_content(self, page_title: str) -> Optional[WikiPage]:
        """Fetch page content and metadata.

        Args:
            page_title: Page title to retrieve

        Returns:
            WikiPage object with content and metadata, or None if page not found
        """
        self.ensure_authenticated()

        try:
            page = self.site.pages[page_title]

            # Check if page exists (may not work on old MediaWiki versions)
            try:
                if not page.exists:
                    self.logger.warning(f"Page does not exist: {page_title}")
                    return None
            except (AttributeError, TypeError):
                # page.exists may not work on old MediaWiki - try to get text instead
                pass

            # Get page text (wikitext)
            text = page.text()

            # Get revision info
            revisions = list(page.revisions(limit=1, prop='timestamp|user|ids'))
            if revisions:
                rev = revisions[0]
                created_at = rev.get('timestamp')
                author = rev.get('user')
                revision_id = str(rev.get('revid', ''))
            else:
                created_at = None
                author = None
                revision_id = None

            # Build page URL
            page_url = f"{self.url}/wiki/{page_title.replace(' ', '_')}"

            # Get namespace
            namespace = self._get_namespace_name(page.namespace)

            wiki_page = WikiPage(
                id=str(page.pageid),
                title=page_title,
                namespace=namespace,
                content=text or "",
                url=page_url,
                revision_id=revision_id,
                author=author,
                created_at=created_at
            )

            return wiki_page

        except Exception as e:
            self.logger.error(f"Error fetching page '{page_title}': {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return None

    def get_page_links(self, page_title: str) -> List[str]:
        """Fetch internal links from a page.

        Args:
            page_title: Page title to get links from

        Returns:
            List of linked page titles
        """
        self.ensure_authenticated()

        try:
            page = self.site.pages[page_title]

            if not page.exists:
                return []

            # Get all links
            links = []
            for link in page.links():
                links.append(link.name)

            return links

        except Exception as e:
            self.logger.error(f"Error fetching links for '{page_title}': {e}")
            return []

    def get_page_categories(self, page_title: str) -> List[str]:
        """Fetch category memberships for a page.

        Args:
            page_title: Page title to get categories from

        Returns:
            List of category names (without "Category:" prefix)
        """
        self.ensure_authenticated()

        try:
            page = self.site.pages[page_title]

            if not page.exists:
                return []

            # Get categories
            categories = []
            for category in page.categories():
                # Remove "Category:" prefix
                cat_name = category.name
                if cat_name.startswith("Category:"):
                    cat_name = cat_name[9:]
                categories.append(cat_name)

            return categories

        except Exception as e:
            self.logger.error(f"Error fetching categories for '{page_title}': {e}")
            return []

    def get_page_images(self, page_title: str) -> List[str]:
        """Fetch image references from a page.

        Args:
            page_title: Page title to get images from

        Returns:
            List of image filenames (with "File:" or "Image:" prefix)
        """
        self.ensure_authenticated()

        try:
            page = self.site.pages[page_title]

            if not page.exists:
                return []

            # Get images
            images = []
            for image in page.images():
                images.append(image.name)

            return images

        except Exception as e:
            self.logger.error(f"Error fetching images for '{page_title}': {e}")
            return []

    def get_image_info(self, image_filename: str) -> Optional[ImageAsset]:
        """Fetch image download URL and metadata.

        Args:
            image_filename: Image filename (e.g., "File:Logo.png")

        Returns:
            ImageAsset object with URL and metadata, or None if not found
        """
        self.ensure_authenticated()

        try:
            # Ensure filename has File: prefix
            if not image_filename.startswith(('File:', 'Image:')):
                image_filename = f"File:{image_filename}"

            image = self.site.images[image_filename]

            if not image.exists:
                self.logger.warning(f"Image does not exist: {image_filename}")
                return None

            # Get image info
            image_info = image.imageinfo

            # Extract URL
            url = image_info.get('url', '')
            if not url:
                self.logger.warning(f"No URL found for image: {image_filename}")
                return None

            # Extract metadata
            size = image_info.get('size', 0)
            mime = image_info.get('mime', '')

            # Remove prefix from filename
            original_filename = image_filename
            if ':' in original_filename:
                original_filename = original_filename.split(':', 1)[1]

            image_asset = ImageAsset(
                original_filename=original_filename,
                url=url,
                page_references=[],  # Will be populated by caller
                download_status=DownloadStatus.PENDING,
                content_type=mime,
                size_bytes=size
            )

            return image_asset

        except Exception as e:
            self.logger.error(f"Error fetching image info for '{image_filename}': {e}")
            return None

    def _get_namespace_name(self, namespace_id: int) -> str:
        """Convert namespace ID to name.

        Args:
            namespace_id: Namespace numeric ID

        Returns:
            Namespace name (e.g., "Main", "User", "Help")
        """
        namespace_map = {
            0: "Main",
            1: "Talk",
            2: "User",
            3: "User talk",
            4: "Project",
            5: "Project talk",
            6: "File",
            7: "File talk",
            8: "MediaWiki",
            9: "MediaWiki talk",
            10: "Template",
            11: "Template talk",
            12: "Help",
            13: "Help talk",
            14: "Category",
            15: "Category talk"
        }

        return namespace_map.get(namespace_id, f"Namespace{namespace_id}")
