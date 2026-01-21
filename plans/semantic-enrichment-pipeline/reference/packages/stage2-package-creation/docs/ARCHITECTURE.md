# Package Creation Architecture

## Overview

This package implements intelligent package creation using a two-phase approach:

1. **Semantic Clustering**: Groups similar deals using embeddings
2. **LLM-Based Grouping**: Uses Google Gemini to propose intelligent package groupings

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Input: Enriched Deals                    │
│                                                             │
│  [Deal 1] [Deal 2] [Deal 3] ... [Deal N]                  │
│  (with taxonomy, safety, audience, commercial data)        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Phase 1: Semantic Embeddings                   │
│                                                             │
│  For each deal:                                             │
│    1. Create text representation                            │
│    2. Generate embedding (sentence-transformers)            │
│                                                             │
│  Output: Embedding vectors [N × 384]                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│        Phase 2: Clustering (K-Means or GMM)                │
│                                                             │
│  Option A: K-Means (hard clustering)                       │
│    1. Determine optimal cluster count                       │
│    2. Perform K-means clustering                            │
│                                                             │
│  Option B: GMM (soft clustering) - RECOMMENDED             │
│    1. Auto-select optimal components (BIC)                  │
│    2. Perform GMM clustering                                │
│    3. Optional: Use soft assignments for overlap            │
│                                                             │
│  3. Split large clusters                                    │
│  4. Filter tiny clusters                                    │
│                                                             │
│  Output: Clusters [[deal_idx...], [deal_idx...], ...]      │
│  (with potential overlaps if using soft assignments)        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│            Phase 3: LLM-Based Grouping                      │
│                                                             │
│  For each cluster:                                          │
│    1. Format deals as JSON                                  │
│    2. Call LLM with prompt                                  │
│    3. Parse package proposals                               │
│                                                             │
│  Output: Package Proposals                                  │
│  [                                                           │
│    {package_name, deal_ids, reasoning},                     │
│    {package_name, deal_ids, reasoning},                     │
│    ...                                                       │
│  ]                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Embeddings Module (`embeddings.py`)

**Purpose**: Create semantic embeddings for deals

**Key Functions**:
- `create_deal_text_representation()`: Converts deal to text
- `create_deal_embeddings()`: Generates embeddings using sentence-transformers

**Model**: `all-MiniLM-L6-v2` (384-dimensional embeddings)

**Text Representation Includes**:
- Deal name, SSP, format
- Taxonomy (Tier 1, 2, 3)
- Concepts
- Safety ratings
- Audience segments
- Commercial tiers
- Publishers

### 2. Clustering Module (`clustering.py`)

**Purpose**: Cluster deals by semantic similarity

**Key Functions**:
- `cluster_deals_semantically()`: Performs K-means or GMM clustering
- `cluster_deals_with_soft_assignments()`: GMM with probabilistic assignments for deal overlap

**Algorithms**:
- **K-Means**: Hard clustering (each deal belongs to one cluster)
- **GMM (Gaussian Mixture Model)**: Soft clustering (recommended)
  - Better for overlapping clusters
  - Handles non-spherical cluster shapes
  - Supports probabilistic assignments
  - Auto-selects optimal components using BIC

**Parameters**:
- `max_deals_per_cluster`: Target cluster size (default: 30)
- `min_cluster_size`: Minimum cluster size (default: 5)
- `method`: "kmeans" or "gmm" (default: "gmm")
- `use_soft_assignments`: Enable deal overlap via probabilities (default: False)

**Adaptive Clustering**:
- Calculates optimal number of clusters/components based on deal count
- GMM auto-selects components using Bayesian Information Criterion (BIC)
- Splits large clusters into smaller batches
- Filters out tiny clusters

**GMM Advantages**:
- **Soft Clustering**: Probabilistic assignments support deal overlap strategy
- **Non-Spherical Clusters**: Better handles elliptical/elongated shapes
- **Automatic Tuning**: BIC-based component selection reduces manual tuning
- **Overlap Support**: Soft assignments naturally allow deals in multiple clusters

### 3. Creator Module (`creator.py`)

**Purpose**: Main orchestration class

**Key Class**: `PackageCreator`

**Methods**:
- `create_packages()`: Main entry point
- `_propose_packages_for_cluster()`: LLM grouping for a cluster

**LLM Configuration**:
- Model: `gemini-2.5-flash`
- Temperature: `0.5` (creative groupings)
- Timeout: `60 seconds`
- Retries: `2`

## Data Flow

### Input Format

```python
deals = [
    {
        "deal_id": "3001",
        "deal_name": "Premium CTV Auto Inventory",
        "ssp_name": "BidSwitch",
        "format": "video",
        "taxonomy": {
            "tier1": "Automotive",
            "tier2": "Auto Parts & Accessories",
            "tier3": "Auto Repair"
        },
        "concepts": ["auto", "luxury", "premium"],
        "safety": {
            "garm_risk_rating": "Low",
            "family_safe": True
        },
        "audience": {
            "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
            "demographic_hint": "25-54, High Income"
        },
        "commercial": {
            "quality_tier": "Premium",
            "volume_tier": "High",
            "floor_price": 5.50
        },
        "publishers": ["Paramount", "Disney+"]
    },
    # ... more deals
]
```

### Output Format

```python
proposals = [
    {
        "package_name": "Premium Auto Intender CTV Package",
        "deal_ids": ["3001", "3002", "3003", "3004"],
        "reasoning": "Combines auto-focused CTV inventory with luxury audience overlap for premium auto campaigns. All deals are family-safe and premium quality tier."
    },
    # ... more proposals
]
```

## Scalability Considerations

### Clustering Strategy

- **Adaptive Clustering**: Automatically determines optimal cluster count
- **Batch Processing**: Splits large clusters for LLM processing
- **Parallel Processing**: Can process clusters in parallel (future enhancement)

### LLM Processing

- **Batch Size**: ~25 deals per cluster (optimal for LLM)
- **Rate Limiting**: 1-second delay between clusters
- **Timeout Handling**: 60-second timeout per LLM call
- **Retry Logic**: 2 retries on failure

### Memory Management

- **Embeddings**: Generated in batches (batch_size=32)
- **Clustering**: Uses efficient K-means implementation
- **LLM Calls**: Processed sequentially to manage API rate limits

## Configuration

### PackageCreator Parameters

```python
PackageCreator(
    llm_api_key="...",              # Required: Google Gemini API key
    prompt_template="...",           # Required: LLM prompt template
    model_name="gemini-2.5-flash",   # Optional: LLM model
    temperature=0.5,                 # Optional: LLM temperature
    embedding_model="all-MiniLM-L6-v2",  # Optional: Embedding model
    max_deals_per_cluster=25,        # Optional: Max deals per cluster
    min_cluster_size=5,              # Optional: Min cluster size
    clustering_method="gmm",        # Optional: "kmeans" or "gmm" (default: "gmm")
    use_soft_assignments=False      # Optional: Enable soft assignments for overlap
)
```

### Clustering Method Selection

**GMM (Recommended)**:
```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="gmm"  # Default
)
```

**K-Means**:
```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="kmeans"
)
```

**GMM with Soft Assignments** (for deal overlap):
```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    clustering_method="gmm",
    use_soft_assignments=True  # Enables probabilistic deal overlap
)
```

### Prompt Template

The prompt template uses `{enriched_deals}` placeholder:

```python
prompt = prompt_template.format(enriched_deals=json.dumps(deals, indent=2))
```

## Error Handling

### Embedding Errors

- **Model Loading**: Handles missing sentence-transformers
- **Encoding Errors**: Returns empty embeddings on failure

### Clustering Errors

- **Insufficient Deals**: Returns empty clusters if < min_cluster_size
- **K-Means Errors**: Handles clustering failures gracefully

### LLM Errors

- **JSON Parse Errors**: Logs error and skips cluster
- **API Errors**: Retries up to 2 times
- **Timeout Errors**: Logs timeout and continues

## Performance Characteristics

### Time Complexity

- **Embeddings**: O(N) where N = number of deals
- **Clustering**: O(N × K × I) where K = clusters, I = iterations
- **LLM Processing**: O(C) where C = number of clusters

### Typical Performance

- **100 deals**: ~30 seconds (embeddings + clustering + LLM)
- **1000 deals**: ~5 minutes
- **10000 deals**: ~45 minutes

### Bottlenecks

1. **Embedding Generation**: Can be parallelized
2. **LLM API Calls**: Rate-limited, sequential processing
3. **Clustering**: Efficient, not a bottleneck

## Future Enhancements

1. **Parallel Processing**: Process clusters in parallel
2. **Caching**: Cache embeddings for unchanged deals
3. **Incremental Clustering**: Add new deals to existing clusters
4. **Alternative Clustering**: Support DBSCAN, hierarchical clustering
5. **Multi-Model Support**: Support other LLM providers

## Dependencies

- `sentence-transformers`: Semantic embeddings
- `scikit-learn`: K-means clustering
- `langchain-google-genai`: LLM integration
- `numpy`: Array operations

## Testing Strategy

1. **Unit Tests**: Test individual functions
2. **Integration Tests**: Test full pipeline
3. **Mock LLM**: Use mock LLM responses for testing
4. **Performance Tests**: Measure scalability
