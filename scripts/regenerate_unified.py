#!/usr/bin/env python3
"""
Regenerate unified TSV file from JSON and upload to Google Sheets.

This script:
1. Adds 'source' field to deals (if missing)
2. Regenerates unified TSV file
3. Optionally uploads to Google Sheets
"""
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from src.common.data_exporter import UnifiedDataExporter, flatten_dict
import pandas as pd

# Load environment variables from .env file
load_dotenv()


def add_source_field(deal: Dict[str, Any], vendor_name: str) -> str:
    """Determine source field from vendor name or existing source."""
    if "source" in deal and deal["source"]:
        return deal["source"]
    
    # Map vendor name to source
    if vendor_name == "Google Authorized Buyers":
        return "Google Authorized Buyers"
    elif vendor_name == "Google Curated":
        return "Google Curated"
    elif vendor_name == "BidSwitch":
        return "BidSwitch"
    else:
        return vendor_name


def process_json_file(json_file: Path) -> Dict[str, list]:
    """Process JSON file to add source field if missing."""
    print(f"Reading JSON file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_deals = 0
    
    for vendor_name, deals in data.items():
        print(f"\nProcessing {vendor_name}: {len(deals)} deals")
        for deal in deals:
            total_deals += 1
            source = add_source_field(deal, vendor_name)
            deal["source"] = source
    
    print(f"\n✅ Processed {total_deals} deals")
    return data


def regenerate_unified_tsv(json_file: Path, timestamp: str, output_dir: Path) -> Path:
    """Regenerate unified TSV file from JSON."""
    print(f"\nRegenerating unified TSV from: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_deals = []
    for vendor_deals in data.values():
        all_deals.extend(vendor_deals)
    
    print(f"Total deals: {len(all_deals)}")
    
    # For unified TSV: exclude raw_deal_data from flattening, keep it as JSON string
    # This prevents vendor-specific columns from polluting the unified schema
    flattened_deals = [
        flatten_dict(deal, exclude_keys={'raw_deal_data'}) 
        for deal in all_deals
    ]
    df_unified = pd.DataFrame(flattened_deals)
    
    # Ensure raw_deal_data is present as a JSON string column (if it exists in any deal)
    if 'raw_deal_data' not in df_unified.columns:
        # Extract raw_deal_data from original deals and add as JSON string
        raw_deal_data_col = []
        for deal in all_deals:
            raw_deal_data_col.append(json.dumps(deal.get('raw_deal_data', {})))
        df_unified['raw_deal_data'] = raw_deal_data_col
    
    # Ensure source column comes before ssp_name
    cols = list(df_unified.columns)
    if "source" in cols and "ssp_name" in cols:
        source_idx = cols.index("source")
        ssp_idx = cols.index("ssp_name")
        if source_idx > ssp_idx:
            cols.remove("source")
            cols.insert(ssp_idx, "source")
            df_unified = df_unified[cols]
    
    filename = f"deals_unified_{timestamp}.tsv"
    filepath = output_dir / filename
    df_unified.to_csv(filepath, index=False, sep='\t')
    print(f"✅ Saved unified TSV: {filepath} ({len(df_unified)} rows, {len(df_unified.columns)} columns)")
    
    return filepath


def upload_to_sheets(tsv_file: Path, exporter: UnifiedDataExporter) -> bool:
    """Upload unified TSV to Google Sheets."""
    if not exporter.google_sheets_id:
        print("⚠️  GOOGLE_SHEETS_ID not set. Skipping Google Sheets upload.")
        return False
    
    print(f"\nUploading unified TSV to Google Sheets...")
    
    try:
        df = pd.read_csv(tsv_file, sep='\t')
        
        # Use exporter's method which handles NaN, truncation, and batching
        spreadsheet = exporter._get_spreadsheet()
        if not spreadsheet:
            print("⚠️  Could not authenticate with Google Sheets. Skipping upload.")
            return False
        
        success = exporter._upload_dataframe_to_worksheet(spreadsheet, df, "Unified")
        
        if success:
            print(f"✅ Successfully uploaded {len(df)} rows to worksheet 'Unified'")
        else:
            print("❌ Failed to upload to Google Sheets")
        
        return success
        
    except Exception as e:
        print(f"❌ Failed to upload to Google Sheets: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Regenerate unified TSV file from JSON and optionally upload to Google Sheets"
    )
    parser.add_argument(
        "--json-file",
        type=Path,
        default=Path("output/deals_2026-01-21T0358.json"),
        help="Path to JSON file"
    )
    parser.add_argument(
        "--timestamp",
        type=str,
        help="Timestamp for output filename (default: extracted from JSON filename)"
    )
    parser.add_argument(
        "--no-sheets",
        action="store_true",
        help="Don't upload to Google Sheets"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Output directory (default: output)"
    )
    
    args = parser.parse_args()
    
    if not args.timestamp:
        if "deals_" in args.json_file.stem:
            args.timestamp = args.json_file.stem.replace("deals_", "")
        else:
            args.timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
    
    if not args.json_file.exists():
        print(f"❌ Error: JSON file not found: {args.json_file}")
        return 1
    
    data = process_json_file(args.json_file)
    
    print(f"\nSaving updated JSON to: {args.json_file}")
    with open(args.json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    tsv_file = regenerate_unified_tsv(args.json_file, args.timestamp, args.output_dir)
    
    if not args.no_sheets:
        exporter = UnifiedDataExporter(args.output_dir)
        upload_to_sheets(tsv_file, exporter)
    
    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
