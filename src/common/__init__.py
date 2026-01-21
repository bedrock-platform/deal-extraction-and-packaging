"""
Common utilities and base classes for multi-vendor deal extraction.

Provides:
- BaseSSPClient: Base interface for vendor API clients
- BaseTransformer: Base interface for vendor data transformers
- UnifiedDataExporter: Multi-vendor data export functionality
- DealExtractor: Unified orchestrator for extracting deals from multiple vendors
"""

from .base_client import BaseSSPClient
from .base_transformer import BaseTransformer
from .data_exporter import UnifiedDataExporter
from .orchestrator import DealExtractor

# Schema definitions (DEAL-101)
try:
    from .schema import (
        UnifiedPreEnrichmentSchema,
        EnrichedDeal,
        FormatEnum,
        InventoryTypeEnum,
        VolumeMetrics,
        Taxonomy,
        Safety,
        Audience,
        Commercial,
        normalize_to_unified_schema,
        validate_unified_schema,
    )
    __all__ = [
        "BaseSSPClient",
        "BaseTransformer",
        "UnifiedDataExporter",
        "DealExtractor",
        "UnifiedPreEnrichmentSchema",
        "EnrichedDeal",
        "FormatEnum",
        "InventoryTypeEnum",
        "VolumeMetrics",
        "Taxonomy",
        "Safety",
        "Audience",
        "Commercial",
        "normalize_to_unified_schema",
        "validate_unified_schema",
    ]
except ImportError:
    # Schema not available (pydantic not installed)
    __all__ = [
        "BaseSSPClient",
        "BaseTransformer",
        "UnifiedDataExporter",
        "DealExtractor",
    ]
