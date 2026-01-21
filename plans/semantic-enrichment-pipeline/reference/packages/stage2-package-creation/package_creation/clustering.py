"""
Semantic Clustering Module

Clusters deals using semantic similarity (K-means or GMM on embeddings).

GMM (Gaussian Mixture Model) is recommended for better handling of:
- Overlapping clusters (supports deal overlap strategy)
- Non-spherical cluster shapes
- Probabilistic assignments
"""
from typing import List, Dict, Any, Literal, Optional
import numpy as np

try:
    from sklearn.cluster import KMeans
    from sklearn.mixture import GaussianMixture
except ImportError:
    raise ImportError(
        "scikit-learn is required. "
        "Install with: pip install scikit-learn"
    )


def cluster_deals_semantically(
    deals: List[Dict[str, Any]],
    embeddings: np.ndarray,
    max_deals_per_cluster: int = 30,
    min_cluster_size: int = 5,
    method: Literal["kmeans", "gmm"] = "gmm",
    n_components: Optional[int] = None,
    covariance_type: str = "full"
) -> List[List[int]]:
    """
    Cluster deals using semantic similarity.
    
    Supports both K-means (hard clustering) and GMM (soft clustering).
    GMM is recommended for better handling of overlapping clusters and non-spherical shapes.
    
    Uses adaptive clustering to ensure clusters are small enough for LLM processing.
    
    Args:
        deals: List of deal dictionaries
        embeddings: Semantic embeddings array (numpy array)
        max_deals_per_cluster: Maximum deals per cluster (default: 30)
        min_cluster_size: Minimum cluster size (default: 5)
        method: Clustering method - "kmeans" or "gmm" (default: "gmm")
        n_components: Number of components for GMM (None = auto-select using BIC)
        covariance_type: GMM covariance type - "full", "tied", "diag", "spherical" (default: "full")
        
    Returns:
        List of clusters, where each cluster is a list of deal indices
    """
    if len(deals) < min_cluster_size:
        return []
    
    # Determine optimal number of clusters/components
    # We want clusters of size ~max_deals_per_cluster
    n_clusters = max(3, len(deals) // max_deals_per_cluster)
    n_clusters = min(n_clusters, len(deals) // min_cluster_size)  # Don't over-cluster
    
    if method == "gmm":
        # Use GMM clustering (recommended)
        if n_components is None:
            # Auto-select optimal number of components using BIC
            n_components = _select_optimal_components(embeddings, max_components=n_clusters)
        
        gmm = GaussianMixture(
            n_components=n_components,
            covariance_type=covariance_type,
            random_state=42,
            max_iter=100
        )
        cluster_labels = gmm.fit_predict(embeddings)
        
    else:
        # Use K-means clustering (original method)
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)
    
    # Group deals by cluster
    clusters = {}
    for idx, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = []
        clusters[label].append(idx)
    
    # Split large clusters
    final_clusters = []
    for cluster_idx, deal_indices in clusters.items():
        if len(deal_indices) <= max_deals_per_cluster:
            final_clusters.append(deal_indices)
        else:
            # Split large cluster into smaller batches
            for i in range(0, len(deal_indices), max_deals_per_cluster):
                final_clusters.append(deal_indices[i:i + max_deals_per_cluster])
    
    # Filter out tiny clusters
    final_clusters = [c for c in final_clusters if len(c) >= min_cluster_size]
    
    return final_clusters


def _select_optimal_components(
    embeddings: np.ndarray,
    max_components: int = 20,
    min_components: int = 3
) -> int:
    """
    Select optimal number of GMM components using Bayesian Information Criterion (BIC).
    
    Tests different numbers of components and selects the one with the lowest BIC score.
    
    Args:
        embeddings: Embedding vectors
        max_components: Maximum number of components to test
        min_components: Minimum number of components
        
    Returns:
        Optimal number of components
    """
    n_samples = len(embeddings)
    max_components = min(max_components, n_samples // 2)  # Don't exceed sample size
    
    best_bic = np.inf
    best_n = min_components
    
    for n in range(min_components, max_components + 1):
        try:
            gmm = GaussianMixture(
                n_components=n,
                covariance_type='full',
                random_state=42,
                max_iter=50  # Faster for selection
            )
            gmm.fit(embeddings)
            bic = gmm.bic(embeddings)
            
            if bic < best_bic:
                best_bic = bic
                best_n = n
        except Exception:
            # If fitting fails, skip this n
            continue
    
    return best_n


def cluster_deals_with_soft_assignments(
    deals: List[Dict[str, Any]],
    embeddings: np.ndarray,
    max_deals_per_cluster: int = 30,
    min_cluster_size: int = 5,
    probability_threshold: float = 0.3
) -> List[List[int]]:
    """
    Cluster deals using GMM with soft assignments for deal overlap strategy.
    
    This allows deals to appear in multiple clusters if they have high probability
    in multiple components, supporting the deal overlap strategy where deals
    can belong to multiple packages.
    
    Args:
        deals: List of deal dictionaries
        embeddings: Semantic embeddings array
        max_deals_per_cluster: Maximum deals per cluster
        min_cluster_size: Minimum cluster size
        probability_threshold: Minimum probability for a deal to be included in a cluster (default: 0.3)
        
    Returns:
        List of clusters with potential overlaps (deals can appear in multiple clusters)
    """
    if len(deals) < min_cluster_size:
        return []
    
    n_components = max(3, len(deals) // max_deals_per_cluster)
    n_components = min(n_components, len(deals) // min_cluster_size)
    
    # Fit GMM
    gmm = GaussianMixture(
        n_components=n_components,
        covariance_type='full',
        random_state=42,
        max_iter=100
    )
    gmm.fit(embeddings)
    
    # Get soft assignments (probabilities)
    probabilities = gmm.predict_proba(embeddings)  # Shape: [n_samples, n_components]
    
    # Create clusters based on probability threshold
    clusters = []
    for component_idx in range(n_components):
        # Get deals with probability > threshold for this component
        deal_indices = [
            idx for idx, prob in enumerate(probabilities[:, component_idx])
            if prob >= probability_threshold
        ]
        
        if len(deal_indices) >= min_cluster_size:
            # Split if too large
            if len(deal_indices) <= max_deals_per_cluster:
                clusters.append(deal_indices)
            else:
                # Sort by probability and take top deals
                sorted_indices = sorted(
                    deal_indices,
                    key=lambda idx: probabilities[idx, component_idx],
                    reverse=True
                )
                for i in range(0, len(sorted_indices), max_deals_per_cluster):
                    clusters.append(sorted_indices[i:i + max_deals_per_cluster])
    
    return clusters
