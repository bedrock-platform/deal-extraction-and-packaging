"""
Semantic Embeddings Module

Creates semantic embeddings for deals using sentence-transformers.
"""
from typing import Dict, Any, List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "sentence-transformers is required. "
        "Install with: pip install sentence-transformers"
    )


def create_deal_text_representation(deal: Dict[str, Any]) -> str:
    """
    Create a text representation of a deal for embedding.
    
    Combines key metadata fields into a searchable text string.
    
    Args:
        deal: Deal dictionary with enrichment data
        
    Returns:
        Text representation string
    """
    parts = []
    
    # Basic info
    parts.append(f"Deal: {deal.get('deal_name', 'Unknown')}")
    parts.append(f"SSP: {deal.get('ssp_name', 'Unknown')}")
    parts.append(f"Format: {deal.get('format', 'Unknown')}")
    
    # Taxonomy
    taxonomy = deal.get('taxonomy', {})
    if taxonomy.get('tier1'):
        parts.append(f"Category: {taxonomy.get('tier1')}")
    if taxonomy.get('tier2'):
        parts.append(f"Subcategory: {taxonomy.get('tier2')}")
    if taxonomy.get('tier3'):
        parts.append(f"Topic: {taxonomy.get('tier3')}")
    
    # Concepts
    concepts = deal.get('concepts', [])
    if concepts:
        parts.append(f"Concepts: {', '.join(concepts[:5])}")
    
    # Safety
    safety = deal.get('safety', {})
    if safety.get('family_safe'):
        parts.append("Family Safe")
    if safety.get('garm_risk_rating'):
        parts.append(f"Risk: {safety.get('garm_risk_rating')}")
    
    # Audience
    audience = deal.get('audience', {})
    if audience.get('inferred_audience'):
        parts.append(f"Audience: {', '.join(audience.get('inferred_audience', [])[:3])}")
    if audience.get('demographic_hint'):
        parts.append(f"Demographics: {audience.get('demographic_hint')}")
    
    # Commercial
    commercial = deal.get('commercial', {})
    if commercial.get('quality_tier'):
        parts.append(f"Quality: {commercial.get('quality_tier')}")
    if commercial.get('volume_tier'):
        parts.append(f"Volume: {commercial.get('volume_tier')}")
    
    # Publishers
    publishers = deal.get('publishers', [])
    if publishers:
        parts.append(f"Publishers: {', '.join(publishers[:3])}")
    
    return " | ".join(parts)


def create_deal_embeddings(
    deals: List[Dict[str, Any]],
    model_name: str = 'all-MiniLM-L6-v2',
    batch_size: int = 32
) -> tuple[np.ndarray, SentenceTransformer]:
    """
    Create semantic embeddings for all deals.
    
    Args:
        deals: List of deal dictionaries
        model_name: Sentence transformer model name (default: 'all-MiniLM-L6-v2')
        batch_size: Batch size for encoding
        
    Returns:
        Tuple of (embeddings array, embedding model)
    """
    # Load embedding model
    model = SentenceTransformer(model_name)
    
    # Create text representations
    deal_texts = [create_deal_text_representation(deal) for deal in deals]
    
    # Generate embeddings
    embeddings = model.encode(
        deal_texts,
        show_progress_bar=True,
        batch_size=batch_size
    )
    
    return embeddings, model
