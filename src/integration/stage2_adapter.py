"""
Stage 2 Adapter

Converts EnrichedDeal objects to Stage 2 (Package Creation) format.
"""
import logging
from typing import List, Dict, Any

from ..common.schema import EnrichedDeal

logger = logging.getLogger(__name__)


def convert_enriched_deals_to_stage2_format(
    enriched_deals: List[EnrichedDeal]
) -> List[Dict[str, Any]]:
    """
    Convert EnrichedDeal objects to Stage 2 format (dictionaries for PackageCreator).
    
    Stage 2 expects dictionaries with enrichment fields in a specific structure:
    - taxonomy: {tier1, tier2, tier3}
    - safety: {garm_risk_rating, family_safe, safe_for_verticals}
    - audience: {inferred_audience, demographic_hint, audience_provenance}
    - commercial: {quality_tier, volume_tier, floor_price}
    - concepts: List[str]
    
    Args:
        enriched_deals: List of EnrichedDeal instances
        
    Returns:
        List of deal dictionaries in Stage 2 format
    """
    stage2_deals = []
    
    for deal in enriched_deals:
        # Convert EnrichedDeal to dictionary
        deal_dict = deal.model_dump(mode='json')
        
        # Ensure nested structures are properly formatted
        # PackageCreator expects these fields at the top level
        stage2_deal = {
            'deal_id': deal_dict.get('deal_id'),
            'deal_name': deal_dict.get('deal_name'),
            'ssp_name': deal_dict.get('ssp_name'),
            'format': deal_dict.get('format'),
            'publishers': deal_dict.get('publishers', []),
            'floor_price': deal_dict.get('floor_price'),
            'description': deal_dict.get('description'),
            
            # Enrichment fields (nested structures)
            'taxonomy': deal_dict.get('taxonomy') or {},
            'safety': deal_dict.get('safety') or {},
            'audience': deal_dict.get('audience') or {},
            'commercial': deal_dict.get('commercial') or {},
            'concepts': deal_dict.get('concepts', []),
            
            # Additional metadata
            'inventory_type': deal_dict.get('inventory_type'),
            'start_time': deal_dict.get('start_time'),
            'end_time': deal_dict.get('end_time'),
            'inventory_scale': deal_dict.get('inventory_scale'),
            'inventory_scale_type': deal_dict.get('inventory_scale_type'),
        }
        
        stage2_deals.append(stage2_deal)
    
    logger.info(f"Converted {len(stage2_deals)} enriched deals to Stage 2 format")
    return stage2_deals
