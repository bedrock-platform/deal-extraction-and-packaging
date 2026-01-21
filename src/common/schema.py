"""
Unified Schema Definitions

This module defines the unified schemas for deal data throughout the enrichment pipeline:
- UnifiedPreEnrichmentSchema: Normalized schema for all deals before Stage 1 enrichment
- EnrichedDeal: Schema for deals after Stage 1 enrichment (with semantic metadata)

These schemas ensure data consistency across vendors and stages.
"""
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

try:
    from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
except ImportError:
    raise ImportError(
        "pydantic is required. Install with: pip install pydantic"
    )


class FormatEnum(str, Enum):
    """Valid format values for deals."""
    VIDEO = "video"
    DISPLAY = "display"
    NATIVE = "native"
    AUDIO = "audio"


class InventoryTypeEnum(str, Enum):
    """Valid inventory type values."""
    APPS = "apps"
    WEBSITES = "websites"
    CTV = "ctv"
    DOOH = "dooh"


class VolumeMetrics(BaseModel):
    """Volume metrics for a deal."""
    bid_requests: Optional[int] = Field(None, description="Total bid requests")
    impressions: Optional[int] = Field(None, description="Total impressions")
    uniques: Optional[int] = Field(None, description="Unique users")
    bid_requests_ratio: Optional[float] = Field(None, description="Bid requests per day")


class UnifiedPreEnrichmentSchema(BaseModel):
    """
    Unified schema for all deals before Stage 1 enrichment.
    
    This schema normalizes vendor-specific data (Google Ads, BidSwitch) into a
    consistent format that Stage 1 can process. All transformers must output
    this schema.
    
    Schema Version: 1.0
    """
    
    # Required fields
    deal_id: str = Field(..., description="Unique deal identifier")
    deal_name: str = Field(..., description="Human-readable deal name")
    source: str = Field(..., description="Source vendor (e.g., \'Google Authorized Buyers\', \'Google Curated\', \'BidSwitch\')")
    ssp_name: str = Field(..., description="SSP name (e.g., 'Google Authorized Buyers', 'BidSwitch')")
    format: FormatEnum = Field(..., description="Creative format: video, display, native, or audio")
    publishers: List[str] = Field(default_factory=list, description="List of publisher names/domains")
    floor_price: float = Field(..., ge=0, description="Bid floor price (must be >= 0)")
    raw_deal_data: Dict[str, Any] = Field(..., description="Original vendor data preserved for reference")
    
    # Optional fields
    inventory_type: Optional[Union[str, int]] = Field(None, description="Inventory type (apps, websites, ctv, dooh or numeric ID)")
    start_time: Optional[str] = Field(None, description="Deal start time (ISO 8601)")
    end_time: Optional[str] = Field(None, description="Deal end time (ISO 8601)")
    description: Optional[str] = Field(None, description="Deal description")
    volume_metrics: Optional[VolumeMetrics] = Field(None, description="Volume metrics")
    inventory_scale: Optional[int] = Field(None, description="Unified inventory scale metric (bid_requests for BidSwitch, impressions for Google)")
    inventory_scale_type: Optional[str] = Field(None, description="Type of inventory_scale metric: 'bid_requests' or 'impressions'")
    schema_version: str = Field(default="1.0", description="Schema version for future migrations")
    
    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",  # Don't allow extra fields
        json_encoders={
            datetime: lambda v: v.isoformat() if v else None
        }
    )
    
    @field_validator('format', mode='before')
    @classmethod
    def normalize_format(cls, v):
        """Normalize format values from vendor-specific formats."""
        if v is None:
            raise ValueError("format is required")
        
        # Convert to lowercase string
        v_str = str(v).lower().strip()
        
        # Normalize vendor-specific values
        format_map = {
            'banner': 'display',
            'display': 'display',
            'video': 'video',
            'native': 'native',
            'audio': 'audio',
            # Google Ads specific
            'video': 'video',
            'display': 'display',
        }
        
        normalized = format_map.get(v_str, v_str)
        
        # Validate against enum
        try:
            return FormatEnum(normalized)
        except ValueError:
            raise ValueError(f"Invalid format: {v}. Must be one of: video, display, native, audio")
    
    @field_validator('publishers', mode='before')
    @classmethod
    def normalize_publishers(cls, v):
        """Ensure publishers is always a list."""
        if v is None:
            return []
        if isinstance(v, str):
            # Single publisher string -> list
            return [v.strip()] if v.strip() else []
        if isinstance(v, list):
            # Already a list, clean up
            return [str(p).strip() for p in v if p and str(p).strip()]
        return []
    
    @field_validator('floor_price', mode='before')
    @classmethod
    def normalize_floor_price(cls, v):
        """Convert floor price to float, handling string inputs."""
        if v is None:
            raise ValueError("floor_price is required")
        
        if isinstance(v, (int, float)):
            return float(v)
        
        if isinstance(v, str):
            # Remove any currency symbols or whitespace
            cleaned = v.strip().replace('$', '').replace(',', '').strip()
            try:
                return float(cleaned)
            except ValueError:
                raise ValueError(f"Invalid floor_price format: {v}")
        
        raise ValueError(f"Cannot convert floor_price to float: {v}")
    
    @field_validator('ssp_name', mode='before')
    @classmethod
    def normalize_ssp_name(cls, v):
        """Normalize SSP name to standard values."""
        if v is None:
            raise ValueError("ssp_name is required")
        
        v_str = str(v).strip()
        
        # Normalize common variations
        ssp_map = {
            'google authorized buyers': 'Google Authorized Buyers',
            'google ads': 'Google Authorized Buyers',
            'bidswitch': 'BidSwitch',
            'bid switch': 'BidSwitch',
        }
        
        normalized = ssp_map.get(v_str.lower(), v_str)
        return normalized
    
    @model_validator(mode='after')
    def validate_deal_id(self):
        """Ensure deal_id is not empty."""
        if not self.deal_id or not str(self.deal_id).strip():
            raise ValueError("deal_id cannot be empty")
        return self


class Taxonomy(BaseModel):
    """IAB Content Taxonomy classification."""
    tier1: Optional[str] = Field(None, description="Tier 1 category (e.g., 'Automotive')")
    tier2: Optional[str] = Field(None, description="Tier 2 subcategory (e.g., 'Auto Parts & Accessories')")
    tier3: Optional[str] = Field(None, description="Tier 3 specific topic (e.g., 'Auto Repair')")


class Safety(BaseModel):
    """Brand safety metadata (GARM alignment)."""
    garm_risk_rating: Optional[str] = Field(None, description="GARM risk rating: Floor, Low, Medium, High")
    family_safe: Optional[bool] = Field(None, description="Family-safe flag")
    safe_for_verticals: Optional[List[str]] = Field(default_factory=list, description="List of safe-for verticals")


class Audience(BaseModel):
    """Audience profile metadata."""
    inferred_audience: List[str] = Field(default_factory=list, description="Inferred audience segments")
    demographic_hint: Optional[str] = Field(None, description="Demographic hints (e.g., '25-54, High Income')")
    audience_provenance: str = Field(default="Inferred", description="Audience data provenance")


class Commercial(BaseModel):
    """Commercial profile metadata."""
    quality_tier: Optional[str] = Field(None, description="Quality tier: Premium, Mid-tier, RON")
    volume_tier: Optional[str] = Field(None, description="Volume tier: High, Medium, Low")
    floor_price: Optional[float] = Field(None, description="Floor price (may differ from pre-enrichment)")


class EnrichedDeal(BaseModel):
    """
    Schema for deals after Stage 1 enrichment.
    
    This schema extends UnifiedPreEnrichmentSchema with semantic metadata
    inferred by Stage 1 enrichment (LLM inference, validation, etc.).
    
    Schema Version: 1.0
    """
    
    # All fields from UnifiedPreEnrichmentSchema
    deal_id: str
    deal_name: str
    source: str
    ssp_name: str
    format: FormatEnum
    publishers: List[str]
    floor_price: float
    raw_deal_data: Dict[str, Any]
    
    # Optional pre-enrichment fields (preserved)
    inventory_type: Optional[Union[str, int]] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    volume_metrics: Optional[VolumeMetrics] = None
    inventory_scale: Optional[int] = None
    inventory_scale_type: Optional[str] = None
    
    # Stage 1 enrichment fields
    taxonomy: Optional[Taxonomy] = Field(None, description="IAB Content Taxonomy")
    concepts: List[str] = Field(default_factory=list, description="Semantic concepts/keywords")
    safety: Optional[Safety] = Field(None, description="Brand safety metadata")
    audience: Optional[Audience] = Field(None, description="Audience profile")
    commercial: Optional[Commercial] = Field(None, description="Commercial profile")
    
    # Metadata
    schema_version: str = Field(default="1.0", description="Schema version")
    enrichment_timestamp: Optional[str] = Field(None, description="When enrichment was performed (ISO 8601)")
    
    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid"
    )


# Helper functions for schema conversion

def normalize_to_unified_schema(data: Dict[str, Any]) -> UnifiedPreEnrichmentSchema:
    """
    Normalize a dictionary to UnifiedPreEnrichmentSchema.
    
    Handles vendor-specific field names and converts them to unified schema.
    
    Args:
        data: Dictionary with deal data (may have vendor-specific field names)
        
    Returns:
        UnifiedPreEnrichmentSchema instance
        
    Raises:
        ValidationError: If data doesn't match schema requirements
    """
    # Handle vendor-specific field mappings
    normalized = {}
    
    # Map common vendor-specific fields
    field_mappings = {
        # Google Ads
        'entityId': 'deal_id',
        'entityName': 'deal_name',
        'vendor': 'ssp_name',
        'publisher': 'publishers',  # Single -> list handled by validator
        'primary_request_format': 'format',
        
        # BidSwitch
        'display_name': 'deal_name',
        'price': 'floor_price',
        'creative_type': 'format',
    }
    
    # Apply field mappings
    for old_key, new_key in field_mappings.items():
        if old_key in data and new_key not in data:
            normalized[new_key] = data[old_key]
    
    # Copy all other fields
    for key, value in data.items():
        if key not in field_mappings:
            normalized[key] = value
    
    # Ensure raw_deal_data is preserved
    if 'raw_deal_data' not in normalized:
        normalized['raw_deal_data'] = data.copy()
    
    return UnifiedPreEnrichmentSchema(**normalized)


def validate_unified_schema(data: Dict[str, Any]) -> tuple:
    """
    Validate data against UnifiedPreEnrichmentSchema.
    
    Args:
        data: Dictionary to validate
        
    Returns:
        Tuple of (is_valid, error_message, schema_instance)
        - is_valid: True if validation passes
        - error_message: Error message if validation fails, None otherwise
        - schema_instance: UnifiedPreEnrichmentSchema instance if valid, None otherwise
    """
    try:
        schema = normalize_to_unified_schema(data)
        return True, None, schema
    except Exception as e:
        return False, str(e), None
