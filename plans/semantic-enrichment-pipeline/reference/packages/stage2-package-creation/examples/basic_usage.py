#!/usr/bin/env python3
"""
Basic Usage Example

Demonstrates how to create packages from enriched deals.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from package_creation import PackageCreator


def load_prompt_template() -> str:
    """Load prompt template"""
    prompt_path = Path(__file__).parent.parent / "config" / "package_grouping_prompt.txt"
    with open(prompt_path, 'r') as f:
        return f.read()


def main():
    """Basic example of creating packages"""
    
    # Sample enriched deals (in real usage, load from your database)
    sample_deals = [
        {
            "deal_id": "3001",
            "deal_name": "Premium CTV Auto Inventory",
            "ssp_name": "BidSwitch",
            "format": "video",
            "taxonomy": {
                "tier1": "Automotive",
                "tier2": "Auto Parts & Accessories",
                "tier3": "Auto Repair"
            },
            "concepts": ["auto", "luxury", "premium"],
            "safety": {
                "garm_risk_rating": "Low",
                "family_safe": True
            },
            "audience": {
                "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
                "demographic_hint": "25-54, High Income"
            },
            "commercial": {
                "quality_tier": "Premium",
                "volume_tier": "High",
                "floor_price": 5.50
            },
            "publishers": ["Paramount", "Disney+"]
        },
        {
            "deal_id": "3002",
            "deal_name": "Family Entertainment Streaming",
            "ssp_name": "BidSwitch",
            "format": "video",
            "taxonomy": {
                "tier1": "Entertainment",
                "tier2": "Streaming",
                "tier3": "Family Entertainment"
            },
            "concepts": ["streaming", "family", "entertainment"],
            "safety": {
                "garm_risk_rating": "Floor",
                "family_safe": True
            },
            "audience": {
                "inferred_audience": ["Cord-cutters", "Streaming Subscribers"],
                "demographic_hint": "18-49, Family Households"
            },
            "commercial": {
                "quality_tier": "Premium",
                "volume_tier": "High",
                "floor_price": 4.25
            },
            "publishers": ["Disney+", "ESPN"]
        },
        # Add more deals...
    ]
    
    # Initialize creator
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("✗ GEMINI_API_KEY environment variable not set")
        return 1
    
    prompt_template = load_prompt_template()
    
    creator = PackageCreator(
        llm_api_key=api_key,
        prompt_template=prompt_template
    )
    
    print("Creating packages from deals...")
    
    # Progress callback
    def progress(msg):
        print(f"  {msg}")
    
    # Create packages
    proposals = creator.create_packages(sample_deals, progress_callback=progress)
    
    print(f"\n✓ Created {len(proposals)} package proposals:")
    for i, proposal in enumerate(proposals, 1):
        print(f"\n{i}. {proposal['package_name']}")
        print(f"   Deals: {len(proposal['deal_ids'])}")
        print(f"   Reasoning: {proposal['reasoning']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
