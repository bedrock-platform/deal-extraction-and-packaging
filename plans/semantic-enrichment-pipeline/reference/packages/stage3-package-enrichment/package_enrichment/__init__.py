"""
Package Enrichment Package

A standalone package for enriching audience packages with aggregated deal-level metadata
and LLM-generated recommendations.

Provides:
- PackageEnricher: Main class for enriching packages
- Aggregation utilities: Functions for aggregating deal-level enrichments
- LLM-based recommendations: Package-level use case and vertical recommendations
"""

from .enricher import PackageEnricher
from .aggregation import (
    aggregate_taxonomy,
    aggregate_safety,
    aggregate_audience,
    aggregate_commercial,
    calculate_health_score
)

__version__ = "1.0.0"
__all__ = [
    "PackageEnricher",
    "aggregate_taxonomy",
    "aggregate_safety",
    "aggregate_audience",
    "aggregate_commercial",
    "calculate_health_score"
]
