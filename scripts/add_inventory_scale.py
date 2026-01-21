#!/usr/bin/env python3
"""
Add inventory_scale and inventory_scale_type to existing extracted deals.

This script reads the extracted JSON file and adds inventory_scale fields
to each deal based on the existing volume_metrics or raw_deal_data.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.data_exporter import UnifiedDataExporter, flatten_dict


def compute_inventory_scale(deal: Dict[str, Any], ssp_name: str) -> tuple[Optional[int], Optional[str]]:
    """
    Compute inventory_scale and inventory_scale_type for a deal.
    
    Args:
        deal: Deal dictionary
        ssp_name: SSP name (e.g., "Google Authorized Buyers", "BidSwitch", "Google Curated")
        
    Returns:
        Tuple of (inventory_scale, inventory_scale_type)
    """
    inventory_scale = None
    inventory_scale_type = None
    
    # Check if volume_metrics already exists
    volume_metrics = deal.get("volume_metrics")
    if volume_metrics:
        if isinstance(volume_metrics, dict):
            # Already a dict (from JSON)
            impressions = volume_metrics.get("impressions")
            bid_requests = volume_metrics.get("bid_requests")
            
            if impressions:
                inventory_scale = int(impressions)
                inventory_scale_type = "impressions"
            elif bid_requests:
                inventory_scale = int(bid_requests)
                inventory_scale_type = "bid_requests"
    
    # If not found in volume_metrics, compute from raw_deal_data
    if inventory_scale is None:
        raw_data = deal.get("raw_deal_data", {})
        
        if ssp_name in ["Google Authorized Buyers", "Google Curated"]:
            # Google deals: use impressions from forecast metrics
            if ssp_name == "Google Authorized Buyers":
                forecast = raw_data.get("forecast", {})
                metrics = forecast.get("metrics", {})
                impressions = metrics.get("impressions", "0")
            else:  # Google Curated
                forecast_metrics = raw_data.get("forecastMetrics", {})
                impressions = forecast_metrics.get("impressions", "0")
            
            if impressions and impressions != "0":
                try:
                    inventory_scale = int(impressions)
                    inventory_scale_type = "impressions"
                except (ValueError, TypeError):
                    pass
        
        elif ssp_name == "BidSwitch":
            # BidSwitch: prefer weekly_total_avails, fallback to bid_requests
            weekly_total_avails = raw_data.get("weekly_total_avails")
            bid_requests = raw_data.get("bid_requests")
            
            if weekly_total_avails and weekly_total_avails > 0:
                try:
                    inventory_scale = int(weekly_total_avails)
                    inventory_scale_type = "bid_requests"
                except (ValueError, TypeError):
                    pass
            
            if inventory_scale is None and bid_requests:
                try:
                    inventory_scale = int(bid_requests)
                    inventory_scale_type = "bid_requests"
                except (ValueError, TypeError):
                    pass
    
    return inventory_scale, inventory_scale_type


def add_inventory_scale_to_json(json_file: Path, output_file: Optional[Path] = None):
    """
    Add inventory_scale and inventory_scale_type to all deals in JSON file.
    
    Args:
        json_file: Path to input JSON file
        output_file: Path to output JSON file (if None, overwrites input)
    """
    print(f"Reading JSON file: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total_deals = 0
    deals_with_scale = 0
    
    # Process each vendor's deals
    for vendor_name, deals in data.items():
        print(f"\nProcessing {vendor_name}: {len(deals)} deals")
        vendor_scale_count = 0
        
        for deal in deals:
            total_deals += 1
            inventory_scale, inventory_scale_type = compute_inventory_scale(deal, vendor_name)
            
            if inventory_scale is not None:
                deal["inventory_scale"] = inventory_scale
                deal["inventory_scale_type"] = inventory_scale_type
                deals_with_scale += 1
                vendor_scale_count += 1
        
        print(f"  Added inventory_scale to {vendor_scale_count}/{len(deals)} deals")
    
    # Write updated JSON
    if output_file is None:
        output_file = json_file
    
    print(f"\nWriting updated JSON to: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\nSummary:")
    print(f"  Total deals processed: {total_deals}")
    print(f"  Deals with inventory_scale: {deals_with_scale}")
    print(f"  Deals without inventory_scale: {total_deals - deals_with_scale}")
    
    return data


def regenerate_tsv(json_file: Path, timestamp: str):
    """
    Regenerate TSV files from updated JSON.
    
    Args:
        json_file: Path to JSON file with inventory_scale added
        timestamp: Timestamp string for output filenames
    """
    print(f"\nRegenerating TSV files from: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    exporter = UnifiedDataExporter(Path("output"))
    
    # Export unified TSV
    print("Exporting unified TSV...")
    all_deals = []
    for vendor_deals in data.values():
        all_deals.extend(vendor_deals)
    
    flattened_deals = [flatten_dict(deal) for deal in all_deals]
    df_unified = pd.DataFrame(flattened_deals)
    filename = f"deals_unified_{timestamp}.tsv"
    filepath = Path("output") / filename
    df_unified.to_csv(filepath, index=False, sep='\t')
    print(f"  Saved: {filepath}")
    
    # Export vendor-specific TSVs
    for vendor_name, deals in data.items():
        worksheet_name = exporter._get_worksheet_name(vendor_name)
        filename_base = exporter._worksheet_name_to_filename(worksheet_name)
        filename = f"{filename_base}_{timestamp}.tsv"
        filepath = Path("output") / filename
        
        flattened_deals = [flatten_dict(deal) for deal in deals]
        df_vendor = pd.DataFrame(flattened_deals)
        df_vendor.to_csv(filepath, index=False, sep='\t')
        print(f"  Saved: {filepath}")


if __name__ == "__main__":
    import pandas as pd
    
    # Find the JSON file
    json_file = Path("output/deals_2026-01-21T0358.json")
    
    if not json_file.exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    # Extract timestamp from filename
    timestamp = json_file.stem.replace("deals_", "")
    
    # Add inventory_scale to JSON
    data = add_inventory_scale_to_json(json_file)
    
    # Regenerate TSV files
    try:
        regenerate_tsv(json_file, timestamp)
        print("\n✅ Successfully added inventory_scale and regenerated TSV files!")
    except Exception as e:
        print(f"\n⚠️  Error regenerating TSV files: {e}")
        print("JSON file has been updated with inventory_scale fields.")
        import traceback
        traceback.print_exc()
