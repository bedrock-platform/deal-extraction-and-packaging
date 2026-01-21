"""
Base Transformer Interface

Abstract base class for vendor-specific transformers.
All transformers convert vendor deal formats to UnifiedPreEnrichmentSchema.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

from .schema import UnifiedPreEnrichmentSchema


class BaseTransformer(ABC):
    """
    Abstract base class for vendor-specific transformers.
    
    All vendor transformers (BidSwitch, Google Ads, IndexExchange, etc.) should
    implement this interface to convert vendor deals to UnifiedPreEnrichmentSchema.
    """
    
    @abstractmethod
    def transform(self, deal: Dict[str, Any], package_id_start: int = 3000) -> List[UnifiedPreEnrichmentSchema]:
        """
        Transform a vendor deal to one or more UnifiedPreEnrichmentSchema records.
        
        Some deals may need to be split into multiple records based on
        inventory types or creative types (see splitting rules).
        
        Args:
            deal: Raw deal dictionary from vendor API
            package_id_start: Starting ID for record ID generation (default: 3000)
            
        Returns:
            List of UnifiedPreEnrichmentSchema instances
        """
        pass
    
    @abstractmethod
    def validate(self, deal: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that vendor deal has required fields.
        
        Args:
            deal: Raw vendor deal dictionary
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        pass
    
    @abstractmethod
    def get_vendor_name(self) -> str:
        """
        Get the vendor name this transformer handles.
        
        Returns:
            Vendor name string (e.g., "BidSwitch", "Google Authorized Buyers")
        """
        pass
