# Package Creation: Clustering Settings and Package Count

## Overview

Stage 2 (Package Creation) uses semantic clustering to group similar deals, then processes each cluster through an LLM to create buyer-ready packages. The number of packages produced depends on clustering settings.

**Key Relationship**: More clusters → More packages (each cluster typically produces 1-5 packages)

---

## Current Default Settings

| Parameter | Default Value | Location |
|-----------|--------------|----------|
| `max_deals_per_cluster` | 25 | `src/package_creation/creator.py` |
| `min_cluster_size` | 5 | `src/package_creation/creator.py` |
| `probability_threshold` | 0.3 | `src/package_creation/clustering.py` (soft assignments) |
| `clustering_method` | `"gmm"` | `src/common/orchestrator.py` |
| `use_soft_assignments` | `True` | `src/common/orchestrator.py` |

**Current Results** (with 804 deals):
- **Clusters created**: 46
- **Packages produced**: ~174 (includes ~3 "Excluded Deals" packages)
- **Average packages per cluster**: ~3.8

---

## How Clustering Works

### The Process

1. **Semantic Embeddings**: Each deal is converted to a vector representation using sentence transformers
2. **Clustering**: Deals are grouped by similarity using Gaussian Mixture Model (GMM) clustering
3. **LLM Processing**: Each cluster is sent to the LLM to propose packages
4. **Package Output**: Each cluster typically produces 1-5 packages

### Why Package Count Matters

- **More packages** = More granular targeting options for buyers
- **Fewer packages** = Broader, simpler packages (may miss niche opportunities)
- **Balance**: Too many packages can be overwhelming; too few may miss valuable segments

### Understanding "Excluded Deals" Packages

Stage 2 creates "Excluded Deals" packages to document deals that couldn't be packaged. These packages have empty `deal_ids` arrays and are automatically skipped in Stage 3. They're included in the package count but don't affect the actual deal packages available to buyers.

---

## Adjusting Settings to Get More Packages

### 1. Reduce `max_deals_per_cluster` ⭐ **Most Effective**

**What it does**: Limits the maximum number of deals per cluster before splitting.

**Current**: 25 deals per cluster  
**Recommended**: 15-18 deals per cluster

**How it works**:
- Lower value = More clusters created (deals split into smaller groups)
- More clusters = More LLM calls = More packages produced
- Formula: `clusters ≈ total_deals ÷ max_deals_per_cluster`

**Impact**:
- More clusters created (46 → ~50-60)
- More packages produced (174 → ~200-250)
- Still manageable for LLM processing

**Example Calculation**:
```
804 deals ÷ 15 deals/cluster = ~54 clusters
54 clusters × ~3.8 packages/cluster = ~205 packages
```

**How to change**: Edit `src/common/orchestrator.py` line ~412:

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
    clustering_method="gmm",
    use_soft_assignments=True,
    max_deals_per_cluster=15,  # Changed from default 25
    min_cluster_size=5
)
```

**Trade-offs**:
- ✅ More granular packages
- ✅ Better niche targeting
- ⚠️ More LLM API calls (more cost/time)
- ⚠️ Smaller clusters may have less statistical significance

---

### 2. Reduce `min_cluster_size`

**What it does**: Minimum number of deals required to form a cluster.

**Current**: 5 deals minimum  
**Recommended**: 3 deals minimum (if you want more granularity)

**How it works**:
- Lower value = Allows smaller clusters to be created
- More small clusters = More total clusters = More packages
- Deals that would be filtered out can now form clusters

**Impact**:
- Allows smaller clusters to be created
- More clusters overall
- More packages

**How to change**: Edit `src/common/orchestrator.py`:

```python
creator = PackageCreator(
    # ... other params ...
    min_cluster_size=3,  # Changed from default 5
)
```

**Trade-offs**:
- ✅ More granular packages
- ✅ Captures smaller niche segments
- ⚠️ Smaller clusters may be less meaningful
- ⚠️ May create packages with limited inventory

---

### 3. Lower `probability_threshold` (Soft Assignments Only)

**What it does**: Minimum probability for a deal to be included in a cluster (when using soft assignments).

**Current**: 0.3 (30% probability)  
**Recommended**: 0.2-0.25 (20-25% probability)

**How it works**:
- Lower threshold = More deals included per component
- More deals per component = Potentially more clusters
- More overlap between clusters (deals can appear in multiple packages)

**Impact**:
- More deals included per component
- Potentially more clusters
- More overlap between clusters

**How to change**: Edit `src/package_creation/clustering.py` line ~153:

```python
def cluster_deals_with_soft_assignments(
    deals: List[Dict[str, Any]],
    embeddings: np.ndarray,
    max_deals_per_cluster: int = 30,
    min_cluster_size: int = 5,
    probability_threshold: float = 0.2  # Changed from default 0.3
) -> List[List[int]]:
```

Then update the call in `src/package_creation/creator.py` to pass this parameter.

**Trade-offs**:
- ✅ More deals per cluster
- ✅ Better deal overlap support
- ⚠️ More overlap between clusters (deals appear in multiple packages)
- ⚠️ Clusters may be less distinct

---

### 4. Force Higher GMM Components (Advanced)

**What it does**: Override auto-calculation of GMM components.

**Current**: Auto-calculated as `len(deals) // max_deals_per_cluster`  
**Example**: 804 deals ÷ 25 = ~32 components

**Recommended**: Manually set to 50-60 components

**How it works**:
- More components = More potential clusters
- GMM creates more mixture components = More ways to group deals
- More packages

**Impact**:
- More components → More potential clusters
- More packages

**How to change**: Requires modifying `src/package_creation/clustering.py` to accept and use `n_components` parameter directly.

**Trade-offs**:
- ✅ More control over cluster count
- ⚠️ Requires understanding of GMM internals
- ⚠️ May create too many small clusters

---

## Adjusting Settings to Get Fewer Packages

### 1. Increase `max_deals_per_cluster`

**What it does**: Allows larger clusters before splitting.

**How it works**:
- Higher value = Fewer clusters created (deals grouped into larger clusters)
- Fewer clusters = Fewer LLM calls = Fewer packages

**Example**: Change from 25 to 35-40
- Clusters: 46 → ~20-25
- Packages: 174 → ~80-100

**Trade-offs**:
- ✅ Fewer API calls (lower cost/time)
- ✅ Broader packages
- ⚠️ Less granular targeting

---

### 2. Increase `min_cluster_size`

**What it does**: Requires more deals to form a cluster.

**How it works**:
- Higher value = Filters out smaller clusters
- Fewer clusters = Fewer packages

**Example**: Change from 5 to 8-10
- Filters out clusters with < 8 deals
- Reduces total cluster count

**Trade-offs**:
- ✅ More meaningful clusters
- ✅ Packages with better inventory scale
- ⚠️ May miss niche segments

---

### 3. Raise `probability_threshold` (Soft Assignments Only)

**What it does**: Requires higher probability for deal inclusion.

**How it works**:
- Higher threshold = Fewer deals per component
- More distinct clusters (less overlap)
- Potentially fewer total clusters

**Example**: Change from 0.3 to 0.4-0.5

**Trade-offs**:
- ✅ More distinct clusters
- ✅ Less overlap between packages
- ⚠️ May exclude deals that could be valuable

---

## Recommended Approaches

### For Most Users: Start with `max_deals_per_cluster`

**Quick Win**: Reduce `max_deals_per_cluster` from 25 to 15-18:

```python
# In src/common/orchestrator.py, around line 412
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
    clustering_method="gmm",
    use_soft_assignments=True,
    max_deals_per_cluster=18,  # Reduced from 25
    min_cluster_size=5
)
```

**Expected Results**:
- Clusters: 46 → ~45-50
- Packages: 174 → ~200-250
- Processing time: Slightly longer (more clusters to process)

---

### For Maximum Packages: Combine Settings

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
    clustering_method="gmm",
    use_soft_assignments=True,
    max_deals_per_cluster=15,  # Reduced
    min_cluster_size=3          # Reduced
)
```

**Expected Results**:
- Clusters: 46 → ~55-65
- Packages: 174 → ~250-300
- Processing time: Significantly longer

---

### For Fewer Packages: Increase Settings

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
    clustering_method="gmm",
    use_soft_assignments=True,
    max_deals_per_cluster=35,  # Increased
    min_cluster_size=8          # Increased
)
```

**Expected Results**:
- Clusters: 46 → ~20-25
- Packages: 174 → ~80-100
- Processing time: Faster (fewer clusters to process)

---

## Understanding Your Results

### Check Cluster Count

After Stage 2 completes, check the logs for:
```
Created 46 clusters
```

### Check Package Count

After Stage 2 completes:
- Check `output/packages_{timestamp}.json` - count the array length
- Check Google Sheets "Packages" worksheet - count rows (minus header)

### Typical Ratios

- **Deals → Clusters**: ~15-20 deals per cluster (with default settings)
- **Clusters → Packages**: ~3-4 packages per cluster (varies by LLM)

---

## Cost and Time Considerations

### API Costs

- Each cluster requires 1 LLM API call
- More clusters = More API calls = Higher cost
- Example: 46 clusters → 46 API calls; 60 clusters → 60 API calls

### Processing Time

- Each LLM call takes ~15-30 seconds
- More clusters = Longer processing time
- Example: 46 clusters × 20s = ~15 minutes; 60 clusters × 20s = ~20 minutes

### Incremental Export

✅ **Good news**: Packages are exported incrementally, so you can:
- Monitor progress in real-time (Google Sheets updates row-by-row)
- Resume if interrupted (checkpoint system tracks progress)
- See packages as they're created (no need to wait for completion)

---

## Troubleshooting

### "I'm not getting enough packages"

1. **Check your deal count**: More deals = More potential packages
2. **Reduce `max_deals_per_cluster`**: Most effective way to increase package count
3. **Reduce `min_cluster_size`**: Allows smaller clusters
4. **Check logs**: Verify clusters are being created (look for "Created X clusters")

### "I'm getting too many packages"

1. **Increase `max_deals_per_cluster`**: Creates fewer, larger clusters
2. **Increase `min_cluster_size`**: Filters out small clusters
3. **Check for duplicates**: Some packages may be similar (this is normal with overlap)

### "Processing is taking too long"

1. **Reduce number of clusters**: Increase `max_deals_per_cluster`
2. **Use checkpoint/resume**: Process in batches if needed
3. **Check API rate limits**: May need to add delays between clusters

---

## Example Scenarios

### Scenario 1: Small Dataset (200 deals)

**Default settings**:
- Clusters: ~8-10
- Packages: ~30-40

**To get more packages**:
- Reduce `max_deals_per_cluster` to 12-15
- Reduce `min_cluster_size` to 3
- Expected: ~15-20 clusters → ~50-70 packages

**To get fewer packages**:
- Increase `max_deals_per_cluster` to 30-35
- Increase `min_cluster_size` to 8
- Expected: ~5-7 clusters → ~15-25 packages

---

### Scenario 2: Large Dataset (2000 deals)

**Default settings**:
- Clusters: ~80-100
- Packages: ~300-400

**To get more packages**:
- Reduce `max_deals_per_cluster` to 15-18
- Expected: ~110-130 clusters → ~400-500 packages

**To get fewer packages**:
- Increase `max_deals_per_cluster` to 40-50
- Expected: ~40-50 clusters → ~150-200 packages

**Note**: With large datasets, consider processing in batches or using more aggressive clustering settings.

---

### Scenario 3: Need Maximum Granularity

**Settings**:
- `max_deals_per_cluster`: 10-12
- `min_cluster_size`: 3
- `probability_threshold`: 0.2

**Expected**:
- Many small, highly targeted clusters
- Maximum package count
- Longer processing time
- Higher API costs

---

### Scenario 4: Need Broad Packages

**Settings**:
- `max_deals_per_cluster`: 40-50
- `min_cluster_size`: 10
- `probability_threshold`: 0.4

**Expected**:
- Fewer, larger clusters
- Broader packages
- Faster processing
- Lower API costs

---

## Code Locations

### Main Configuration

**File**: `src/common/orchestrator.py`  
**Line**: ~412  
**Class**: `DealExtractor.create_packages()`

```python
creator = PackageCreator(
    llm_api_key=api_key,
    prompt_template=prompt_template,
    model_name=os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash"),
    clustering_method="gmm",
    use_soft_assignments=True,
    max_deals_per_cluster=25,  # ← Change this
    min_cluster_size=5          # ← Change this
)
```

### Clustering Functions

**File**: `src/package_creation/clustering.py`
- `cluster_deals_semantically()`: Standard clustering
- `cluster_deals_with_soft_assignments()`: Soft assignments with probability threshold

### Package Creator

**File**: `src/package_creation/creator.py`  
**Class**: `PackageCreator`  
**Default parameters**: Lines 44-45

---

## Best Practices

1. **Start with defaults**: Test with default settings first
2. **Adjust incrementally**: Change one parameter at a time to understand impact
3. **Monitor results**: Check package quality, not just quantity
4. **Consider use case**: More packages = Better for niche targeting; Fewer packages = Better for broad campaigns
5. **Use checkpoints**: With incremental export, you can test settings and resume if needed

---

## Summary

**To get more packages**:
1. ⭐ **Reduce `max_deals_per_cluster`** (15-18 instead of 25) - Most effective
2. Reduce `min_cluster_size` (3 instead of 5) - For more granularity
3. Lower `probability_threshold` (0.2 instead of 0.3) - For soft assignments

**To get fewer packages**:
1. ⭐ **Increase `max_deals_per_cluster`** (35-40 instead of 25) - Most effective
2. Increase `min_cluster_size` (8-10 instead of 5) - Filters small clusters
3. Raise `probability_threshold` (0.4-0.5 instead of 0.3) - For soft assignments

**Remember**: More packages = More API calls = More cost/time, but better granularity for buyers. Fewer packages = Faster processing and lower costs, but less granular targeting.
