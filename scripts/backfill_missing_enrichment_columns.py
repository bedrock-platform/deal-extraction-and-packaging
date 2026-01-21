#!/usr/bin/env python3
"""
Backfill Missing Enrichment Columns

Fixes rows in Google Sheets that are missing enrichment columns.
Reads enriched deals from JSONL and updates Google Sheets rows with complete enrichment data.

Usage:
    python scripts/backfill_missing_enrichment_columns.py \
        --jsonl output/deals_enriched_2026-01-21T0642.jsonl \
        --start-row 428 \
        --end-row 527 \
        --sheets-id <GOOGLE_SHEETS_ID>
"""
import json
import logging
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_enriched_deals(jsonl_path: Path) -> Dict[str, dict]:
    """
    Load enriched deals from JSONL file, indexed by deal_id.
    
    Args:
        jsonl_path: Path to JSONL file
        
    Returns:
        Dictionary mapping deal_id to enriched deal dict
    """
    deals = {}
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    deal = json.loads(line)
                    deal_id = str(deal.get('deal_id'))
                    if deal_id:
                        deals[deal_id] = deal
        logger.info(f"Loaded {len(deals)} enriched deals from {jsonl_path}")
        return deals
    except Exception as e:
        logger.error(f"Failed to load enriched deals: {e}")
        raise


def get_deal_ids_from_rows(worksheet, start_row: int, end_row: int) -> Dict[int, str]:
    """
    Get deal_ids from specified rows in Google Sheets.
    
    Args:
        worksheet: Google Sheets worksheet object
        start_row: Starting row number (1-based, includes header)
        end_row: Ending row number (1-based, includes header)
        
    Returns:
        Dictionary mapping row number to deal_id
    """
    try:
        # Read header to find deal_id column index
        header = worksheet.row_values(1)
        deal_id_col_idx = None
        for idx, col_name in enumerate(header):
            if col_name.lower() == 'deal_id':
                deal_id_col_idx = idx  # 0-based index for list access
                break
        
        if deal_id_col_idx is None:
            raise ValueError("Could not find 'deal_id' column in Google Sheets")
        
        # Read all rows in batch (more efficient than individual cell reads)
        # get_all_values() returns 0-based rows, so row 1 (header) is index 0
        all_rows = worksheet.get_all_values()
        
        # Extract deal_ids from specified rows (start_row and end_row are 1-based)
        row_to_deal_id = {}
        for row_idx in range(start_row - 1, min(end_row, len(all_rows))):  # Convert to 0-based
            if row_idx < len(all_rows):
                row_data = all_rows[row_idx]
                if len(row_data) > deal_id_col_idx:
                    deal_id_cell = row_data[deal_id_col_idx]
                    if deal_id_cell:
                        deal_id = str(deal_id_cell).strip()
                        if deal_id:
                            row_to_deal_id[row_idx + 1] = deal_id  # Store as 1-based row number
        
        logger.info(f"Found {len(row_to_deal_id)} deal_ids in rows {start_row}-{end_row}")
        return row_to_deal_id
        
    except Exception as e:
        logger.error(f"Failed to get deal_ids from rows: {e}")
        raise


def get_column_letter(col_num: int) -> str:
    """Convert column number (1-based) to Google Sheets column letter (A, B, ..., Z, AA, ...)."""
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(65 + (col_num % 26)) + result
        col_num //= 26
    return result


def prepare_row_values(deal_dict: dict, header: List[str]) -> List:
    """
    Prepare row values matching the header columns.
    
    Args:
        deal_dict: Enriched deal dictionary
        header: List of column names from Google Sheets header
        
    Returns:
        List of values matching header order
    """
    from src.common.data_exporter import flatten_dict
    
    # Flatten deal dict
    flattened = flatten_dict(deal_dict, exclude_keys={'raw_deal_data'})
    
    # Ensure raw_deal_data is present as JSON string
    if 'raw_deal_data' not in flattened:
        flattened['raw_deal_data'] = json.dumps(deal_dict.get('raw_deal_data', {}))
    
    # Create DataFrame to ensure column order matches
    df_row = pd.DataFrame([flattened])
    
    # Reorder to match header (fill missing columns with None)
    df_row = df_row.reindex(columns=header, fill_value=None)
    
    # Convert to list, handling NaN and types
    row_values = []
    for val in df_row.iloc[0]:
        if pd.isna(val):
            row_values.append(None)
        elif isinstance(val, (np.integer,)):
            row_values.append(int(val))
        elif isinstance(val, (np.floating,)):
            row_values.append(float(val))
        elif isinstance(val, (np.bool_,)):
            row_values.append(bool(val))
        elif isinstance(val, str) and len(val) > 49000:
            # Truncate long strings
            row_values.append(val[:49000])
        else:
            row_values.append(val)
    
    return row_values


def backfill_rows(
    jsonl_path: Path,
    google_sheets_id: str,
    start_row: int,
    end_row: int,
    dry_run: bool = False
) -> None:
    """
    Backfill missing enrichment columns for specified rows.
    
    Args:
        jsonl_path: Path to enriched deals JSONL file
        google_sheets_id: Google Sheets spreadsheet ID
        start_row: Starting row number (1-based, includes header)
        end_row: Ending row number (1-based, includes header)
        dry_run: If True, only log what would be updated without making changes
    """
    try:
        from src.common.data_exporter import UnifiedDataExporter
        
        # Load enriched deals
        enriched_deals = load_enriched_deals(jsonl_path)
        
        if not enriched_deals:
            logger.error("No enriched deals found in JSONL file")
            return
        
        # Connect to Google Sheets
        output_dir = Path("output")
        exporter = UnifiedDataExporter(output_dir, google_sheets_id=google_sheets_id)
        spreadsheet = exporter._get_spreadsheet()
        
        if not spreadsheet:
            logger.error("Failed to connect to Google Sheets")
            return
        
        worksheet = spreadsheet.worksheet("Unified")
        if not worksheet:
            logger.error("Could not find 'Unified' worksheet")
            return
        
        # Get header
        header = worksheet.row_values(1)
        num_cols = len(header)
        logger.info(f"Google Sheets header has {num_cols} columns")
        
        # Get deal_ids from specified rows
        row_to_deal_id = get_deal_ids_from_rows(worksheet, start_row, end_row)
        
        if not row_to_deal_id:
            logger.warning(f"No deal_ids found in rows {start_row}-{end_row}")
            return
        
        # Update rows with enrichment data
        updated_count = 0
        missing_count = 0
        col_letter_end = get_column_letter(num_cols)
        
        for row_num, deal_id in row_to_deal_id.items():
            if deal_id not in enriched_deals:
                logger.warning(f"Deal {deal_id} (row {row_num}) not found in enriched deals")
                missing_count += 1
                continue
            
            deal_dict = enriched_deals[deal_id]
            
            # Prepare row values matching header
            row_values = prepare_row_values(deal_dict, header)
            
            # Ensure row_values matches header length
            while len(row_values) < num_cols:
                row_values.append(None)
            if len(row_values) > num_cols:
                row_values = row_values[:num_cols]
            
            if dry_run:
                logger.info(f"[DRY RUN] Would update row {row_num} (deal {deal_id}) with {len(row_values)} columns")
            else:
                try:
                    range_name = f'A{row_num}:{col_letter_end}{row_num}'
                    worksheet.update([row_values], range_name)
                    updated_count += 1
                    if updated_count % 10 == 0:
                        logger.info(f"Updated {updated_count}/{len(row_to_deal_id)} rows...")
                except Exception as e:
                    logger.error(f"Failed to update row {row_num} (deal {deal_id}): {e}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would update {len(row_to_deal_id)} rows")
            logger.info(f"[DRY RUN] {missing_count} deals not found in enriched data")
        else:
            logger.info(f"✅ Successfully updated {updated_count} rows")
            logger.info(f"⚠️  {missing_count} deals not found in enriched data")
            logger.info(f"📊 Rows {start_row}-{end_row} backfilled with enrichment data")
        
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Backfill missing enrichment columns in Google Sheets"
    )
    parser.add_argument(
        '--jsonl',
        type=Path,
        required=True,
        help='Path to enriched deals JSONL file'
    )
    parser.add_argument(
        '--sheets-id',
        type=str,
        required=True,
        help='Google Sheets spreadsheet ID'
    )
    parser.add_argument(
        '--start-row',
        type=int,
        required=True,
        help='Starting row number (1-based, includes header)'
    )
    parser.add_argument(
        '--end-row',
        type=int,
        required=True,
        help='Ending row number (1-based, includes header)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode (log what would be updated without making changes)'
    )
    
    args = parser.parse_args()
    
    if not args.jsonl.exists():
        logger.error(f"JSONL file not found: {args.jsonl}")
        return
    
    logger.info("=" * 60)
    logger.info("Backfilling Missing Enrichment Columns")
    logger.info("=" * 60)
    logger.info(f"JSONL file: {args.jsonl}")
    logger.info(f"Google Sheets ID: {args.sheets_id}")
    logger.info(f"Rows: {args.start_row}-{args.end_row}")
    logger.info(f"Dry run: {args.dry_run}")
    logger.info("=" * 60)
    
    backfill_rows(
        jsonl_path=args.jsonl,
        google_sheets_id=args.sheets_id,
        start_row=args.start_row,
        end_row=args.end_row,
        dry_run=args.dry_run
    )


if __name__ == '__main__':
    main()
