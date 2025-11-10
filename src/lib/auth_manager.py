"""Authentication manager for MediaWiki to Wiki.js migration tool.

This module handles authentication timeout detection and reconnection logic
for both MediaWiki and Wiki.js APIs.
"""

import time
from typing import Optional, Callable
from datetime import datetime, timedelta


class AuthManager:
    """Manages authentication sessions and timeout detection.

    Tracks last request time and automatically triggers reconnection
    when inactivity threshold is exceeded (default: 5 minutes).
    """

    def __init__(self, timeout_seconds: int = 300):
        """Initialize authentication manager.

        Args:
            timeout_seconds: Inactivity timeout in seconds (default: 300 = 5 minutes)
        """
        self.timeout_seconds = timeout_seconds
        self.last_request_time: Optional[datetime] = None
        self.is_authenticated = False
        self.auth_callback: Optional[Callable] = None

    def mark_request(self):
        """Update last request timestamp.

        Call this after every successful API request.
        """
        self.last_request_time = datetime.now()

    def mark_authenticated(self):
        """Mark session as authenticated."""
        self.is_authenticated = True
        self.mark_request()

    def mark_unauthenticated(self):
        """Mark session as unauthenticated."""
        self.is_authenticated = False
        self.last_request_time = None

    def is_timed_out(self) -> bool:
        """Check if authentication session has timed out.

        Returns:
            True if session timed out (exceeded inactivity threshold)
        """
        if not self.is_authenticated:
            return True

        if self.last_request_time is None:
            return True

        elapsed = datetime.now() - self.last_request_time
        return elapsed.total_seconds() > self.timeout_seconds

    def check_and_reconnect(self, reconnect_callback: Callable):
        """Check timeout and trigger reconnection if needed.

        Args:
            reconnect_callback: Function to call for re-authentication
                               Should return True if reconnection succeeds
        """
        if self.is_timed_out():
            if reconnect_callback():
                self.mark_authenticated()
                return True
            else:
                self.mark_unauthenticated()
                return False
        return True

    def seconds_since_last_request(self) -> Optional[float]:
        """Calculate seconds since last request.

        Returns:
            Seconds elapsed since last request, or None if no requests yet
        """
        if self.last_request_time is None:
            return None

        elapsed = datetime.now() - self.last_request_time
        return elapsed.total_seconds()

    def seconds_until_timeout(self) -> Optional[float]:
        """Calculate seconds remaining until timeout.

        Returns:
            Seconds until timeout, or None if no active session
        """
        if not self.is_authenticated or self.last_request_time is None:
            return None

        elapsed = self.seconds_since_last_request()
        if elapsed is None:
            return None

        remaining = self.timeout_seconds - elapsed
        return max(0.0, remaining)


class MediaWikiAuthManager(AuthManager):
    """Authentication manager specifically for MediaWiki sessions."""

    def __init__(self, timeout_seconds: int = 300):
        """Initialize MediaWiki authentication manager.

        Args:
            timeout_seconds: Inactivity timeout in seconds (default: 300 = 5 minutes)
        """
        super().__init__(timeout_seconds)
        self.session_cookies = None

    def store_session(self, cookies):
        """Store session cookies after successful login.

        Args:
            cookies: Session cookies from MediaWiki API
        """
        self.session_cookies = cookies
        self.mark_authenticated()

    def clear_session(self):
        """Clear stored session cookies."""
        self.session_cookies = None
        self.mark_unauthenticated()


class WikiJsAuthManager(AuthManager):
    """Authentication manager specifically for Wiki.js API."""

    def __init__(self, timeout_seconds: int = 300):
        """Initialize Wiki.js authentication manager.

        Args:
            timeout_seconds: Inactivity timeout in seconds (default: 300 = 5 minutes)
        """
        super().__init__(timeout_seconds)
        self.api_key = None

    def store_api_key(self, api_key: str):
        """Store API key for Wiki.js authentication.

        Args:
            api_key: Wiki.js API key
        """
        self.api_key = api_key
        self.mark_authenticated()

    def clear_api_key(self):
        """Clear stored API key."""
        self.api_key = None
        self.mark_unauthenticated()

    def get_auth_header(self) -> dict:
        """Get authentication header for GraphQL requests.

        Returns:
            Dictionary with Authorization header
        """
        if not self.api_key:
            raise ValueError("No API key stored. Cannot generate auth header.")

        return {
            'Authorization': f'Bearer {self.api_key}'
        }
