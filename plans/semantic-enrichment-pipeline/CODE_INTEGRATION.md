# Code Integration Guide

This document provides specific guidance on integrating the existing code packages (`package_creation_package` and `package_enrichment_package`) into the main pipeline.

## Package Locations

All code packages are located in `reference/packages/`:
- **Stage 2:** `reference/packages/stage2-package-creation/`
- **Stage 3:** `reference/packages/stage3-package-enrichment/`

## Stage 2: Package Creation Integration

### Key Classes and Functions

**Main Entry Point:**
- **File:** `reference/packages/stage2-package-creation/package_creation/creator.py`
- **Class:** `PackageCreator`
- **Key Method:** `create_packages(deals: List[Dict]) -> List[Dict]`

**Supporting Modules:**
- **`embeddings.py`:** `create_deal_embeddings()` - Converts deals to embeddings
- **`clustering.py`:** 
  - `cluster_deals_semantically()` - K-means clustering
  - `cluster_deals_with_soft_assignments()` - GMM clustering (recommended)

### Integration Steps (DEAL-302)

1. **Import PackageCreator:**
   ```python
   # Option 1: Direct import (if packages are in Python path)
   from package_creation.creator import PackageCreator
   
   # Option 2: Relative import from reference directory
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "reference" / "packages" / "stage2-package-creation"))
   from package_creation.creator import PackageCreator
   ```

2. **Initialize with LLM API key:**
   ```python
   creator = PackageCreator(
       llm_api_key=os.getenv("GEMINI_API_KEY"),
       prompt_template=prompt_template_path,
       clustering_method="gmm",  # Recommended
       use_soft_assignments=True  # For deal overlap
   )
   ```

3. **Convert Stage 1 enriched deals to Stage 2 format:**
   - Stage 1 outputs `EnrichedDeal` objects
   - Stage 2 expects list of dictionaries with enrichment fields
   - Create adapter function to convert format

4. **Execute package creation:**
   ```python
   packages = creator.create_packages(enriched_deals_dicts)
   ```

### Expected Input Format (Stage 2)

```python
[
    {
        "deal_id": "3001",
        "deal_name": "Premium CTV Auto Inventory",
        "taxonomy": {"tier1": "Automotive", ...},
        "safety": {"garm_risk_rating": "Low", ...},
        "audience": {"inferred_audience": [...], ...},
        "commercial": {"quality_tier": "Premium", ...},
        # ... other enrichment fields
    },
    # ... more deals
]
```

### Expected Output Format (Stage 2)

```python
[
    {
        "package_name": "Premium Auto Intender CTV Package",
        "deal_ids": [3001, 3002, 3003, 3004],
        "reasoning": "...",
        "metadata": {...}
    },
    # ... more packages
]
```

## Stage 3: Package Enrichment Integration

### Key Classes and Functions

**Main Entry Point:**
- **File:** `reference/packages/stage3-package-enrichment/package_enrichment/enricher.py`
- **Class:** `PackageEnricher`
- **Key Method:** `enrich_package(package: Dict, deals: List[Dict]) -> Dict`

**Supporting Modules:**
- **`aggregation.py`:**
  - `aggregate_taxonomy()` - Taxonomy aggregation
  - `aggregate_safety()` - Safety aggregation (worst-case)
  - `aggregate_audience()` - Audience aggregation
  - `aggregate_commercial()` - Commercial aggregation
  - `calculate_health_score()` - Health score calculation

### Integration Steps (DEAL-303)

1. **Import PackageEnricher:**
   ```python
   # Option 1: Direct import (if packages are in Python path)
   from package_enrichment.enricher import PackageEnricher
   
   # Option 2: Relative import from reference directory
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent / "reference" / "packages" / "stage3-package-enrichment"))
   from package_enrichment.enricher import PackageEnricher
   ```

2. **Initialize with LLM API key:**
   ```python
   enricher = PackageEnricher(
       llm_api_key=os.getenv("GEMINI_API_KEY"),
       prompt_template=prompt_template_path
   )
   ```

3. **Match packages with enriched deals:**
   - Stage 2 outputs packages with `deal_ids`
   - Stage 3 needs packages + their constituent enriched deals
   - Create matching function to pair packages with deals

4. **Execute package enrichment:**
   ```python
   enriched_package = enricher.enrich_package(package, matching_deals)
   ```

### Expected Input Format (Stage 3)

**Packages:**
```python
[
    {
        "package_name": "Premium Auto Intender CTV Package",
        "deal_ids": [3001, 3002, 3003, 3004],
        # ... other package fields
    }
]
```

**Enriched Deals (matching deal_ids):**
```python
[
    {
        "deal_id": "3001",
        "taxonomy": {...},
        "safety": {...},
        "audience": {...},
        "commercial": {...},
        # ... other enrichment fields
    },
    # ... matching deals for each package
]
```

### Expected Output Format (Stage 3)

```python
{
    "package_id": "pkg_001",
    "package_name": "Premium Auto Intender CTV Package",
    "deal_ids": [3001, 3002, 3003, 3004],
    "aggregated_taxonomy": {...},
    "aggregated_safety": {...},
    "aggregated_audience": {...},
    "aggregated_commercial": {...},
    "health_score": {...},
    "recommendations": {...}
}
```

## Common Integration Patterns

### 1. Import Path Handling

Since packages are in `reference/packages/`, you may need to:

**Option A: Add to Python path**
```python
import sys
from pathlib import Path
# For Stage 2
sys.path.insert(0, str(Path(__file__).parent.parent / "reference" / "packages" / "stage2-package-creation"))
# For Stage 3
sys.path.insert(0, str(Path(__file__).parent.parent / "reference" / "packages" / "stage3-package-enrichment"))
```

**Option B: Use relative imports (if packages are installed)**
```python
# If packages are installed via setup.py
from package_creation.creator import PackageCreator
from package_enrichment.enricher import PackageEnricher
```

**Option C: Move packages to src/ (Recommended for Phase 3)**
- Move `reference/packages/stage2-package-creation/package_creation/` → `src/enrichment/package_creation/`
- Move `reference/packages/stage3-package-enrichment/package_enrichment/` → `src/enrichment/package_enrichment/`
- Update imports accordingly

### 2. Format Adapters

Create adapter functions to convert between formats:

```python
# src/integration/stage2_adapter.py
def convert_enriched_deal_to_stage2_format(enriched_deal: EnrichedDeal) -> Dict:
    """Convert EnrichedDeal Pydantic model to Stage 2 dictionary format."""
    return {
        "deal_id": enriched_deal.deal_id,
        "deal_name": enriched_deal.deal_name,
        "taxonomy": enriched_deal.taxonomy.dict() if enriched_deal.taxonomy else {},
        "safety": enriched_deal.safety.dict() if enriched_deal.safety else {},
        # ... convert all fields
    }

# src/integration/stage3_adapter.py
def match_packages_with_deals(
    packages: List[Dict], 
    enriched_deals: List[EnrichedDeal]
) -> List[Tuple[Dict, List[Dict]]]:
    """Match packages with their constituent enriched deals."""
    deal_lookup = {deal.deal_id: deal for deal in enriched_deals}
    result = []
    for package in packages:
        deal_ids = package.get("deal_ids", [])
        matching_deals = [
            convert_enriched_deal_to_stage3_format(deal_lookup[deal_id])
            for deal_id in deal_ids
            if deal_id in deal_lookup
        ]
        result.append((package, matching_deals))
    return result
```

### 3. Error Handling

Both packages may raise exceptions. Handle gracefully:

```python
try:
    packages = creator.create_packages(deals)
except Exception as e:
    logger.error(f"Package creation failed: {e}")
    # Continue with partial results or skip Stage 2
    packages = []
```

## Dependencies

Both packages require:
- `langchain-google-genai` - For Gemini LLM integration
- `sentence-transformers` - For embeddings (Stage 2)
- `scikit-learn` - For clustering (Stage 2)
- `pydantic` - For data validation (if using models)

Install with:
```bash
pip install langchain-google-genai sentence-transformers scikit-learn pydantic
```

## Testing Integration

### Unit Tests
- Test format adapters
- Test package/deal matching
- Mock PackageCreator/PackageEnricher calls

### Integration Tests
- Test Stage 1 → Stage 2 flow with real enriched deals
- Test Stage 2 → Stage 3 flow with real packages
- Verify output formats match expectations

### Example Test
```python
def test_stage1_to_stage2_integration():
    # Create sample enriched deals
    enriched_deals = [create_sample_enriched_deal() for _ in range(10)]
    
    # Convert to Stage 2 format
    stage2_deals = [convert_to_stage2_format(deal) for deal in enriched_deals]
    
    # Create packages
    creator = PackageCreator(...)
    packages = creator.create_packages(stage2_deals)
    
    # Verify packages
    assert len(packages) > 0
    assert all("deal_ids" in pkg for pkg in packages)
```

## Migration Path

**Phase 3 (Weeks 9-12):** Integrate packages as-is from `reference/packages/`

**Future:** Consider moving packages into `src/enrichment/` for better organization:
- `src/enrichment/package_creation/` (from `reference/packages/stage2-package-creation/package_creation/`)
- `src/enrichment/package_enrichment/` (from `reference/packages/stage3-package-enrichment/package_enrichment/`)

This would require:
- Updating all imports
- Updating package structure
- Maintaining backward compatibility during transition

---

**See Also:**
- [DEAL-302](../tickets/DEAL-302-stage-integration-1-2.md) - Stage 1 → Stage 2 Integration
- [DEAL-303](../tickets/DEAL-303-stage-integration-2-3.md) - Stage 2 → Stage 3 Integration
- [Package Creation Examples](reference/packages/stage2-package-creation/examples/)
- [Package Enrichment Examples](reference/packages/stage3-package-enrichment/examples/)
