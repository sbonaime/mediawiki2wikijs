"""Wiki.js GraphQL client for MediaWiki to Wiki.js migration tool.

This module provides a GraphQL client for Wiki.js API interactions,
including page creation, image uploads, and query operations.
"""

from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from typing import List, Dict, Optional, Any
import requests
from pathlib import Path

from ..models import WikiPage, ImageAsset
from .auth_manager import WikiJsAuthManager
from .logger import setup_logger


class WikiJsClient:
    """Client for interacting with Wiki.js GraphQL API."""

    def __init__(self, url: str, api_key: str, timeout_seconds: int = 300):
        """Initialize Wiki.js GraphQL client.

        Args:
            url: Wiki.js base URL (e.g., "https://wiki.example.com")
            api_key: API key for authentication
            timeout_seconds: Authentication timeout threshold (default: 300 = 5 minutes)
        """
        self.url = url.rstrip('/')
        self.graphql_url = f"{self.url}/graphql"
        self.api_key = api_key
        self.auth_manager = WikiJsAuthManager(api_key, timeout_seconds)
        self.logger = setup_logger(__name__)

        # Initialize GraphQL client
        self._init_client()

    def _init_client(self):
        """Initialize or reinitialize GraphQL client with authentication."""
        # Setup transport with authentication header
        transport = RequestsHTTPTransport(
            url=self.graphql_url,
            headers=self.auth_manager.get_auth_header(),
            use_json=True,
            timeout=30
        )

        # Create GraphQL client
        self.client = Client(
            transport=transport,
            fetch_schema_from_transport=False
        )

        self.auth_manager.mark_authenticated()
        self.logger.info(f"GraphQL client initialized for {self.graphql_url}")

    def ensure_authenticated(self):
        """Check authentication status and reconnect if needed.

        Note: Wiki.js API keys don't expire automatically, but we check
        for timeout to detect stale connections.
        """
        if self.auth_manager.is_timed_out():
            self.logger.warning("Authentication timeout detected, reinitializing client...")
            self._init_client()

        self.auth_manager.mark_request()

    def create_page(
        self,
        content: str,
        description: str,
        path: str,
        title: str,
        tags: Optional[List[str]] = None,
        is_published: bool = True,
        is_private: bool = False,
        locale: str = "en",
        editor: str = "markdown"
    ) -> Dict[str, Any]:
        """Create a new page in Wiki.js.

        Args:
            content: Page content (markdown)
            description: Page description
            path: URL path for the page (e.g., "getting-started")
            title: Page title
            tags: List of tags
            is_published: Whether page is published
            is_private: Whether page is private
            locale: Page locale (default: "en")
            editor: Editor type (default: "markdown")

        Returns:
            Response dictionary with 'responseResult' and 'page' fields
        """
        self.ensure_authenticated()

        # Build mutation
        mutation = gql("""
            mutation CreatePage(
                $content: String!
                $description: String!
                $editor: String!
                $isPublished: Boolean!
                $isPrivate: Boolean!
                $locale: String!
                $path: String!
                $tags: [String]!
                $title: String!
            ) {
                pages {
                    create(
                        content: $content
                        description: $description
                        editor: $editor
                        isPublished: $isPublished
                        isPrivate: $isPrivate
                        locale: $locale
                        path: $path
                        tags: $tags
                        title: $title
                    ) {
                        responseResult {
                            succeeded
                            errorCode
                            slug
                            message
                        }
                        page {
                            id
                            path
                            title
                        }
                    }
                }
            }
        """)

        # Prepare variables
        variables = {
            "content": content,
            "description": description or f"Migrated from MediaWiki: {title}",
            "editor": editor,
            "isPublished": is_published,
            "isPrivate": is_private,
            "locale": locale,
            "path": path,
            "tags": tags or [],
            "title": title
        }

        try:
            # Execute mutation
            result = self.client.execute(mutation, variable_values=variables)

            create_result = result['pages']['create']
            response = create_result['responseResult']

            if response['succeeded']:
                self.logger.info(f"Successfully created page: {title} at /{path}")
            else:
                self.logger.warning(f"Page creation failed: {response.get('message', 'Unknown error')}")

            return create_result

        except Exception as e:
            self.logger.error(f"Error creating page '{title}': {e}")
            raise

    def update_page(
        self,
        page_id: int,
        content: str,
        description: str,
        path: str,
        title: str,
        tags: Optional[List[str]] = None,
        is_published: bool = True,
        is_private: bool = False,
        locale: str = "en",
        editor: str = "markdown"
    ) -> Dict[str, Any]:
        """Update an existing page in Wiki.js.

        Args:
            page_id: ID of page to update
            content: Page content (markdown)
            description: Page description
            path: URL path for the page
            title: Page title
            tags: List of tags
            is_published: Whether page is published
            is_private: Whether page is private
            locale: Page locale (default: "en")
            editor: Editor type (default: "markdown")

        Returns:
            Response dictionary with 'responseResult' and 'page' fields
        """
        self.ensure_authenticated()

        # Build mutation
        mutation = gql("""
            mutation UpdatePage(
                $id: Int!
                $content: String!
                $description: String!
                $editor: String!
                $isPublished: Boolean!
                $isPrivate: Boolean!
                $locale: String!
                $path: String!
                $tags: [String]!
                $title: String!
            ) {
                pages {
                    update(
                        id: $id
                        content: $content
                        description: $description
                        editor: $editor
                        isPublished: $isPublished
                        isPrivate: $isPrivate
                        locale: $locale
                        path: $path
                        tags: $tags
                        title: $title
                    ) {
                        responseResult {
                            succeeded
                            errorCode
                            slug
                            message
                        }
                        page {
                            id
                            path
                            title
                        }
                    }
                }
            }
        """)

        # Prepare variables
        variables = {
            "id": page_id,
            "content": content,
            "description": description or f"Updated from MediaWiki: {title}",
            "editor": editor,
            "isPublished": is_published,
            "isPrivate": is_private,
            "locale": locale,
            "path": path,
            "tags": tags or [],
            "title": title
        }

        try:
            result = self.client.execute(mutation, variable_values=variables)

            update_result = result['pages']['update']
            response = update_result['responseResult']

            if response['succeeded']:
                self.logger.info(f"Successfully updated page: {title} at /{path}")
            else:
                self.logger.warning(f"Page update failed: {response.get('message', 'Unknown error')}")

            return update_result

        except Exception as e:
            self.logger.error(f"Error updating page '{title}': {e}")
            raise

    def list_pages(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """List all pages in Wiki.js.

        Args:
            limit: Maximum number of pages to retrieve
            offset: Offset for pagination

        Returns:
            List of page dictionaries with 'id', 'path', 'title' fields
        """
        self.ensure_authenticated()

        # Build query
        query = gql("""
            query ListPages {
                pages {
                    list {
                        id
                        path
                        title
                        locale
                    }
                }
            }
        """)

        try:
            result = self.client.execute(query)
            pages = result['pages']['list']

            self.logger.info(f"Retrieved {len(pages)} pages from Wiki.js")
            return pages

        except Exception as e:
            self.logger.error(f"Error listing pages: {e}")
            raise

    def get_page_by_path(self, path: str, locale: str = "en") -> Optional[Dict[str, Any]]:
        """Get a page by its path.

        Args:
            path: Page path (e.g., "getting-started")
            locale: Page locale (default: "en")

        Returns:
            Page dictionary or None if not found
        """
        self.ensure_authenticated()

        # Build query
        query = gql("""
            query GetPage($path: String!, $locale: String!) {
                pages {
                    single(path: $path, locale: $locale) {
                        id
                        path
                        title
                        content
                    }
                }
            }
        """)

        variables = {
            "path": path,
            "locale": locale
        }

        try:
            result = self.client.execute(query, variable_values=variables)
            page = result['pages']['single']

            if page:
                self.logger.debug(f"Found page at path: {path}")

            return page

        except Exception as e:
            self.logger.debug(f"Page not found at path '{path}': {e}")
            return None

    def upload_asset(
        self,
        file_path: str,
        folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Upload an image/asset to Wiki.js.

        Note: Uses REST API multipart upload, not GraphQL mutation.

        Args:
            file_path: Local path to file to upload
            folder_id: Target folder ID (optional, defaults to root)

        Returns:
            Response dictionary with upload result
        """
        self.ensure_authenticated()

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Prepare multipart upload
        url = f"{self.url}/u"  # Upload endpoint

        with open(file_path_obj, 'rb') as f:
            files = {
                'mediaUpload': (file_path_obj.name, f, 'application/octet-stream')
            }

            data = {}
            if folder_id is not None:
                data['folderId'] = folder_id

            headers = self.auth_manager.get_auth_header()

            try:
                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )

                response.raise_for_status()
                result = response.json()

                if result.get('ok'):
                    self.logger.info(f"Successfully uploaded: {file_path_obj.name}")
                else:
                    self.logger.warning(f"Upload failed: {result.get('error', 'Unknown error')}")

                return result

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error uploading file '{file_path}': {e}")
                raise

    def get_asset_folders(self) -> List[Dict[str, Any]]:
        """Get list of asset folders.

        Returns:
            List of folder dictionaries
        """
        self.ensure_authenticated()

        # Build query
        query = gql("""
            query GetAssetFolders {
                assets {
                    folders {
                        id
                        name
                        slug
                    }
                }
            }
        """)

        try:
            result = self.client.execute(query)
            folders = result['assets']['folders']

            self.logger.info(f"Retrieved {len(folders)} asset folders")
            return folders

        except Exception as e:
            self.logger.error(f"Error getting asset folders: {e}")
            raise
