"""
Checkpoint Manager for Incremental Package Creation (Stage 2)

Tracks which clusters have been processed to enable resume capability.
"""
import json
import logging
from pathlib import Path
from typing import Set, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class PackageCreationCheckpoint:
    """
    Manages checkpoint state for incremental package creation.
    
    Tracks:
    - Which cluster indices have been successfully processed
    - Timestamp of last update
    - Source enriched deals JSONL file path
    """
    
    def __init__(self, checkpoint_file: Path):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_file: Path to checkpoint JSON file
        """
        self.checkpoint_file = checkpoint_file
        self.processed_cluster_indices: Set[int] = set()
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
                    self.processed_cluster_indices = set(data.get('processed_cluster_indices', []))
                    self.source_file = data.get('source_file')
                    self.last_updated = data.get('last_updated')
                    logger.info(f"Loaded checkpoint: {len(self.processed_cluster_indices)} clusters already processed")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}. Starting fresh.")
                self.processed_cluster_indices = set()
        else:
            logger.info("No existing checkpoint found. Starting fresh.")
    
    def save(self, source_file: Optional[str] = None) -> None:
        """
        Save checkpoint to file.
        
        Args:
            source_file: Optional source JSONL file path
        """
        if source_file:
            self.source_file = str(source_file)
        
        self.last_updated = datetime.now().isoformat()
        
        data = {
            'processed_cluster_indices': sorted(list(self.processed_cluster_indices)),
            'source_file': self.source_file,
            'last_updated': self.last_updated,
            'count': len(self.processed_cluster_indices)
        }
        
        try:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved checkpoint: {len(self.processed_cluster_indices)} clusters processed")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def is_processed(self, cluster_idx: int) -> bool:
        """
        Check if a cluster has already been processed.
        
        Args:
            cluster_idx: Cluster index (1-based)
            
        Returns:
            True if cluster has been processed, False otherwise
        """
        return cluster_idx in self.processed_cluster_indices
    
    def mark_processed(self, cluster_idx: int) -> None:
        """
        Mark a cluster as processed.
        
        Args:
            cluster_idx: Cluster index (1-based) to mark as processed
        """
        self.processed_cluster_indices.add(cluster_idx)
    
    def get_unprocessed_clusters(self, clusters: list) -> list:
        """
        Filter out clusters that have already been processed.
        
        Args:
            clusters: List of clusters (each cluster is a list of deal indices)
            
        Returns:
            List of (cluster_index, cluster_data) tuples for unprocessed clusters
        """
        unprocessed = []
        for cluster_idx, cluster_deal_indices in enumerate(clusters, 1):
            if not self.is_processed(cluster_idx):
                unprocessed.append((cluster_idx, cluster_deal_indices))
        
        skipped = len(clusters) - len(unprocessed)
        if skipped > 0:
            logger.info(f"Resume mode: Skipping {skipped} already-processed clusters, {len(unprocessed)} remaining")
        elif len(self.processed_cluster_indices) == 0:
            logger.debug(f"Checkpoint is empty, processing all {len(clusters)} clusters")
        
        return unprocessed
    
    def get_timestamp(self) -> Optional[str]:
        """
        Get timestamp from checkpoint file name.
        
        Returns:
            Timestamp string if available, None otherwise
        """
        # Extract from checkpoint filename (format: package_creation_checkpoint_TIMESTAMP.json)
        if 'package_creation_checkpoint_' in str(self.checkpoint_file):
            parts = self.checkpoint_file.stem.split('_')
            if len(parts) >= 4:
                timestamp = '_'.join(parts[3:])  # Handle timestamp with underscores
                # Validate timestamp format (YYYY-MM-DDTHHMM)
                if len(timestamp) >= 15 and 'T' in timestamp:
                    return timestamp
        
        return None
    
    def reset(self) -> None:
        """Reset checkpoint (clear all processed clusters)."""
        self.processed_cluster_indices = set()
        self.source_file = None
        self.last_updated = None
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
        logger.info("Checkpoint reset")
