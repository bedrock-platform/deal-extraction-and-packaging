#!/usr/bin/env python3
"""
Clear the Unified worksheet in Google Sheets.
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.data_exporter import UnifiedDataExporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def clear_unified_worksheet(output_dir: Path) -> bool:
    """
    Clear the Unified worksheet in Google Sheets.
    
    Args:
        output_dir: Output directory (for exporter initialization)
        
    Returns:
        True if successful, False otherwise
    """
    # Initialize exporter
    exporter = UnifiedDataExporter(output_dir)
    
    # Get spreadsheet
    spreadsheet = exporter._get_spreadsheet()
    if not spreadsheet:
        logger.error("Could not authenticate with Google Sheets")
        return False
    
    # Get or create Unified worksheet
    try:
        worksheet = spreadsheet.worksheet("Unified")
        logger.info("Found 'Unified' worksheet")
    except Exception:
        logger.warning("'Unified' worksheet not found - nothing to clear")
        return True
    
    # Clear all data
    try:
        worksheet.clear()
        logger.info("✅ Successfully cleared 'Unified' worksheet")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to clear worksheet: {e}")
        return False


if __name__ == "__main__":
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("output")
    
    success = clear_unified_worksheet(output_dir)
    sys.exit(0 if success else 1)
