"""
Stage 3 Adapter

Converts Stage 2 package proposals to Stage 3 (Package Enrichment) format.
Matches package deal IDs with enriched deals.
"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


def convert_packages_to_stage3_format(
    packages: List[Dict[str, Any]],
    enriched_deals: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Convert Stage 2 package proposals to Stage 3 format.
    
    Matches package deal IDs with enriched deals and creates package-deal pairs
    for enrichment.
    
    Args:
        packages: List of package proposals from Stage 2
                  Format: [{"package_name": str, "deal_ids": List[str], "reasoning": str}, ...]
        enriched_deals: List of enriched deal dictionaries (from Stage 1)
        
    Returns:
        List of package dictionaries with matched deals:
        [{"package_name": str, "deal_ids": List[str], "deals": List[Dict]}, ...]
    """
    # Create deal lookup by deal_id
    deal_lookup = {deal.get('deal_id'): deal for deal in enriched_deals}
    
    stage3_packages = []
    
    for package in packages:
        package_name = package.get('package_name') or package.get('name', 'Unknown Package')
        deal_ids = package.get('deal_ids', [])
        
        # Match deals to package
        matched_deals = []
        for deal_id in deal_ids:
            if deal_id in deal_lookup:
                matched_deals.append(deal_lookup[deal_id])
            else:
                logger.warning(f"Deal {deal_id} not found in enriched deals for package {package_name}")
        
        if not matched_deals:
            logger.warning(f"No deals matched for package {package_name}, skipping")
            continue
        
        stage3_package = {
            'package_id': package.get('package_id') or package.get('id'),
            'package_name': package_name,
            'deal_ids': deal_ids,
            'deals': matched_deals,
            'reasoning': package.get('reasoning', '')
        }
        
        stage3_packages.append(stage3_package)
    
    logger.info(f"Converted {len(stage3_packages)} packages to Stage 3 format")
    return stage3_packages
