"""
Package Enricher Module

Main class for enriching packages with aggregated deal-level metadata.
"""
import json
import time
from typing import Dict, Any, List, Optional, Callable

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    raise ImportError(
        "langchain-google-genai is required. "
        "Install with: pip install langchain-google-genai"
    )

from .aggregation import (
    aggregate_taxonomy,
    aggregate_safety,
    aggregate_audience,
    aggregate_commercial,
    calculate_health_score
)


def sanitize_numeric_field(value: Any) -> Optional[float]:
    """
    Sanitize numeric fields by converting "N/A", empty strings, or non-numeric strings to None.
    """
    if value is None:
        return None
    
    # If it's already a number, return as-is
    if isinstance(value, (int, float)):
        return float(value)
    
    # If it's a string, check if it's "N/A" or similar
    if isinstance(value, str):
        value_upper = value.strip().upper()
        # Check for N/A patterns
        if value_upper in ('N/A', 'NA', 'NULL', 'NONE', '') or value_upper.startswith('N/A'):
            return None
        # Try to parse as float
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    return None


class PackageEnricher:
    """
    Enriches packages with aggregated deal-level metadata and LLM-generated recommendations.
    
    Process:
    1. Formats deal enrichments for LLM
    2. Aggregates deal-level data (prices, volumes, taxonomy)
    3. Calls LLM for package-level recommendations
    4. Returns enriched package data
    """
    
    def __init__(
        self,
        llm_api_key: str,
        prompt_template: str,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.3,
        timeout: int = 90,
        max_retries: int = 3
    ):
        """
        Initialize PackageEnricher.
        
        Args:
            llm_api_key: Google Gemini API key
            prompt_template: LLM prompt template string (uses {package_name}, {deal_count}, {deal_enrichments} placeholders)
            model_name: LLM model name (default: "gemini-2.5-flash")
            temperature: LLM temperature (default: 0.3, lower for consistency)
            timeout: LLM timeout in seconds (default: 90)
            max_retries: Maximum retries on failure (default: 3)
        """
        self.prompt_template = prompt_template
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=llm_api_key,
            timeout=timeout,
            max_retries=max_retries
        )
    
    def enrich_package(
        self,
        package: Dict[str, Any],
        deals: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich a package using aggregated deal data and LLM.
        
        Args:
            package: Package dictionary with at least 'name' or 'package_name'
            deals: List of enriched deal dictionaries
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Enriched package dictionary with aggregated metadata and recommendations, or None on error
        """
        if not deals:
            if progress_callback:
                progress_callback("No deals provided for enrichment")
            return None
        
        # Format deal enrichments for LLM
        deal_enrichments = []
        total_avails = 0
        min_price = None
        max_price = None
        
        for deal in deals:
            enrichment = {
                "deal_id": deal.get("deal_id"),
                "deal_name": deal.get("deal_name"),
                "taxonomy": {
                    "tier1": deal.get("taxonomy_tier1") or deal.get("taxonomy", {}).get("tier1"),
                    "tier2": deal.get("taxonomy_tier2") or deal.get("taxonomy", {}).get("tier2"),
                    "tier3": deal.get("taxonomy_tier3") or deal.get("taxonomy", {}).get("tier3"),
                },
                "format": deal.get("format") or deal.get("creative_type"),
                "safety": {
                    "garm_risk_rating": deal.get("garm_risk_rating") or deal.get("safety", {}).get("garm_risk_rating"),
                    "family_safe": deal.get("family_safe") if deal.get("family_safe") is not None else deal.get("safety", {}).get("family_safe"),
                },
                "audience": {
                    "inferred_audience": deal.get("inferred_audience", []) or deal.get("audience", {}).get("inferred_audience", []),
                    "demographic_hint": deal.get("demographic_hint") or deal.get("audience", {}).get("demographic_hint"),
                },
                "commercial": {
                    "quality_tier": deal.get("quality_tier") or deal.get("commercial", {}).get("quality_tier"),
                    "volume_tier": deal.get("volume_tier") or deal.get("commercial", {}).get("volume_tier"),
                    "floor_price": deal.get("floor_price") or deal.get("commercial", {}).get("floor_price"),
                }
            }
            deal_enrichments.append(enrichment)
            
            # Aggregate commercial data
            price = enrichment["commercial"]["floor_price"]
            if price:
                price_float = sanitize_numeric_field(price)
                if price_float is not None:
                    if min_price is None or price_float < min_price:
                        min_price = price_float
                    if max_price is None or price_float > max_price:
                        max_price = price_float
            
            volume = deal.get("bid_request_volume") or deal.get("bidRequestsRatio") or deal.get("inventory_scale")
            if volume:
                volume_float = sanitize_numeric_field(volume)
                if volume_float:
                    total_avails += volume_float
        
        # Calculate enrichment coverage
        enriched_count = sum(1 for d in deals if d.get("taxonomy_tier1") or d.get("taxonomy", {}).get("tier1"))
        enrichment_coverage = enriched_count / len(deals) if deals else 0.0
        
        # Format prompt
        package_name = package.get("name") or package.get("package_name", "Unknown Package")
        prompt = self.prompt_template.format(
            package_name=package_name,
            deal_count=len(deals),
            deal_enrichments=json.dumps(deal_enrichments, indent=2)
        )
        
        # Call LLM
        try:
            if progress_callback:
                progress_callback(f"Calling LLM for package enrichment...")
            
            start_time = time.time()
            response = self.llm.invoke(prompt)
            elapsed = time.time() - start_time
            content = response.content
            
            if progress_callback:
                progress_callback(f"LLM response received ({elapsed:.1f}s)")
            
            # Parse JSON response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            enrichment = json.loads(content)
            
            # Get aggregated data
            taxonomy_agg = aggregate_taxonomy(deal_enrichments)
            safety_agg = aggregate_safety(deal_enrichments)
            audience_agg = aggregate_audience(deal_enrichments)
            commercial_agg = aggregate_commercial(deal_enrichments)
            
            # Calculate health score
            health_data = calculate_health_score(
                deals,
                quality_tier=commercial_agg.get('quality_tier'),
                risk_rating=safety_agg.get('garm_risk_rating'),
                volume_tier=commercial_agg.get('volume_tier'),
                enrichment_coverage=enrichment_coverage
            )
            
            # Map to output format
            enriched_data = {
                "package_id": package.get("package_id") or package.get("id"),
                "package_name": package_name,
                "deal_ids": package.get("deal_ids", []),  # Preserve deal_ids from Stage 2
                
                # Taxonomy (from LLM or aggregation)
                "taxonomy_tier1": enrichment.get("inventory", {}).get("dominant_taxonomy_tier1") or taxonomy_agg.get('dominant_taxonomy_tier1'),
                "taxonomy_tier2": enrichment.get("inventory", {}).get("dominant_taxonomy_tier2") or taxonomy_agg.get('dominant_taxonomy_tier2'),
                "taxonomy_tier3": enrichment.get("inventory", {}).get("dominant_taxonomy_tier3") or taxonomy_agg.get('dominant_taxonomy_tier3'),
                "dominant_concepts": enrichment.get("inventory", {}).get("dominant_concepts", []),
                
                # Safety (from LLM or aggregation)
                "garm_risk_rating": enrichment.get("safety", {}).get("garm_risk_rating") or safety_agg.get('garm_risk_rating'),
                "family_safe": enrichment.get("safety", {}).get("family_safe") if enrichment.get("safety", {}).get("family_safe") is not None else safety_agg.get('family_safe'),
                "safe_for_verticals": enrichment.get("safety", {}).get("safe_for_verticals", []) or safety_agg.get('safe_for_verticals', []),
                
                # Audience (from LLM or aggregation)
                "inferred_audience": enrichment.get("audience", {}).get("primary_audience", []) or audience_agg.get('primary_audience', []),
                "demographic_hint": enrichment.get("audience", {}).get("demographic_profile") or audience_agg.get('demographic_profile'),
                
                # Commercial (from LLM or aggregation)
                "quality_tier": enrichment.get("commercial", {}).get("quality_tier") or commercial_agg.get('quality_tier'),
                "floor_price_min": sanitize_numeric_field(enrichment.get("commercial", {}).get("floor_price_min")) or commercial_agg.get('floor_price_min') or min_price,
                "floor_price_max": sanitize_numeric_field(enrichment.get("commercial", {}).get("floor_price_max")) or commercial_agg.get('floor_price_max') or max_price,
                "total_daily_avails": sanitize_numeric_field(enrichment.get("commercial", {}).get("total_daily_avails")) or total_avails,
                
                # Health (from LLM or calculation)
                "deal_count": enrichment.get("health", {}).get("deal_count") or health_data.get('deal_count'),
                "enrichment_coverage": enrichment.get("health", {}).get("enrichment_coverage") or health_data.get('enrichment_coverage'),
                "health_score": enrichment.get("health", {}).get("health_score") or health_data.get('health_score'),
                
                # Recommendations (from LLM)
                "recommended_use_cases": enrichment.get("recommendations", {}).get("recommended_use_cases", []),
                "recommended_verticals": enrichment.get("recommendations", {}).get("recommended_verticals", []),
                "agent_recommendation": enrichment.get("recommendations", {}).get("agent_recommendation"),
                
                # Confidence
                "confidence": enrichment.get("confidence", 0.5),
                
                # Raw LLM response for debugging
                "raw_llm_response": json.dumps(enrichment)
            }
            
            return enriched_data
            
        except json.JSONDecodeError as e:
            if progress_callback:
                progress_callback(f"JSON parse error: {e}")
            return None
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error: {e}")
            return None
