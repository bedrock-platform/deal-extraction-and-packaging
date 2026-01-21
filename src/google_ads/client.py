"""
Google Authorized Buyers API Client

Implements BaseSSPClient for Google Authorized Buyers internal API.
Wraps the existing APIClient to provide a consistent interface.
"""
import logging
from typing import Dict, List, Any, Optional
import os

from ..common.base_client import BaseSSPClient
from .api_client import APIClient
from .auth import AuthManager

logger = logging.getLogger(__name__)


class GoogleAdsClient(BaseSSPClient):
    """
    Google Authorized Buyers API client implementing BaseSSPClient interface.
    
    Wraps the existing APIClient to provide a consistent interface for the
    multi-vendor orchestrator.
    """
    
    def __init__(self, account_id: Optional[str] = None, api_key: Optional[str] = None, debug: bool = False):
        """
        Initialize Google Ads client.
        
        Args:
            account_id: Google Authorized Buyers account ID (reads from env if None)
            api_key: API key (reads from env if None)
            debug: Enable debug logging
        """
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        self.account_id = account_id or os.getenv('AUTHORIZED_BUYERS_ACCOUNT_ID')
        self.api_key = api_key or os.getenv('AUTHORIZED_BUYERS_API_KEY')
        
        if not self.account_id:
            raise ValueError(
                "AUTHORIZED_BUYERS_ACCOUNT_ID must be provided either as argument or environment variable"
            )
        
        if not self.api_key:
            raise ValueError(
                "AUTHORIZED_BUYERS_API_KEY must be provided either as argument or environment variable"
            )
        
        # Initialize authentication manager
        self.auth_manager = AuthManager()
        
        # Initialize API client
        self.api_client = APIClient(self.account_id, self.api_key, self.auth_manager)
        
        logger.info(f"Initialized Google Ads client for account: {self.account_id}")
    
    def authenticate(self) -> bool:
        """Authenticate with Google Authorized Buyers API."""
        # AuthManager handles authentication automatically
        # Just verify we have valid auth
        return self.auth_manager.get_authenticated_headers() is not None
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        try:
            headers = self.auth_manager.get_authenticated_headers()
            return headers is not None and len(headers) > 0
        except Exception:
            return False
    
    def get_vendor_name(self) -> str:
        """Get vendor name"""
        return "Google Authorized Buyers"
    
    def discover_deals(
        self,
        payload: Optional[Dict] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Discover available deals/packages from Google Authorized Buyers.
        
        Args:
            payload: Optional request payload (filters, etc.)
            **kwargs: Additional parameters (rate_limit_delay, etc.)
            
        Returns:
            List of deal/package dictionaries in Google Ads native format
        """
        rate_limit_delay = kwargs.get('rate_limit_delay', 0.5)
        return self.api_client.fetch_all_inventory(payload, rate_limit_delay)
    
    def discover_google_curated_deals(self, page_size: int = 20) -> List[Dict[str, Any]]:
        """
        Discover Google Curated packages.
        
        Args:
            page_size: Number of packages per page
            
        Returns:
            List of Google Curated package dictionaries
        """
        return self.api_client.fetch_google_curated_packages(page_size)
    
    def hydrate_package_details(self, entity_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch package details for multiple entities.
        
        Args:
            entity_ids: List of entity IDs
            
        Returns:
            Dictionary mapping entity_id -> detail data
        """
        return self.api_client.hydrate_package_details(entity_ids)
