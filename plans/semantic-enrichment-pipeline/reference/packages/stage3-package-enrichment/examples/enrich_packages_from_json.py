#!/usr/bin/env python3
"""
Enrich Packages from JSON Example

Loads packages and deals from JSON files and enriches packages.
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
    """Enrich packages from JSON files"""
    
    # Check for input files
    if len(sys.argv) < 3:
        print("Usage: python enrich_packages_from_json.py <packages.json> <deals.json>")
        return 1
    
    packages_file = sys.argv[1]
    deals_file = sys.argv[2]
    
    if not Path(packages_file).exists():
        print(f"✗ File not found: {packages_file}")
        return 1
    
    if not Path(deals_file).exists():
        print(f"✗ File not found: {deals_file}")
        return 1
    
    # Load packages
    print(f"Loading packages from {packages_file}...")
    with open(packages_file, 'r') as f:
        packages_data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(packages_data, list):
        packages = packages_data
    elif isinstance(packages_data, dict) and 'packages' in packages_data:
        packages = packages_data['packages']
    else:
        print("✗ Invalid packages JSON structure")
        return 1
    
    print(f"✓ Loaded {len(packages)} packages")
    
    # Load deals
    print(f"Loading deals from {deals_file}...")
    with open(deals_file, 'r') as f:
        deals_data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(deals_data, list):
        all_deals = deals_data
    elif isinstance(deals_data, dict) and 'deals' in deals_data:
        all_deals = deals_data['deals']
    else:
        print("✗ Invalid deals JSON structure")
        return 1
    
    # Create deals lookup
    deals_lookup = {deal['deal_id']: deal for deal in all_deals}
    print(f"✓ Loaded {len(all_deals)} deals")
    
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
    
    # Progress callback
    def progress(msg):
        print(f"  {msg}")
    
    # Enrich packages
    print(f"\nEnriching {len(packages)} packages...")
    enriched_packages = []
    
    for i, package in enumerate(packages, 1):
        package_id = package.get('package_id') or package.get('id')
        package_name = package.get('name') or package.get('package_name', f'Package {package_id}')
        
        print(f"\n[{i}/{len(packages)}] {package_name}...")
        
        # Get deal IDs
        deal_ids = package.get('included_deal_ids') or package.get('includedSupplyDealIDs', [])
        if not deal_ids:
            print("  ⚠️  No deal IDs found, skipping")
            continue
        
        # Get deals for this package
        deals = [deals_lookup.get(did) for did in deal_ids if did in deals_lookup]
        deals = [d for d in deals if d is not None]  # Remove None values
        
        if not deals:
            print("  ⚠️  No deals found, skipping")
            continue
        
        print(f"  Found {len(deals)} deals")
        
        # Enrich package
        enriched = enricher.enrich_package(package, deals, progress_callback=progress)
        
        if enriched:
            enriched_packages.append(enriched)
            print(f"  ✓ Enriched (health score: {enriched.get('health_score', 'N/A')})")
        else:
            print(f"  ✗ Enrichment failed")
    
    if not enriched_packages:
        print("\n✗ No packages enriched")
        return 1
    
    # Save enriched packages
    output_file = "enriched_packages.json"
    print(f"\nSaving enriched packages to {output_file}...")
    
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'source': 'Package Enrichment Package',
                'input_packages': len(packages),
                'enriched_count': len(enriched_packages)
            },
            'packages': enriched_packages
        }, f, indent=2, default=str)
    
    print(f"✓ Saved {len(enriched_packages)} enriched packages to {output_file}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("Enrichment Summary:")
    print("=" * 60)
    print(f"Input packages: {len(packages)}")
    print(f"Enriched packages: {len(enriched_packages)}")
    print(f"Output file: {output_file}")
    print("\nSample enriched packages:")
    for i, pkg in enumerate(enriched_packages[:3], 1):
        print(f"\n{i}. {pkg['package_name']}")
        print(f"   Health Score: {pkg.get('health_score', 'N/A')}")
        print(f"   Taxonomy: {pkg.get('taxonomy_tier1', 'N/A')}")
        print(f"   Use Cases: {', '.join(pkg.get('recommended_use_cases', [])[:3])}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
