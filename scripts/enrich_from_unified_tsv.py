#!/usr/bin/env python3
"""
Enrich Deals from Unified TSV

Loads deals from unified TSV file, enriches them with Phase 2 enhancements,
and exports enriched deals to JSON and TSV files.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import pandas as pd
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.schema import UnifiedPreEnrichmentSchema, EnrichedDeal
from src.enrichment import DealEnricher
from src.common.data_exporter import UnifiedDataExporter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_deals_from_tsv(tsv_path: Path) -> List[Dict[str, Any]]:
    """
    Load deals from unified TSV file.
    
    Args:
        tsv_path: Path to unified TSV file
        
    Returns:
        List of deal dictionaries
    """
    logger.info(f"Loading deals from {tsv_path}")
    
    df = pd.read_csv(tsv_path, sep='\t', dtype=str)
    logger.info(f"Loaded {len(df)} deals from TSV")
    
    # Convert DataFrame to list of dictionaries
    deals = []
    for _, row in df.iterrows():
        deal_dict = row.to_dict()
        
        # Parse raw_deal_data if it's a JSON string
        if 'raw_deal_data' in deal_dict and isinstance(deal_dict['raw_deal_data'], str):
            try:
                deal_dict['raw_deal_data'] = json.loads(deal_dict['raw_deal_data'])
            except (json.JSONDecodeError, TypeError):
                deal_dict['raw_deal_data'] = {}
        
        # Parse publishers if it's a JSON string
        if 'publishers' in deal_dict and isinstance(deal_dict['publishers'], str):
            try:
                deal_dict['publishers'] = json.loads(deal_dict['publishers'])
            except (json.JSONDecodeError, TypeError):
                # Try comma-separated
                deal_dict['publishers'] = [p.strip() for p in deal_dict['publishers'].split(',') if p.strip()]
        
        # Convert floor_price to float
        if 'floor_price' in deal_dict:
            try:
                deal_dict['floor_price'] = float(deal_dict['floor_price'])
            except (ValueError, TypeError):
                logger.warning(f"Invalid floor_price for deal {deal_dict.get('deal_id', 'unknown')}: {deal_dict.get('floor_price')}")
                deal_dict['floor_price'] = 0.0
        
        deals.append(deal_dict)
    
    return deals


def convert_to_schema(deals: List[Dict[str, Any]]) -> List[UnifiedPreEnrichmentSchema]:
    """
    Convert deal dictionaries to UnifiedPreEnrichmentSchema instances.
    
    Args:
        deals: List of deal dictionaries
        
    Returns:
        List of UnifiedPreEnrichmentSchema instances
    """
    schema_deals = []
    errors = 0
    
    for deal_dict in deals:
        try:
            # Ensure required fields
            if 'deal_id' not in deal_dict or not deal_dict['deal_id']:
                logger.warning(f"Skipping deal with missing deal_id: {deal_dict.get('deal_name', 'unknown')}")
                errors += 1
                continue
            
            if 'deal_name' not in deal_dict:
                deal_dict['deal_name'] = deal_dict.get('deal_id', 'Unknown')
            
            if 'source' not in deal_dict:
                deal_dict['source'] = deal_dict.get('ssp_name', 'Unknown')
            
            if 'ssp_name' not in deal_dict:
                deal_dict['ssp_name'] = deal_dict.get('source', 'Unknown')
            
            if 'format' not in deal_dict:
                deal_dict['format'] = 'display'  # Default
            
            if 'publishers' not in deal_dict:
                deal_dict['publishers'] = []
            elif isinstance(deal_dict['publishers'], str):
                deal_dict['publishers'] = [deal_dict['publishers']]
            
            if 'raw_deal_data' not in deal_dict:
                deal_dict['raw_deal_data'] = {}
            
            if 'floor_price' not in deal_dict:
                deal_dict['floor_price'] = 0.0
            
            schema_deal = UnifiedPreEnrichmentSchema(**deal_dict)
            schema_deals.append(schema_deal)
            
        except Exception as e:
            logger.error(f"Failed to convert deal {deal_dict.get('deal_id', 'unknown')}: {e}")
            errors += 1
    
    logger.info(f"Converted {len(schema_deals)}/{len(deals)} deals to schema ({errors} errors)")
    return schema_deals


def enrich_deals(deals: List[UnifiedPreEnrichmentSchema], limit: Optional[int] = None) -> List[EnrichedDeal]:
    """
    Enrich deals using Phase 2 enhanced enrichment pipeline.
    
    Args:
        deals: List of UnifiedPreEnrichmentSchema instances
        limit: Optional limit on number of deals to enrich (for testing)
        
    Returns:
        List of EnrichedDeal instances
    """
    if limit:
        deals = deals[:limit]
        logger.info(f"Limiting enrichment to first {limit} deals")
    
    logger.info(f"Starting enrichment of {len(deals)} deals with Phase 2 enhancements...")
    
    enricher = DealEnricher()
    
    def progress_callback(current: int, total: int, enriched_deal: EnrichedDeal):
        if current % 10 == 0 or current == total:
            logger.info(f"Enriched {current}/{total} deals...")
    
    enriched = enricher.enrich_batch(deals, progress_callback=progress_callback)
    
    logger.info(f"Enrichment complete: {len(enriched)}/{len(deals)} deals enriched successfully")
    return enriched


def export_enriched_deals(
    enriched_deals: List[EnrichedDeal],
    output_dir: Path,
    timestamp: str
) -> Dict[str, Path]:
    """
    Export enriched deals to JSON and TSV files.
    
    Args:
        enriched_deals: List of EnrichedDeal instances
        output_dir: Output directory
        timestamp: Timestamp string for filenames
        
    Returns:
        Dictionary mapping file type to file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert to dictionaries
    enriched_dicts = [deal.model_dump(mode='json') for deal in enriched_deals]
    
    # Export JSON
    json_path = output_dir / f"deals_enriched_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(enriched_dicts, f, indent=2, ensure_ascii=False)
    logger.info(f"Exported enriched JSON: {json_path}")
    
    # Export TSV - flatten enriched deals
    from src.common.data_exporter import flatten_dict
    
    flattened_deals = [
        flatten_dict(deal, exclude_keys={'raw_deal_data'})
        for deal in enriched_dicts
    ]
    
    df = pd.DataFrame(flattened_deals)
    
    # Ensure raw_deal_data is present as JSON string
    if 'raw_deal_data' not in df.columns:
        raw_deal_data_col = []
        for deal in enriched_dicts:
            raw_deal_data_col.append(json.dumps(deal.get('raw_deal_data', {})))
        df['raw_deal_data'] = raw_deal_data_col
    
    tsv_path = output_dir / f"deals_enriched_{timestamp}.tsv"
    df.to_csv(tsv_path, index=False, sep='\t')
    logger.info(f"Exported enriched TSV: {tsv_path} ({len(df)} rows, {len(df.columns)} columns)")
    
    return {
        'json': json_path,
        'tsv': tsv_path,
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Enrich deals from unified TSV file with Phase 2 enhancements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich all deals from unified TSV
  python scripts/enrich_from_unified_tsv.py output/deals_unified_2026-01-21T0440.tsv
  
  # Enrich first 10 deals (for testing)
  python scripts/enrich_from_unified_tsv.py output/deals_unified_2026-01-21T0440.tsv --limit 10
  
  # Custom output directory
  python scripts/enrich_from_unified_tsv.py output/deals_unified_2026-01-21T0440.tsv --output-dir enriched_output
        """
    )
    
    parser.add_argument(
        'tsv_file',
        type=Path,
        help='Path to unified TSV file'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path('output'),
        help='Output directory for enriched files (default: output)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of deals to enrich (for testing)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable DEBUG level logging'
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input file
    if not args.tsv_file.exists():
        logger.error(f"TSV file not found: {args.tsv_file}")
        return 1
    
    try:
        # Load deals from TSV
        deals = load_deals_from_tsv(args.tsv_file)
        
        if not deals:
            logger.error("No deals found in TSV file")
            return 1
        
        # Convert to schema
        schema_deals = convert_to_schema(deals)
        
        if not schema_deals:
            logger.error("No valid deals after schema conversion")
            return 1
        
        # Enrich deals
        timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        enriched_deals = enrich_deals(schema_deals, limit=args.limit)
        
        if not enriched_deals:
            logger.error("No deals were successfully enriched")
            return 1
        
        # Export enriched deals
        output_files = export_enriched_deals(enriched_deals, args.output_dir, timestamp)
        
        logger.info("\n" + "=" * 60)
        logger.info("Enrichment Complete!")
        logger.info("=" * 60)
        logger.info(f"Enriched {len(enriched_deals)} deals")
        for file_type, filepath in output_files.items():
            logger.info(f"{file_type.upper()}: {filepath}")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error during enrichment: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
