"""
Google Authorized Buyers Transformer

Transforms Google Authorized Buyers inventory entities to UnifiedPreEnrichmentSchema.
Implements BaseTransformer interface.
"""
import logging
from typing import Dict, Any, List, Tuple, Optional, Union

from ..common.base_transformer import BaseTransformer
from ..common.schema import UnifiedPreEnrichmentSchema, VolumeMetrics
from .data_transform import (
    extract_package_details,
    extract_publisher_info,
    calculate_cpm_metrics,
    get_top_breakdown_slice,
    build_breakdown_json,
)

logger = logging.getLogger(__name__)


class GoogleAdsTransformer(BaseTransformer):
    """
    Transforms Google Authorized Buyers inventory entities to a generic schema.
    
    Google Ads entities have nested forecast/breakdown data, which is different
    from BidSwitch's flat structure. This transformer extracts all available
    data and normalizes it to a consistent format.
    """
    
    def __init__(self, package_id_counter: int = 1000):
        """
        Initialize transformer with package ID counter.
        
        Args:
            package_id_counter: Starting package ID (increments per package created)
        """
        self.package_id_counter = package_id_counter
    
    def get_vendor_name(self) -> str:
        """Get vendor name"""
        return "Google Authorized Buyers"
    
    def validate(self, deal: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that Google Ads entity has required fields.
        
        Args:
            deal: Raw Google Ads entity dictionary
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        required = ["entityId", "entityName"]
        missing = [field for field in required if not deal.get(field)]
        return len(missing) == 0, missing
    
    def transform(
        self,
        deal: Dict[str, Any],
        package_id_start: int = None,
        package_details: Optional[Dict[str, Dict]] = None
    ) -> List[UnifiedPreEnrichmentSchema]:
        """
        Transform Google Ads entity to UnifiedPreEnrichmentSchema.
        
        Google Ads entities contain nested forecast/breakdown data. This method
        extracts all available information and creates a unified schema record.
        
        Args:
            deal: Raw Google Ads entity dictionary
            package_id_start: Starting package ID (if None, uses instance counter)
            package_details: Optional hydrated package details dictionary
            
        Returns:
            List of UnifiedPreEnrichmentSchema instances
        """
        if package_id_start is not None:
            self.package_id_counter = package_id_start
        
        # Validate deal
        is_valid, missing = self.validate(deal)
        if not is_valid:
            logger.warning(f"Skipping invalid deal (missing: {missing}): {deal.get('entityId', 'unknown')}")
            return []
        
        # Extract package details if provided
        entity_id = deal.get("entityId", "")
        pkg_details = {}
        pub_info = {}
        
        if package_details:
            pkg_details = extract_package_details(entity_id, package_details)
            pub_info = extract_publisher_info(deal, package_details.get(entity_id, {}))
        
        # Extract forecast data
        forecast = deal.get("forecast", {})
        metrics = forecast.get("metrics", {})
        total_metrics = forecast.get("totalMetrics", {})
        breakdowns = forecast.get("breakdowns", [])
        
        # Extract top breakdown slices for format inference
        total_impressions = int(metrics.get("impressions", 0))
        request_format_top = get_top_breakdown_slice(breakdowns, "REQUEST_FORMAT", total_impressions)
        
        # Infer format from primary_request_format or breakdowns
        format_value = "display"  # Default
        primary_format = request_format_top.get("name", "").upper() if request_format_top else ""
        if primary_format:
            # Map Google Ads format values to unified format
            format_map = {
                "VIDEO": "video",
                "DISPLAY": "display",
                "NATIVE": "native",
                "AUDIO": "audio",
            }
            format_value = format_map.get(primary_format, "display")
        else:
            # Fallback: check if there's any video breakdown
            for breakdown in breakdowns:
                if breakdown.get("filterType") == "REQUEST_FORMAT":
                    slices = breakdown.get("slices", [])
                    for slice_data in slices:
                        if "VIDEO" in slice_data.get("name", "").upper():
                            format_value = "video"
                            break
        
        # Extract publisher (convert single publisher to list)
        publisher_name = pub_info.get("publisher", "").strip()
        publishers = [publisher_name] if publisher_name else []
        
        # Extract and normalize floor_price (string to float)
        floor_price_str = pkg_details.get("floor_price", "")
        floor_price = 0.0
        if floor_price_str:
            try:
                # Remove currency symbols and whitespace
                cleaned = str(floor_price_str).strip().replace('$', '').replace(',', '').strip()
                floor_price = float(cleaned) if cleaned else 0.0
            except (ValueError, TypeError):
                logger.warning(f"Could not parse floor_price '{floor_price_str}' for deal {entity_id}, using 0.0")
                floor_price = 0.0
        
        # Build volume metrics if available
        volume_metrics = None
        impressions = metrics.get("impressions", "0")
        uniques = metrics.get("uniqueUsers", "0")
        if impressions or uniques:
            try:
                volume_metrics = VolumeMetrics(
                    impressions=int(impressions) if impressions else None,
                    uniques=int(uniques) if uniques else None,
                )
            except (ValueError, TypeError):
                pass  # volume_metrics remains None
        
        # Compute unified inventory_scale (for LLM health scoring)
        inventory_scale = None
        inventory_scale_type = None
        if impressions:
            try:
                inventory_scale = int(impressions)
                inventory_scale_type = "impressions"
            except (ValueError, TypeError):
                pass
        
        # Build unified schema record
        unified_record = UnifiedPreEnrichmentSchema(
            deal_id=str(entity_id),
            deal_name=deal.get("entityName", ""),
            source="Google Authorized Buyers",
            ssp_name="Google Authorized Buyers",
            format=format_value,
            publishers=publishers,
            floor_price=floor_price,
            description=deal.get("description"),
            volume_metrics=volume_metrics,
            inventory_scale=inventory_scale,
            inventory_scale_type=inventory_scale_type,
            raw_deal_data=deal,
        )
        
        return [unified_record]


class GoogleCuratedTransformer(BaseTransformer):
    """
    Transforms Google Curated packages to UnifiedPreEnrichmentSchema.
    
    Google Curated packages have a different structure than Marketplace packages:
    - Uses `externalDealId` instead of `entityId`
    - Has `auctionPackage` wrapper
    - Has `forecastMetrics` instead of `forecast.breakdowns`
    - Has `targeting` array instead of breakdowns
    """
    
    def __init__(self, package_id_counter: int = 2000):
        """
        Initialize transformer with package ID counter.
        
        Args:
            package_id_counter: Starting package ID (increments per package created)
        """
        self.package_id_counter = package_id_counter
    
    def get_vendor_name(self) -> str:
        """Get vendor name"""
        return "Google Curated"
    
    def validate(self, deal: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that Google Curated package has required fields.
        
        Args:
            deal: Raw Google Curated package dictionary
            
        Returns:
            Tuple of (is_valid, missing_fields)
        """
        auction_pkg = deal.get("auctionPackage", {})
        required = ["externalDealId", "name"]
        missing = [field for field in required if not auction_pkg.get(field)]
        return len(missing) == 0, missing
    
    def transform(
        self,
        deal: Dict[str, Any],
        package_id_start: int = None,
        package_details: Optional[Dict[str, Dict]] = None
    ) -> List[UnifiedPreEnrichmentSchema]:
        """
        Transform Google Curated package to UnifiedPreEnrichmentSchema.
        
        Args:
            deal: Raw Google Curated package dictionary (with auctionPackage wrapper)
            package_id_start: Starting package ID (if None, uses instance counter)
            package_details: Optional hydrated package details (not used for Google Curated)
            
        Returns:
            List of UnifiedPreEnrichmentSchema instances
        """
        if package_id_start is not None:
            self.package_id_counter = package_id_start
        
        # Validate deal
        is_valid, missing = self.validate(deal)
        if not is_valid:
            auction_pkg = deal.get("auctionPackage", {})
            deal_id = auction_pkg.get("externalDealId", "unknown")
            logger.warning(f"Skipping invalid Google Curated package (missing: {missing}): {deal_id}")
            return []
        
        auction_pkg = deal.get("auctionPackage", {})
        forecast_metrics = deal.get("forecastMetrics", {})
        targeting = auction_pkg.get("targeting", [])
        
        # Extract deal ID and name
        deal_id = str(auction_pkg.get("externalDealId", ""))
        deal_name = auction_pkg.get("name", "")
        
        # Infer format from contentType (Google Curated doesn't have breakdowns)
        content_type = deal.get("contentType", "").upper()
        format_value = "display"  # Default
        if "VIDEO" in content_type or "CTV" in content_type:
            format_value = "video"
        elif "NATIVE" in content_type:
            format_value = "native"
        elif "AUDIO" in content_type:
            format_value = "audio"
        
        # Extract publishers from targeting (if available)
        publishers = []
        for target in targeting:
            if target.get("targetingType") == "TARGETING_TYPE_PUBLISHER":
                values = target.get("includedValues", [])
                publishers = [v.get("displayName", v.get("id", "")) for v in values]
                break
        
        # Google Curated packages don't have floor price in the list response
        # Would need to fetch detail endpoint for floor price
        floor_price = 0.0
        
        # Build volume metrics from forecastMetrics
        volume_metrics = None
        impressions = forecast_metrics.get("impressions", "0")
        uniques = forecast_metrics.get("uniqueUsers", "0")
        if impressions or uniques:
            try:
                volume_metrics = VolumeMetrics(
                    impressions=int(impressions) if impressions else None,
                    uniques=int(uniques) if uniques else None,
                )
            except (ValueError, TypeError):
                pass  # volume_metrics remains None
        
        # Compute unified inventory_scale (for LLM health scoring)
        inventory_scale = None
        inventory_scale_type = None
        if impressions:
            try:
                inventory_scale = int(impressions)
                inventory_scale_type = "impressions"
            except (ValueError, TypeError):
                pass
        
        # Build unified schema record
        unified_record = UnifiedPreEnrichmentSchema(
            deal_id=deal_id,
            deal_name=deal_name,
            source="Google Curated",
            ssp_name="Google Curated",
            format=format_value,
            publishers=publishers if publishers else [],
            floor_price=floor_price,
            description=auction_pkg.get("description"),
            volume_metrics=volume_metrics,
            inventory_scale=inventory_scale,
            inventory_scale_type=inventory_scale_type,
            raw_deal_data=deal,
        )
        
        return [unified_record]
