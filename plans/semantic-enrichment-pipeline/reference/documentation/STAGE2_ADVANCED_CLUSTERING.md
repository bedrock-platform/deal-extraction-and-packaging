# Stage 2: Advanced Clustering Strategies

## Overview

This document outlines advanced clustering strategies for Stage 2 (Package Creation) that go beyond basic semantic similarity to create more buyer-ready packages.

## Current Clustering Approach

The current implementation uses:
- **Semantic Embeddings**: `sentence-transformers` to convert deals to embeddings
- **Clustering Algorithms**: K-means or GMM (Gaussian Mixture Models)
- **LLM Grouping**: Google Gemini processes clusters to propose package groupings

**Limitation**: Clustering is purely semantic - deals with similar embeddings are grouped together, regardless of constraints or business rules.

## Proposed Enhancements

### 1. Constraint-Based Clustering

**The Problem:** Semantic similarity can group incompatible deals (e.g., "Political" deals with "Pharma" deals because both are "High Reg").

**The Solution:** Force clustering algorithm to separate deals based on business constraints.

**Implementation:**
```python
from sklearn.cluster import KMeans
import numpy as np

def constraint_based_clustering(
    embeddings: np.ndarray,
    deals: List[Dict],
    constraints: Dict[str, List[str]]
) -> np.ndarray:
    """
    Cluster deals with hard constraints.
    
    Args:
        embeddings: Deal embeddings (n_samples, n_features)
        deals: List of deal dictionaries
        constraints: Dict mapping constraint name to list of incompatible values
                     e.g., {"safety": ["High Risk", "High Reg"]}
    
    Returns:
        Cluster labels with constraints enforced
    """
    # Pre-cluster with constraints
    constraint_groups = {}
    for i, deal in enumerate(deals):
        # Extract constraint values
        safety = deal.get("safety", {}).get("garm_risk_rating", "")
        
        # Group by constraints
        constraint_key = f"safety_{safety}"
        if constraint_key not in constraint_groups:
            constraint_groups[constraint_key] = []
        constraint_groups[constraint_key].append(i)
    
    # Cluster within each constraint group
    labels = np.zeros(len(deals), dtype=int)
    cluster_id = 0
    
    for group_indices in constraint_groups.values():
        if len(group_indices) > 1:
            group_embeddings = embeddings[group_indices]
            kmeans = KMeans(n_clusters=min(3, len(group_indices)), random_state=42)
            group_labels = kmeans.fit_predict(group_embeddings)
            labels[group_indices] = group_labels + cluster_id
            cluster_id += max(group_labels) + 1
        else:
            labels[group_indices[0]] = cluster_id
            cluster_id += 1
    
    return labels
```

**Constraints to Enforce:**
- **Brand Safety**: Separate "High Risk" from "High Reg" (Pharma)
- **Content Type**: Separate "Political" from "Kids" content
- **Quality Tier**: Separate "Premium" from "RON" (optional, can overlap)
- **Format**: Separate "Video" from "Display" (optional, can overlap)

### 2. The "Anti-Package" Filter

**The Problem:** LLM might group deals that are semantically similar but should NOT be packaged together.

**The Solution:** Use LLM to identify deals that should NOT be packaged together despite semantic similarity.

**Implementation:**
```python
def anti_package_filter(
    cluster_deals: List[Dict],
    llm_client: Any
) -> List[Dict]:
    """
    Filter out deals that should NOT be in the same package.
    
    Example: "Kids" publisher deal appearing in "Political" package
    because of high volume.
    """
    prompt = f"""
    Review these deals that were clustered together:
    {json.dumps(cluster_deals, indent=2)}
    
    Identify any deals that should NOT be packaged together:
    1. Content incompatibility (e.g., Kids + Political)
    2. Safety incompatibility (e.g., High Risk + High Reg)
    3. Audience incompatibility (e.g., Family + Adult)
    
    Return JSON with:
    {{
        "incompatible_pairs": [
            {{"deal_id_1": "...", "deal_id_2": "...", "reason": "..."}}
        ],
        "recommended_split": true/false
    }}
    """
    
    response = llm_client.generate(prompt)
    result = json.loads(response)
    
    # Remove incompatible pairs from cluster
    if result.get("recommended_split"):
        # Split cluster or remove incompatible deals
        pass
    
    return filtered_deals
```

**Anti-Package Rules:**
- **Kids + Political**: Never package together
- **High Risk + High Reg**: Separate packages
- **Family-Safe + Adult**: Separate packages
- **Premium + RON**: Can overlap, but flag for review

### 3. Recursive Clustering

**The Opportunity:** Instead of single-pass clustering, use recursive clustering to refine packages.

**Process:**
1. **Initial Clustering**: Group deals by semantic similarity
2. **Constraint Enforcement**: Apply constraint-based clustering
3. **Anti-Package Filter**: Remove incompatible deals
4. **Recursive Refinement**: Re-cluster remaining deals with tighter constraints
5. **LLM Validation**: Final LLM pass to validate package coherence

**Example:**
```python
def recursive_clustering(
    deals: List[Dict],
    embeddings: np.ndarray,
    max_iterations: int = 3
) -> List[List[Dict]]:
    """
    Recursively refine clusters with increasing constraints.
    """
    current_deals = deals
    current_embeddings = embeddings
    
    for iteration in range(max_iterations):
        # Cluster with current constraints
        labels = constraint_based_clustering(
            current_embeddings,
            current_deals,
            constraints=get_constraints(iteration)
        )
        
        # Filter incompatible pairs
        clusters = group_by_labels(current_deals, labels)
        filtered_clusters = [
            anti_package_filter(cluster, llm_client)
            for cluster in clusters
        ]
        
        # If no changes, stop
        if len(filtered_clusters) == len(clusters):
            break
        
        # Prepare for next iteration
        current_deals = flatten(filtered_clusters)
        current_embeddings = recompute_embeddings(current_deals)
    
    return filtered_clusters
```

### 4. Diversity-Aware Clustering

**The Opportunity:** Ensure packages have diversity (different publishers, formats, geos) while maintaining semantic coherence.

**Implementation:**
```python
def diversity_aware_clustering(
    embeddings: np.ndarray,
    deals: List[Dict],
    diversity_targets: Dict[str, int]
) -> np.ndarray:
    """
    Cluster with diversity constraints.
    
    Args:
        diversity_targets: {"publishers": 3, "formats": 2, "geos": 2}
                          Minimum diversity per package
    """
    # Initial semantic clustering
    kmeans = KMeans(n_clusters=estimate_clusters(len(deals)), random_state=42)
    labels = kmeans.fit_predict(embeddings)
    
    # Check diversity per cluster
    for cluster_id in range(max(labels) + 1):
        cluster_deals = [d for i, d in enumerate(deals) if labels[i] == cluster_id]
        
        # Check publisher diversity
        publishers = set()
        for deal in cluster_deals:
            publishers.update(deal.get("publishers", []))
        
        if len(publishers) < diversity_targets.get("publishers", 1):
            # Split cluster or merge with diverse cluster
            pass
    
    return labels
```

### 5. Volume-Aware Clustering

**The Opportunity:** Balance package sizes based on volume (don't create tiny packages or massive packages).

**Implementation:**
```python
def volume_aware_clustering(
    embeddings: np.ndarray,
    deals: List[Dict],
    min_volume: int = 1_000_000,
    max_volume: int = 100_000_000
) -> np.ndarray:
    """
    Cluster with volume constraints.
    
    Ensures each package has:
    - Minimum volume (for viability)
    - Maximum volume (for manageability)
    """
    # Cluster semantically
    labels = semantic_clustering(embeddings)
    
    # Check volume per cluster
    for cluster_id in range(max(labels) + 1):
        cluster_deals = [d for i, d in enumerate(deals) if labels[i] == cluster_id]
        total_volume = sum(d.get("bid_requests", 0) for d in cluster_deals)
        
        if total_volume < min_volume:
            # Merge with similar small cluster
            pass
        elif total_volume > max_volume:
            # Split into smaller clusters
            pass
    
    return labels
```

## Integration with Current Pipeline

### Updated Stage 2 Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Semantic Embeddings                                 │
│ • Convert deals to embeddings                                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Constraint-Based Clustering                        │
│ • Enforce business rules (safety, content type)            │
│ • Separate incompatible deals                                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: Anti-Package Filter                                 │
│ • LLM identifies incompatible pairs                          │
│ • Remove deals that shouldn't be together                     │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Recursive Refinement                                │
│ • Re-cluster with tighter constraints                        │
│ • Iterate until stable                                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 5: Diversity & Volume Balancing                        │
│ • Ensure package diversity                                  │
│ • Balance package sizes                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 6: LLM Package Grouping                               │
│ • Final LLM pass for package proposals                      │
│ • Generate package names and descriptions                    │
└─────────────────────────────────────────────────────────────┘
```

## Benefits

1. **Buyer-Ready Packages**: Packages respect business constraints
2. **Safety Compliance**: Incompatible content never packaged together
3. **Diversity**: Packages have variety (publishers, formats, geos)
4. **Volume Balance**: Packages are viable and manageable
5. **Quality**: Recursive refinement improves package coherence

## Implementation Priority

1. **High Priority:**
   - Constraint-based clustering (safety, content type)
   - Anti-package filter (LLM-based)

2. **Medium Priority:**
   - Diversity-aware clustering
   - Volume-aware clustering

3. **Low Priority:**
   - Recursive clustering (can be added incrementally)

## References

- **Stage 1 Strategies**: [STAGE1_ENRICHMENT_STRATEGIES.md](STAGE1_ENRICHMENT_STRATEGIES.md)
- **Package Creation**: [../packages/stage2-package-creation/README.md](../packages/stage2-package-creation/README.md)
