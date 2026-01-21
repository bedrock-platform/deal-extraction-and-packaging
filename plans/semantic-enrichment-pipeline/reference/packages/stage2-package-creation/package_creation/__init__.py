"""
Package Creation Package

A standalone package for creating intelligent audience packages from enriched deals
using semantic clustering and LLM-based grouping.

Provides:
- PackageCreator: Main class for creating packages from deals
- Semantic clustering using sentence-transformers
- LLM-based intelligent grouping
"""

from .creator import PackageCreator
from .embeddings import create_deal_embeddings, create_deal_text_representation
from .clustering import cluster_deals_semantically, cluster_deals_with_soft_assignments

__version__ = "1.0.0"
__all__ = [
    "PackageCreator",
    "create_deal_embeddings",
    "create_deal_text_representation",
    "cluster_deals_semantically",
    "cluster_deals_with_soft_assignments"
]
