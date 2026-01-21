#!/usr/bin/env python3
"""
Basic Usage Example

Demonstrates how to enrich packages with aggregated deal-level metadata.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from package_enrichment import PackageEnricher


def load_prompt_template() -> str:
    """Load prompt template"""
    prompt_path = Path(__file__).parent.parent / "config" / "package_enrichment_prompt.txt"
    with open(prompt_path, 'r') as f:
        return f.read()


def main():
    """Basic example of enriching packages"""
    
    # Sample package with deal IDs
    package = {
        "package_id": 5001,
        "name": "Premium Auto Intender CTV Package",
        "included_deal_ids": [3001, 3002, 3003, 3004]
    }
    
    # Sample enriched deals (in real usage, load from your database)
    deals = [
        {
            "deal_id": 3001,
            "deal_name": "Premium CTV Auto Inventory",
            "taxonomy_tier1": "Automotive",
            "taxonomy_tier2": "Auto Parts & Accessories",
            "taxonomy_tier3": "Auto Repair",
            "format": "video",
            "garm_risk_rating": "Low",
            "family_safe": True,
            "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
            "demographic_hint": "25-54, High Income",
            "quality_tier": "Premium",
            "volume_tier": "High",
            "floor_price": 5.50,
            "bid_request_volume": 50000000
        },
        {
            "deal_id": 3002,
            "deal_name": "Auto-Focused CTV Streaming",
            "taxonomy_tier1": "Automotive",
            "taxonomy_tier2": "Auto Parts & Accessories",
            "taxonomy_tier3": "Auto Repair",
            "format": "video",
            "garm_risk_rating": "Low",
            "family_safe": True,
            "inferred_audience": ["Auto Intenders"],
            "demographic_hint": "25-54, High Income",
            "quality_tier": "Premium",
            "volume_tier": "High",
            "floor_price": 6.00,
            "bid_request_volume": 45000000
        },
        # Add more deals...
    ]
    
    # Initialize enricher
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("✗ GEMINI_API_KEY environment variable not set")
        return 1
    
    prompt_template = load_prompt_template()
    
    enricher = PackageEnricher(
        llm_api_key=api_key,
        prompt_template=prompt_template
    )
    
    print("Enriching package with aggregated deal data...")
    
    # Progress callback
    def progress(msg):
        print(f"  {msg}")
    
    # Enrich package
    enriched = enricher.enrich_package(package, deals, progress_callback=progress)
    
    if not enriched:
        print("✗ Enrichment failed")
        return 1
    
    print(f"\n✓ Package enriched successfully!")
    print(f"\nEnriched Package Data:")
    print(json.dumps(enriched, indent=2, default=str))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
