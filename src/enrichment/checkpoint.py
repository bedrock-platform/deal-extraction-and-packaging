"""
Checkpoint Manager for Incremental Enrichment

Tracks which deals have been processed to enable resume capability.
"""
import json
import logging
from pathlib import Path
from typing import Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class EnrichmentCheckpoint:
    """
    Manages checkpoint state for incremental enrichment.
    
    Tracks:
    - Which deal IDs have been successfully enriched
    - Timestamp of last update
    - Source TSV file path
    """
    
    def __init__(self, checkpoint_file: Path):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = checkpoint_file
        self.processed_deal_ids: Set[str] = set()
        self.source_file: Optional[str] = None
        self.last_updated: Optional[str] = None
        
        # Load existing checkpoint if it exists
        self._load()
    
    def _load(self) -> None:
        """Load checkpoint from file."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_deal_ids = set(data.get('processed_deal_ids', []))
                    self.source_file = data.get('source_file')
                    self.last_updated = data.get('last_updated')
                    logger.info(f"Loaded checkpoint: {len(self.processed_deal_ids)} deals already processed")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}. Starting fresh.")
                self.processed_deal_ids = set()
        else:
            logger.info("No existing checkpoint found. Starting fresh.")
    
    def save(self, source_file: Optional[str] = None) -> None:
        """
        Save checkpoint to file.
        
        Args:
            source_file: Optional source TSV file path
        """
        if source_file:
            self.source_file = str(source_file)
        
        self.last_updated = datetime.now().isoformat()
        
        data = {
            'processed_deal_ids': sorted(list(self.processed_deal_ids)),
            'source_file': self.source_file,
            'last_updated': self.last_updated,
            'count': len(self.processed_deal_ids)
        }
        
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved checkpoint: {len(self.processed_deal_ids)} deals processed")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def is_processed(self, deal_id: str) -> bool:
        """
        Check if a deal has already been processed.
        
        Args:
            deal_id: Deal ID to check
            
        Returns:
            True if deal has been processed, False otherwise
        """
        return deal_id in self.processed_deal_ids
    
    def mark_processed(self, deal_id: str) -> None:
        """
        Mark a deal as processed.
        
        Args:
            deal_id: Deal ID to mark as processed
        """
        self.processed_deal_ids.add(deal_id)
    
    def get_unprocessed_deals(self, deals: list) -> list:
        """
        Filter out deals that have already been processed.
        
        Args:
            deals: List of deal objects with 'deal_id' attribute
            
        Returns:
            List of unprocessed deals
        """
        unprocessed = []
        for deal in deals:
            # Try multiple ways to get deal_id
            deal_id = None
            if hasattr(deal, 'deal_id'):
                deal_id = getattr(deal, 'deal_id')
            elif isinstance(deal, dict):
                deal_id = deal.get('deal_id')
            elif hasattr(deal, '__dict__'):
                deal_id = getattr(deal, 'deal_id', None)
            
            if deal_id and not self.is_processed(deal_id):
                unprocessed.append(deal)
            elif not deal_id:
                # If deal_id is missing, log warning but include it (shouldn't happen)
                logger.warning(f"Deal missing deal_id: {deal}")
                unprocessed.append(deal)
        
        skipped = len(deals) - len(unprocessed)
        if skipped > 0:
            logger.info(f"Resume mode: Skipping {skipped} already-processed deals, {len(unprocessed)} remaining")
        elif len(self.processed_deal_ids) == 0:
            # If checkpoint is empty, don't log the "skipping" message
            logger.debug(f"Checkpoint is empty, processing all {len(deals)} deals")
        
        return unprocessed
    
    def get_timestamp(self) -> Optional[str]:
        """
        Get timestamp from checkpoint file name.
        
        Returns:
            Timestamp string if available, None otherwise
        """
        # Extract from checkpoint filename (format: enrichment_checkpoint_TIMESTAMP.json)
        if 'enrichment_checkpoint_' in str(self.checkpoint_file):
            parts = self.checkpoint_file.stem.split('_')
            if len(parts) >= 3:
                timestamp = parts[2]  # Assuming format: enrichment_checkpoint_TIMESTAMP.json
                # Validate timestamp format (YYYY-MM-DDTHHMM)
                if len(timestamp) == 15 and timestamp[10] == 'T':
                    return timestamp
        
        return None
    
    def reset(self) -> None:
        """Reset checkpoint (clear all processed deals)."""
        self.processed_deal_ids = set()
        self.source_file = None
        self.last_updated = None
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        logger.info("Checkpoint reset")
