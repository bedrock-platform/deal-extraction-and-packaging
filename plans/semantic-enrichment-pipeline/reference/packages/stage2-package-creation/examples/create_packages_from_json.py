#!/usr/bin/env python3
"""
Create Packages from JSON Example

Loads enriched deals from a JSON file and creates packages.
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
    """Create packages from JSON file"""
    
    # Check for input file
    if len(sys.argv) < 2:
        print("Usage: python create_packages_from_json.py <deals.json>")
        return 1
    
    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"✗ File not found: {input_file}")
        return 1
    
    # Load deals
    print(f"Loading deals from {input_file}...")
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Handle different JSON structures
    if isinstance(data, list):
        deals = data
    elif isinstance(data, dict) and 'deals' in data:
        deals = data['deals']
    elif isinstance(data, dict) and 'publishers' in data:
        deals = data['publishers']  # Handle publisher list format
    else:
        print("✗ Invalid JSON structure")
        return 1
    
    print(f"✓ Loaded {len(deals)} deals")
    
    if len(deals) < 5:
        print("✗ Need at least 5 deals for package creation")
        return 1
    
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
    
    # Progress callback
    def progress(msg):
        print(f"  {msg}")
    
    # Create packages
    print("\nCreating packages...")
    proposals = creator.create_packages(deals, progress_callback=progress)
    
    if not proposals:
        print("\n✗ No packages created")
        return 1
    
    # Save proposals
    output_file = "package_proposals.json"
    print(f"\nSaving proposals to {output_file}...")
    
    with open(output_file, 'w') as f:
        json.dump({
            'metadata': {
                'source': 'Package Creation Package',
                'input_file': input_file,
                'input_deal_count': len(deals),
                'proposal_count': len(proposals)
            },
            'proposals': proposals
        }, f, indent=2)
    
    print(f"✓ Saved {len(proposals)} proposals to {output_file}")
    
    # Display summary
    print("\n" + "=" * 60)
    print("Package Creation Summary:")
    print("=" * 60)
    print(f"Input deals: {len(deals)}")
    print(f"Packages created: {len(proposals)}")
    print(f"Output file: {output_file}")
    print("\nSample packages:")
    for i, proposal in enumerate(proposals[:5], 1):
        print(f"\n{i}. {proposal['package_name']}")
        print(f"   Deals: {len(proposal['deal_ids'])}")
        print(f"   Reasoning: {proposal['reasoning'][:100]}...")
    
    if len(proposals) > 5:
        print(f"\n... and {len(proposals) - 5} more packages")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
