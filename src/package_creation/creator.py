"""
Package Creator Module

Main class for creating intelligent packages from enriched deals.
"""
import json
import time
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    raise ImportError(
        "langchain-google-genai is required. "
        "Install with: pip install langchain-google-genai"
    )

from .embeddings import create_deal_embeddings
from .clustering import cluster_deals_semantically, cluster_deals_with_soft_assignments


class PackageCreator:
    """
    Creates intelligent audience packages from enriched deals using semantic clustering + LLM.
    
    Process:
    1. Creates semantic embeddings for each deal
    2. Clusters deals by similarity (K-means or GMM)
    3. Processes each cluster through LLM to propose package groupings
    4. Returns package proposals
    
    GMM clustering is recommended for better handling of overlapping clusters and
    non-spherical cluster shapes, which aligns with the deal overlap strategy.
    """
    
    def __init__(
        self,
        llm_api_key: str,
        prompt_template: str,
        model_name: str = "gemini-2.5-flash",
        temperature: float = 0.5,
        embedding_model: str = "all-MiniLM-L6-v2",
        max_deals_per_cluster: int = 25,
        min_cluster_size: int = 5,
        clustering_method: str = "gmm",
        use_soft_assignments: bool = False
    ):
        """
        Initialize PackageCreator.
        
        Args:
            llm_api_key: Google Gemini API key
            prompt_template: LLM prompt template string (uses {enriched_deals} placeholder)
            model_name: LLM model name (default: "gemini-2.5-flash")
            temperature: LLM temperature (default: 0.5)
            embedding_model: Sentence transformer model name
            max_deals_per_cluster: Maximum deals per cluster for LLM processing
            min_cluster_size: Minimum cluster size
            clustering_method: "kmeans" or "gmm" (default: "gmm")
            use_soft_assignments: If True, uses GMM soft assignments for deal overlap (default: False)
        """
        self.prompt_template = prompt_template
        self.embedding_model = embedding_model
        self.max_deals_per_cluster = max_deals_per_cluster
        self.min_cluster_size = min_cluster_size
        self.clustering_method = clustering_method
        self.use_soft_assignments = use_soft_assignments
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            google_api_key=llm_api_key,
            timeout=60,
            max_retries=2
        )
    
    def create_packages(
        self,
        deals: List[Dict[str, Any]],
        progress_callback: Optional[Callable[[str], None]] = None,
        checkpoint: Optional[Any] = None,
        incremental_exporter: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Create packages from enriched deals.
        
        Args:
            deals: List of enriched deal dictionaries
            progress_callback: Optional callback function for progress updates
            checkpoint: Optional PackageCreationCheckpoint for resume capability
            incremental_exporter: Optional PackageIncrementalExporter for row-by-row export
            
        Returns:
            List of package proposals: [{"package_name": str, "deal_ids": List[str], "reasoning": str}, ...]
        """
        if len(deals) < self.min_cluster_size:
            if progress_callback:
                progress_callback(f"Not enough deals (need {self.min_cluster_size}, have {len(deals)})")
            return []
        
        # Step 1: Create semantic embeddings
        if progress_callback:
            progress_callback(f"Creating embeddings for {len(deals)} deals...")
        
        embeddings, _ = create_deal_embeddings(deals, model_name=self.embedding_model)
        
        if progress_callback:
            progress_callback(f"Created {len(embeddings)} embeddings")
        
        # Step 2: Cluster deals semantically
        if progress_callback:
            method_name = "GMM (soft)" if self.use_soft_assignments else self.clustering_method.upper()
            progress_callback(f"Clustering deals by semantic similarity using {method_name}...")
        
        if self.use_soft_assignments:
            # Use GMM with soft assignments for deal overlap
            clusters = cluster_deals_with_soft_assignments(
                deals,
                embeddings,
                max_deals_per_cluster=self.max_deals_per_cluster,
                min_cluster_size=self.min_cluster_size
            )
        else:
            # Use standard clustering (K-means or GMM)
            clusters = cluster_deals_semantically(
                deals,
                embeddings,
                max_deals_per_cluster=self.max_deals_per_cluster,
                min_cluster_size=self.min_cluster_size,
                method=self.clustering_method
            )
        
        if not clusters:
            if progress_callback:
                progress_callback("No clusters created")
            return []
        
        if progress_callback:
            progress_callback(f"Created {len(clusters)} clusters")
        
        # Step 3: Process each cluster through LLM (with checkpoint support)
        if progress_callback:
            progress_callback(f"Processing {len(clusters)} clusters through LLM...")
        
        all_proposals = []
        
        # Get unprocessed clusters if checkpoint exists
        if checkpoint:
            unprocessed_clusters = checkpoint.get_unprocessed_clusters(clusters)
        else:
            unprocessed_clusters = [(idx, cluster_deal_indices) for idx, cluster_deal_indices in enumerate(clusters, 1)]
        
        for cluster_idx, cluster_deal_indices in unprocessed_clusters:
            # Get deals for this cluster
            cluster_deals = [deals[i] for i in cluster_deal_indices]
            
            # Propose packages for this cluster
            batch_proposals = self._propose_packages_for_cluster(
                cluster_deals,
                cluster_idx,
                progress_callback
            )
            
            # Export packages immediately if incremental exporter provided
            if incremental_exporter and batch_proposals:
                for package in batch_proposals:
                    incremental_exporter.export_package(package)
                    if progress_callback:
                        progress_callback(f"[Cluster {cluster_idx}] Exported {len(batch_proposals)} packages")
            
            all_proposals.extend(batch_proposals)
            
            # Mark cluster as processed in checkpoint
            if checkpoint:
                checkpoint.mark_processed(cluster_idx)
                # Save checkpoint every 5 clusters to reduce I/O
                if cluster_idx % 5 == 0:
                    checkpoint.save()
            
            # Small delay to avoid rate limits
            if cluster_idx < len(clusters):
                time.sleep(1)
        
        # Final checkpoint save
        if checkpoint:
            checkpoint.save()
        
        if progress_callback:
            progress_callback(f"Total packages proposed: {len(all_proposals)}")
        
        return all_proposals
    
    def _propose_packages_for_cluster(
        self,
        cluster_deals: List[Dict[str, Any]],
        cluster_idx: int,
        progress_callback: Optional[Callable[[str], None]]
    ) -> List[Dict[str, Any]]:
        """Propose packages for a single cluster using LLM"""
        # Format deals for prompt
        deals_json = json.dumps(cluster_deals, indent=2)
        
        # Format prompt
        prompt = self.prompt_template.format(enriched_deals=deals_json)
        
        # Call LLM
        try:
            if progress_callback:
                progress_callback(f"[Cluster {cluster_idx}] Analyzing {len(cluster_deals)} deals...")
            
            start_time = time.time()
            response = self.llm.invoke(prompt)
            elapsed = time.time() - start_time
            content = response.content
            
            if progress_callback:
                progress_callback(f"[Cluster {cluster_idx}] LLM response received ({elapsed:.1f}s)")
            
            # Parse JSON response
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            proposals = json.loads(content)
            
            if not isinstance(proposals, list):
                if progress_callback:
                    progress_callback(f"[Cluster {cluster_idx}] LLM returned non-list response")
                return []
            
            if progress_callback:
                progress_callback(f"[Cluster {cluster_idx}] Proposed {len(proposals)} packages")
            
            return proposals
            
        except json.JSONDecodeError as e:
            if progress_callback:
                progress_callback(f"[Cluster {cluster_idx}] JSON parse error: {e}")
            return []
        except Exception as e:
            if progress_callback:
                progress_callback(f"[Cluster {cluster_idx}] Error: {e}")
            return []
