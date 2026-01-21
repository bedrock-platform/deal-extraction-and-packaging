"""
Pipeline Orchestrator

Orchestrates the complete pipeline: Stage 0 → Stage 1 → Stage 2 → Stage 3.
"""
import json
import logging
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

from .orchestrator import DealExtractor
from .schema import EnrichedDeal

logger = logging.getLogger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the complete semantic enrichment pipeline.
    
    Pipeline stages:
    - Stage 0: Deal extraction from vendors
    - Stage 1: Deal enrichment with semantic metadata
    - Stage 2: Package creation from enriched deals
    - Stage 3: Package enrichment with aggregated metadata
    """
    
    def __init__(
        self,
        output_dir: str = "output",
        debug: bool = False,
        google_sheets_id: Optional[str] = None
    ):
        """
        Initialize pipeline orchestrator.
        
        Args:
            output_dir: Directory for output files
            debug: Enable debug logging
            google_sheets_id: Google Sheets spreadsheet ID
        """
        self.extractor = DealExtractor(output_dir=output_dir, debug=debug, google_sheets_id=google_sheets_id)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("Initialized PipelineOrchestrator")
    
    def load_enriched_deals_from_jsonl(self, jsonl_path: Path) -> List[EnrichedDeal]:
        """
        Load enriched deals from JSONL file.
        
        Args:
            jsonl_path: Path to JSONL file containing enriched deals
            
        Returns:
            List of EnrichedDeal objects
        """
        logger.info(f"Loading enriched deals from {jsonl_path}...")
        
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        enriched_deals = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        deal_dict = json.loads(line)
                        enriched_deal = EnrichedDeal(**deal_dict)
                        enriched_deals.append(enriched_deal)
                    except Exception as e:
                        logger.warning(f"Failed to parse line {line_num} in {jsonl_path}: {e}")
                        continue
        
        logger.info(f"Loaded {len(enriched_deals)} enriched deals from {jsonl_path}")
        return enriched_deals
    
    def load_packages_from_json(self, json_path: Path) -> List[Dict[str, Any]]:
        """
        Load packages from JSON file.
        
        Args:
            json_path: Path to JSON file containing packages
            
        Returns:
            List of package dictionaries
        """
        logger.info(f"Loading packages from {json_path}...")
        
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            packages = json.load(f)
        
        if not isinstance(packages, list):
            raise ValueError(f"Expected list of packages, got {type(packages)}")
        
        logger.info(f"Loaded {len(packages)} packages from {json_path}")
        return packages
    
    def run_stage_0(
        self,
        vendors: Optional[List[str]] = None,
        **filters
    ) -> Dict[str, List[Dict]]:
        """
        Run Stage 0: Deal extraction from vendors.
        
        Args:
            vendors: List of vendor names (None = all available)
            **filters: Vendor-specific filter parameters
            
        Returns:
            Dictionary mapping vendor name -> list of deal dictionaries
        """
        logger.info("=" * 60)
        logger.info("Stage 0: Extracting deals from vendors...")
        logger.info("=" * 60)
        
        results = self.extractor.extract_all(vendors, **filters)
        
        total_deals = sum(len(deals) for deals in results.values())
        logger.info(f"Stage 0 complete: Extracted {total_deals} deals from {len(results)} vendors")
        
        return results
    
    def run_stage_1(
        self,
        deals: Dict[str, List[Dict]],
        progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> List[EnrichedDeal]:
        """
        Run Stage 1: Enrich deals with semantic metadata.
        
        Args:
            deals: Dictionary mapping vendor name -> list of deal dictionaries
            progress_callback: Optional callback function(vendor_name, current, total)
            
        Returns:
            List of EnrichedDeal objects
        """
        logger.info("=" * 60)
        logger.info("Stage 1: Enriching deals with semantic metadata...")
        logger.info("=" * 60)
        
        # Enrich deals
        enriched_results = self.extractor.enrich_deals(deals, progress_callback=progress_callback)
        
        # Flatten to single list
        enriched_deals = []
        for vendor_deals in enriched_results.values():
            for deal_dict in vendor_deals:
                try:
                    enriched_deal = EnrichedDeal(**deal_dict)
                    enriched_deals.append(enriched_deal)
                except Exception as e:
                    logger.warning(f"Failed to convert deal to EnrichedDeal: {e}")
                    continue
        
        logger.info(f"Stage 1 complete: Enriched {len(enriched_deals)} deals")
        
        return enriched_deals
    
    def run_stage_2(
        self,
        enriched_deals: List[EnrichedDeal],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run Stage 2: Create packages from enriched deals.
        
        Args:
            enriched_deals: List of EnrichedDeal objects
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of package proposals
        """
        logger.info("=" * 60)
        logger.info("Stage 2: Creating packages from enriched deals...")
        logger.info("=" * 60)
        
        packages = self.extractor.create_packages(enriched_deals, progress_callback=progress_callback)
        
        logger.info(f"Stage 2 complete: Created {len(packages)} packages")
        
        return packages
    
    def run_stage_3(
        self,
        packages: List[Dict[str, Any]],
        enriched_deals: List[EnrichedDeal],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run Stage 3: Enrich packages with aggregated metadata.
        
        Args:
            packages: List of package proposals from Stage 2
            enriched_deals: List of EnrichedDeal objects from Stage 1
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of enriched packages
        """
        logger.info("=" * 60)
        logger.info("Stage 3: Enriching packages with aggregated metadata...")
        logger.info("=" * 60)
        
        enriched_packages = self.extractor.enrich_packages(
            packages,
            enriched_deals,
            progress_callback=progress_callback
        )
        
        logger.info(f"Stage 3 complete: Enriched {len(enriched_packages)} packages")
        
        return enriched_packages
    
    def load_enriched_deals_from_jsonl(self, jsonl_path: Path) -> List[EnrichedDeal]:
        """
        Load enriched deals from JSONL file.
        
        Args:
            jsonl_path: Path to JSONL file containing enriched deals
            
        Returns:
            List of EnrichedDeal objects
        """
        logger.info(f"Loading enriched deals from {jsonl_path}...")
        
        if not jsonl_path.exists():
            raise FileNotFoundError(f"JSONL file not found: {jsonl_path}")
        
        enriched_deals = []
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        deal_dict = json.loads(line)
                        enriched_deal = EnrichedDeal(**deal_dict)
                        enriched_deals.append(enriched_deal)
                    except Exception as e:
                        logger.warning(f"Failed to parse line {line_num} in {jsonl_path}: {e}")
                        continue
        
        logger.info(f"Loaded {len(enriched_deals)} enriched deals from {jsonl_path}")
        return enriched_deals
    
    def load_packages_from_json(self, json_path: Path) -> List[Dict[str, Any]]:
        """
        Load packages from JSON file.
        
        Args:
            json_path: Path to JSON file containing packages
            
        Returns:
            List of package dictionaries
        """
        logger.info(f"Loading packages from {json_path}...")
        
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            packages = json.load(f)
        
        if not isinstance(packages, list):
            raise ValueError(f"Expected list of packages, got {type(packages)}")
        
        logger.info(f"Loaded {len(packages)} packages from {json_path}")
        return packages
    
    def run_stage_2_only(
        self,
        enriched_jsonl_path: Path,
        timestamp: Optional[str] = None,
        save_intermediate: bool = True,
        upload_to_sheets: bool = False,
        progress_callback: Optional[Callable[[str, Any], None]] = None,
        incremental: bool = True,
        no_resume: bool = False
    ) -> Dict[str, Any]:
        """
        Run Stage 2 only: Create packages from enriched deals loaded from JSONL.
        
        Args:
            enriched_jsonl_path: Path to JSONL file with enriched deals
            timestamp: Optional ISO 8601 timestamp string
            save_intermediate: If True, save results to file
            upload_to_sheets: If True, upload to Google Sheets
            progress_callback: Optional callback function(stage_name, data)
            incremental: If True, enable incremental export (row-by-row) and checkpointing
            no_resume: If True, ignore existing checkpoint and start fresh
            
        Returns:
            Dictionary with Stage 2 results:
            {
                'stage_2': List[Dict],
                'output_files': Dict[str, Path]
            }
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        results = {
            'stage_2': None,
            'output_files': {}
        }
        
        try:
            # Load enriched deals from JSONL
            enriched_deals = self.load_enriched_deals_from_jsonl(enriched_jsonl_path)
            
            if not enriched_deals:
                logger.error("No enriched deals loaded from JSONL file")
                return results
            
            # Setup checkpoint for incremental mode
            checkpoint_file = None
            if incremental:
                checkpoint_file = self.output_dir / f"package_creation_checkpoint_{timestamp}.json"
                if no_resume and checkpoint_file.exists():
                    checkpoint_file.unlink()
                    logger.info("--no-resume specified: deleted existing checkpoint")
            
            # Stage 2: Create packages (with incremental export)
            def stage2_progress(msg):
                if progress_callback:
                    progress_callback('stage_2', {'message': msg})
                logger.info(f"[Stage 2] {msg}")
            
            stage_2_results = self.extractor.create_packages(
                enriched_deals,
                progress_callback=stage2_progress,
                incremental=incremental,
                checkpoint_file=checkpoint_file,
                output_dir=self.output_dir,
                timestamp=timestamp,
                google_sheets_id=self.extractor.exporter.google_sheets_id if upload_to_sheets else None
            )
            results['stage_2'] = stage_2_results
            
            # Load packages from JSONL if incremental mode (they were saved incrementally)
            if incremental:
                jsonl_path = self.output_dir / f"packages_{timestamp}.jsonl"
                if jsonl_path.exists():
                    # Load all packages from JSONL
                    stage_2_results = []
                    with open(jsonl_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                stage_2_results.append(json.loads(line))
                    results['stage_2'] = stage_2_results
                    results['output_files']['stage_2_jsonl'] = jsonl_path
                    
                    # Also save as JSON array
                    json_path = self.output_dir / f"packages_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(stage_2_results, f, indent=2, ensure_ascii=False)
                    results['output_files']['stage_2_json'] = json_path
                else:
                    # Fallback: save from results
                    json_path = self.output_dir / f"packages_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(stage_2_results, f, indent=2, ensure_ascii=False)
                    results['output_files']['stage_2_json'] = json_path
            elif save_intermediate:
                # Save Stage 2 results (non-incremental mode)
                json_path = self.output_dir / f"packages_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(stage_2_results, f, indent=2, ensure_ascii=False)
                results['output_files']['stage_2_json'] = json_path
                
                # Export Stage 2 packages to Google Sheets (batch upload)
                if upload_to_sheets and stage_2_results:
                    logger.info("Uploading Stage 2 packages to Google Sheets worksheet 'Packages Enriched 1'...")
                    success = self.extractor.exporter.export_packages_to_google_sheets(
                        stage_2_results,
                        worksheet_name="Packages Enriched 1"
                    )
                    if success:
                        logger.info("✅ Stage 2 packages uploaded to Google Sheets")
                    else:
                        logger.warning("⚠️  Failed to upload Stage 2 packages to Google Sheets")
            
            if progress_callback:
                progress_callback('stage_2', stage_2_results)
            
            logger.info("=" * 60)
            logger.info("Stage 2 complete!")
            logger.info(f"  - Created: {len(stage_2_results)} packages")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Stage 2 failed: {e}")
            logger.exception(e)
            raise
        
        return results
    
    def run_stage_3_only(
        self,
        packages_json_path: Path,
        enriched_jsonl_path: Path,
        timestamp: Optional[str] = None,
        save_intermediate: bool = True,
        upload_to_sheets: bool = False,
        progress_callback: Optional[Callable[[str, Any], None]] = None,
        incremental: bool = True,
        no_resume: bool = False
    ) -> Dict[str, Any]:
        """
        Run Stage 3 only: Enrich packages loaded from JSON with enriched deals from JSONL.
        
        Args:
            packages_json_path: Path to JSON file with packages from Stage 2
            enriched_jsonl_path: Path to JSONL file with enriched deals (needed for aggregation)
            timestamp: Optional ISO 8601 timestamp string
            save_intermediate: If True, save results to file
            upload_to_sheets: If True, upload to Google Sheets
            progress_callback: Optional callback function(stage_name, data)
            incremental: If True, enable incremental export (row-by-row) and checkpointing
            no_resume: If True, ignore existing checkpoint and start fresh
            
        Returns:
            Dictionary with Stage 3 results:
            {
                'stage_3': List[Dict],
                'output_files': Dict[str, Path]
            }
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        results = {
            'stage_3': None,
            'output_files': {}
        }
        
        try:
            # Load packages from JSON
            packages = self.load_packages_from_json(packages_json_path)
            
            if not packages:
                logger.error("No packages loaded from JSON file")
                return results
            
            # Load enriched deals from JSONL (needed for Stage 3 aggregation)
            enriched_deals = self.load_enriched_deals_from_jsonl(enriched_jsonl_path)
            
            if not enriched_deals:
                logger.error("No enriched deals loaded from JSONL file")
                return results
            
            # Setup checkpoint for incremental mode
            checkpoint_file = None
            if incremental:
                checkpoint_file = self.output_dir / f"package_enrichment_checkpoint_{timestamp}.json"
                if no_resume and checkpoint_file.exists():
                    checkpoint_file.unlink()
                    logger.info("--no-resume specified: deleted existing checkpoint")
            
            # Stage 3: Enrich packages (with incremental export)
            def stage3_progress(msg):
                if progress_callback:
                    progress_callback('stage_3', {'message': msg})
                logger.info(f"[Stage 3] {msg}")
            
            stage_3_results = self.extractor.enrich_packages(
                packages,
                enriched_deals,
                progress_callback=stage3_progress,
                incremental=incremental,
                checkpoint_file=checkpoint_file,
                output_dir=self.output_dir,
                timestamp=timestamp,
                google_sheets_id=self.extractor.exporter.google_sheets_id if upload_to_sheets else None
            )
            results['stage_3'] = stage_3_results
            
            # Load enriched packages from JSONL if incremental mode (they were saved incrementally)
            if incremental:
                jsonl_path = self.output_dir / f"packages_enriched_{timestamp}.jsonl"
                if jsonl_path.exists():
                    # Load all enriched packages from JSONL
                    stage_3_results = []
                    with open(jsonl_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                stage_3_results.append(json.loads(line))
                    results['stage_3'] = stage_3_results
                    results['output_files']['stage_3_jsonl'] = jsonl_path
                    
                    # Also save as JSON array
                    json_path = self.output_dir / f"packages_enriched_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(stage_3_results, f, indent=2, ensure_ascii=False)
                    results['output_files']['stage_3_json'] = json_path
                else:
                    # Fallback: save from results
                    json_path = self.output_dir / f"packages_enriched_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(stage_3_results, f, indent=2, ensure_ascii=False)
                    results['output_files']['stage_3_json'] = json_path
            elif save_intermediate:
                # Save final results (non-incremental mode)
                json_path = self.output_dir / f"packages_enriched_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(stage_3_results, f, indent=2, ensure_ascii=False)
                results['output_files']['stage_3_json'] = json_path
                
                # Export Stage 3 enriched packages to Google Sheets (batch upload)
                if upload_to_sheets and stage_3_results:
                    logger.info("Uploading Stage 3 enriched packages to Google Sheets worksheet 'Packages Enriched 2'...")
                    success = self.extractor.exporter.export_enriched_packages_to_google_sheets(
                        stage_3_results,
                        worksheet_name="Packages Enriched 2"
                    )
                    if success:
                        logger.info("✅ Stage 3 enriched packages uploaded to Google Sheets")
                    else:
                        logger.warning("⚠️  Failed to upload Stage 3 enriched packages to Google Sheets")
            
            if progress_callback:
                progress_callback('stage_3', stage_3_results)
            
            logger.info("=" * 60)
            logger.info("Stage 3 complete!")
            logger.info(f"  - Enriched: {len(stage_3_results)} packages")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Stage 3 failed: {e}")
            logger.exception(e)
            raise
        
        return results
    
    def run_stages_2_3(
        self,
        enriched_jsonl_path: Path,
        timestamp: Optional[str] = None,
        save_intermediate: bool = True,
        upload_to_sheets: bool = False,
        progress_callback: Optional[Callable[[str, Any], None]] = None,
        incremental: bool = True,
        no_resume: bool = False
    ) -> Dict[str, Any]:
        """
        Run Stage 2 → Stage 3: Create packages and enrich them from enriched deals loaded from JSONL.
        
        Args:
            enriched_jsonl_path: Path to JSONL file with enriched deals
            timestamp: Optional ISO 8601 timestamp string
            save_intermediate: If True, save intermediate results at each stage
            upload_to_sheets: If True, upload final results to Google Sheets
            progress_callback: Optional callback function(stage_name, data)
            incremental: If True, enable incremental export (row-by-row) and checkpointing
            no_resume: If True, ignore existing checkpoints and start fresh
            
        Returns:
            Dictionary with Stage 2 and Stage 3 results:
            {
                'stage_2': List[Dict],
                'stage_3': List[Dict],
                'output_files': Dict[str, Path]
            }
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        results = {
            'stage_2': None,
            'stage_3': None,
            'output_files': {}
        }
        
        try:
            # Load enriched deals from JSONL
            enriched_deals = self.load_enriched_deals_from_jsonl(enriched_jsonl_path)
            
            if not enriched_deals:
                logger.error("No enriched deals loaded from JSONL file")
                return results
            
            # Setup checkpoints for incremental mode
            checkpoint_file_stage2 = None
            checkpoint_file_stage3 = None
            if incremental:
                checkpoint_file_stage2 = self.output_dir / f"package_creation_checkpoint_{timestamp}.json"
                checkpoint_file_stage3 = self.output_dir / f"package_enrichment_checkpoint_{timestamp}.json"
                if no_resume:
                    if checkpoint_file_stage2.exists():
                        checkpoint_file_stage2.unlink()
                    if checkpoint_file_stage3.exists():
                        checkpoint_file_stage3.unlink()
                    logger.info("--no-resume specified: deleted existing checkpoints")
            
            # Stage 2: Create packages (with incremental export)
            def stage2_progress(msg):
                if progress_callback:
                    progress_callback('stage_2', {'message': msg})
                logger.info(f"[Stage 2] {msg}")
            
            stage_2_results = self.extractor.create_packages(
                enriched_deals,
                progress_callback=stage2_progress,
                incremental=incremental,
                checkpoint_file=checkpoint_file_stage2,
                output_dir=self.output_dir,
                timestamp=timestamp,
                google_sheets_id=self.extractor.exporter.google_sheets_id if upload_to_sheets else None
            )
            results['stage_2'] = stage_2_results
            
            # Load packages from JSONL if incremental mode
            if incremental:
                jsonl_path = self.output_dir / f"packages_{timestamp}.jsonl"
                if jsonl_path.exists():
                    stage_2_results = []
                    with open(jsonl_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                stage_2_results.append(json.loads(line))
                    results['stage_2'] = stage_2_results
                    results['output_files']['stage_2_jsonl'] = jsonl_path
                    
                    # Also save as JSON array
                    json_path = self.output_dir / f"packages_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(stage_2_results, f, indent=2, ensure_ascii=False)
                    results['output_files']['stage_2_json'] = json_path
            
            if progress_callback:
                progress_callback('stage_2', stage_2_results)
            
            # Stage 3: Enrich packages (with incremental export)
            def stage3_progress(msg):
                if progress_callback:
                    progress_callback('stage_3', {'message': msg})
                logger.info(f"[Stage 3] {msg}")
            
            stage_3_results = self.extractor.enrich_packages(
                stage_2_results,
                enriched_deals,
                progress_callback=stage3_progress,
                incremental=incremental,
                checkpoint_file=checkpoint_file_stage3,
                output_dir=self.output_dir,
                timestamp=timestamp,
                google_sheets_id=self.extractor.exporter.google_sheets_id if upload_to_sheets else None
            )
            results['stage_3'] = stage_3_results
            
            # Load enriched packages from JSONL if incremental mode
            if incremental:
                jsonl_path = self.output_dir / f"packages_enriched_{timestamp}.jsonl"
                if jsonl_path.exists():
                    stage_3_results = []
                    with open(jsonl_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                stage_3_results.append(json.loads(line))
                    results['stage_3'] = stage_3_results
                    results['output_files']['stage_3_jsonl'] = jsonl_path
                    
                    # Also save as JSON array
                    json_path = self.output_dir / f"packages_enriched_{timestamp}.json"
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(stage_3_results, f, indent=2, ensure_ascii=False)
                    results['output_files']['stage_3_json'] = json_path
            
            if progress_callback:
                progress_callback('stage_3', stage_3_results)
            
            logger.info("=" * 60)
            logger.info("Stages 2-3 complete!")
            logger.info(f"  - Created: {len(stage_2_results)} packages")
            logger.info(f"  - Enriched: {len(stage_3_results)} packages")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Pipeline failed at stage: {e}")
            logger.exception(e)
            raise
        
        return results
    
    def run_full_pipeline(
        self,
        vendors: Optional[List[str]] = None,
        timestamp: Optional[str] = None,
        save_intermediate: bool = True,
        upload_to_sheets: bool = False,
        progress_callback: Optional[Callable[[str, Any], None]] = None,
        **filters
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline: Stage 0 → Stage 1 → Stage 2 → Stage 3.
        
        Args:
            vendors: List of vendor names (None = all available)
            timestamp: Optional ISO 8601 timestamp string
            save_intermediate: If True, save intermediate results at each stage
            upload_to_sheets: If True, upload final results to Google Sheets
            progress_callback: Optional callback function(stage_name, data)
            **filters: Vendor-specific filter parameters
            
        Returns:
            Dictionary with results from all stages:
            {
                'stage_0': Dict[str, List[Dict]],
                'stage_1': List[EnrichedDeal],
                'stage_2': List[Dict],
                'stage_3': List[Dict],
                'output_files': Dict[str, Path]
            }
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        results = {
            'stage_0': None,
            'stage_1': None,
            'stage_2': None,
            'stage_3': None,
            'output_files': {}
        }
        
        try:
            # Stage 0: Extract deals
            stage_0_results = self.run_stage_0(vendors, **filters)
            results['stage_0'] = stage_0_results
            
            if save_intermediate:
                # Save Stage 0 results
                self.extractor.export_all(stage_0_results, timestamp, upload_to_sheets=False)
            
            if progress_callback:
                progress_callback('stage_0', stage_0_results)
            
            # Stage 1: Enrich deals
            def stage1_progress(vendor_name, current, total):
                if progress_callback:
                    progress_callback('stage_1', {'vendor': vendor_name, 'current': current, 'total': total})
            
            stage_1_results = self.run_stage_1(stage_0_results, progress_callback=stage1_progress)
            results['stage_1'] = stage_1_results
            
            if save_intermediate:
                # Save Stage 1 results
                enriched_dicts = [deal.model_dump(mode='json') for deal in stage_1_results]
                import json
                json_path = self.output_dir / f"deals_enriched_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(enriched_dicts, f, indent=2, ensure_ascii=False)
                results['output_files']['stage_1_json'] = json_path
            
            if progress_callback:
                progress_callback('stage_1', stage_1_results)
            
            # Stage 2: Create packages
            def stage2_progress(msg):
                if progress_callback:
                    progress_callback('stage_2', {'message': msg})
            
            stage_2_results = self.run_stage_2(stage_1_results, progress_callback=stage2_progress)
            results['stage_2'] = stage_2_results
            
            if save_intermediate:
                # Save Stage 2 results
                import json
                json_path = self.output_dir / f"packages_{timestamp}.json"
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(stage_2_results, f, indent=2, ensure_ascii=False)
                results['output_files']['stage_2_json'] = json_path
                
                # Export Stage 2 packages to Google Sheets
                if upload_to_sheets and stage_2_results:
                    logger.info("Uploading Stage 2 packages to Google Sheets worksheet 'Packages Enriched 1'...")
                    success = self.extractor.exporter.export_packages_to_google_sheets(
                        stage_2_results,
                        worksheet_name="Packages Enriched 1"
                    )
                    if success:
                        logger.info("✅ Stage 2 packages uploaded to Google Sheets")
                    else:
                        logger.warning("⚠️  Failed to upload Stage 2 packages to Google Sheets")
            
            if progress_callback:
                progress_callback('stage_2', stage_2_results)
            
            # Stage 3: Enrich packages
            def stage3_progress(msg):
                if progress_callback:
                    progress_callback('stage_3', {'message': msg})
            
            stage_3_results = self.run_stage_3(stage_2_results, stage_1_results, progress_callback=stage3_progress)
            results['stage_3'] = stage_3_results
            
            # Save final results
            import json
            json_path = self.output_dir / f"packages_enriched_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(stage_3_results, f, indent=2, ensure_ascii=False)
            results['output_files']['stage_3_json'] = json_path
            
            # Export Stage 3 enriched packages to Google Sheets
            if upload_to_sheets and stage_3_results:
                logger.info("Uploading Stage 3 enriched packages to Google Sheets worksheet 'Packages Enriched 2'...")
                success = self.extractor.exporter.export_enriched_packages_to_google_sheets(
                    stage_3_results,
                    worksheet_name="Packages Enriched 2"
                )
                if success:
                    logger.info("✅ Stage 3 enriched packages uploaded to Google Sheets")
                else:
                    logger.warning("⚠️  Failed to upload Stage 3 enriched packages to Google Sheets")
            
            if progress_callback:
                progress_callback('stage_3', stage_3_results)
            
            logger.info("=" * 60)
            logger.info("Full pipeline complete!")
            logger.info(f"  - Extracted: {sum(len(deals) for deals in stage_0_results.values())} deals")
            logger.info(f"  - Enriched: {len(stage_1_results)} deals")
            logger.info(f"  - Created: {len(stage_2_results)} packages")
            logger.info(f"  - Enriched: {len(stage_3_results)} packages")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Pipeline failed at stage: {e}")
            logger.exception(e)
            raise
        
        return results
