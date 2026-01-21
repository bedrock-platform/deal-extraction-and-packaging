#!/usr/bin/env python3
"""
Backfill excluded deals packages to Stage 3 output.

These packages have empty deal_ids arrays and are skipped during normal Stage 3 enrichment.
This script exports them directly to Stage 3 format without LLM enrichment.
"""
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.package_enrichment.incremental_exporter import EnrichedPackageIncrementalExporter
from src.common.data_exporter import UnifiedDataExporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_minimal_enriched_package(package: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a minimal enriched package for excluded deals.
    
    Since these packages have no deals, we create a minimal structure
    with just the package metadata.
    """
    return {
        "package_id": None,
        "package_name": package.get("package_name") or package.get("name"),
        "deal_ids": package.get("deal_ids", []),
        "deals": [],  # Empty since these are excluded deals
        "reasoning": package.get("reasoning", ""),
        "excluded_deals": package.get("excluded_deals", []),
        # Minimal enrichment fields
        "taxonomy": {
            "tier1": "Excluded",
            "tier2": "Excluded Deals",
            "tier3": None
        },
        "dominant_concepts": ["Excluded Deals"],
        "garm_risk_rating": "N/A",
        "family_safe": None,
        "safe_for_verticals": [],
        "target_audience": "N/A - Excluded Deals Package",
        "recommended_use_cases": [],
        "recommended_advertiser_types": [],
        "package_summary": package.get("reasoning", "Package contains excluded deals that did not meet package requirements.")
    }


def backfill_excluded_deals(
    packages_json_path: Path,
    output_dir: Path,
    google_sheets_id: str = None
):
    """Backfill excluded deals packages to Stage 3 output."""
    logger.info("=" * 80)
    logger.info("BACKFILL EXCLUDED DEALS PACKAGES")
    logger.info("=" * 80)
    
    # Load packages
    logger.info(f"Loading packages from {packages_json_path}")
    with open(packages_json_path, 'r') as f:
        all_packages = json.load(f)
    
    # Filter for excluded deals packages (empty deal_ids)
    excluded_packages = [
        pkg for pkg in all_packages
        if not pkg.get('deal_ids') or len(pkg.get('deal_ids', [])) == 0
    ]
    
    logger.info(f"Found {len(excluded_packages)} excluded deals packages")
    
    if not excluded_packages:
        logger.info("No excluded deals packages found. Nothing to backfill.")
        return
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
    
    # Initialize incremental exporter
    exporter = EnrichedPackageIncrementalExporter(
        output_dir=output_dir,
        timestamp=timestamp,
        google_sheets_id=google_sheets_id
    )
    
    # Export each excluded package
    logger.info("\nExporting excluded deals packages...")
    for i, package in enumerate(excluded_packages, 1):
        pkg_name = package.get("package_name") or package.get("name", "Unknown")
        logger.info(f"[{i}/{len(excluded_packages)}] Exporting: {pkg_name}")
        
        # Create minimal enriched package
        enriched_package = create_minimal_enriched_package(package)
        
        # Export to files and Google Sheets
        exporter.export_package(enriched_package)
    
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Exported {len(excluded_packages)} excluded deals packages")
    logger.info(f"Output directory: {output_dir}")
    if google_sheets_id:
        logger.info(f"Google Sheets: Updated 'Packages Enriched 2' worksheet")


if __name__ == "__main__":
    import argparse
    import os
    from dotenv import load_dotenv
    
    parser = argparse.ArgumentParser(description="Backfill excluded deals packages to Stage 3")
    parser.add_argument("packages_json", type=Path, help="Path to packages JSON file")
    parser.add_argument("--output-dir", type=Path, default=Path("output"), help="Output directory")
    parser.add_argument("--google-sheets-id", type=str, help="Google Sheets ID (or use GOOGLE_SHEETS_ID env var)")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    google_sheets_id = args.google_sheets_id or os.getenv("GOOGLE_SHEETS_ID")
    
    if not args.packages_json.exists():
        logger.error(f"Packages JSON file not found: {args.packages_json}")
        sys.exit(1)
    
    backfill_excluded_deals(
        packages_json_path=args.packages_json,
        output_dir=args.output_dir,
        google_sheets_id=google_sheets_id
    )
