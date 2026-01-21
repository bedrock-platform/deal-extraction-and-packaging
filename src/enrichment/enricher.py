"""
Deal Enricher

Batch processing orchestrator for Stage 1 enrichment.
"""
import logging
from typing import List, Optional, Callable
from datetime import datetime
from pathlib import Path

from ..common.schema import UnifiedPreEnrichmentSchema, EnrichedDeal
from .llm_client import GeminiClient
from .inference import enrich_deal
from .checkpoint import EnrichmentCheckpoint
from .incremental_exporter import IncrementalExporter

logger = logging.getLogger(__name__)


class DealEnricher:
    """
    Orchestrates batch enrichment of deals using LLM inference.
    
    Handles:
    - Batch processing with progress tracking
    - Error handling and recovery
    - Optional progress callbacks
    """
    
    def __init__(
        self,
        llm_client: Optional[GeminiClient] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: float = 0.5
    ):
        """
        Initialize DealEnricher.
        
        Args:
            llm_client: Optional GeminiClient instance (creates one if not provided)
            api_key: Google Gemini API key (only used if llm_client not provided)
            model_name: Model name (reads from GEMINI_MODEL_NAME env var if None, only used if llm_client not provided)
            temperature: Sampling temperature (only used if llm_client not provided)
        """
        if llm_client:
            self.llm_client = llm_client
        else:
            self.llm_client = GeminiClient(
                api_key=api_key,
                model_name=model_name,
                temperature=temperature
            )
        
        logger.info("Initialized DealEnricher")
    
    def enrich_batch(
        self,
        deals: List[UnifiedPreEnrichmentSchema],
        progress_callback: Optional[Callable[[int, int, EnrichedDeal], None]] = None,
        continue_on_error: bool = True,
        incremental: bool = False,
        checkpoint_file: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        timestamp: Optional[str] = None,
        google_sheets_id: Optional[str] = None
    ) -> List[EnrichedDeal]:
        """
        Enrich a batch of deals.
        
        Args:
            deals: List of UnifiedPreEnrichmentSchema instances to enrich
            progress_callback: Optional callback function(current_index, total, enriched_deal)
            continue_on_error: If True, continue processing on errors (default: True)
            incremental: If True, save each deal immediately and support resume (default: False)
            checkpoint_file: Path to checkpoint file (only used if incremental=True)
            output_dir: Output directory for incremental files (only used if incremental=True)
            timestamp: Timestamp string for filenames (only used if incremental=True)
            google_sheets_id: Google Sheets ID for incremental upload (only used if incremental=True)
            
        Returns:
            List of EnrichedDeal instances (may be shorter than input if errors occurred)
        """
        total = len(deals)
        enriched = []
        errors = 0
        
        # Initialize checkpoint if incremental mode
        checkpoint = None
        exporter = None
        if incremental:
            if checkpoint_file:
                checkpoint = EnrichmentCheckpoint(checkpoint_file)
                # Filter out already-processed deals
                deals = checkpoint.get_unprocessed_deals(deals)
                total = len(deals)
                logger.info(f"Resume mode: {total} deals remaining to process")
            
            if output_dir and timestamp:
                exporter = IncrementalExporter(
                    output_dir=output_dir,
                    timestamp=timestamp,
                    google_sheets_id=google_sheets_id
                )
        
        logger.info(f"Starting batch enrichment of {total} deals")
        
        for idx, deal in enumerate(deals, 1):
            try:
                enriched_deal = enrich_deal(deal, self.llm_client)
                enriched.append(enriched_deal)
                
                # Incremental persistence: save immediately
                if incremental:
                    if checkpoint:
                        checkpoint.mark_processed(deal.deal_id)
                        # Save checkpoint every 10 deals to reduce I/O
                        if idx % 10 == 0:
                            checkpoint.save()
                    
                    if exporter:
                        exporter.export_deal(enriched_deal)
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(idx, total, enriched_deal)
                
                logger.debug(f"Enriched {idx}/{total}: {deal.deal_id}")
                
            except Exception as e:
                errors += 1
                logger.error(f"Failed to enrich deal {deal.deal_id} ({idx}/{total}): {e}")
                
                if not continue_on_error:
                    raise
                
                # Continue with next deal
        
        # Final checkpoint save
        if incremental and checkpoint:
            checkpoint.save()
        
        logger.info(
            f"Batch enrichment complete: {len(enriched)}/{total} enriched successfully, "
            f"{errors} errors"
        )
        
        return enriched
    
    def enrich_single(self, deal: UnifiedPreEnrichmentSchema) -> EnrichedDeal:
        """
        Enrich a single deal (convenience method).
        
        Args:
            deal: UnifiedPreEnrichmentSchema instance
            
        Returns:
            EnrichedDeal instance
        """
        return enrich_deal(deal, self.llm_client)
