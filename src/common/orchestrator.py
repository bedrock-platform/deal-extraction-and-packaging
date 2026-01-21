"""
Multi-Vendor Deal Extraction Orchestrator

Unified interface for extracting deals from multiple vendors.
Supports Google Authorized Buyers, BidSwitch, and future vendors.
"""
import logging
from typing import List, Dict, Optional, Callable
from pathlib import Path

from .data_exporter import UnifiedDataExporter
from .schema import UnifiedPreEnrichmentSchema

logger = logging.getLogger(__name__)


class DealExtractor:
    """
    Unified interface for extracting deals from multiple vendors.
    
    Supports:
    - Google Authorized Buyers (Marketplace)
    - Google Curated
    - BidSwitch
    - Future vendors...
    """
    
    def __init__(self, output_dir: str = "output", debug: bool = False, google_sheets_id: Optional[str] = None):
        """
        Initialize deal extractor.
        
        Args:
            output_dir: Directory for output files
            debug: Enable debug logging
            google_sheets_id: Google Sheets spreadsheet ID (reads from GOOGLE_SHEETS_ID env var if None)
        """
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize vendors (lazy loading to avoid import errors if credentials missing)
        self.vendors: Dict[str, Dict] = {}
        self.exporter = UnifiedDataExporter(self.output_dir, google_sheets_id=google_sheets_id)
        
        logger.info("Initialized DealExtractor")
    
    def _get_google_ads_vendor(self):
        """Lazy load Google Ads vendor."""
        if "google_ads" not in self.vendors:
            try:
                from ..google_ads.client import GoogleAdsClient
                from ..google_ads.transformer import GoogleAdsTransformer
                
                client = GoogleAdsClient(debug=logging.getLogger().level == logging.DEBUG)
                transformer = GoogleAdsTransformer()
                
                self.vendors["google_ads"] = {
                    "client": client,
                    "transformer": transformer,
                    "name": "Google Authorized Buyers"
                }
                logger.info("Loaded Google Ads vendor")
            except Exception as e:
                logger.warning(f"Failed to load Google Ads vendor: {e}")
                raise
    
    def _get_bidswitch_vendor(self):
        """Lazy load BidSwitch vendor."""
        if "bidswitch" not in self.vendors:
            try:
                from ..bidswitch import BidSwitchClient, BidSwitchTransformer
                
                client = BidSwitchClient()
                transformer = BidSwitchTransformer()
                
                self.vendors["bidswitch"] = {
                    "client": client,
                    "transformer": transformer,
                    "name": "BidSwitch"
                }
                logger.info("Loaded BidSwitch vendor")
            except Exception as e:
                logger.warning(f"Failed to load BidSwitch vendor: {e}")
                raise
    
    def _get_google_curated_vendor(self):
        """Lazy load Google Curated vendor."""
        if "google_curated" not in self.vendors:
            try:
                from ..google_ads.client import GoogleAdsClient
                from ..google_ads.transformer import GoogleCuratedTransformer
                
                # Reuse Google Ads client (it has discover_google_curated_deals method)
                client = GoogleAdsClient(debug=logging.getLogger().level == logging.DEBUG)
                transformer = GoogleCuratedTransformer()
                
                self.vendors["google_curated"] = {
                    "client": client,
                    "transformer": transformer,
                    "name": "Google Curated"
                }
                logger.info("Loaded Google Curated vendor")
            except Exception as e:
                logger.warning(f"Failed to load Google Curated vendor: {e}")
                raise
    
    def extract_vendor(
        self,
        vendor_name: str,
        **filters
    ) -> List[Dict]:
        """
        Extract deals from a single vendor.
        
        Args:
            vendor_name: Vendor name ("google_ads" or "bidswitch")
            **filters: Vendor-specific filter parameters
            
        Returns:
            List of transformed deal dictionaries
        """
        # Load vendor if not already loaded
        if vendor_name == "google_ads":
            self._get_google_ads_vendor()
        elif vendor_name == "bidswitch":
            self._get_bidswitch_vendor()
        elif vendor_name == "google_curated":
            self._get_google_curated_vendor()
        else:
            raise ValueError(f"Unknown vendor: {vendor_name}. Supported: google_ads, google_curated, bidswitch")
        
        if vendor_name not in self.vendors:
            raise ValueError(f"Vendor {vendor_name} not available")
        
        vendor = self.vendors[vendor_name]
        client = vendor["client"]
        transformer = vendor["transformer"]
        
        logger.info(f"Extracting deals from {vendor['name']}...")
        
        # Fetch deals
        if vendor_name == "google_ads":
            # Google Ads uses payload parameter
            payload = filters.pop("payload", None)
            deals = client.discover_deals(payload=payload, **filters)
            
            # Google Ads needs package details hydration
            if deals:
                entity_ids = [d.get("entityId") for d in deals if d.get("entityId")]
                package_details = client.hydrate_package_details(entity_ids) if entity_ids else {}
            else:
                package_details = {}
        elif vendor_name == "google_curated":
            # Google Curated uses discover_google_curated_deals method
            page_size = filters.pop("page_size", 20)
            deals = client.discover_google_curated_deals(page_size=page_size)
            package_details = None  # Google Curated doesn't need hydration
        else:
            # BidSwitch uses keyword arguments directly
            deals = client.discover_deals(**filters)
            package_details = None
        
        # Transform deals
        transformed = []
        for deal in deals:
            # Validate deal
            is_valid, missing = transformer.validate(deal)
            if not is_valid:
                logger.warning(f"Skipping invalid deal from {vendor['name']} (missing: {missing})")
                continue
            
            # Transform deal
            if vendor_name == "google_ads":
                records = transformer.transform(deal, package_details=package_details)
            elif vendor_name == "google_curated":
                # Google Curated packages don't need package_details hydration
                records = transformer.transform(deal)
            else:
                records = transformer.transform(deal)
            
            # Convert UnifiedPreEnrichmentSchema objects to dicts for backward compatibility
            for record in records:
                if hasattr(record, 'model_dump'):  # Pydantic v2
                    transformed.append(record.model_dump())
                elif hasattr(record, 'dict'):  # Pydantic v1
                    transformed.append(record.dict())
                else:
                    # Already a dict (backward compatibility)
                    transformed.append(record)
        
        logger.info(f"Extracted {len(transformed)} deals from {vendor['name']}")
        return transformed
    
    def extract_all(
        self,
        vendors: Optional[List[str]] = None,
        include_google_curated: bool = True,
        **filters
    ) -> Dict[str, List[Dict]]:
        """
        Extract deals from all specified vendors.
        
        Args:
            vendors: List of vendor names to extract from (None = all available)
            include_google_curated: If True and vendors is None, include Google Curated (default: True)
            **filters: Vendor-specific filter parameters (will be passed to each vendor)
            
        Returns:
            Dictionary mapping vendor name -> list of transformed deals
        """
        if vendors is None:
            vendors = ["google_ads", "bidswitch"]
            if include_google_curated:
                vendors.append("google_curated")
        
        results = {}
        
        for vendor_name in vendors:
            try:
                deals = self.extract_vendor(vendor_name, **filters)
                vendor_display_name = self.vendors.get(vendor_name, {}).get("name", vendor_name)
                results[vendor_display_name] = deals
            except Exception as e:
                logger.error(f"Failed to extract deals from {vendor_name}: {e}")
                results[vendor_name] = []
        
        return results
    
    def export_all(
        self,
        results: Dict[str, List[Dict]],
        timestamp: Optional[str] = None,
        upload_to_sheets: bool = True
    ) -> Dict[str, Path]:
        """
        Export all vendor results to files and optionally upload to Google Sheets.
        
        Args:
            results: Dictionary mapping vendor name -> list of transformed deals
            timestamp: Optional ISO 8601 timestamp string
            upload_to_sheets: If True, upload to Google Sheets after file export
            
        Returns:
            Dictionary mapping file type to file path
        """
        return self.exporter.export_multi_vendor(results, timestamp, upload_to_sheets=upload_to_sheets)
    
    def enrich_deals(
        self,
        results: Dict[str, List[Dict]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Enrich deals with semantic metadata using Stage 1 LLM inference.
        
        Args:
            results: Dictionary mapping vendor name -> list of deal dictionaries
            progress_callback: Optional callback function(vendor_name, current, total)
            
        Returns:
            Dictionary mapping vendor name -> list of enriched deal dictionaries
        """
        try:
            from ..enrichment import DealEnricher
        except ImportError:
            logger.error("Enrichment module not available. Install required dependencies.")
            raise
        
        logger.info("=" * 60)
        logger.info("Starting deal enrichment (Stage 1)...")
        logger.info("=" * 60)
        
        enricher = DealEnricher()
        enriched_results = {}
        
        for vendor_name, deals in results.items():
            if not deals:
                enriched_results[vendor_name] = []
                continue
            
            logger.info(f"Enriching {len(deals)} deals from {vendor_name}...")
            
            # Convert dicts back to UnifiedPreEnrichmentSchema for enrichment
            unified_deals = []
            for deal_dict in deals:
                try:
                    # Handle both UnifiedPreEnrichmentSchema dicts and legacy dicts
                    unified_deal = UnifiedPreEnrichmentSchema(**deal_dict)
                    unified_deals.append(unified_deal)
                except Exception as e:
                    logger.warning(f"Failed to convert deal to UnifiedPreEnrichmentSchema: {e}")
                    continue
            
            # Enrich deals
            def progress_cb(current, total, enriched_deal):
                if progress_callback:
                    progress_callback(vendor_name, current, total)
                if current % 10 == 0 or current == total:
                    logger.info(f"{vendor_name}: Enriched {current}/{total} deals...")
            
            enriched_deals = enricher.enrich_batch(
                unified_deals,
                progress_callback=progress_cb,
                continue_on_error=True
            )
            
            # Convert EnrichedDeal objects back to dicts
            enriched_dicts = []
            for enriched_deal in enriched_deals:
                if hasattr(enriched_deal, 'model_dump'):  # Pydantic v2
                    enriched_dict = enriched_deal.model_dump()
                elif hasattr(enriched_deal, 'dict'):  # Pydantic v1
                    enriched_dict = enriched_deal.dict()
                else:
                    enriched_dict = enriched_deal
                
                # Merge enriched fields into original deal dict (preserve all original fields)
                original_deal = next(
                    (d for d in deals if d.get('deal_id') == enriched_dict.get('deal_id')),
                    {}
                )
                merged_deal = {**original_deal, **enriched_dict}
                enriched_dicts.append(merged_deal)
            
            enriched_results[vendor_name] = enriched_dicts
            logger.info(f"Enriched {len(enriched_dicts)}/{len(deals)} deals from {vendor_name}")
        
        logger.info("=" * 60)
        logger.info("Enrichment complete!")
        logger.info("=" * 60)
        
        return enriched_results
    
    def create_packages(
        self,
        enriched_deals: List,
        progress_callback: Optional[Callable[[str], None]] = None,
        incremental: bool = False,
        checkpoint_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        timestamp: Optional[str] = None,
        google_sheets_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Create packages from enriched deals using Stage 2 Package Creation.
        
        Args:
            enriched_deals: List of EnrichedDeal objects or dictionaries
            progress_callback: Optional callback function for progress updates
            incremental: If True, enable incremental export (row-by-row)
            checkpoint_file: Optional checkpoint file path for resume capability
            output_dir: Optional output directory for incremental export
            timestamp: Optional timestamp string for incremental export
            google_sheets_id: Optional Google Sheets ID for incremental export
            
        Returns:
            List of package proposals: [{"package_name": str, "deal_ids": List[str], "reasoning": str}, ...]
        """
        import os
        from pathlib import Path
        from ..package_creation import PackageCreator
        from ..package_creation.checkpoint import PackageCreationCheckpoint
        from ..package_creation.incremental_exporter import PackageIncrementalExporter
        from ..integration.stage2_adapter import convert_enriched_deals_to_stage2_format
        from .schema import EnrichedDeal
        
        logger.info("=" * 60)
        logger.info("Starting package creation (Stage 2)...")
        logger.info("=" * 60)
        
        # Convert to EnrichedDeal objects if needed
        enriched_deal_objects = []
        for deal in enriched_deals:
            if isinstance(deal, EnrichedDeal):
                enriched_deal_objects.append(deal)
            elif isinstance(deal, dict):
                try:
                    enriched_deal_objects.append(EnrichedDeal(**deal))
                except Exception as e:
                    logger.warning(f"Failed to convert deal dict to EnrichedDeal: {e}")
                    continue
            else:
                logger.warning(f"Unknown deal type: {type(deal)}")
                continue
        
        if not enriched_deal_objects:
            logger.warning("No valid enriched deals provided for package creation")
            return []
        
        logger.info(f"Creating packages from {len(enriched_deal_objects)} enriched deals...")
        
        # Convert to Stage 2 format
        stage2_deals = convert_enriched_deals_to_stage2_format(enriched_deal_objects)
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "config" / "package_creation" / "package_grouping_prompt.txt"
        if not prompt_path.exists():
            logger.error(f"Package grouping prompt not found at {prompt_path}")
            raise FileNotFoundError(f"Package grouping prompt not found at {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Initialize PackageCreator
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        creator = PackageCreator(
            llm_api_key=api_key,
            prompt_template=prompt_template,
            model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
            clustering_method="gmm",
            use_soft_assignments=True  # Enable deal overlap
        )
        
        # Initialize checkpoint and incremental exporter if incremental mode
        checkpoint = None
        incremental_exporter = None
        
        if incremental:
            if checkpoint_file:
                checkpoint = PackageCreationCheckpoint(checkpoint_file)
                logger.info(f"Using checkpoint: {len(checkpoint.processed_cluster_indices)} clusters already processed")
            
            if output_dir and timestamp:
                incremental_exporter = PackageIncrementalExporter(
                    output_dir=output_dir,
                    timestamp=timestamp,
                    google_sheets_id=google_sheets_id
                )
                logger.info("Incremental export enabled: packages will be saved row-by-row")
        
        # Create packages
        def progress_cb(msg: str):
            if progress_callback:
                progress_callback(msg)
            logger.info(f"[Package Creation] {msg}")
        
        packages = creator.create_packages(
            stage2_deals,
            progress_callback=progress_cb,
            checkpoint=checkpoint,
            incremental_exporter=incremental_exporter
        )
        
        logger.info("=" * 60)
        logger.info(f"Package creation complete! Created {len(packages)} packages")
        logger.info("=" * 60)
        
        return packages
    
    def enrich_packages(
        self,
        packages: List[Dict[str, Any]],
        enriched_deals: List,
        progress_callback: Optional[Callable[[str], None]] = None,
        incremental: bool = False,
        checkpoint_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        timestamp: Optional[str] = None,
        google_sheets_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich packages using Stage 3 Package Enrichment.
        
        Args:
            packages: List of package proposals from Stage 2
                      Format: [{"package_name": str, "deal_ids": List[str], "reasoning": str}, ...]
            enriched_deals: List of enriched deal objects or dictionaries (from Stage 1)
            progress_callback: Optional callback function for progress updates
            incremental: If True, enable incremental export (row-by-row)
            checkpoint_file: Optional checkpoint file path for resume capability
            output_dir: Optional output directory for incremental export
            timestamp: Optional timestamp string for incremental export
            google_sheets_id: Optional Google Sheets ID for incremental export
            
        Returns:
            List of enriched packages with aggregated metadata and recommendations
        """
        import os
        from pathlib import Path
        from ..package_enrichment import PackageEnricher
        from ..package_enrichment.checkpoint import PackageEnrichmentCheckpoint
        from ..package_enrichment.incremental_exporter import EnrichedPackageIncrementalExporter
        from ..integration.stage3_adapter import convert_packages_to_stage3_format
        from .schema import EnrichedDeal
        
        logger.info("=" * 60)
        logger.info("Starting package enrichment (Stage 3)...")
        logger.info("=" * 60)
        
        # Convert enriched_deals to dictionaries if needed
        enriched_deal_dicts = []
        for deal in enriched_deals:
            if isinstance(deal, EnrichedDeal):
                enriched_deal_dicts.append(deal.model_dump(mode='json'))
            elif isinstance(deal, dict):
                enriched_deal_dicts.append(deal)
            else:
                logger.warning(f"Unknown deal type: {type(deal)}")
                continue
        
        if not enriched_deal_dicts:
            logger.warning("No enriched deals provided for package enrichment")
            return []
        
        # Convert packages to Stage 3 format
        stage3_packages = convert_packages_to_stage3_format(packages, enriched_deal_dicts)
        
        if not stage3_packages:
            logger.warning("No valid packages for enrichment")
            return []
        
        logger.info(f"Enriching {len(stage3_packages)} packages...")
        
        # Load prompt template
        prompt_path = Path(__file__).parent.parent.parent / "config" / "package_enrichment" / "package_enrichment_prompt.txt"
        if not prompt_path.exists():
            logger.error(f"Package enrichment prompt not found at {prompt_path}")
            raise FileNotFoundError(f"Package enrichment prompt not found at {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Initialize PackageEnricher
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY environment variable not set")
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        enricher = PackageEnricher(
            llm_api_key=api_key,
            prompt_template=prompt_template,
            model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
            temperature=0.3
        )
        
        # Initialize checkpoint and incremental exporter if incremental mode
        checkpoint = None
        incremental_exporter = None
        
        if incremental:
            if checkpoint_file:
                checkpoint = PackageEnrichmentCheckpoint(checkpoint_file)
                logger.info(f"Using checkpoint: {len(checkpoint.processed_package_ids)} packages already enriched")
            
            if output_dir and timestamp:
                incremental_exporter = EnrichedPackageIncrementalExporter(
                    output_dir=output_dir,
                    timestamp=timestamp,
                    google_sheets_id=google_sheets_id
                )
                logger.info("Incremental export enabled: enriched packages will be saved row-by-row")
        
        # Get unprocessed packages if checkpoint exists
        if checkpoint:
            unprocessed_packages = checkpoint.get_unprocessed_packages(stage3_packages)
        else:
            unprocessed_packages = stage3_packages
        
        # Enrich each package
        enriched_packages = []
        
        def progress_cb(msg: str):
            if progress_callback:
                progress_callback(msg)
            logger.info(f"[Package Enrichment] {msg}")
        
        for idx, package in enumerate(unprocessed_packages, 1):
            package_id = checkpoint.get_package_id(package) if checkpoint else None
            
            progress_cb(f"Enriching package {idx}/{len(unprocessed_packages)}: {package['package_name']}")
            
            enriched = enricher.enrich_package(
                package,
                package['deals'],
                progress_callback=progress_cb
            )
            
            if enriched:
                enriched_packages.append(enriched)
                
                # Export immediately if incremental exporter provided
                if incremental_exporter:
                    incremental_exporter.export_package(enriched)
                    progress_cb(f"Exported enriched package: {package['package_name']}")
                
                # Mark as processed in checkpoint
                if checkpoint and package_id:
                    checkpoint.mark_processed(package_id)
                    # Save checkpoint every 10 packages to reduce I/O
                    if idx % 10 == 0:
                        checkpoint.save()
            else:
                logger.warning(f"Failed to enrich package: {package['package_name']}")
        
        # Final checkpoint save
        if checkpoint:
            checkpoint.save()
        
        logger.info("=" * 60)
        logger.info(f"Package enrichment complete! Enriched {len(enriched_packages)}/{len(unprocessed_packages)} packages")
        logger.info("=" * 60)
        
        return enriched_packages
    
    def extract_and_export(
        self,
        vendors: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
        upload_to_sheets: bool = True,
        enrich: bool = False,
        **filters
    ) -> Dict[str, Path]:
        """
        Complete workflow: extract deals from vendors, optionally enrich, and export to files.
        
        Args:
            vendors: List of vendor names to extract from (None = all available)
            timestamp: Optional ISO 8601 timestamp string
            upload_to_sheets: If True, upload to Google Sheets after file export
            enrich: If True, enrich deals with semantic metadata before exporting
            **filters: Vendor-specific filter parameters
            
        Returns:
            Dictionary mapping file type to file path
        """
        # Extract deals
        results = self.extract_all(vendors, **filters)
        
        # Optionally enrich deals (non-fatal - continue with unenriched data if enrichment fails)
        if enrich:
            try:
                results = self.enrich_deals(results)
                logger.info("Enrichment completed successfully")
            except Exception as e:
                logger.error(f"Enrichment failed: {e}")
                logger.warning("Continuing with unenriched data - deals will be exported without semantic metadata")
                # Continue with unenriched results (results already contains extracted deals)
        
        # Export to files and optionally upload to Google Sheets
        output_files = self.export_all(results, timestamp, upload_to_sheets=upload_to_sheets)
        
        return output_files
