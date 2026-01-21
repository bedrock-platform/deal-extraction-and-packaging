#!/usr/bin/env python3
"""
Multi-Vendor Deal Extractor

Unified CLI for extracting deals from multiple vendors:
- Google Authorized Buyers (Marketplace)
- Google Curated
- BidSwitch
- Future vendors...

Usage:
    python -m src.deal_extractor --vendor google_ads
    python -m src.deal_extractor --vendor bidswitch
    python -m src.deal_extractor --all
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from .common.orchestrator import DealExtractor

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description="Extract deals from multiple vendors (Google Authorized Buyers, BidSwitch, etc.)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract from Google Ads only
  python -m src.deal_extractor --vendor google_ads
  
  # Extract from BidSwitch only
  python -m src.deal_extractor --vendor bidswitch
  
  # Extract from all vendors (Marketplace + Google Curated + BidSwitch)
  python -m src.deal_extractor --all
  
  # Extract and enrich deals with semantic metadata
  python -m src.deal_extractor --all --enrich
  
  # Extract with filters (vendor-specific)
  python -m src.deal_extractor --vendor bidswitch --inventory-format video --countries US
  
  # Extract Google Ads with custom payload
  python -m src.deal_extractor --vendor google_ads --payload filters.json
  
  # Extract Google Curated packages only
  python -m src.deal_extractor --vendor google_ads --google-curated
  
  # Extract and enrich from one vendor
  python -m src.deal_extractor --vendor google_ads --enrich
  
  # Enrich deals from existing unified TSV file
  python -m src.deal_extractor --enrich-from-tsv output/deals_unified_2026-01-21T0440.tsv
  
  # Enrich first 10 deals from TSV (for testing)
  python -m src.deal_extractor --enrich-from-tsv output/deals_unified_2026-01-21T0440.tsv --enrich-limit 10
        """,
    )

    # Vendor selection (required unless using --enrich-from-tsv or --regenerate-unified)
    vendor_group = parser.add_mutually_exclusive_group(required=False)
    vendor_group.add_argument(
        "--vendor",
        choices=["google_ads", "bidswitch"],
        help="Extract deals from a specific vendor",
    )
    vendor_group.add_argument(
        "--all", action="store_true", help="Extract deals from all available vendors"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for files (default: output)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable DEBUG level logging"
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip file export (only return data in memory)",
    )
    parser.add_argument(
        "--no-sheets",
        action="store_true",
        help="Skip Google Sheets upload (only export to local files)",
    )
    
    # Enrichment options
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Enrich extracted deals with semantic metadata using LLM inference (Stage 1)",
    )
    parser.add_argument(
        "--regenerate-unified",
        action="store_true",
        help="Regenerate unified TSV from existing JSON and upload to Google Sheets",
    )
    parser.add_argument(
        "--enrich-from-tsv",
        type=str,
        metavar="TSV_FILE",
        help="Enrich deals from unified TSV file and upload enriched results to Google Sheets Unified worksheet",
    )
    parser.add_argument(
        "--enrich-limit",
        type=int,
        help="Limit number of deals to enrich (for testing, use with --enrich-from-tsv)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Disable resume from checkpoint (start fresh even if checkpoint exists)",
    )
    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run complete pipeline: Stage 0 (extract) → Stage 1 (enrich) → Stage 2 (create packages) → Stage 3 (enrich packages)",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Enable incremental processing (only process new/modified deals). Requires --full-pipeline.",
    )
    parser.add_argument(
        "--stage-2",
        type=str,
        metavar="JSONL_PATH",
        help="Run Stage 2 only: Create packages from enriched deals. Requires path to enriched deals JSONL file (e.g., output/deals_enriched_2026-01-21T0657.jsonl)",
    )
    parser.add_argument(
        "--stage-3",
        type=str,
        nargs=2,
        metavar=("PACKAGES_JSON", "ENRICHED_JSONL"),
        help="Run Stage 3 only: Enrich packages. Requires two paths: packages JSON file and enriched deals JSONL file (e.g., output/packages_2026-01-21.json output/deals_enriched_2026-01-21T0657.jsonl)",
    )
    parser.add_argument(
        "--stages-2-3",
        type=str,
        metavar="JSONL_PATH",
        help="Run Stage 2 → Stage 3: Create packages and enrich them. Requires path to enriched deals JSONL file (e.g., output/deals_enriched_2026-01-21T0657.jsonl)",
    )

    # Google Ads specific options
    parser.add_argument(
        "--payload",
        type=str,
        help="Path to JSON file containing Google Ads request payload (filters, etc.)",
    )
    parser.add_argument(
        "--google-curated",
        action="store_true",
        help="Fetch Google Curated packages instead of Marketplace packages (Google Ads only)",
    )

    # BidSwitch specific options
    parser.add_argument(
        "--inventory-format",
        type=str,
        choices=["video", "display"],
        help="Ad format filter (BidSwitch)",
    )
    parser.add_argument(
        "--countries",
        type=str,
        help="ISO Alpha-2 country codes, comma-separated (e.g., US,CA,GB) (BidSwitch)",
    )
    parser.add_argument(
        "--floor-price-min", type=float, help="Minimum CPM filter (BidSwitch)"
    )
    parser.add_argument(
        "--floor-price-max", type=float, help="Maximum CPM filter (BidSwitch)"
    )
    parser.add_argument(
        "--ssp-id",
        type=int,
        help="Filter by SSP ID (BidSwitch: 7=Sovrn, 68=Nexxen, 6=OpenX, 1=Magnite, 52=Sonobi, 255=Commerce Grid)",
    )
    parser.add_argument(
        "--limit", type=int, default=100, help="Maximum results per page (default: 100)"
    )
    parser.add_argument(
        "--max-pages", type=int, help="Maximum pages to fetch (BidSwitch)"
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Get Google Sheets ID from environment
        google_sheets_id = os.getenv("GOOGLE_SHEETS_ID")

        # Initialize extractor
        extractor = DealExtractor(
            output_dir=args.output_dir,
            debug=args.debug,
            google_sheets_id=google_sheets_id,
        )

        # Validate that vendor selection is provided unless using special commands
        if not args.enrich_from_tsv and not args.regenerate_unified and not args.stage_2 and not args.stage_3 and not args.stages_2_3:
            if not args.vendor and not args.all:
                parser.error("one of the arguments --vendor --all is required (unless using --enrich-from-tsv, --regenerate-unified, --stage-2, --stage-3, or --stages-2-3)")
        
        # Determine vendors to extract
        if args.all:
            vendors = None  # Extract from all (includes Google Curated by default)
        elif args.google_curated and args.vendor == "google_ads":
            vendors = ["google_curated"]  # Extract only Google Curated
        elif args.vendor:
            vendors = [args.vendor]
        else:
            vendors = None  # Will be None for enrich-from-tsv or regenerate-unified

        # Build filters
        filters = {}

        # Google Ads filters
        if args.payload:
            with open(args.payload, "r") as f:
                filters["payload"] = json.load(f)
            logger.info(f"Loaded payload from: {args.payload}")

        # Handle Google Curated flag
        if args.google_curated:
            if args.all:
                # --all already includes Google Curated, no need to do anything special
                logger.info("Google Curated will be included in --all extraction")
            elif args.vendor == "google_ads":
                # Extract only Google Curated (not Marketplace)
                vendors = ["google_curated"]
            else:
                logger.warning("--google-curated flag only works with --vendor google_ads or --all")

        # BidSwitch filters
        if args.inventory_format:
            filters["inventory_format"] = args.inventory_format
        if args.countries:
            filters["countries"] = args.countries
        if args.floor_price_min is not None:
            filters["floor_price_min"] = args.floor_price_min
        if args.floor_price_max is not None:
            filters["floor_price_max"] = args.floor_price_max
        if args.ssp_id is not None:
            filters["ssp_id"] = args.ssp_id
        if args.limit:
            filters["limit"] = args.limit
        if args.max_pages:
            filters["max_pages"] = args.max_pages

        # Handle enrichment from TSV (separate workflow)
        # Handle full pipeline command
        if args.full_pipeline:
            from src.common.pipeline import PipelineOrchestrator
            
            if args.incremental:
                logger.warning("Incremental processing (--incremental) is not yet implemented. Running full pipeline.")
            
            # Validate vendor selection
            if not args.vendor and not args.all:
                parser.error("--full-pipeline requires --vendor or --all")
            
            # Initialize pipeline orchestrator
            pipeline = PipelineOrchestrator(
                output_dir=args.output_dir,
                debug=args.debug,
                google_sheets_id=google_sheets_id
            )
            
            # Run full pipeline
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
            
            def progress_callback(stage_name, data):
                logger.info(f"[Pipeline Progress] {stage_name}: {type(data).__name__}")
            
            results = pipeline.run_full_pipeline(
                vendors=vendors,
                timestamp=timestamp,
                save_intermediate=True,
                upload_to_sheets=not args.no_sheets,
                progress_callback=progress_callback,
                **filters
            )
            
            logger.info("\n" + "=" * 60)
            logger.info("Pipeline Summary:")
            logger.info(f"  Stage 0: Extracted deals from {len(results['stage_0'])} vendors")
            logger.info(f"  Stage 1: Enriched {len(results['stage_1'])} deals")
            logger.info(f"  Stage 2: Created {len(results['stage_2'])} packages")
            logger.info(f"  Stage 3: Enriched {len(results['stage_3'])} packages")
            logger.info(f"\nOutput files:")
            for file_type, file_path in results['output_files'].items():
                logger.info(f"  {file_type}: {file_path}")
            logger.info("=" * 60)
            
            return 0
        
        # Handle Stage 2 only
        if args.stage_2:
            from src.common.pipeline import PipelineOrchestrator
            from pathlib import Path
            
            jsonl_path = Path(args.stage_2)
            if not jsonl_path.exists():
                logger.error(f"Enriched deals JSONL file not found: {jsonl_path}")
                return 1
            
            # Initialize pipeline orchestrator
            pipeline = PipelineOrchestrator(
                output_dir=args.output_dir,
                debug=args.debug,
                google_sheets_id=google_sheets_id
            )
            
            # Run Stage 2 only
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
            
            def progress_callback(stage_name, data):
                logger.info(f"[Pipeline Progress] {stage_name}: {type(data).__name__}")
            
            results = pipeline.run_stage_2_only(
                enriched_jsonl_path=jsonl_path,
                timestamp=timestamp,
                save_intermediate=True,
                upload_to_sheets=not args.no_sheets,
                progress_callback=progress_callback,
                incremental=True,  # Enable incremental export by default
                no_resume=args.no_resume
            )
            
            logger.info("\n" + "=" * 60)
            logger.info("Stage 2 Summary:")
            logger.info(f"  Stage 2: Created {len(results['stage_2'])} packages")
            logger.info(f"\nOutput files:")
            for file_type, file_path in results['output_files'].items():
                logger.info(f"  {file_type}: {file_path}")
            logger.info("=" * 60)
            
            return 0
        
        # Handle Stage 3 only
        if args.stage_3:
            from src.common.pipeline import PipelineOrchestrator
            from pathlib import Path
            
            packages_json_path = Path(args.stage_3[0])
            enriched_jsonl_path = Path(args.stage_3[1])
            
            if not packages_json_path.exists():
                logger.error(f"Packages JSON file not found: {packages_json_path}")
                return 1
            
            if not enriched_jsonl_path.exists():
                logger.error(f"Enriched deals JSONL file not found: {enriched_jsonl_path}")
                return 1
            
            # Initialize pipeline orchestrator
            pipeline = PipelineOrchestrator(
                output_dir=args.output_dir,
                debug=args.debug,
                google_sheets_id=google_sheets_id
            )
            
            # Run Stage 3 only
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
            
            def progress_callback(stage_name, data):
                logger.info(f"[Pipeline Progress] {stage_name}: {type(data).__name__}")
            
            results = pipeline.run_stage_3_only(
                packages_json_path=packages_json_path,
                enriched_jsonl_path=enriched_jsonl_path,
                timestamp=timestamp,
                save_intermediate=True,
                upload_to_sheets=not args.no_sheets,
                progress_callback=progress_callback,
                incremental=True,  # Enable incremental export by default
                no_resume=args.no_resume
            )
            
            logger.info("\n" + "=" * 60)
            logger.info("Stage 3 Summary:")
            logger.info(f"  Stage 3: Enriched {len(results['stage_3'])} packages")
            logger.info(f"\nOutput files:")
            for file_type, file_path in results['output_files'].items():
                logger.info(f"  {file_type}: {file_path}")
            logger.info("=" * 60)
            
            return 0
        
        # Handle Stages 2-3 together
        if args.stages_2_3:
            from src.common.pipeline import PipelineOrchestrator
            from pathlib import Path
            
            jsonl_path = Path(args.stages_2_3)
            if not jsonl_path.exists():
                logger.error(f"Enriched deals JSONL file not found: {jsonl_path}")
                return 1
            
            # Initialize pipeline orchestrator
            pipeline = PipelineOrchestrator(
                output_dir=args.output_dir,
                debug=args.debug,
                google_sheets_id=google_sheets_id
            )
            
            # Run Stages 2-3
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
            
            def progress_callback(stage_name, data):
                logger.info(f"[Pipeline Progress] {stage_name}: {type(data).__name__}")
            
            results = pipeline.run_stages_2_3(
                enriched_jsonl_path=jsonl_path,
                timestamp=timestamp,
                save_intermediate=True,
                upload_to_sheets=not args.no_sheets,
                progress_callback=progress_callback,
                incremental=True,  # Enable incremental export by default
                no_resume=args.no_resume
            )
            
            logger.info("\n" + "=" * 60)
            logger.info("Stages 2-3 Summary:")
            logger.info(f"  Stage 2: Created {len(results['stage_2'])} packages")
            logger.info(f"  Stage 3: Enriched {len(results['stage_3'])} packages")
            logger.info(f"\nOutput files:")
            for file_type, file_path in results['output_files'].items():
                logger.info(f"  {file_type}: {file_path}")
            logger.info("=" * 60)
            
            return 0
        
        if args.enrich_from_tsv:
            from pathlib import Path
            import pandas as pd
            from src.common.schema import UnifiedPreEnrichmentSchema, EnrichedDeal
            from src.enrichment import DealEnricher
            
            tsv_path = Path(args.enrich_from_tsv)
            if not tsv_path.exists():
                logger.error(f"TSV file not found: {tsv_path}")
                return 1
            
            logger.info("=" * 60)
            logger.info("Enriching deals from unified TSV (Phase 2 enhancements)...")
            logger.info("=" * 60)
            
            # Upload pre-enrichment data to Google Sheets Unified worksheet first
            # This gives visibility into what deals are about to be enriched
            # Note: Enriched rows will have additional columns, so they'll append with more fields
            if not args.no_sheets:
                logger.info("Uploading pre-enrichment data to Google Sheets 'Unified' worksheet...")
                spreadsheet = extractor.exporter._get_spreadsheet()
                if spreadsheet:
                    try:
                        df_pre = pd.read_csv(tsv_path, sep='\t')
                        success = extractor.exporter._upload_dataframe_to_worksheet(spreadsheet, df_pre, "Unified")
                        if success:
                            logger.info(f"✅ Successfully uploaded {len(df_pre)} pre-enrichment deals to worksheet 'Unified'")
                            logger.info("Note: Enriched rows will append with additional enrichment columns")
                        else:
                            logger.warning("❌ Failed to upload pre-enrichment data to Google Sheets")
                    except Exception as e:
                        logger.warning(f"Failed to upload pre-enrichment data: {e}")
                else:
                    logger.warning("Could not authenticate with Google Sheets. Skipping pre-enrichment upload.")
            
            # Load deals from TSV
            logger.info(f"Loading deals from {tsv_path}")
            df = pd.read_csv(tsv_path, sep='\t', dtype=str)
            logger.info(f"Loaded {len(df)} deals from TSV")
            
            # Convert to schema
            import numpy as np
            from src.common.schema import VolumeMetrics
            
            schema_deals = []
            for _, row in df.iterrows():
                deal_dict = row.to_dict()
                
                # Clean up NaN values - convert to None for optional fields
                for key, value in list(deal_dict.items()):
                    if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
                        deal_dict[key] = None
                    elif isinstance(value, str) and value.lower() in ('nan', 'none', ''):
                        deal_dict[key] = None
                
                # Reconstruct volume_metrics from flattened fields BEFORE removing them
                volume_metrics_dict = {}
                if 'volume_metrics_bid_requests' in deal_dict and deal_dict['volume_metrics_bid_requests']:
                    try:
                        volume_metrics_dict['bid_requests'] = int(float(deal_dict['volume_metrics_bid_requests']))
                    except (ValueError, TypeError):
                        pass
                if 'volume_metrics_impressions' in deal_dict and deal_dict['volume_metrics_impressions']:
                    try:
                        volume_metrics_dict['impressions'] = int(float(deal_dict['volume_metrics_impressions']))
                    except (ValueError, TypeError):
                        pass
                if 'volume_metrics_uniques' in deal_dict and deal_dict['volume_metrics_uniques']:
                    try:
                        volume_metrics_dict['uniques'] = int(float(deal_dict['volume_metrics_uniques']))
                    except (ValueError, TypeError):
                        pass
                if 'volume_metrics_bid_requests_ratio' in deal_dict and deal_dict['volume_metrics_bid_requests_ratio']:
                    try:
                        volume_metrics_dict['bid_requests_ratio'] = float(deal_dict['volume_metrics_bid_requests_ratio'])
                    except (ValueError, TypeError):
                        pass
                
                # Remove flattened volume_metrics fields (they're not in schema)
                for key in list(deal_dict.keys()):
                    if key.startswith('volume_metrics_'):
                        del deal_dict[key]
                
                # Create VolumeMetrics object if we have any values
                if volume_metrics_dict:
                    try:
                        deal_dict['volume_metrics'] = VolumeMetrics(**volume_metrics_dict)
                    except Exception:
                        deal_dict['volume_metrics'] = None
                else:
                    deal_dict['volume_metrics'] = None
                
                # Parse raw_deal_data if it's a JSON string
                if 'raw_deal_data' in deal_dict and deal_dict['raw_deal_data']:
                    if isinstance(deal_dict['raw_deal_data'], str):
                        try:
                            deal_dict['raw_deal_data'] = json.loads(deal_dict['raw_deal_data'])
                        except (json.JSONDecodeError, TypeError):
                            deal_dict['raw_deal_data'] = {}
                    elif deal_dict['raw_deal_data'] is None:
                        deal_dict['raw_deal_data'] = {}
                else:
                    deal_dict['raw_deal_data'] = {}
                
                # Parse publishers if it's a JSON string
                if 'publishers' in deal_dict and deal_dict['publishers']:
                    if isinstance(deal_dict['publishers'], str):
                        try:
                            deal_dict['publishers'] = json.loads(deal_dict['publishers'])
                        except (json.JSONDecodeError, TypeError):
                            deal_dict['publishers'] = [p.strip() for p in deal_dict['publishers'].split(',') if p.strip()]
                    elif deal_dict['publishers'] is None:
                        deal_dict['publishers'] = []
                else:
                    deal_dict['publishers'] = []
                
                # Convert floor_price to float
                if 'floor_price' in deal_dict and deal_dict['floor_price']:
                    try:
                        deal_dict['floor_price'] = float(deal_dict['floor_price'])
                    except (ValueError, TypeError):
                        deal_dict['floor_price'] = 0.0
                elif 'floor_price' not in deal_dict or deal_dict['floor_price'] is None:
                    deal_dict['floor_price'] = 0.0
                
                # Ensure required fields
                if 'deal_id' not in deal_dict or not deal_dict['deal_id']:
                    continue
                if 'deal_name' not in deal_dict or not deal_dict['deal_name']:
                    deal_dict['deal_name'] = deal_dict.get('deal_id', 'Unknown')
                if 'source' not in deal_dict or not deal_dict['source']:
                    deal_dict['source'] = deal_dict.get('ssp_name', 'Unknown')
                if 'ssp_name' not in deal_dict or not deal_dict['ssp_name']:
                    deal_dict['ssp_name'] = deal_dict.get('source', 'Unknown')
                if 'format' not in deal_dict or not deal_dict['format']:
                    deal_dict['format'] = 'display'
                if 'raw_deal_data' not in deal_dict or not deal_dict['raw_deal_data']:
                    deal_dict['raw_deal_data'] = {}
                
                # Clean up optional fields that are None
                for field in ['inventory_type', 'start_time', 'end_time', 'description']:
                    if field in deal_dict and deal_dict[field] is None:
                        # Keep None for optional fields
                        pass
                
                try:
                    schema_deal = UnifiedPreEnrichmentSchema(**deal_dict)
                    schema_deals.append(schema_deal)
                except Exception as e:
                    logger.warning(f"Failed to convert deal {deal_dict.get('deal_id', 'unknown')}: {e}")
                    continue
            
            if not schema_deals:
                logger.error("No valid deals found in TSV")
                return 1
            
            # Limit if specified
            if args.enrich_limit:
                schema_deals = schema_deals[:args.enrich_limit]
                logger.info(f"Limited to first {args.enrich_limit} deals")
            
            # Enrich deals
            logger.info(f"Enriching {len(schema_deals)} deals with Phase 2 enhancements...")
            enricher = DealEnricher()
            
            # Setup incremental persistence
            output_dir = Path(extractor.output_dir)
            
            # Check for existing checkpoint to resume from
            checkpoint_files = list(output_dir.glob("enrichment_checkpoint_*.json"))
            use_incremental = True  # Always use incremental for --enrich-from-tsv
            
            if checkpoint_files and not args.no_resume:
                # Use most recent checkpoint
                checkpoint_file = max(checkpoint_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"Found existing checkpoint: {checkpoint_file}")
                logger.info("Resuming from checkpoint (use --no-resume to start fresh)")
                
                # Try to extract timestamp from checkpoint
                from src.enrichment.checkpoint import EnrichmentCheckpoint
                temp_checkpoint = EnrichmentCheckpoint(checkpoint_file)
                checkpoint_timestamp = temp_checkpoint.get_timestamp()
                if checkpoint_timestamp:
                    timestamp = checkpoint_timestamp
                    logger.info(f"Using checkpoint timestamp: {timestamp}")
                else:
                    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
                checkpoint_file = output_dir / f"enrichment_checkpoint_{timestamp}.json"
                if args.no_resume and checkpoint_file.exists():
                    logger.info("--no-resume specified: deleting existing checkpoint")
                    checkpoint_file.unlink()
            
            def progress_callback(current: int, total: int, enriched_deal: EnrichedDeal):
                if current % 10 == 0 or current == total:
                    logger.info(f"Enriched {current}/{total} deals...")
            
            enriched_deals = enricher.enrich_batch(
                schema_deals,
                progress_callback=progress_callback,
                incremental=use_incremental,
                checkpoint_file=checkpoint_file,
                output_dir=output_dir,
                timestamp=timestamp,
                google_sheets_id=google_sheets_id
            )
            
            if not enriched_deals:
                logger.error("No deals were successfully enriched")
                return 1
            
            logger.info(f"Enrichment complete: {len(enriched_deals)}/{len(schema_deals)} deals enriched")
            
            # If incremental mode was used, files are already written row-by-row
            # Just log the file locations
            if use_incremental:
                jsonl_path = output_dir / f"deals_enriched_{timestamp}.jsonl"
                tsv_path_enriched = output_dir / f"deals_enriched_{timestamp}.tsv"
                
                if jsonl_path.exists():
                    logger.info(f"Incremental JSONL export: {jsonl_path}")
                if tsv_path_enriched.exists():
                    # Count rows in TSV
                    df_check = pd.read_csv(tsv_path_enriched, sep='\t', nrows=0)
                    row_count = sum(1 for _ in open(tsv_path_enriched)) - 1  # Subtract header
                    logger.info(f"Incremental TSV export: {tsv_path_enriched} ({row_count} rows, {len(df_check.columns)} columns)")
                
                # Google Sheets was updated incrementally, no need to upload again
                if not args.no_sheets:
                    logger.info("✅ Google Sheets updated incrementally during enrichment")
                
                # Set paths for final logging
                json_path = jsonl_path  # Use jsonl for incremental mode
            else:
                # Legacy batch export (shouldn't happen with incremental=True, but keep for safety)
                timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
                output_dir = Path(extractor.output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                
                # Export JSON
                enriched_dicts = [deal.model_dump(mode='json') for deal in enriched_deals]
                json_path = output_dir / f"deals_enriched_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(enriched_dicts, f, indent=2, ensure_ascii=False)
                logger.info(f"Exported enriched JSON: {json_path}")
                
                # Export TSV
                from src.common.data_exporter import flatten_dict
                flattened_deals = [
                    flatten_dict(deal, exclude_keys={'raw_deal_data'})
                    for deal in enriched_dicts
                ]
                df_enriched = pd.DataFrame(flattened_deals)
                
                # Ensure raw_deal_data is present as JSON string
                if 'raw_deal_data' not in df_enriched.columns:
                    raw_deal_data_col = []
                    for deal in enriched_dicts:
                        raw_deal_data_col.append(json.dumps(deal.get('raw_deal_data', {})))
                    df_enriched['raw_deal_data'] = raw_deal_data_col
                
                tsv_path_enriched = output_dir / f"deals_enriched_{timestamp}.tsv"
                df_enriched.to_csv(tsv_path_enriched, index=False, sep='\t')
                logger.info(f"Exported enriched TSV: {tsv_path_enriched} ({len(df_enriched)} rows, {len(df_enriched.columns)} columns)")
                
                # Upload to Google Sheets Unified worksheet
                if not args.no_sheets:
                    logger.info("Uploading enriched deals to Google Sheets 'Unified' worksheet...")
                    spreadsheet = extractor.exporter._get_spreadsheet()
                    if spreadsheet:
                        success = extractor.exporter._upload_dataframe_to_worksheet(spreadsheet, df_enriched, "Unified")
                        if success:
                            logger.info(f"✅ Successfully uploaded {len(df_enriched)} enriched deals to worksheet 'Unified'")
                        else:
                            logger.warning("❌ Failed to upload enriched deals to Google Sheets")
                    else:
                        logger.warning("Could not authenticate with Google Sheets. Skipping upload.")
            
            logger.info("\n" + "=" * 60)
            logger.info("Enrichment Complete!")
            logger.info("=" * 60)
            logger.info(f"Enriched {len(enriched_deals)} deals")
            logger.info(f"JSON: {json_path}")
            logger.info(f"TSV: {tsv_path_enriched}")
            
            return 0
        
        # Extract deals
        logger.info("=" * 60)
        logger.info("Starting deal extraction...")
        logger.info("=" * 60)

        # Determine if we should upload to Google Sheets
        upload_to_sheets = not args.no_sheets

        if args.regenerate_unified:
            # Regenerate unified TSV from existing JSON
            from scripts.regenerate_unified import process_json_file, regenerate_unified_tsv, upload_to_sheets as upload_unified_to_sheets
            from pathlib import Path
            
            json_file = Path("output/deals_2026-01-21T0358.json")
            if not json_file.exists():
                logger.error(f"JSON file not found: {json_file}")
                return 1
            
            timestamp = json_file.stem.replace("deals_", "") if "deals_" in json_file.stem else None
            if not timestamp:
                timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
            
            data = process_json_file(json_file)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            tsv_file = regenerate_unified_tsv(json_file, timestamp, Path(extractor.output_dir))
            
            if not args.no_sheets:
                upload_unified_to_sheets(tsv_file, extractor.exporter)
            
            logger.info("\n" + "=" * 60)
            logger.info("Unified TSV regeneration complete!")
            logger.info("=" * 60)
            return 0
        
        if args.no_export:
            # Just extract (and optionally enrich), don't export
            results = extractor.extract_all(vendors, **filters)
            
            # Optionally enrich deals
            if args.enrich:
                results = extractor.enrich_deals(results)
            
            logger.info("\n" + "=" * 60)
            if args.enrich:
                logger.info("Extraction and Enrichment Complete!")
            else:
                logger.info("Extraction Complete!")
            logger.info("=" * 60)
            for vendor_name, deals in results.items():
                logger.info(f"{vendor_name}: {len(deals)} deals")
        else:
            # Extract, optionally enrich, and export
            output_files = extractor.extract_and_export(
                vendors,
                upload_to_sheets=upload_to_sheets,
                enrich=args.enrich,
                **filters
            )

            logger.info("\n" + "=" * 60)
            if args.enrich:
                logger.info("Extraction, Enrichment, and Export Complete!")
            else:
                logger.info("Extraction and Export Complete!")
            logger.info("=" * 60)
            for file_type, filepath in output_files.items():
                logger.info(f"{file_type.upper()}: {filepath}")

        return 0

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
