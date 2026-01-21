"""
Base Client Interface

Abstract base class for SSP API clients.
All vendor-specific clients should inherit from this.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseSSPClient(ABC):
    """
    Abstract base class for SSP API clients.
    
    All vendor-specific clients (BidSwitch, Google Ads, IndexExchange, etc.) should
    implement this interface for consistent usage across the pipeline.
    """
    
    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the SSP API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_authenticated(self) -> bool:
        """
        Check if client is currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        pass
    
    @abstractmethod
    def discover_deals(
        self,
        **filters
    ) -> List[Dict[str, Any]]:
        """
        Discover available deals/packages from the SSP.
        
        Args:
            **filters: Vendor-specific filter parameters
            
        Returns:
            List of deal/package dictionaries in vendor's native format
        """
        pass
    
    @abstractmethod
    def get_vendor_name(self) -> str:
        """
        Get the vendor name (e.g., "BidSwitch", "Google Authorized Buyers").
        
        Returns:
            Vendor name string
        """
        pass
