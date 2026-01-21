"""
Publisher Intelligence

Recognizes publisher brands, domains, and quality indicators to enhance enrichment.
"""
import logging
import re
from typing import Optional, Dict, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# Publisher knowledge base: brand name → (domain, quality_tier, category_hints, safety_hints)
PUBLISHER_KNOWLEDGE_BASE = {
    # Premium CTV/Streaming
    "Paramount+": ("paramountplus.com", "Premium", ["Arts & Entertainment", "Television", "Streaming"], "Floor"),
    "Paramount Plus": ("paramountplus.com", "Premium", ["Arts & Entertainment", "Television", "Streaming"], "Floor"),
    "Disney+": ("disneyplus.com", "Premium", ["Arts & Entertainment", "Television", "Streaming"], "Floor"),
    "Disney Plus": ("disneyplus.com", "Premium", ["Arts & Entertainment", "Television", "Streaming"], "Floor"),
    "ESPN": ("espn.com", "Premium", ["Sports", "News & Information"], "Low"),
    "Hulu": ("hulu.com", "Premium", ["Arts & Entertainment", "Television", "Streaming"], "Floor"),
    "Netflix": ("netflix.com", "Premium", ["Arts & Entertainment", "Television", "Streaming"], "Floor"),
    "Tubi": ("tubitv.com", "Mid-tier", ["Arts & Entertainment", "Television", "Streaming"], "Low"),
    "Pluto TV": ("pluto.tv", "Mid-tier", ["Arts & Entertainment", "Television", "Streaming"], "Low"),
    
    # News & Information
    "CNN": ("cnn.com", "Premium", ["News & Information", "News"], "Low"),
    "BBC": ("bbc.com", "Premium", ["News & Information", "News"], "Low"),
    "Reuters": ("reuters.com", "Premium", ["News & Information", "News"], "Low"),
    "The New York Times": ("nytimes.com", "Premium", ["News & Information", "News"], "Low"),
    "NYTimes": ("nytimes.com", "Premium", ["News & Information", "News"], "Low"),
    "The Wall Street Journal": ("wsj.com", "Premium", ["Business", "Finance", "News & Information"], "Low"),
    "WSJ": ("wsj.com", "Premium", ["Business", "Finance", "News & Information"], "Low"),
    "Forbes": ("forbes.com", "Premium", ["Business", "Finance"], "Low"),
    "The Hill": ("thehill.com", "Mid-tier", ["News & Information", "Politics"], "Medium"),
    
    # Business & Finance
    "Bloomberg": ("bloomberg.com", "Premium", ["Business", "Finance"], "Low"),
    "CNBC": ("cnbc.com", "Premium", ["Business", "Finance"], "Low"),
    
    # Technology
    "TechCrunch": ("techcrunch.com", "Premium", ["Technology & Computing", "News & Information"], "Low"),
    "The Verge": ("theverge.com", "Premium", ["Technology & Computing"], "Low"),
    
    # Gaming
    "Twitch": ("twitch.tv", "Mid-tier", ["Video Gaming", "Entertainment"], "Medium"),
    "Overwolf": ("overwolf.com", "Mid-tier", ["Video Gaming"], "Medium"),
    
    # SSPs/Publishers (often appear in BidSwitch)
    "Sovrn": ("sovrn.com", "Mid-tier", None, "Medium"),  # SSP, not a publisher
    "OpenX": ("openx.com", "Mid-tier", None, "Medium"),  # SSP
    "Magnite": ("magnite.com", "Mid-tier", None, "Medium"),  # SSP
}


class PublisherIntelligence:
    """
    Publisher intelligence for recognizing brands, domains, and quality indicators.
    """
    
    def __init__(self):
        """Initialize publisher intelligence."""
        self.knowledge_base = PUBLISHER_KNOWLEDGE_BASE
        self.brand_aliases = self._build_brand_aliases()
    
    def _build_brand_aliases(self) -> Dict[str, str]:
        """Build mapping from variations to canonical brand names."""
        aliases = {}
        for brand in self.knowledge_base.keys():
            # Add lowercase version
            aliases[brand.lower()] = brand
            # Add version without special chars
            aliases[re.sub(r'[^a-zA-Z0-9]', '', brand.lower())] = brand
        return aliases
    
    def _normalize_publisher_name(self, name: str) -> str:
        """Normalize publisher name for matching."""
        if not name:
            return ""
        # Remove common prefixes/suffixes
        name = re.sub(r'^(contact|reach out|please reach out for|list of)\s+', '', name, flags=re.IGNORECASE)
        name = name.strip()
        return name
    
    def _extract_domain(self, publisher_str: str) -> Optional[str]:
        """
        Extract domain from publisher string (may contain URLs or domains).
        
        Args:
            publisher_str: Publisher string that may contain domain/URL
            
        Returns:
            Extracted domain or None
        """
        if not publisher_str:
            return None
        
        # Check if it's already a domain/URL
        if '.' in publisher_str:
            # Try to parse as URL
            if not publisher_str.startswith(('http://', 'https://')):
                publisher_str = 'https://' + publisher_str
            
            try:
                parsed = urlparse(publisher_str)
                domain = parsed.netloc or parsed.path.split('/')[0]
                if domain:
                    return domain.lower()
            except Exception:
                pass
        
        return None
    
    def recognize_publisher(self, publisher_name: str) -> Optional[Dict[str, any]]:
        """
        Recognize publisher and return intelligence data.
        
        Args:
            publisher_name: Publisher name/string to recognize
            
        Returns:
            Dictionary with publisher intelligence or None if not recognized
            {
                'brand': canonical brand name,
                'domain': domain,
                'quality_tier': 'Premium'|'Mid-tier'|'RON',
                'category_hints': [list of taxonomy hints],
                'safety_hint': 'Floor'|'Low'|'Medium'|'High'
            }
        """
        if not publisher_name:
            return None
        
        normalized = self._normalize_publisher_name(publisher_name)
        
        # Direct match
        if normalized in self.knowledge_base:
            domain, quality_tier, category_hints, safety_hint = self.knowledge_base[normalized]
            return {
                'brand': normalized,
                'domain': domain,
                'quality_tier': quality_tier,
                'category_hints': category_hints or [],
                'safety_hint': safety_hint,
            }
        
        # Alias match
        normalized_lower = normalized.lower()
        if normalized_lower in self.brand_aliases:
            brand = self.brand_aliases[normalized_lower]
            domain, quality_tier, category_hints, safety_hint = self.knowledge_base[brand]
            return {
                'brand': brand,
                'domain': domain,
                'quality_tier': quality_tier,
                'category_hints': category_hints or [],
                'safety_hint': safety_hint,
            }
        
        # Try domain extraction
        domain = self._extract_domain(normalized)
        if domain:
            # Check if domain matches any known publisher
            for brand, (known_domain, quality_tier, category_hints, safety_hint) in self.knowledge_base.items():
                if known_domain and domain == known_domain:
                    return {
                        'brand': brand,
                        'domain': domain,
                        'quality_tier': quality_tier,
                        'category_hints': category_hints or [],
                        'safety_hint': safety_hint,
                    }
        
        return None
    
    def extract_publisher_context(self, publishers: List[str]) -> Dict[str, any]:
        """
        Extract publisher intelligence context from list of publishers.
        
        Args:
            publishers: List of publisher names
            
        Returns:
            Dictionary with aggregated publisher context:
            {
                'recognized_publishers': [list of recognized brands],
                'quality_tiers': [list of quality tiers],
                'category_hints': [aggregated category hints],
                'safety_hints': [list of safety hints],
                'has_premium': bool,
                'has_known_publishers': bool
            }
        """
        if not publishers:
            return {
                'recognized_publishers': [],
                'quality_tiers': [],
                'category_hints': [],
                'safety_hints': [],
                'has_premium': False,
                'has_known_publishers': False,
            }
        
        recognized = []
        quality_tiers = []
        category_hints_set = set()
        safety_hints = []
        
        for pub in publishers:
            intelligence = self.recognize_publisher(pub)
            if intelligence:
                recognized.append(intelligence['brand'])
                quality_tiers.append(intelligence['quality_tier'])
                category_hints_set.update(intelligence.get('category_hints', []))
                safety_hints.append(intelligence['safety_hint'])
        
        return {
            'recognized_publishers': recognized,
            'quality_tiers': list(set(quality_tiers)),
            'category_hints': list(category_hints_set),
            'safety_hints': list(set(safety_hints)),
            'has_premium': 'Premium' in quality_tiers,
            'has_known_publishers': len(recognized) > 0,
        }
    
    def format_publisher_context_for_prompt(self, publishers: List[str]) -> str:
        """
        Format publisher intelligence context for LLM prompt.
        
        Args:
            publishers: List of publisher names
            
        Returns:
            Formatted string with publisher context
        """
        context = self.extract_publisher_context(publishers)
        
        if not context['has_known_publishers']:
            return "Publisher Intelligence: No recognized publishers"
        
        parts = [f"Publisher Intelligence: Recognized {len(context['recognized_publishers'])} publisher(s)"]
        
        if context['recognized_publishers']:
            parts.append(f"Brands: {', '.join(context['recognized_publishers'][:5])}")
        
        if context['quality_tiers']:
            parts.append(f"Quality Tiers: {', '.join(context['quality_tiers'])}")
        
        if context['category_hints']:
            parts.append(f"Category Hints: {', '.join(context['category_hints'][:3])}")
        
        if context['safety_hints']:
            parts.append(f"Safety Hints: {', '.join(context['safety_hints'])}")
        
        return " | ".join(parts)
