#!/usr/bin/env python3
"""
Audit packages across Stage 2 JSON, Google Sheets worksheets, and TSV files.

Identifies missing packages and creates a backfill plan.
"""
import sys
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.data_exporter import UnifiedDataExporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_package_name(package: Dict[str, Any]) -> str:
    """Extract package name as unique identifier."""
    # Try various name fields (handle both nested and flattened structures)
    package_name = (
        package.get('package_name') or
        package.get('name') or
        None
    )
    
    # Handle flattened dicts (e.g., from Google Sheets)
    if not package_name:
        # Check for flattened keys
        for key in package.keys():
            if 'package_name' in key.lower():
                val = package.get(key)
                if val and isinstance(val, str) and val.strip():
                    package_name = val
                    break
    
    # Also check for just 'name' field
    if not package_name:
        for key in package.keys():
            if key.lower() == 'name' and 'package' not in key.lower():
                val = package.get(key)
                if val and isinstance(val, str) and val.strip():
                    package_name = val
                    break
    
    if not package_name:
        # Last resort: try to construct from deal_ids
        deal_ids = package.get('deal_ids', [])
        if not deal_ids:
            # Check for flattened deal_ids
            for key in package.keys():
                if 'deal_id' in key.lower() and 's' in key.lower():
                    val = package.get(key)
                    if val:
                        if isinstance(val, list):
                            deal_ids = val
                        elif isinstance(val, str):
                            # Try to parse JSON string
                            try:
                                deal_ids = json.loads(val)
                            except:
                                deal_ids = [val] if val else []
                        break
        
        if deal_ids:
            if isinstance(deal_ids, str):
                deal_ids = [deal_ids]
            package_name = f"package_{'_'.join(map(str, deal_ids[:3]))}"
        else:
            # Last resort: hash
            package_name = f"unknown_{hash(str(sorted(package.items())))}"
    
    return str(package_name).strip()


def load_packages_from_json(json_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load packages from Stage 2 JSON file."""
    logger.info(f"Loading packages from {json_path}")
    with open(json_path, 'r') as f:
        packages = json.load(f)
    
    result = {}
    for pkg in packages:
        pkg_name = get_package_name(pkg)
        result[pkg_name] = pkg
    
    logger.info(f"Loaded {len(result)} packages from JSON")
    return result


def load_packages_from_sheets(exporter: UnifiedDataExporter, worksheet_name: str) -> Dict[str, Dict[str, Any]]:
    """Load packages from Google Sheets worksheet."""
    logger.info(f"Loading packages from Google Sheets worksheet '{worksheet_name}'")
    
    spreadsheet = exporter._get_spreadsheet()
    if not spreadsheet:
        logger.error("Could not authenticate with Google Sheets")
        return {}
    
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
        all_values = worksheet.get_all_values()
        
        logger.info(f"Retrieved {len(all_values)} total rows from worksheet")
        
        if len(all_values) < 1:
            logger.warning(f"Worksheet '{worksheet_name}' is empty")
            return {}
        
        if len(all_values) < 2:  # Need at least header + 1 row
            logger.warning(f"Worksheet '{worksheet_name}' has header but no data rows")
            return {}
        
        # First row is header
        header = all_values[0]
        data_rows = all_values[1:]
        
        logger.info(f"Found {len(data_rows)} data rows with {len(header)} columns")
        logger.info(f"Sample columns: {header[:10]}")
        
        # Convert to list of dicts
        packages = []
        for row_idx, row in enumerate(data_rows):
            if not any(row):  # Skip empty rows
                continue
            pkg_dict = {}
            for i, col_name in enumerate(header):
                if i < len(row):
                    val = row[i] if row[i] else None
                    # Try to parse JSON strings
                    if val and isinstance(val, str) and val.startswith('['):
                        try:
                            val = json.loads(val)
                        except:
                            pass
                    pkg_dict[col_name] = val
            packages.append(pkg_dict)
            
            # Log first package structure for debugging
            if row_idx == 0:
                logger.info(f"First package keys: {list(pkg_dict.keys())[:10]}")
                logger.info(f"First package sample values: {dict(list(pkg_dict.items())[:5])}")
        
        # Index by package name
        result = {}
        sample_names = []
        for pkg in packages:
            pkg_name = get_package_name(pkg)
            result[pkg_name] = pkg
            if len(sample_names) < 5:
                sample_names.append(pkg_name)
        
        logger.info(f"Loaded {len(result)} packages from worksheet '{worksheet_name}'")
        if sample_names:
            logger.info(f"Sample package names: {sample_names}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to load from worksheet '{worksheet_name}': {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return {}


def load_packages_from_tsv(tsv_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load packages from TSV file."""
    logger.info(f"Loading packages from TSV: {tsv_path}")
    
    try:
        df = pd.read_csv(tsv_path, sep='\t')
        packages = df.to_dict('records')
        
        result = {}
        for pkg in packages:
            pkg_name = get_package_name(pkg)
            result[pkg_name] = pkg
        
        logger.info(f"Loaded {len(result)} packages from TSV")
        return result
    except Exception as e:
        logger.error(f"Failed to load TSV: {e}")
        return {}


def find_missing_packages(
    source_packages: Dict[str, Dict[str, Any]],
    target_packages: Dict[str, Dict[str, Any]],
    target_name: str
) -> List[Dict[str, Any]]:
    """Find packages in source but not in target."""
    source_ids = set(source_packages.keys())
    target_ids = set(target_packages.keys())
    
    missing_ids = source_ids - target_ids
    missing_packages = [source_packages[pkg_id] for pkg_id in missing_ids]
    
    if missing_packages:
        logger.warning(f"Found {len(missing_packages)} missing packages in {target_name}")
        for pkg in missing_packages:
            pkg_name = get_package_name(pkg)
            logger.info(f"  - Missing: {pkg_name}")
    else:
        logger.info(f"All packages present in {target_name}")
    
    return missing_packages


def audit_packages(
    packages_json_path: Path,
    google_sheets_id: Optional[str] = None,
    tsv_path_stage2: Optional[Path] = None,
    tsv_path_stage3: Optional[Path] = None
):
    """Audit packages across all sources."""
    logger.info("=" * 80)
    logger.info("PACKAGE AUDIT")
    logger.info("=" * 80)
    
    # Load source of truth (Stage 2 JSON)
    source_packages = load_packages_from_json(packages_json_path)
    
    if not source_packages:
        logger.error("No packages found in source JSON file")
        return
    
    logger.info(f"\nSource (Stage 2 JSON): {len(source_packages)} packages")
    
    # Load from Google Sheets if available
    sheets_packages_stage2 = {}
    sheets_packages_stage3 = {}
    
    if google_sheets_id:
        exporter = UnifiedDataExporter(Path("output"))
        exporter.google_sheets_id = google_sheets_id
        
        sheets_packages_stage2 = load_packages_from_sheets(exporter, "Packages Enriched 1")
        sheets_packages_stage3 = load_packages_from_sheets(exporter, "Packages Enriched 2")
    
    # Load from TSV files if provided
    tsv_packages_stage2 = {}
    tsv_packages_stage3 = {}
    
    if tsv_path_stage2 and tsv_path_stage2.exists():
        tsv_packages_stage2 = load_packages_from_tsv(tsv_path_stage2)
    
    if tsv_path_stage3 and tsv_path_stage3.exists():
        tsv_packages_stage3 = load_packages_from_tsv(tsv_path_stage3)
    
    # Compare and find missing packages
    logger.info("\n" + "=" * 80)
    logger.info("MISSING PACKAGES ANALYSIS")
    logger.info("=" * 80)
    
    missing_stage2_sheets = find_missing_packages(source_packages, sheets_packages_stage2, "Stage 2 Sheets")
    missing_stage3_sheets = find_missing_packages(source_packages, sheets_packages_stage3, "Stage 3 Sheets")
    
    missing_stage2_tsv = []
    missing_stage3_tsv = []
    
    if tsv_packages_stage2:
        missing_stage2_tsv = find_missing_packages(source_packages, tsv_packages_stage2, "Stage 2 TSV")
    
    if tsv_packages_stage3:
        missing_stage3_tsv = find_missing_packages(source_packages, tsv_packages_stage3, "Stage 3 TSV")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Source packages (Stage 2 JSON): {len(source_packages)}")
    logger.info(f"Stage 2 Sheets: {len(sheets_packages_stage2)} packages ({len(missing_stage2_sheets)} missing)")
    logger.info(f"Stage 3 Sheets: {len(sheets_packages_stage3)} packages ({len(missing_stage3_sheets)} missing)")
    
    if tsv_packages_stage2:
        logger.info(f"Stage 2 TSV: {len(tsv_packages_stage2)} packages ({len(missing_stage2_tsv)} missing)")
    
    if tsv_packages_stage3:
        logger.info(f"Stage 3 TSV: {len(tsv_packages_stage3)} packages ({len(missing_stage3_tsv)} missing)")
    
    # Create backfill plan
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL PLAN")
    logger.info("=" * 80)
    
    # Find packages missing from BOTH sheets
    missing_stage2_names = {get_package_name(p) for p in missing_stage2_sheets}
    missing_stage3_names = {get_package_name(p) for p in missing_stage3_sheets}
    missing_both = missing_stage2_names & missing_stage3_names
    
    if missing_both:
        logger.info(f"\nPackages missing from BOTH sheets ({len(missing_both)}):")
        for pkg_name in sorted(missing_both):
            logger.info(f"  - {pkg_name}")
    
    # Save missing packages to JSON for backfill
    if missing_stage2_sheets or missing_stage3_sheets:
        missing_all = {}
        for pkg in missing_stage2_sheets + missing_stage3_sheets:
            pkg_name = get_package_name(pkg)
            if pkg_name not in missing_all:
                missing_all[pkg_name] = pkg
        
        missing_file = packages_json_path.parent / f"missing_packages_{packages_json_path.stem}.json"
        with open(missing_file, 'w') as f:
            json.dump(list(missing_all.values()), f, indent=2)
        
        logger.info(f"\nSaved {len(missing_all)} unique missing packages to: {missing_file}")
        logger.info("\nTo backfill Stage 2 packages:")
        logger.info(f"  python -m src.deal_extractor --stage-2-only <deals_enriched.jsonl> --packages-json {missing_file}")
        logger.info("\nTo backfill Stage 3 packages:")
        logger.info(f"  python -m src.deal_extractor --stage-3 <packages_json> <deals_enriched.jsonl>")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Audit packages across sources")
    parser.add_argument("packages_json", type=Path, help="Path to Stage 2 packages JSON file")
    parser.add_argument("--google-sheets-id", type=str, help="Google Sheets ID (or use GOOGLE_SHEETS_ID env var)")
    parser.add_argument("--tsv-stage2", type=Path, help="Path to Stage 2 TSV file (optional)")
    parser.add_argument("--tsv-stage3", type=Path, help="Path to Stage 3 TSV file (optional)")
    
    args = parser.parse_args()
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    google_sheets_id = args.google_sheets_id or os.getenv("GOOGLE_SHEETS_ID")
    
    if not google_sheets_id:
        logger.warning("No Google Sheets ID provided. Skipping Google Sheets audit.")
    
    audit_packages(
        packages_json_path=args.packages_json,
        google_sheets_id=google_sheets_id,
        tsv_path_stage2=args.tsv_stage2,
        tsv_path_stage3=args.tsv_stage3
    )
