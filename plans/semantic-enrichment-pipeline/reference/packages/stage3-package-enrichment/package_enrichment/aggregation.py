"""
Aggregation Utilities Module

Functions for aggregating deal-level enrichments into package-level metadata.
"""
from typing import Dict, Any, List, Optional
from collections import Counter


def aggregate_taxonomy(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate taxonomy data from deals.
    
    Uses most common taxonomy across deals.
    
    Args:
        deals: List of deal dictionaries with taxonomy fields
        
    Returns:
        Dictionary with dominant_taxonomy_tier1/2/3 and taxonomy_distribution
    """
    tier1_counts = Counter()
    tier2_counts = Counter()
    tier3_counts = Counter()
    
    for deal in deals:
        taxonomy = deal.get('taxonomy', {})
        if taxonomy.get('tier1'):
            tier1_counts[taxonomy['tier1']] += 1
        if taxonomy.get('tier2'):
            tier2_counts[taxonomy['tier2']] += 1
        if taxonomy.get('tier3'):
            tier3_counts[taxonomy['tier3']] += 1
    
    return {
        'dominant_taxonomy_tier1': tier1_counts.most_common(1)[0][0] if tier1_counts else None,
        'dominant_taxonomy_tier2': tier2_counts.most_common(1)[0][0] if tier2_counts else None,
        'dominant_taxonomy_tier3': tier3_counts.most_common(1)[0][0] if tier3_counts else None,
        'taxonomy_distribution': {
            'tier1': dict(tier1_counts),
            'tier2': dict(tier2_counts),
            'tier3': dict(tier3_counts)
        }
    }


def aggregate_safety(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate safety data from deals.
    
    Uses most restrictive rating (worst-case approach).
    
    Args:
        deals: List of deal dictionaries with safety fields
        
    Returns:
        Dictionary with garm_risk_rating, family_safe, and safe_for_verticals
    """
    risk_ratings = []
    family_safe_flags = []
    
    for deal in deals:
        safety = deal.get('safety', {})
        risk_rating = safety.get('garm_risk_rating')
        family_safe = safety.get('family_safe')
        
        if risk_rating:
            risk_ratings.append(risk_rating)
        if family_safe is not None:
            family_safe_flags.append(family_safe)
    
    # Determine most restrictive risk rating
    # Order: High > Medium > Low > Floor
    risk_order = {'High': 4, 'Medium': 3, 'Low': 2, 'Floor': 1}
    garm_risk_rating = None
    if risk_ratings:
        max_risk = max(risk_ratings, key=lambda r: risk_order.get(r, 0))
        garm_risk_rating = max_risk
    
    # Family safe only if ALL deals are family-safe
    family_safe = all(family_safe_flags) if family_safe_flags else None
    
    return {
        'garm_risk_rating': garm_risk_rating,
        'family_safe': family_safe,
        'safe_for_verticals': _determine_safe_verticals(garm_risk_rating, family_safe)
    }


def _determine_safe_verticals(risk_rating: Optional[str], family_safe: Optional[bool]) -> List[str]:
    """Determine which verticals this package is safe for"""
    safe_verticals = []
    
    if risk_rating in ('Floor', 'Low'):
        safe_verticals.extend(['Automotive', 'Finance', 'CPG', 'Retail', 'Technology'])
    
    if family_safe:
        safe_verticals.extend(['Family Brands', 'Education', 'Healthcare'])
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(safe_verticals))


def aggregate_audience(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate audience data from deals.
    
    Combines audience segments and demographic hints.
    
    Args:
        deals: List of deal dictionaries with audience fields
        
    Returns:
        Dictionary with primary_audience and demographic_profile
    """
    all_audiences = []
    demographic_hints = []
    
    for deal in deals:
        audience = deal.get('audience', {})
        inferred_audience = audience.get('inferred_audience', [])
        if inferred_audience:
            all_audiences.extend(inferred_audience)
        
        demographic_hint = audience.get('demographic_hint')
        if demographic_hint:
            demographic_hints.append(demographic_hint)
    
    # Remove duplicates while preserving order
    primary_audience = list(dict.fromkeys(all_audiences))
    
    # Aggregate demographic hints (use most common or combine)
    demographic_profile = None
    if demographic_hints:
        # Use most common demographic hint, or combine if similar
        demographic_profile = demographic_hints[0] if len(set(demographic_hints)) == 1 else ', '.join(set(demographic_hints))
    
    return {
        'primary_audience': primary_audience,
        'demographic_profile': demographic_profile,
        'provenance': 'Inferred'
    }


def aggregate_commercial(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate commercial data from deals.
    
    Calculates min/max prices, sums volumes, determines quality tier.
    
    Args:
        deals: List of deal dictionaries with commercial fields
        
    Returns:
        Dictionary with floor_price_min/max, quality_tier, total_daily_avails
    """
    prices = []
    volumes = []
    quality_tiers = []
    
    for deal in deals:
        commercial = deal.get('commercial', {})
        
        floor_price = commercial.get('floor_price')
        if floor_price is not None:
            try:
                prices.append(float(floor_price))
            except (ValueError, TypeError):
                pass
        
        volume = commercial.get('volume_tier')
        if volume:
            volumes.append(volume)
        
        quality_tier = commercial.get('quality_tier')
        if quality_tier:
            quality_tiers.append(quality_tier)
    
    # Determine dominant quality tier
    quality_tier = None
    if quality_tiers:
        quality_tier = Counter(quality_tiers).most_common(1)[0][0]
    
    # Calculate volume tier from individual volumes
    volume_tier = None
    if volumes:
        volume_tier = Counter(volumes).most_common(1)[0][0]
    
    return {
        'floor_price_min': min(prices) if prices else None,
        'floor_price_max': max(prices) if prices else None,
        'quality_tier': quality_tier,
        'volume_tier': volume_tier
    }


def calculate_health_score(
    deals: List[Dict[str, Any]],
    quality_tier: Optional[str] = None,
    risk_rating: Optional[str] = None,
    volume_tier: Optional[str] = None,
    enrichment_coverage: float = 1.0
) -> Dict[str, Any]:
    """
    Calculate package health score.
    
    Health score formula: (quality_points + safety_points + volume_points + coverage_points) / 4
    
    Args:
        deals: List of deal dictionaries
        quality_tier: Dominant quality tier
        risk_rating: GARM risk rating
        volume_tier: Volume tier
        enrichment_coverage: Percentage of deals that are enriched (0.0-1.0)
        
    Returns:
        Dictionary with health_score, deal_count, and enrichment_coverage
    """
    # Quality points
    quality_points = {
        'Premium': 30,
        'Mid-tier': 20,
        'RON': 10
    }.get(quality_tier, 15)  # Default to 15 if unknown
    
    # Safety points
    safety_points = {
        'Floor': 30,
        'Low': 30,
        'Medium': 20,
        'High': 10
    }.get(risk_rating, 15)  # Default to 15 if unknown
    
    # Volume points
    volume_points = {
        'High': 25,
        'Medium': 15,
        'Low': 5
    }.get(volume_tier, 10)  # Default to 10 if unknown
    
    # Coverage points
    if enrichment_coverage >= 1.0:
        coverage_points = 15
    elif enrichment_coverage >= 0.8:
        coverage_points = 12
    else:
        coverage_points = 8
    
    # Calculate health score
    health_score = (quality_points + safety_points + volume_points + coverage_points) / 4
    
    return {
        'deal_count': len(deals),
        'enrichment_coverage': enrichment_coverage,
        'health_score': round(health_score, 1)
    }
