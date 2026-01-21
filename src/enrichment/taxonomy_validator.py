"""
IAB Taxonomy Validator

Validates and auto-corrects IAB Content Taxonomy tags inferred by LLM.
Uses fuzzy matching to handle variations in taxonomy naming.
Now loads from IAB Content Taxonomy v3.1 JSON file.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, List, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Default path to IAB taxonomy JSON file
DEFAULT_TAXONOMY_FILE = Path(__file__).parent.parent.parent / "data" / "iab_taxonomy" / "iab_content_taxonomy_v3.json"

# Backward compatibility: Map v2.2 category names to v3.1 equivalents
V2_TO_V3_MAPPINGS = {
    "Arts & Entertainment": "Entertainment",
    "Business": "Business and Finance",
    "Family & Parenting": "Family and Relationships",
    "Health & Fitness": "Healthy Living",
    "News & Information": "Politics",  # Closest match, but may need refinement
    # Note: Some v2.2 categories don't have direct v3.1 equivalents
    # These will be handled by fuzzy matching
}


class TaxonomyValidator:
    """
    Validates and auto-corrects IAB Content Taxonomy tags.
    
    Uses fuzzy matching to handle variations in taxonomy naming.
    Loads taxonomy from IAB Content Taxonomy v3.1 JSON file.
    """
    
    def __init__(self, taxonomy_file: Optional[Path] = None):
        """
        Initialize the taxonomy validator.
        
        Args:
            taxonomy_file: Path to IAB taxonomy JSON file. If None, uses default path.
        """
        self.taxonomy_file = taxonomy_file or DEFAULT_TAXONOMY_FILE
        self.taxonomy_data = None
        self.tier1_names: Set[str] = set()
        self.tier2_by_tier1: Dict[str, Set[str]] = {}
        self.tier3_by_tier2: Dict[Tuple[str, str], Set[str]] = {}
        self.tier1_map: Dict[str, str] = {}
        self.tier2_map: Dict[str, Dict[str, str]] = {}
        self.tier3_map: Dict[Tuple[str, str], Dict[str, str]] = {}
        
        # Load taxonomy and build lookup structures
        self._load_taxonomy()
        self._build_lookup_structures()
        
        logger.info(f"Initialized TaxonomyValidator with {len(self.tier1_names)} Tier 1 categories, "
                   f"{sum(len(t2) for t2 in self.tier2_by_tier1.values())} Tier 2 categories, "
                   f"{sum(len(t3) for t3 in self.tier3_by_tier2.values())} Tier 3 categories")
    
    def _load_taxonomy(self) -> None:
        """Load IAB taxonomy from JSON file."""
        if not self.taxonomy_file.exists():
            logger.warning(f"IAB taxonomy file not found: {self.taxonomy_file}. "
                          "Falling back to hardcoded categories.")
            self._load_fallback_taxonomy()
            return
        
        try:
            with open(self.taxonomy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.taxonomy_data = data.get('taxonomy', {})
            version = data.get('version', 'unknown')
            logger.info(f"Loaded IAB Content Taxonomy v{version} from {self.taxonomy_file}")
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load taxonomy file {self.taxonomy_file}: {e}. "
                        "Falling back to hardcoded categories.")
            self._load_fallback_taxonomy()
    
    def _load_fallback_taxonomy(self) -> None:
        """Load fallback hardcoded taxonomy (backward compatibility)."""
        # Fallback to hardcoded v2.2 categories for backward compatibility
        fallback_tier1 = {
            "Arts & Entertainment", "Automotive", "Business", "Careers", "Education",
            "Family & Parenting", "Health & Fitness", "Food & Drink", "Home & Garden",
            "Hobbies & Interests", "News & Information", "Personal Finance", "Pets",
            "Pop Culture", "Real Estate", "Religion & Spirituality", "Science", "Shopping",
            "Society", "Sports", "Style & Fashion", "Technology & Computing", "Travel",
            "Video Gaming", "Sensitive Topics"
        }
        
        self.tier1_names = fallback_tier1
        self.tier2_by_tier1 = {}
        self.tier3_by_tier2 = {}
        logger.warning("Using fallback hardcoded taxonomy (limited coverage)")
    
    def _build_lookup_structures(self) -> None:
        """Build lookup structures from taxonomy data."""
        if not self.taxonomy_data:
            return
        
        # Build Tier 1, 2, 3 lookup structures
        for entry in self.taxonomy_data.values():
            tier1 = entry.get('tier1')
            tier2 = entry.get('tier2')
            tier3 = entry.get('tier3')
            
            if tier1:
                self.tier1_names.add(tier1)
                
                if tier2:
                    if tier1 not in self.tier2_by_tier1:
                        self.tier2_by_tier1[tier1] = set()
                    self.tier2_by_tier1[tier1].add(tier2)
                    
                    if tier3:
                        key = (tier1, tier2)
                        if key not in self.tier3_by_tier2:
                            self.tier3_by_tier2[key] = set()
                        self.tier3_by_tier2[key].add(tier3)
        
        # Build variation maps for fuzzy matching
        self.tier1_map = {name.lower(): name for name in self.tier1_names}
        
        # Build Tier 2 map
        for tier1, tier2_set in self.tier2_by_tier1.items():
            self.tier2_map[tier1] = {name.lower(): name for name in tier2_set}
        
        # Build Tier 3 map
        for (tier1, tier2), tier3_set in self.tier3_by_tier2.items():
            key = (tier1, tier2)
            self.tier3_map[key] = {name.lower(): name for name in tier3_set}
    
    def _similarity(self, a: str, b: str) -> float:
        """Calculate similarity ratio between two strings."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()
    
    def _find_best_match(self, value: str, candidates: List[str], threshold: float = 0.7) -> Optional[str]:
        """
        Find best matching candidate using fuzzy matching.
        
        Args:
            value: Value to match
            candidates: List of candidate strings
            threshold: Minimum similarity threshold (0-1)
            
        Returns:
            Best matching candidate or None if below threshold
        """
        if not value or not candidates:
            return None
        
        value_lower = value.lower().strip()
        best_match = None
        best_score = 0.0
        
        for candidate in candidates:
            score = self._similarity(value_lower, candidate.lower())
            if score > best_score:
                best_score = score
                best_match = candidate
        
        return best_match if best_score >= threshold else None
    
    def validate_tier1(self, tier1: Optional[str]) -> Tuple[Optional[str], bool]:
        """
        Validate and correct Tier 1 category.
        
        Args:
            tier1: Tier 1 category name (may be incorrect)
            
        Returns:
            Tuple of (corrected_tier1, was_corrected)
        """
        if not tier1:
            return None, False
        
        tier1_original = tier1.strip()
        tier1_lower = tier1_original.lower()
        
        # Check v2.2 to v3.1 mapping first (backward compatibility)
        if tier1_original in V2_TO_V3_MAPPINGS:
            mapped = V2_TO_V3_MAPPINGS[tier1_original]
            if mapped.lower() in self.tier1_map:
                logger.debug(f"Mapped v2.2 → v3.1: '{tier1_original}' → '{mapped}'")
                return mapped, True
        
        # Direct match
        if tier1_lower in self.tier1_map:
            corrected = self.tier1_map[tier1_lower]
            return corrected, corrected != tier1_original
        
        # Fuzzy match against all canonical names
        canonical_names = list(self.tier1_names)
        best_match = self._find_best_match(tier1_original, canonical_names, threshold=0.7)
        
        if best_match:
            logger.debug(f"Corrected Tier 1: '{tier1_original}' → '{best_match}'")
            return best_match, True
        
        # No match found - return original (backward compatibility)
        logger.warning(f"Could not validate Tier 1: '{tier1_original}' (not in IAB v3.1 taxonomy)")
        return tier1_original, False
    
    def validate_tier2(self, tier1: Optional[str], tier2: Optional[str]) -> Tuple[Optional[str], bool]:
        """
        Validate and correct Tier 2 subcategory.
        
        Args:
            tier1: Validated Tier 1 category
            tier2: Tier 2 subcategory name (may be incorrect)
            
        Returns:
            Tuple of (corrected_tier2, was_corrected)
        """
        if not tier2:
            return None, False
        
        if not tier1 or tier1 not in self.tier2_by_tier1:
            # No Tier 2 mappings for this Tier 1 - return as-is
            logger.debug(f"No Tier 2 mappings for Tier 1: '{tier1}'")
            return tier2, False
        
        tier2_lower = tier2.strip().lower()
        tier2_variations = self.tier2_map.get(tier1, {})
        
        # Direct match
        if tier2_lower in tier2_variations:
            corrected = tier2_variations[tier2_lower]
            return corrected, corrected != tier2
        
        # Fuzzy match against canonical Tier 2 names for this Tier 1
        canonical_names = list(self.tier2_by_tier1.get(tier1, set()))
        best_match = self._find_best_match(tier2, canonical_names, threshold=0.7)
        
        if best_match:
            logger.debug(f"Corrected Tier 2: '{tier2}' → '{best_match}' (Tier 1: {tier1})")
            return best_match, True
        
        # No match found - return original (backward compatibility)
        logger.debug(f"Could not validate Tier 2: '{tier2}' (Tier 1: {tier1})")
        return tier2, False
    
    def validate_tier3(self, tier1: Optional[str], tier2: Optional[str], tier3: Optional[str]) -> Tuple[Optional[str], bool]:
        """
        Validate and correct Tier 3 specific topic.
        
        Args:
            tier1: Validated Tier 1 category
            tier2: Validated Tier 2 subcategory
            tier3: Tier 3 specific topic name (may be incorrect)
            
        Returns:
            Tuple of (corrected_tier3, was_corrected)
        """
        if not tier3:
            return None, False
        
        if not tier1 or not tier2:
            # Need both Tier 1 and Tier 2 for Tier 3 validation
            return tier3, False
        
        key = (tier1, tier2)
        if key not in self.tier3_by_tier2:
            # No Tier 3 mappings for this Tier 1/Tier 2 combination
            logger.debug(f"No Tier 3 mappings for Tier 1: '{tier1}', Tier 2: '{tier2}'")
            return tier3, False
        
        tier3_lower = tier3.strip().lower()
        tier3_variations = self.tier3_map.get(key, {})
        
        # Direct match
        if tier3_lower in tier3_variations:
            corrected = tier3_variations[tier3_lower]
            return corrected, corrected != tier3
        
        # Fuzzy match against canonical Tier 3 names for this Tier 1/Tier 2
        canonical_names = list(self.tier3_by_tier2.get(key, set()))
        best_match = self._find_best_match(tier3, canonical_names, threshold=0.7)
        
        if best_match:
            logger.debug(f"Corrected Tier 3: '{tier3}' → '{best_match}' (Tier 1: {tier1}, Tier 2: {tier2})")
            return best_match, True
        
        # No match found - return original (backward compatibility)
        logger.debug(f"Could not validate Tier 3: '{tier3}' (Tier 1: {tier1}, Tier 2: {tier2})")
        return tier3, False
    
    def validate_and_correct(
        self,
        tier1: Optional[str],
        tier2: Optional[str] = None,
        tier3: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, bool]]:
        """
        Validate and auto-correct all taxonomy tiers.
        
        Args:
            tier1: Tier 1 category
            tier2: Tier 2 subcategory (optional)
            tier3: Tier 3 specific topic (optional)
            
        Returns:
            Tuple of (corrected_tier1, corrected_tier2, corrected_tier3, corrections_applied)
            corrections_applied is a dict with keys: 'tier1', 'tier2', 'tier3'
        """
        corrections = {'tier1': False, 'tier2': False, 'tier3': False}
        
        # Validate Tier 1
        corrected_tier1, corrections['tier1'] = self.validate_tier1(tier1)
        
        # Validate Tier 2 (requires valid Tier 1)
        corrected_tier2 = None
        if tier2:
            corrected_tier2, corrections['tier2'] = self.validate_tier2(corrected_tier1, tier2)
        
        # Validate Tier 3 (requires valid Tier 1 and Tier 2)
        corrected_tier3 = None
        if tier3:
            corrected_tier3, corrections['tier3'] = self.validate_tier3(corrected_tier1, corrected_tier2, tier3)
        
        return corrected_tier1, corrected_tier2, corrected_tier3, corrections
