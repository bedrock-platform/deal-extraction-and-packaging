"""
Authentication module for Google Authorized Buyers API.

Handles SAPISIDHASH and Bearer token authentication methods.
"""

import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages authentication for Google Authorized Buyers API."""
    
    def __init__(self):
        """Initialize authentication manager with credentials from environment."""
        self.sapisidhash = os.getenv('AUTHORIZED_BUYERS_SAPISIDHASH')
        self.cookies = os.getenv('AUTHORIZED_BUYERS_COOKIES')
        self.bearer_token = os.getenv('AUTHORIZED_BUYERS_BEARER_TOKEN')
        self.user_agent = os.getenv(
            'AUTHORIZED_BUYERS_USER_AGENT',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
        )
        self.auth_user = os.getenv('AUTHORIZED_BUYERS_AUTH_USER', '0')
        self.origin = os.getenv('AUTHORIZED_BUYERS_ORIGIN', 'https://realtimebidding.google.com')
        self.referer = os.getenv('AUTHORIZED_BUYERS_REFERER', 'https://realtimebidding.google.com/')
        
        # Initialize authentication method
        self.auth_method = self._initialize_authentication()
        
        # Setup cookies if provided
        self.cookies_dict = None
        if self.cookies:
            self.cookies_dict = {}
            for cookie_pair in self.cookies.split('; '):
                if '=' in cookie_pair:
                    key, value = cookie_pair.split('=', 1)
                    self.cookies_dict[key.strip()] = value.strip()
    
    def _initialize_authentication(self) -> str:
        """
        Initialize authentication method based on available credentials.
        
        Returns:
            String describing the authentication method used
            
        Raises:
            ValueError: If no valid authentication method is configured
        """
        # Priority 1: SAPISIDHASH
        if self.sapisidhash:
            if not self.cookies:
                raise ValueError(
                    "AUTHORIZED_BUYERS_SAPISIDHASH provided but AUTHORIZED_BUYERS_COOKIES is missing. "
                    "Both are required for SAPISIDHASH authentication."
                )
            logger.info("Using SAPISIDHASH authentication (manual)")
            return "SAPISIDHASH"
        
        # Priority 2: Bearer Token
        if self.bearer_token:
            logger.info("Using Bearer token authentication")
            return "Bearer Token"
        
        # No valid authentication method found
        raise ValueError(
            "No valid authentication method configured. Please set one of:\n"
            "  - AUTHORIZED_BUYERS_SAPISIDHASH + AUTHORIZED_BUYERS_COOKIES\n"
            "  - AUTHORIZED_BUYERS_BEARER_TOKEN"
        )
    
    def get_base_headers(self) -> Dict[str, str]:
        """
        Get base headers for API requests (without authentication).
        
        Returns:
            Dictionary of base headers
        """
        return {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Origin": self.origin,
            "Referer": self.referer,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-GB",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "x-goog-authuser": self.auth_user,
            "x-goog-adx-buyer-impersonation": "su=false",
        }
    
    def get_authenticated_headers(self) -> Dict[str, str]:
        """
        Get headers with current authentication token.
        
        Returns:
            Dictionary of headers with Authorization header set
        """
        headers = self.get_base_headers()
        
        if self.auth_method == "SAPISIDHASH":
            # Clean SAPISIDHASH (remove 'SAPISIDHASH ' prefix if present)
            sapisidhash = self.sapisidhash
            if sapisidhash.startswith('SAPISIDHASH '):
                sapisidhash = sapisidhash[12:]
            headers["Authorization"] = f"SAPISIDHASH {sapisidhash}"
            
            # Add cookies as Cookie header (browser sends cookies as header, not parameter)
            if self.cookies:
                headers["Cookie"] = self.cookies
            
        elif self.auth_method == "Bearer Token":
            # Clean bearer token (remove 'Bearer ' prefix if present)
            bearer_token = self.bearer_token
            if bearer_token.startswith('Bearer '):
                bearer_token = bearer_token[7:]
            headers["Authorization"] = f"Bearer {bearer_token}"
        
        return headers
