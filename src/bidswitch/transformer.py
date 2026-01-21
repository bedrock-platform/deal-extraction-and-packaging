"""
BidSwitch Transformer

Transforms BidSwitch API deal objects to UnifiedPreEnrichmentSchema.
This transformer normalizes BidSwitch deals to the unified schema.

Note: BidSwitch API returns a flat structure (not nested).
Fields like creative_type and bid_requests are at the top level.
"""
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import json

from ..common.base_transformer import BaseTransformer
from ..common.schema import UnifiedPreEnrichmentSchema, VolumeMetrics


# SSP ID to Name mapping
SSP_MAP = {
    7: "Sovrn",
    52: "Sonobi",
    6: "OpenX",
    1: "Magnite",
    255: "Commerce Grid",
    68: "Nexxen",
}

# Inventory type mapping (BidSwitch → numeric IDs)
INVENTORY_TYPE_MAP = {
    "applications": 1,  # Applications
    "app": 1,
    "websites": 2,  # Websites
    "website": 2,
    "web": 2,
    "ctv": 3,  # CTV
    "dooh": 4,  # DOOH
}

# Creative type mapping (BidSwitch → standard enum values)
CREATIVE_TYPE_MAP = {
    "display": "banner",
    "banner": "banner",
    "video": "video",
    "native": "native",
    "audio": "audio",
}

# Device type mapping (BidSwitch → standard enum values)
DEVICE_TYPE_MAP = {
    "phone": "Mobile",
    "tablet": "Tablet",
    "pc": "PC",
    "desktop": "PC",
    "ctv": "CTV",
    "mediacenter": "MediaCenter",
}


class BidSwitchTransformer(BaseTransformer):
    """
    Transforms BidSwitch deals to a generic schema.
    
    This transformer extracts all available data from BidSwitch deals and
    returns it in a structured format. You can customize the output schema
    by overriding the transform() method or modifying _create_package().
    
    Note: BidSwitch API returns a flat structure (not nested).
    Fields like creative_type and bid_requests are at the top level.
    """
    
    def __init__(self, package_id_counter: int = 3000):
        """
        Initialize transformer with package ID counter.
        
        Args:
            package_id_counter: Starting package ID (increments per package created)
        """
        self.package_id_counter = package_id_counter
    
    def get_vendor_name(self) -> str:
        """Get vendor name"""
        return "BidSwitch"
    
    def validate(self, deal: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that BidSwitch deal has required fields.
        
        Args:
            deal: Raw BidSwitch deal dictionary
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        required = ["deal_id", "display_name"]
        missing = [field for field in required if not deal.get(field)]
        return len(missing) == 0, missing
    
    def _calculate_days_between(self, start_time: Optional[str], end_time: Optional[str]) -> Optional[float]:
        """
        Calculate days between start_time and end_time.
        
        Args:
            start_time: ISO datetime string
            end_time: ISO datetime string
            
        Returns:
            Number of days as float, or None if invalid
        """
        if not start_time or not end_time:
            return None
        
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            delta = end - start
            days = delta.total_seconds() / 86400
            return days if days > 0 else None
        except (ValueError, AttributeError):
            return None
    
    def _parse_price(self, price_str: Optional[str]) -> Optional[float]:
        """
        Parse price string to float.
        
        Args:
            price_str: Price as decimal string (e.g., "10.50")
            
        Returns:
            Price as float, or None if invalid
        """
        if not price_str:
            return None
        try:
            return float(price_str)
        except (ValueError, TypeError):
            return None
    
    def transform(self, deal: Dict[str, Any], package_id_start: int = None) -> List[UnifiedPreEnrichmentSchema]:
        """
        Transform BidSwitch deal to UnifiedPreEnrichmentSchema.
        
        Note: BidSwitch API uses flat structure. No nested forecasting/inventory objects.
        
        Args:
            deal: Raw BidSwitch deal dictionary (flat structure)
            package_id_start: Starting package ID (if None, uses instance counter)
            
        Returns:
            List of UnifiedPreEnrichmentSchema instances
        """
        if package_id_start is not None:
            self.package_id_counter = package_id_start
        
        # Validate deal
        is_valid, missing = self.validate(deal)
        if not is_valid:
            return []
        
        # Extract core fields
        deal_id = deal.get("deal_id")
        display_name = deal.get("display_name", "")
        description = deal.get("description")
        start_time = deal.get("start_time")
        end_time = deal.get("end_time")
        publishers = deal.get("publishers", [])
        price_str = deal.get("price")
        bid_requests = deal.get("bid_requests")
        weekly_total_avails = deal.get("weekly_total_avails")
        ssp_id = deal.get("ssp_id")
        
        # Map SSP ID to name
        ssp_name = SSP_MAP.get(ssp_id, f"SSP_{ssp_id}" if ssp_id else "BidSwitch")
        
        # Normalize format from creative_type
        creative_type_raw = deal.get("creative_type", "")
        creative_type_enum = CREATIVE_TYPE_MAP.get(creative_type_raw.lower(), "banner")
        # Map banner -> display for unified schema
        format_value = "display" if creative_type_enum == "banner" else creative_type_enum
        
        # Infer inventory type from deal metadata
        inventory_highlights = deal.get("inventory_highlights", [])
        inventory_highlights_str = " ".join(str(h).lower() for h in inventory_highlights)
        creative_type_lower = creative_type_raw.lower()
        
        inventory_type = None
        if "ctv" in inventory_highlights_str or "connected tv" in inventory_highlights_str:
            inventory_type = 3  # CTV
        elif creative_type_lower == "video" and ("ctv" in display_name.lower()):
            inventory_type = 3  # CTV
        elif creative_type_lower == "video":
            inventory_type = 3  # CTV (default for video)
        else:
            inventory_type = 2  # Websites (default)
        
        # Parse floor_price
        floor_price = 0.0
        if price_str:
            price_numeric = self._parse_price(price_str)
            if price_numeric is not None:
                floor_price = price_numeric
        
        # Build volume metrics
        volume_metrics = None
        days = self._calculate_days_between(start_time, end_time)
        bid_requests_ratio = None
        if days and bid_requests:
            bid_requests_ratio = bid_requests / days
        
        if bid_requests is not None or bid_requests_ratio is not None:
            volume_metrics = VolumeMetrics(
                bid_requests=int(bid_requests) if bid_requests else None,
                bid_requests_ratio=bid_requests_ratio,
            )
        
        # Compute unified inventory_scale (for LLM health scoring)
        # Prefer weekly_total_avails if available and > 0, otherwise use bid_requests
        inventory_scale = None
        inventory_scale_type = None
        if weekly_total_avails and weekly_total_avails > 0:
            try:
                inventory_scale = int(weekly_total_avails)
                inventory_scale_type = "bid_requests"  # weekly_total_avails is also bid requests
            except (ValueError, TypeError):
                pass
        
        if inventory_scale is None and bid_requests:
            try:
                inventory_scale = int(bid_requests)
                inventory_scale_type = "bid_requests"
            except (ValueError, TypeError):
                pass
        
        # Normalize publishers to list
        if isinstance(publishers, str):
            publishers = [p.strip() for p in publishers.split(',') if p.strip()]
        elif not isinstance(publishers, list):
            publishers = []
        
        # Create unified schema record
        unified_record = UnifiedPreEnrichmentSchema(
            deal_id=str(deal_id),
            deal_name=display_name,
            source="BidSwitch",
            ssp_name=ssp_name,
            format=format_value,
            publishers=publishers,
            floor_price=floor_price,
            inventory_type=inventory_type,
            start_time=start_time,
            end_time=end_time,
            description=description,
            volume_metrics=volume_metrics,
            inventory_scale=inventory_scale,
            inventory_scale_type=inventory_scale_type,
            raw_deal_data=deal,
        )
        
        return [unified_record]
    
    def _create_record(
        self,
        deal: Dict[str, Any],
        inventory_type_id: int,
        creative_type_enum: str
    ) -> Optional[Dict[str, Any]]:
        """
        Create a single transformed record from BidSwitch deal.
        
        This method extracts all available data from the BidSwitch deal.
        Customize this method to match your target database schema.
        
        Args:
            deal: Raw BidSwitch deal dictionary
            inventory_type_id: Inventory type ID (1=Applications, 2=Websites, 3=CTV, 4=DOOH)
            creative_type_enum: Creative type enum value ("banner", "video", "native", "audio")
            
        Returns:
            Transformed dictionary ready for database insertion, or None if invalid
        """
        # Extract core fields from top level (flat structure)
        deal_id = deal.get("deal_id")
        display_name = deal.get("display_name")
        description = deal.get("description")
        start_time = deal.get("start_time")
        end_time = deal.get("end_time")
        publishers = deal.get("publishers", [])
        auction_type = deal.get("auction_type")
        inventory_highlights = deal.get("inventory_highlights", [])
        ssp_id = deal.get("ssp_id")
        price_str = deal.get("price")
        bid_requests = deal.get("bid_requests")
        
        # Calculate bidRequestsRatio
        days = self._calculate_days_between(start_time, end_time)
        bid_requests_ratio = None
        if days and bid_requests:
            bid_requests_ratio = bid_requests / days
        
        # Map price
        price_numeric = self._parse_price(price_str)
        
        # Map SSP name
        ssp_name = SSP_MAP.get(ssp_id, str(ssp_id) if ssp_id else None)
        
        # Build transformed record
        # NOTE: Customize this structure to match your database schema
        record = {
            # Core identity
            "deal_id": deal_id,
            "name": display_name,
            "description": description,
            
            # Inventory & Creative
            "inventory_type": inventory_type_id,
            "creative_type": creative_type_enum,
            
            # Temporal
            "start_time": start_time,
            "end_time": end_time,
            
            # Publishers
            "publishers": publishers if isinstance(publishers, list) else [],
            
            # Pricing
            "price": price_numeric,
            "floor_price": price_numeric,  # BidSwitch uses single price field
            
            # Auction
            "auction_type": auction_type,
            
            # Inventory metadata
            "inventory_highlights": inventory_highlights,
            "ssp_id": ssp_id,
            "ssp_name": ssp_name,
            
            # Volume metrics
            "bid_requests": bid_requests,
            "bid_requests_ratio": bid_requests_ratio,
            
            # Raw data (for reference)
            "raw_deal_data": deal,
        }
        
        return record
