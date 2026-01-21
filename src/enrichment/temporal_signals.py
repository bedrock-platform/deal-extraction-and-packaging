"""
Temporal Signal Extraction

Extracts temporal signals from deal start_time/end_time to enhance enrichment.
Detects seasonal patterns, temporal mismatches, and time-based taxonomy hints.
"""
import logging
import re
from typing import Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# Seasonal patterns
SEASONAL_KEYWORDS = {
    'holiday': ['holiday', 'christmas', 'xmas', 'thanksgiving', 'halloween', 'easter', 'valentine', 'new year'],
    'seasonal': ['summer', 'winter', 'spring', 'fall', 'autumn', 'back to school', 'bfcm', 'black friday', 'cyber monday'],
    'sports': ['world cup', 'super bowl', 'olympics', 'nfl', 'nba', 'mlb', 'playoffs', 'championship'],
    'events': ['election', 'political', 'inauguration', 'awards', 'oscars', 'grammy'],
}


class TemporalSignalExtractor:
    """
    Extracts temporal signals from deal metadata.
    """
    
    def __init__(self):
        """Initialize temporal signal extractor."""
        pass
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse ISO 8601 datetime string."""
        if not dt_str:
            return None
        
        try:
            # Handle ISO 8601 with 'Z' suffix
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            return datetime.fromisoformat(dt_str)
        except Exception as e:
            logger.debug(f"Failed to parse datetime '{dt_str}': {e}")
            return None
    
    def _extract_year_from_name(self, deal_name: str) -> Optional[int]:
        """Extract year from deal name (e.g., 'WorldCup_2022' -> 2022)."""
        if not deal_name:
            return None
        
        # Look for 4-digit years (2000-2099)
        year_match = re.search(r'20\d{2}', deal_name)
        if year_match:
            try:
                return int(year_match.group())
            except ValueError:
                pass
        
        return None
    
    def _detect_seasonal_keywords(self, deal_name: str, description: Optional[str] = None) -> List[str]:
        """Detect seasonal keywords in deal name/description."""
        if not deal_name:
            return []
        
        text = (deal_name + ' ' + (description or '')).lower()
        detected = []
        
        for category, keywords in SEASONAL_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    detected.append(category)
                    break
        
        return list(set(detected))  # Remove duplicates
    
    def extract_temporal_signals(
        self,
        deal_name: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Extract temporal signals from deal metadata.
        
        Args:
            deal_name: Deal name (may contain temporal references)
            start_time: Deal start time (ISO 8601)
            end_time: Deal end time (ISO 8601)
            description: Deal description (optional)
            
        Returns:
            Dictionary with temporal signals:
            {
                'seasonal_patterns': [list of detected patterns],
                'temporal_relevance': 'current'|'legacy'|'future'|'unknown',
                'deal_year': extracted year from name,
                'active_year': year from start_time,
                'year_mismatch': bool,
                'duration_days': deal duration in days,
                'is_long_term': bool (duration > 365 days),
                'taxonomy_hints': [time-based taxonomy hints]
            }
        """
        signals = {
            'seasonal_patterns': [],
            'temporal_relevance': 'unknown',
            'deal_year': None,
            'active_year': None,
            'year_mismatch': False,
            'duration_days': None,
            'is_long_term': False,
            'taxonomy_hints': [],
        }
        
        # Extract year from deal name
        deal_year = self._extract_year_from_name(deal_name)
        signals['deal_year'] = deal_year
        
        # Parse start/end times
        start_dt = self._parse_datetime(start_time)
        end_dt = self._parse_datetime(end_time)
        
        if start_dt:
            signals['active_year'] = start_dt.year
        
        # Calculate duration
        if start_dt and end_dt:
            duration = end_dt - start_dt
            signals['duration_days'] = duration.days
            signals['is_long_term'] = duration.days > 365
        
        # Detect seasonal patterns
        seasonal_patterns = self._detect_seasonal_keywords(deal_name, description)
        signals['seasonal_patterns'] = seasonal_patterns
        
        # Check temporal relevance
        if deal_year and start_dt:
            active_year = start_dt.year
            year_diff = active_year - deal_year
            
            if year_diff < -1:
                signals['temporal_relevance'] = 'future'
            elif year_diff == 0 or year_diff == -1:
                signals['temporal_relevance'] = 'current'
            elif year_diff > 0:
                signals['temporal_relevance'] = 'legacy'
                signals['year_mismatch'] = True
        elif start_dt:
            signals['temporal_relevance'] = 'current'
        
        # Generate taxonomy hints from temporal signals
        taxonomy_hints = []
        
        if 'holiday' in seasonal_patterns:
            taxonomy_hints.append('Holiday Content')
        if 'seasonal' in seasonal_patterns:
            taxonomy_hints.append('Seasonal Content')
        if 'sports' in seasonal_patterns:
            taxonomy_hints.append('Sports')
            if signals['year_mismatch']:
                taxonomy_hints.append('Legacy Sports Content')
        if 'events' in seasonal_patterns:
            taxonomy_hints.append('News & Information')
            if 'political' in deal_name.lower() or 'election' in deal_name.lower():
                taxonomy_hints.append('Politics')
        
        signals['taxonomy_hints'] = taxonomy_hints
        
        return signals
    
    def format_temporal_context_for_prompt(self, signals: Dict[str, any]) -> str:
        """
        Format temporal signals for LLM prompt.
        
        Args:
            signals: Temporal signals dictionary
            
        Returns:
            Formatted string with temporal context
        """
        if not signals or signals['temporal_relevance'] == 'unknown':
            return ""
        
        parts = []
        
        # Temporal relevance
        if signals['temporal_relevance'] == 'legacy':
            parts.append(f"⚠️ TEMPORAL MISMATCH: Deal name references year {signals['deal_year']} but is active in {signals['active_year']}")
            parts.append("This may be legacy content or a reused deal ID")
        elif signals['temporal_relevance'] == 'future':
            parts.append(f"Future event: Deal name references year {signals['deal_year']}")
        
        # Seasonal patterns
        if signals['seasonal_patterns']:
            parts.append(f"Seasonal Patterns: {', '.join(signals['seasonal_patterns'])}")
        
        # Duration
        if signals['duration_days']:
            if signals['is_long_term']:
                parts.append(f"Long-term deal: {signals['duration_days']} days duration")
            else:
                parts.append(f"Duration: {signals['duration_days']} days")
        
        # Taxonomy hints
        if signals['taxonomy_hints']:
            parts.append(f"Temporal Taxonomy Hints: {', '.join(signals['taxonomy_hints'])}")
        
        return " | ".join(parts) if parts else ""
