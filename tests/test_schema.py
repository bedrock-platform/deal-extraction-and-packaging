"""
Tests for unified schema definitions.

Tests DEAL-101: Unified Schema Definition
"""
import pytest
from pydantic import ValidationError

from src.common.schema import (
    UnifiedPreEnrichmentSchema,
    EnrichedDeal,
    FormatEnum,
    VolumeMetrics,
    normalize_to_unified_schema,
    validate_unified_schema,
)


class TestUnifiedPreEnrichmentSchema:
    """Tests for UnifiedPreEnrichmentSchema."""
    
    def test_valid_google_ads_deal(self):
        """Test schema validation with Google Ads deal data."""
        data = {
            "deal_id": "12345",
            "deal_name": "Premium CTV Auto Inventory",
            "ssp_name": "Google Authorized Buyers",
            "format": "video",
            "publishers": ["Paramount", "Disney+"],
            "floor_price": 5.50,
            "raw_deal_data": {"entityId": "12345", "entityName": "Premium CTV Auto Inventory"},
            "inventory_type": "ctv",
            "start_time": "2025-01-01T00:00:00Z",
            "end_time": "2025-12-31T23:59:59Z",
        }
        
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.deal_id == "12345"
        assert schema.deal_name == "Premium CTV Auto Inventory"
        assert schema.ssp_name == "Google Authorized Buyers"
        assert schema.format == FormatEnum.VIDEO
        assert schema.publishers == ["Paramount", "Disney+"]
        assert schema.floor_price == 5.50
    
    def test_valid_bidswitch_deal(self):
        """Test schema validation with BidSwitch deal data."""
        data = {
            "deal_id": "Sovrn_N365",
            "deal_name": "Sovrn_N365_Adform",
            "ssp_name": "BidSwitch",
            "format": "display",
            "publishers": ["CNN", "BBC"],
            "floor_price": 3.82,
            "raw_deal_data": {"deal_id": "Sovrn_N365", "display_name": "Sovrn_N365_Adform"},
            "inventory_type": 2,
            "volume_metrics": {
                "bid_requests": 339489613748,
                "bid_requests_ratio": 159824247.52,
            },
        }
        
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.deal_id == "Sovrn_N365"
        assert schema.ssp_name == "BidSwitch"
        assert schema.format == FormatEnum.DISPLAY
        assert schema.inventory_type == 2
        assert schema.volume_metrics is not None
        assert schema.volume_metrics.bid_requests == 339489613748
    
    def test_format_normalization(self):
        """Test format field normalization."""
        # Test banner -> display
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "banner",  # Should normalize to "display"
            "publishers": [],
            "floor_price": 1.0,
            "raw_deal_data": {},
        }
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.format == FormatEnum.DISPLAY
        
        # Test uppercase
        data["format"] = "VIDEO"
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.format == FormatEnum.VIDEO
    
    def test_publishers_normalization(self):
        """Test publishers field normalization."""
        # Single string -> list
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "video",
            "publishers": "Paramount",  # Single string
            "floor_price": 1.0,
            "raw_deal_data": {},
        }
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.publishers == ["Paramount"]
        
        # Already a list
        data["publishers"] = ["CNN", "BBC"]
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.publishers == ["CNN", "BBC"]
        
        # None -> empty list
        data["publishers"] = None
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.publishers == []
    
    def test_floor_price_normalization(self):
        """Test floor_price field normalization."""
        # String -> float
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "video",
            "publishers": [],
            "floor_price": "5.50",  # String
            "raw_deal_data": {},
        }
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.floor_price == 5.50
        assert isinstance(schema.floor_price, float)
        
        # Already float
        data["floor_price"] = 3.82
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.floor_price == 3.82
    
    def test_ssp_name_normalization(self):
        """Test SSP name normalization."""
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "google authorized buyers",  # Lowercase
            "format": "video",
            "publishers": [],
            "floor_price": 1.0,
            "raw_deal_data": {},
        }
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.ssp_name == "Google Authorized Buyers"
        
        data["ssp_name"] = "bidswitch"
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.ssp_name == "BidSwitch"
    
    def test_missing_required_fields(self):
        """Test validation fails for missing required fields."""
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            # Missing ssp_name, format, publishers, floor_price, raw_deal_data
        }
        
        with pytest.raises(ValidationError):
            UnifiedPreEnrichmentSchema(**data)
    
    def test_invalid_format(self):
        """Test validation fails for invalid format."""
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "invalid_format",  # Invalid
            "publishers": [],
            "floor_price": 1.0,
            "raw_deal_data": {},
        }
        
        with pytest.raises(ValidationError):
            UnifiedPreEnrichmentSchema(**data)
    
    def test_negative_floor_price(self):
        """Test validation fails for negative floor price."""
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "video",
            "publishers": [],
            "floor_price": -1.0,  # Negative
            "raw_deal_data": {},
        }
        
        with pytest.raises(ValidationError):
            UnifiedPreEnrichmentSchema(**data)
    
    def test_volume_metrics(self):
        """Test volume_metrics field."""
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "video",
            "publishers": [],
            "floor_price": 1.0,
            "raw_deal_data": {},
            "volume_metrics": {
                "bid_requests": 1000000,
                "impressions": 500000,
                "uniques": 250000,
                "bid_requests_ratio": 10000.0,
            },
        }
        
        schema = UnifiedPreEnrichmentSchema(**data)
        assert schema.volume_metrics is not None
        assert schema.volume_metrics.bid_requests == 1000000
        assert schema.volume_metrics.impressions == 500000


class TestNormalizeToUnifiedSchema:
    """Tests for normalize_to_unified_schema helper function."""
    
    def test_google_ads_field_mapping(self):
        """Test field mapping for Google Ads data."""
        data = {
            "entityId": "12345",
            "entityName": "Premium CTV",
            "vendor": "Google Authorized Buyers",
            "publisher": "Paramount",  # Single -> list
            "primary_request_format": "video",
            "floor_price": "5.50",  # String
            "raw_deal_data": {"entityId": "12345"},
        }
        
        schema = normalize_to_unified_schema(data)
        assert schema.deal_id == "12345"
        assert schema.deal_name == "Premium CTV"
        assert schema.ssp_name == "Google Authorized Buyers"
        assert schema.publishers == ["Paramount"]
        assert schema.format == FormatEnum.VIDEO
    
    def test_bidswitch_field_mapping(self):
        """Test field mapping for BidSwitch data."""
        data = {
            "deal_id": "Sovrn_N365",
            "display_name": "Sovrn_N365_Adform",
            "creative_type": "display",
            "price": "3.82",
            "publishers": ["CNN"],
            "raw_deal_data": {"deal_id": "Sovrn_N365"},
        }
        
        schema = normalize_to_unified_schema(data)
        assert schema.deal_id == "Sovrn_N365"
        assert schema.deal_name == "Sovrn_N365_Adform"
        assert schema.format == FormatEnum.DISPLAY
        assert schema.floor_price == 3.82


class TestValidateUnifiedSchema:
    """Tests for validate_unified_schema helper function."""
    
    def test_valid_data(self):
        """Test validation succeeds for valid data."""
        data = {
            "deal_id": "test1",
            "deal_name": "Test",
            "ssp_name": "BidSwitch",
            "format": "video",
            "publishers": [],
            "floor_price": 1.0,
            "raw_deal_data": {},
        }
        
        is_valid, error, schema = validate_unified_schema(data)
        assert is_valid is True
        assert error is None
        assert schema is not None
        assert isinstance(schema, UnifiedPreEnrichmentSchema)
    
    def test_invalid_data(self):
        """Test validation fails for invalid data."""
        data = {
            "deal_id": "test1",
            # Missing required fields
        }
        
        is_valid, error, schema = validate_unified_schema(data)
        assert is_valid is False
        assert error is not None
        assert schema is None


class TestEnrichedDeal:
    """Tests for EnrichedDeal schema."""
    
    def test_enriched_deal_creation(self):
        """Test creating an enriched deal."""
        base_data = {
            "deal_id": "3001",
            "deal_name": "Premium CTV Auto Inventory",
            "ssp_name": "BidSwitch",
            "format": "video",
            "publishers": ["Paramount", "Disney+"],
            "floor_price": 5.50,
            "raw_deal_data": {},
        }
        
        enriched_data = {
            **base_data,
            "taxonomy": {
                "tier1": "Automotive",
                "tier2": "Auto Parts & Accessories",
                "tier3": "Auto Repair",
            },
            "concepts": ["auto", "luxury", "premium"],
            "safety": {
                "garm_risk_rating": "Low",
                "family_safe": True,
            },
            "audience": {
                "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
                "demographic_hint": "25-54, High Income",
            },
            "commercial": {
                "quality_tier": "Premium",
                "volume_tier": "High",
                "floor_price": 5.50,
            },
        }
        
        deal = EnrichedDeal(**enriched_data)
        assert deal.deal_id == "3001"
        assert deal.taxonomy is not None
        assert deal.taxonomy.tier1 == "Automotive"
        assert deal.safety.garm_risk_rating == "Low"
        assert len(deal.concepts) == 3
