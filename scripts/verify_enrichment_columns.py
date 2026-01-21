#!/usr/bin/env python3
"""
Verify Enrichment Columns

Quick verification script to check if enrichment columns are populated in Google Sheets.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from src.common.data_exporter import UnifiedDataExporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_rows(google_sheets_id: str, sample_rows: list):
    """Verify enrichment columns are populated in sample rows."""
    try:
        output_dir = Path("output")
        exporter = UnifiedDataExporter(output_dir, google_sheets_id=google_sheets_id)
        spreadsheet = exporter._get_spreadsheet()
        
        if not spreadsheet:
            logger.error("Failed to connect to Google Sheets")
            return False
        
        worksheet = spreadsheet.worksheet("Unified")
        if not worksheet:
            logger.error("Could not find 'Unified' worksheet")
            return False
        
        # Get header
        header = worksheet.row_values(1)
        logger.info(f"Header has {len(header)} columns")
        
        # Check enrichment columns (these should be present)
        enrichment_columns = [
            'taxonomy_tier1', 'taxonomy_tier2', 'taxonomy_tier3',
            'safety_family_safe', 'safety_garm_risk_rating',
            'commercial_quality_tier', 'commercial_volume_tier',
            'audience_inferred_audience', 'concepts', 'enrichment_timestamp'
        ]
        
        enrichment_col_indices = {}
        for col in enrichment_columns:
            try:
                idx = header.index(col)
                enrichment_col_indices[col] = idx
            except ValueError:
                logger.warning(f"Enrichment column '{col}' not found in header")
        
        logger.info(f"Found {len(enrichment_col_indices)} enrichment columns in header")
        
        # Check sample rows
        all_rows = worksheet.get_all_values()
        verified_count = 0
        
        for row_num in sample_rows:
            if row_num - 1 < len(all_rows):  # Convert to 0-based
                row_data = all_rows[row_num - 1]
                
                # Check if enrichment columns have data
                has_enrichment = False
                enrichment_values = {}
                
                for col_name, col_idx in enrichment_col_indices.items():
                    if col_idx < len(row_data):
                        value = row_data[col_idx]
                        if value and str(value).strip():
                            has_enrichment = True
                            enrichment_values[col_name] = value[:50] if len(str(value)) > 50 else value
                
                if has_enrichment:
                    verified_count += 1
                    logger.info(f"✅ Row {row_num}: Has enrichment data")
                    for col, val in enrichment_values.items():
                        logger.info(f"   - {col}: {val}")
                else:
                    logger.warning(f"⚠️  Row {row_num}: Missing enrichment data")
        
        logger.info(f"\n📊 Verification Summary:")
        logger.info(f"   Verified: {verified_count}/{len(sample_rows)} rows have enrichment data")
        
        return verified_count == len(sample_rows)
        
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        return False


if __name__ == '__main__':
    google_sheets_id = "1Zi5Kc9DuoIH_CVWqM-uU_BMmkU7hHM8tM0x0mJWgo3g"
    
    # Sample rows from the backfilled range (428-527)
    sample_rows = [428, 450, 475, 500, 527]
    
    logger.info("=" * 60)
    logger.info("Verifying Enrichment Columns")
    logger.info("=" * 60)
    logger.info(f"Google Sheets ID: {google_sheets_id}")
    logger.info(f"Sample rows: {sample_rows}")
    logger.info("=" * 60)
    
    success = verify_rows(google_sheets_id, sample_rows)
    
    if success:
        logger.info("\n✅ All sample rows have enrichment data!")
    else:
        logger.warning("\n⚠️  Some rows may be missing enrichment data")
