"""
Enrichment Module

Stage 1 enrichment pipeline for semantic deal enrichment using LLM inference.
Phase 2 enhancements: Taxonomy validator, Publisher intelligence, Temporal signals.
"""
from .llm_client import GeminiClient
from .inference import enrich_deal, get_taxonomy_validator, get_publisher_intelligence, get_temporal_extractor
from .enricher import DealEnricher
from .taxonomy_validator import TaxonomyValidator
from .publisher_intelligence import PublisherIntelligence
from .temporal_signals import TemporalSignalExtractor
from .garm_utils import aggregate_garm_ratings, aggregate_family_safe, determine_safe_verticals, get_risk_order
from .checkpoint import EnrichmentCheckpoint
from .incremental_exporter import IncrementalExporter

__all__ = [
    "GeminiClient",
    "enrich_deal",
    "DealEnricher",
    "TaxonomyValidator",
    "PublisherIntelligence",
    "TemporalSignalExtractor",
    "get_taxonomy_validator",
    "get_publisher_intelligence",
    "get_temporal_extractor",
    "aggregate_garm_ratings",
    "aggregate_family_safe",
    "determine_safe_verticals",
    "get_risk_order",
    "EnrichmentCheckpoint",
    "IncrementalExporter",
]
