# Package Creation: Clustering Settings and Package Count

## Overview

Stage 2 (Package Creation) uses semantic clustering to group similar deals, then processes each cluster through an LLM to create buyer-ready packages. The number of packages produced depends on clustering settings.

**Key Relationship**: More clusters → More packages (each cluster typically produces 1-5 packages)

---

## ⚠️ Known Issues

### Missing `deal_ids` Column in Stage 3 Output

**Issue**: The `deal_ids` column from Stage 2 packages is not being included in Stage 3 enriched package output.

**Current State**: The `deal_ids` field exists in Stage 2 packages but is not preserved when packages are enriched in Stage 3.

**Impact**:
- Stage 2 packages include `deal_ids` (list of deal IDs in the package)
- Stage 3 enriched packages are missing this field

**Action Needed**: Ensure `deal_ids` from Stage 2 packages is preserved and included in Stage 3 enriched package output (both JSON/JSONL files and Google Sheets).

**Workaround**: 
- Export Stage 2 packages to get `deal_ids`
- Manually match packages by `package_name` or other identifier
- Add `deal_ids` column to Stage 3 enriched packages spreadsheet

---

### "Excluded Deals" Packages in Stage 2

**Design Decision**: Stage 2 creates "Excluded Deals" packages to document deals that couldn't be packaged.

**What They Are**:
- Packages with **empty `deal_ids` arrays** (no actual deals)
- Created by the LLM during package creation to document excluded deals
- Contain metadata about why deals were excluded (safety mismatches, quality conflicts, insufficient scale, etc.)

**Why They Exist**:
- **Transparency**: Buyers can see which deals were excluded and why
- **Audit Trail**: Documents deals that didn't meet package requirements (minimum 3 deals, safety alignment, quality consistency)
- **Accountability**: Shows the curation process is thorough and documented

**Examples**:
- "Excluded Deals (Safety & Coherence Mismatch)" - deals with safety conflicts
- "Excluded Deals" - deals that didn't meet minimum package requirements
- "Excluded Deals - Geographic & Volume Outliers" - deals that were geographic/volume outliers

**Stage 3 Behavior**:
- These packages are **automatically skipped** during Stage 3 enrichment
- Reason: They have no deals to enrich (empty `deal_ids` array)
- Location: Skipped in `src/integration/stage3_adapter.py` (packages with no matched deals are filtered out)

**Impact**:
- Stage 2 output: Includes all packages (including "Excluded Deals" packages)
- Stage 3 output: Only includes packages with actual deals (excludes "Excluded Deals" packages)
- Result: Stage 3 package count will be lower than Stage 2 if excluded deals packages exist

**This is Expected Behavior**: The system is designed to:
1. Document excluded deals in Stage 2 for transparency
2. Skip them in Stage 3 since there's nothing to enrich

**If You Need Excluded Deals in Stage 3**:
- Use the backfill script: `scripts/backfill_excluded_deals.py`
- This exports excluded deals packages with minimal enrichment (no LLM call needed)

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
- **Note**: "Excluded Deals" packages are included in Stage 2 but skipped in Stage 3

## How Clustering Affects Package Count

### The Process

1. **Semantic Embeddings**: Each deal is converted to a vector representation
2. **Clustering**: Deals are grouped by similarity (GMM clustering)
3. **LLM Processing**: Each cluster is sent to the LLM to propose packages
4. **Package Output**: Each cluster typically produces 1-5 packages

### Why Package Count Matters

- **More packages** = More granular targeting options for buyers
- **Fewer packages** = Broader, simpler packages (may miss niche opportunities)
- **Balance**: Too many packages can be overwhelming; too few may miss valuable segments

## Adjusting Settings to Get More Packages

### 1. Reduce `max_deals_per_cluster` ⭐ **Most Effective**

**What it does**: Limits the maximum number of deals per cluster before splitting.

**Current**: 25 deals per cluster  
**Recommended**: 15-18 deals per cluster

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

**Impact**:
- More components → More potential clusters
- More packages

**How to change**: Requires modifying `src/package_creation/clustering.py` to accept and use `n_components` parameter directly.

**Trade-offs**:
- ✅ More control over cluster count
- ⚠️ Requires understanding of GMM internals
- ⚠️ May create too many small clusters

---

## Recommended Approach

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

### Scenario 2: Large Dataset (2000 deals)

**Default settings**:
- Clusters: ~80-100
- Packages: ~300-400

**To get more packages**:
- Reduce `max_deals_per_cluster` to 15-18
- Expected: ~110-130 clusters → ~400-500 packages

**Note**: With large datasets, consider processing in batches or using more aggressive clustering settings.

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

## Ensuring Data Integrity: All Packages in Both Sheets

**Important Note**: If Stage 3 has fewer packages than Stage 2, this may be **expected** if "Excluded Deals" packages exist. These packages are intentionally skipped in Stage 3 (see "Excluded Deals Packages in Stage 2" section above).

After running Stages 2-3, you need to verify that all packages from Stage 2 appear in both the "Packages" and "Packages Enriched" worksheets.

### Understanding the Two Worksheets

1. **"Packages" Worksheet** (Stage 2 output):
   - Contains raw packages created from clusters
   - Includes: `package_name`, `deal_ids`, `reasoning`
   - Created incrementally during Stage 2

2. **"Packages Enriched" Worksheet** (Stage 3 output):
   - Contains enriched packages with aggregated metadata
   - Includes: taxonomy, safety, audience, commercial data, recommendations
   - Created incrementally during Stage 3
   - **May have fewer packages than Stage 2** if "Excluded Deals" packages exist (these are skipped)

### Verification Steps

#### 1. Count Packages in Each Worksheet

**In Google Sheets**:
- "Packages" worksheet: Count rows (excluding header) = Stage 2 package count
- "Packages Enriched" worksheet: Count rows (excluding header) = Stage 3 enriched package count

**Expected**: 
- If no "Excluded Deals" packages: Both counts should match (e.g., 174 packages in both)
- If "Excluded Deals" packages exist: Stage 3 count will be lower (e.g., Stage 2: 177, Stage 3: 174)

#### 2. Check for Missing Packages

**Method 1: Compare Package Names**
```python
# Quick Python script to compare
import json

# Load Stage 2 packages
with open('output/packages_TIMESTAMP.json', 'r') as f:
    stage2 = json.load(f)

# Load Stage 3 enriched packages
with open('output/packages_enriched_TIMESTAMP.json', 'r') as f:
    stage3 = json.load(f)

stage2_names = {p.get('package_name') for p in stage2}
stage3_names = {p.get('package_name') for p in stage3}

missing_in_stage3 = stage2_names - stage3_names
if missing_in_stage3:
    print(f"Missing {len(missing_in_stage3)} packages in Stage 3:")
    for name in missing_in_stage3:
        print(f"  - {name}")
else:
    print("✅ All packages present in Stage 3")
```

**Method 2: Check Google Sheets Directly**
- Sort both worksheets by `package_name`
- Compare row-by-row
- Look for gaps or missing entries

#### 3. Common Causes of Mismatches

**Stage 3 Interruption**:
- If Stage 3 was interrupted (e.g., KeyboardInterrupt), some packages may not be enriched
- **Solution**: Resume Stage 3 - it will skip already-enriched packages and continue

**LLM Failures**:
- If a package enrichment fails (LLM timeout/error), that package won't appear in Stage 3
- **Solution**: Check logs for errors, then resume Stage 3

**Checkpoint Issues**:
- If checkpoint is corrupted or missing, Stage 3 may skip packages
- **Solution**: Delete checkpoint and re-run Stage 3 (or manually fix checkpoint)

### How to Fix Missing Packages

**Note**: If you see fewer packages in Stage 3 than Stage 2, check if the difference is due to "Excluded Deals" packages (see section above). These are **expected** to be missing from Stage 3.

#### Option 1: Resume Stage 3 (Recommended)

If Stage 3 was interrupted, simply re-run the same command:

```bash
python -m src.deal_extractor --stage-3 output/packages_TIMESTAMP.json output/deals_enriched_TIMESTAMP.jsonl
```

The checkpoint system will:
- Load existing checkpoint
- Skip packages 1-142 (already enriched)
- Continue from package 143 onwards
- Export missing packages incrementally

#### Option 2: Re-run Stage 3 from Scratch

If you want to re-enrich all packages:

```bash
python -m src.deal_extractor --stage-3 output/packages_TIMESTAMP.json output/deals_enriched_TIMESTAMP.jsonl --no-resume
```

**Warning**: This will re-process all packages (costs more API calls and time)

#### Option 3: Manual Verification Script

Create a script to identify and re-enrich missing packages:

```python
import json
from pathlib import Path

# Load packages
stage2_path = Path('output/packages_TIMESTAMP.json')
stage3_path = Path('output/packages_enriched_TIMESTAMP.json')

with open(stage2_path, 'r') as f:
    stage2_packages = json.load(f)

with open(stage3_path, 'r') as f:
    stage3_packages = json.load(f)

# Find missing
stage2_names = {p.get('package_name'): p for p in stage2_packages}
stage3_names = {p.get('package_name') for p in stage3_packages}

missing = [p for name, p in stage2_names.items() if name not in stage3_names]

if missing:
    print(f"Found {len(missing)} missing packages")
    # You can then manually enrich these or re-run Stage 3
else:
    print("✅ All packages accounted for")
```

### Ensuring Complete Data Export

#### Check Incremental Export Status

**Stage 2 Checkpoint**:
- File: `output/package_creation_checkpoint_TIMESTAMP.json`
- Shows which clusters were processed
- If all clusters processed → All packages created

**Stage 3 Checkpoint**:
- File: `output/package_enrichment_checkpoint_TIMESTAMP.json`
- Shows which packages were enriched
- Compare count with Stage 2 package count

#### Verify File Counts Match Sheet Counts

```bash
# Count packages in JSON file
python3 -c "import json; data = json.load(open('output/packages_TIMESTAMP.json')); print(f'Stage 2: {len(data)} packages')"

# Count packages in JSONL file (should match)
wc -l output/packages_TIMESTAMP.jsonl

# Count enriched packages
python3 -c "import json; data = json.load(open('output/packages_enriched_TIMESTAMP.json')); print(f'Stage 3: {len(data)} packages')"
```

**Expected**: All counts should match

### Best Practices for Data Integrity

1. **Always check counts after completion**:
   - Stage 2 packages count = Stage 3 enriched packages count
   - File counts = Google Sheets row counts

2. **Use incremental export**:
   - Packages appear in sheets as they're created
   - Easy to monitor progress
   - Can resume if interrupted

3. **Keep checkpoints**:
   - Don't delete checkpoint files until verification complete
   - Checkpoints enable resume capability

4. **Verify before proceeding**:
   - Check package counts match
   - Spot-check a few package names
   - Verify `deal_ids` are present (once fixed)

5. **Document discrepancies**:
   - If counts don't match, note which packages are missing
   - Check logs for errors
   - Re-run Stage 3 if needed

---

## Summary

**To get more packages**:
1. ⭐ **Reduce `max_deals_per_cluster`** (15-18 instead of 25) - Most effective
2. Reduce `min_cluster_size` (3 instead of 5) - For more granularity
3. Lower `probability_threshold` (0.2 instead of 0.3) - For soft assignments

**Remember**: More packages = More API calls = More cost/time, but better granularity for buyers.
