"""
Checkpoint Manager for Incremental Package Enrichment (Stage 3)

Tracks which packages have been enriched to enable resume capability.
"""
import json
import logging
from pathlib import Path
from typing import Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PackageEnrichmentCheckpoint:
    """
    Manages checkpoint state for incremental package enrichment.
    
    Tracks:
    - Which package IDs/names have been successfully enriched
    - Timestamp of last update
    - Source packages JSON file path
    """
    
    def __init__(self, checkpoint_file: Path):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = checkpoint_file
        self.processed_package_ids: Set[str] = set()
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
                    self.processed_package_ids = set(data.get('processed_package_ids', []))
                    self.source_file = data.get('source_file')
                    self.last_updated = data.get('last_updated')
                    logger.info(f"Loaded checkpoint: {len(self.processed_package_ids)} packages already enriched")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}. Starting fresh.")
                self.processed_package_ids = set()
        else:
            logger.info("No existing checkpoint found. Starting fresh.")
    
    def save(self, source_file: Optional[str] = None) -> None:
        """
        Save checkpoint to file.
        
        Args:
            source_file: Optional source JSON file path
        """
        if source_file:
            self.source_file = str(source_file)
        
        self.last_updated = datetime.now().isoformat()
        
        data = {
            'processed_package_ids': sorted(list(self.processed_package_ids)),
            'source_file': self.source_file,
            'last_updated': self.last_updated,
            'count': len(self.processed_package_ids)
        }
        
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved checkpoint: {len(self.processed_package_ids)} packages enriched")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def is_processed(self, package_id: str) -> bool:
        """
        Check if a package has already been processed.
        
        Args:
            package_id: Package ID or name to check
            
        Returns:
            True if package has been processed, False otherwise
        """
        return package_id in self.processed_package_ids
    
    def mark_processed(self, package_id: str) -> None:
        """
        Mark a package as processed.
        
        Args:
            package_id: Package ID or name to mark as processed
        """
        self.processed_package_ids.add(package_id)
    
    def get_package_id(self, package: dict) -> str:
        """
        Extract package ID from package dict.
        
        Args:
            package: Package dictionary
            
        Returns:
            Package ID (uses package_id, package_name, name, or generates from deal_ids)
        """
        package_id = (
            package.get('package_id') or
            package.get('package_name') or
            package.get('name') or
            None
        )
        
        if not package_id:
            # Generate ID from deal_ids if available
            deal_ids = package.get('deal_ids', [])
            if deal_ids:
                package_id = f"package_{'_'.join(map(str, deal_ids[:3]))}"
            else:
                package_id = f"package_{hash(str(package))}"
        
        return str(package_id)
    
    def get_unprocessed_packages(self, packages: list) -> list:
        """
        Filter out packages that have already been processed.
        
        Args:
            packages: List of package dictionaries
            
        Returns:
            List of unprocessed packages
        """
        unprocessed = []
        for package in packages:
            package_id = self.get_package_id(package)
            if not self.is_processed(package_id):
                unprocessed.append(package)
        
        skipped = len(packages) - len(unprocessed)
        if skipped > 0:
            logger.info(f"Resume mode: Skipping {skipped} already-enriched packages, {len(unprocessed)} remaining")
        elif len(self.processed_package_ids) == 0:
            logger.debug(f"Checkpoint is empty, enriching all {len(packages)} packages")
        
        return unprocessed
    
    def get_timestamp(self) -> Optional[str]:
        """
        Get timestamp from checkpoint file name.
        
        Returns:
            Timestamp string if available, None otherwise
        """
        # Extract from checkpoint filename (format: package_enrichment_checkpoint_TIMESTAMP.json)
        if 'package_enrichment_checkpoint_' in str(self.checkpoint_file):
            parts = self.checkpoint_file.stem.split('_')
            if len(parts) >= 4:
                timestamp = '_'.join(parts[3:])  # Handle timestamp with underscores
                # Validate timestamp format (YYYY-MM-DDTHHMM)
                if len(timestamp) >= 15 and 'T' in timestamp:
                    return timestamp
        
        return None
    
    def reset(self) -> None:
        """Reset checkpoint (clear all processed packages)."""
        self.processed_package_ids = set()
        self.source_file = None
        self.last_updated = None
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        logger.info("Checkpoint reset")
