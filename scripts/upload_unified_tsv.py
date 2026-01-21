#!/usr/bin/env python3
"""
Upload unified TSV to Google Sheets Unified worksheet.
"""
import sys
import logging
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.data_exporter import UnifiedDataExporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def upload_unified_tsv(tsv_path: Path, output_dir: Path) -> bool:
    """
    Upload unified TSV to Google Sheets Unified worksheet.
    
    Args:
        tsv_path: Path to unified TSV file
        output_dir: Output directory (for exporter initialization)
        
    Returns:
        True if successful, False otherwise
    """
    if not tsv_path.exists():
        logger.error(f"TSV file not found: {tsv_path}")
        return False
    
    logger.info(f"Loading unified TSV: {tsv_path}")
    try:
        df_unified = pd.read_csv(tsv_path, sep='\t')
        logger.info(f"Loaded {len(df_unified)} rows from unified TSV")
    except Exception as e:
        logger.error(f"Failed to load TSV: {e}")
        return False
    
    # Initialize exporter
    exporter = UnifiedDataExporter(output_dir)
    
    # Upload to Google Sheets
    spreadsheet = exporter._get_spreadsheet()
    if not spreadsheet:
        logger.error("Could not authenticate with Google Sheets")
        return False
    
    logger.info("Uploading to Google Sheets 'Unified' worksheet...")
    success = exporter._upload_dataframe_to_worksheet(spreadsheet, df_unified, "Unified")
    
    if success:
        logger.info(f"✅ Successfully uploaded {len(df_unified)} rows to worksheet 'Unified'")
        return True
    else:
        logger.error("❌ Failed to upload to Google Sheets")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/upload_unified_tsv.py <tsv_file> [output_dir]")
        sys.exit(1)
    
    tsv_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("output")
    
    success = upload_unified_tsv(tsv_path, output_dir)
    sys.exit(0 if success else 1)
