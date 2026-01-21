"""
GARM (Global Alliance for Responsible Media) Utilities

Utilities for aggregating GARM risk ratings and family-safe flags.
Used for package-level enrichment (Stage 2/3).
"""
from typing import List, Optional


# GARM risk rating order (lowest to highest)
GARM_RISK_ORDER = {
    'Floor': 1,
    'Low': 2,
    'Medium': 3,
    'High': 4
}


def aggregate_garm_ratings(ratings: List[str]) -> str:
    """
    Aggregate multiple GARM ratings using most restrictive rule (worst-case approach).
    
    Args:
        ratings: List of GARM ratings (Floor, Low, Medium, High)
    
    Returns:
        Most restrictive rating
    
    Examples:
        >>> aggregate_garm_ratings(['Low', 'Low', 'Low'])
        'Low'
        >>> aggregate_garm_ratings(['Low', 'Medium', 'Low'])
        'Medium'
        >>> aggregate_garm_ratings(['Low', 'High', 'Medium'])
        'High'
        >>> aggregate_garm_ratings(['Floor', 'Floor', 'Floor'])
        'Floor'
    """
    if not ratings:
        return 'Low'  # Default
    
    # Filter out None values
    valid_ratings = [r for r in ratings if r]
    
    if not valid_ratings:
        return 'Low'  # Default if all None
    
    # Find highest risk rating (most restrictive)
    max_rating = max(
        valid_ratings,
        key=lambda r: GARM_RISK_ORDER.get(r, 0)
    )
    
    return max_rating


def aggregate_family_safe(flags: List[Optional[bool]]) -> Optional[bool]:
    """
    Aggregate family-safe flags (all must be true).
    
    Args:
        flags: List of boolean family-safe flags (may include None)
    
    Returns:
        True if all are true, False if any is false, None if all are None
    
    Examples:
        >>> aggregate_family_safe([True, True, True])
        True
        >>> aggregate_family_safe([True, False, True])
        False
        >>> aggregate_family_safe([None, True, True])
        None
        >>> aggregate_family_safe([True, None, True])
        None
    """
    if not flags:
        return None
    
    # Filter out None values
    valid_flags = [f for f in flags if f is not None]
    
    if not valid_flags:
        return None  # All were None
    
    # All must be true
    return all(valid_flags)


def determine_safe_verticals(risk_rating: str) -> List[str]:
    """
    Determine safe-for-verticals based on GARM risk rating.
    
    Args:
        risk_rating: GARM risk rating (Floor, Low, Medium, High)
    
    Returns:
        List of safe verticals
    
    Examples:
        >>> determine_safe_verticals('Floor')
        ['Automotive', 'Finance', 'Retail', 'Technology', 'Travel', 'CPG', 'Health', 'Education', 'Entertainment']
        >>> determine_safe_verticals('High')
        []
    """
    if risk_rating in ('Floor', 'Low'):
        # All verticals safe
        return [
            'Automotive', 'Finance', 'Retail', 'Technology', 'Travel',
            'CPG', 'Health', 'Education', 'Entertainment', 'Food & Drink',
            'Home & Garden', 'Sports', 'Style & Fashion'
        ]
    elif risk_rating == 'Medium':
        # Limited verticals (exclude sensitive brands)
        return [
            'Automotive', 'Finance', 'Retail', 'Technology', 'Travel',
            'Sports', 'Entertainment'
        ]
    else:  # High
        # Very limited or no verticals safe
        return []


def get_risk_order(rating: str) -> int:
    """
    Get numeric order for GARM risk rating (for sorting/comparison).
    
    Args:
        rating: GARM risk rating
    
    Returns:
        Numeric order (1=Floor, 4=High)
    """
    return GARM_RISK_ORDER.get(rating, 0)
