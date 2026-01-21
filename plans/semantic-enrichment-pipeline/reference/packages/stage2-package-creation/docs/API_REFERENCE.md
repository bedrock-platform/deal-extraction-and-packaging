# Package Creation API Reference

Complete API reference for the Package Creation Python package.

## PackageCreator

### Class: `PackageCreator`

Main class for creating intelligent packages from enriched deals.

#### Constructor

```python
PackageCreator(
    llm_api_key: str,
    prompt_template: str,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.5,
    embedding_model: str = "all-MiniLM-L6-v2",
    max_deals_per_cluster: int = 25,
    min_cluster_size: int = 5,
    clustering_method: str = "gmm",
    use_soft_assignments: bool = False
)
```

**Parameters:**

- `llm_api_key` (str, required): Google Gemini API key
- `prompt_template` (str, required): LLM prompt template string (uses `{enriched_deals}` placeholder)
- `model_name` (str, optional): LLM model name (default: "gemini-2.5-flash")
- `temperature` (float, optional): LLM temperature (default: 0.5)
- `embedding_model` (str, optional): Sentence transformer model name (default: "all-MiniLM-L6-v2")
- `max_deals_per_cluster` (int, optional): Maximum deals per cluster (default: 25)
- `min_cluster_size` (int, optional): Minimum cluster size (default: 5)
- `clustering_method` (str, optional): Clustering method - "kmeans" or "gmm" (default: "gmm")
- `use_soft_assignments` (bool, optional): Enable GMM soft assignments for deal overlap (default: False)

**Example:**

```python
from package_creation import PackageCreator

creator = PackageCreator(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)
```

#### Method: `create_packages(deals, progress_callback=None) -> List[Dict]`

Create packages from enriched deals.

**Parameters:**

- `deals` (List[Dict]): List of enriched deal dictionaries
- `progress_callback` (Callable, optional): Optional callback function for progress updates

**Returns:** List of package proposals

**Example:**

```python
proposals = creator.create_packages(deals, progress_callback=print)

for proposal in proposals:
    print(f"Package: {proposal['package_name']}")
    print(f"Deals: {proposal['deal_ids']}")
    print(f"Reasoning: {proposal['reasoning']}")
```

**Package Proposal Format:**

```python
{
    "package_name": "Premium Auto Intender CTV Package",
    "deal_ids": ["3001", "3002", "3003"],
    "reasoning": "Combines auto-focused CTV inventory..."
}
```

## Embedding Functions

### `create_deal_text_representation(deal: Dict) -> str`

Create a text representation of a deal for embedding.

**Parameters:**

- `deal` (Dict): Deal dictionary with enrichment data

**Returns:** Text representation string

**Example:**

```python
from package_creation import create_deal_text_representation

text = create_deal_text_representation(deal)
# Returns: "Deal: Premium CTV Auto | Category: Automotive | ..."
```

### `create_deal_embeddings(deals, model_name, batch_size) -> Tuple[np.ndarray, SentenceTransformer]`

Create semantic embeddings for all deals.

**Parameters:**

- `deals` (List[Dict]): List of deal dictionaries
- `model_name` (str): Sentence transformer model name (default: "all-MiniLM-L6-v2")
- `batch_size` (int): Batch size for encoding (default: 32)

**Returns:** Tuple of (embeddings array, embedding model)

**Example:**

```python
from package_creation import create_deal_embeddings

embeddings, model = create_deal_embeddings(deals)
# embeddings: numpy array [N × 384]
# model: SentenceTransformer instance
```

## Clustering Functions

### `cluster_deals_semantically(deals, embeddings, max_deals_per_cluster, min_cluster_size, method, n_components, covariance_type) -> List[List[int]]`

Cluster deals using semantic similarity (K-means or GMM).

**Parameters:**

- `deals` (List[Dict]): List of deal dictionaries
- `embeddings` (np.ndarray): Semantic embeddings array
- `max_deals_per_cluster` (int): Maximum deals per cluster (default: 30)
- `min_cluster_size` (int): Minimum cluster size (default: 5)
- `method` (str): Clustering method - "kmeans" or "gmm" (default: "gmm")
- `n_components` (int, optional): Number of GMM components (None = auto-select using BIC)
- `covariance_type` (str): GMM covariance type - "full", "tied", "diag", "spherical" (default: "full")

**Returns:** List of clusters, where each cluster is a list of deal indices

**Example:**

```python
from package_creation import cluster_deals_semantically

# GMM clustering (recommended)
clusters = cluster_deals_semantically(
    deals,
    embeddings,
    max_deals_per_cluster=25,
    min_cluster_size=5,
    method="gmm"
)

# K-means clustering
clusters = cluster_deals_semantically(
    deals,
    embeddings,
    method="kmeans"
)
```

### `cluster_deals_with_soft_assignments(deals, embeddings, max_deals_per_cluster, min_cluster_size, probability_threshold) -> List[List[int]]`

Cluster deals using GMM with soft assignments for deal overlap strategy.

**Parameters:**

- `deals` (List[Dict]): List of deal dictionaries
- `embeddings` (np.ndarray): Semantic embeddings array
- `max_deals_per_cluster` (int): Maximum deals per cluster (default: 30)
- `min_cluster_size` (int): Minimum cluster size (default: 5)
- `probability_threshold` (float): Minimum probability for deal inclusion (default: 0.3)

**Returns:** List of clusters with potential overlaps (deals can appear in multiple clusters)

**Example:**

```python
from package_creation import cluster_deals_with_soft_assignments

# GMM with soft assignments (for deal overlap)
clusters = cluster_deals_with_soft_assignments(
    deals,
    embeddings,
    probability_threshold=0.3  # Deals with >= 30% probability included
)
```

## Deal Format

### Required Fields

```python
{
    "deal_id": str,              # Required: Unique deal identifier
    "deal_name": str,            # Required: Deal display name
    "ssp_name": str,             # Optional: SSP name
    "format": str,               # Optional: Creative format
    "taxonomy": {                # Optional: Taxonomy data
        "tier1": str,
        "tier2": str,
        "tier3": str
    },
    "concepts": List[str],       # Optional: Dominant concepts
    "safety": {                  # Optional: Safety data
        "garm_risk_rating": str,
        "family_safe": bool
    },
    "audience": {                # Optional: Audience data
        "inferred_audience": List[str],
        "demographic_hint": str
    },
    "commercial": {              # Optional: Commercial data
        "quality_tier": str,
        "volume_tier": str,
        "floor_price": float
    },
    "publishers": List[str]      # Optional: Publisher names
}
```

## Error Handling

### Common Exceptions

**ImportError**: Missing dependencies
```python
try:
    from package_creation import PackageCreator
except ImportError as e:
    print(f"Missing dependency: {e}")
```

**ValueError**: Missing API key
```python
try:
    creator = PackageCreator(llm_api_key=None, prompt_template="...")
except ValueError as e:
    print(f"Configuration error: {e}")
```

**JSONDecodeError**: LLM response parsing
```python
try:
    proposals = creator.create_packages(deals)
except json.JSONDecodeError as e:
    print(f"Failed to parse LLM response: {e}")
```

## Progress Callback

Optional callback function for progress updates:

```python
def progress_callback(message: str):
    print(f"[Progress] {message}")

proposals = creator.create_packages(deals, progress_callback=progress_callback)
```

**Example Output:**
```
[Progress] Creating embeddings for 100 deals...
[Progress] Created 100 embeddings
[Progress] Clustering deals by semantic similarity...
[Progress] Created 4 clusters
[Progress] Processing 4 clusters through LLM...
[Progress] [Cluster 1] Analyzing 25 deals...
[Progress] [Cluster 1] LLM response received (2.3s)
[Progress] [Cluster 1] Proposed 3 packages
...
[Progress] Total packages proposed: 12
```

## Best Practices

1. **Enrich Deals First**: Ensure deals have enrichment data before creating packages
2. **Minimum Deal Count**: Have at least 10+ enriched deals for meaningful packages
3. **Progress Monitoring**: Use progress callback to monitor long-running operations
4. **Error Handling**: Wrap `create_packages()` in try/except for error handling
5. **Validation**: Validate package proposals before using them

## Performance Tips

1. **Batch Size**: Adjust `max_deals_per_cluster` based on your LLM rate limits
2. **Embedding Model**: Use smaller models for faster processing
3. **Parallel Processing**: Process clusters in parallel (future enhancement)
4. **Caching**: Cache embeddings for unchanged deals
