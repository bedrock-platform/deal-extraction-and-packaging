"""
Integration module for connecting pipeline stages.

Provides adapters for converting data between stages:
- Stage 1 → Stage 2: EnrichedDeal → Package Creation format
- Stage 2 → Stage 3: Package proposals → Package Enrichment format
"""

from .stage2_adapter import convert_enriched_deals_to_stage2_format
from .stage3_adapter import convert_packages_to_stage3_format

__all__ = [
    "convert_enriched_deals_to_stage2_format",
    "convert_packages_to_stage3_format",
]
