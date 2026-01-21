# Package Creation Package - Overview for Dev Agents

This document provides a quick overview for AI dev agents integrating this package.

## What This Package Does

Creates intelligent audience packages from enriched deals using:
- **Semantic Clustering**: Groups similar deals using sentence-transformers embeddings
- **LLM-Based Grouping**: Uses Google Gemini to propose intelligent package groupings

## Package Structure

```
package_creation/
├── creator.py              # Main PackageCreator class
├── embeddings.py           # Semantic embeddings (sentence-transformers)
└── clustering.py           # K-means clustering (scikit-learn)
```

## Dependencies

- Python 3.7+
- `sentence-transformers` library
- `scikit-learn` library
- `langchain-google-genai` library
- `numpy` library

## Quick Integration

```python
from package_creation import PackageCreator
import os

# Load prompt template
with open('config/package_grouping_prompt.txt', 'r') as f:
    prompt_template = f.read()

# Initialize creator
creator = PackageCreator(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)

# Create packages from enriched deals
proposals = creator.create_packages(enriched_deals)
```

## Key Methods

### PackageCreator

- `create_packages(deals, progress_callback=None)` - Create packages from enriched deals

### Utility Functions

- `create_deal_embeddings(deals)` - Create semantic embeddings
- `cluster_deals_semantically(deals, embeddings)` - Cluster deals by similarity

## Configuration

Set environment variable:
- `GEMINI_API_KEY` (required)

Or pass directly:
```python
creator = PackageCreator(
    llm_api_key="your-api-key",
    prompt_template="..."
)
```

## Input Format

Enriched deals must have:
- `deal_id`, `deal_name`
- `taxonomy` (tier1, tier2, tier3)
- `safety` (garm_risk_rating, family_safe)
- `audience` (inferred_audience, demographic_hint)
- `commercial` (quality_tier, volume_tier, floor_price)

## Output Format

Package proposals:
```python
[
    {
        "package_name": "Premium Auto Intender CTV Package",
        "deal_ids": ["3001", "3002", "3003"],
        "reasoning": "Combines auto-focused CTV inventory..."
    }
]
```

## Documentation Files

- `README.md` - User-facing documentation
- `docs/THREE_STAGE_PROCESS.md` - Complete 3-stage pipeline explanation
- `docs/INTEGRATION_GUIDE.md` - Step-by-step integration
- `docs/API_REFERENCE.md` - Complete API reference
- `docs/ARCHITECTURE.md` - System architecture

## Example Files

- `examples/basic_usage.py` - Simple example
- `examples/create_packages_from_json.py` - Load from JSON

## Integration Checklist

- [ ] Copy `package_creation/` directory to project
- [ ] Install `sentence-transformers`, `scikit-learn`, `langchain-google-genai`, `numpy`
- [ ] Set up Google Gemini API key
- [ ] Prepare enriched deals (from Stage 1)
- [ ] Load prompt template
- [ ] Initialize PackageCreator
- [ ] Call `create_packages()` with enriched deals
- [ ] Process package proposals

## Common Patterns

### Basic Usage
```python
creator = PackageCreator(api_key, prompt_template)
proposals = creator.create_packages(deals)
```

### With Progress Callback
```python
def progress(msg):
    print(f"[Progress] {msg}")

proposals = creator.create_packages(deals, progress_callback=progress)
```

### Error Handling
```python
try:
    proposals = creator.create_packages(deals)
except ValueError as e:
    logger.error(f"Configuration error: {e}")
except json.JSONDecodeError as e:
    logger.error(f"LLM response parsing error: {e}")
```

## The Three-Stage Process

This package is **Stage 2** of a three-stage pipeline:

1. **Stage 1**: Individual deal enrichment (taxonomy, safety, audience)
2. **Stage 2**: Package creation (semantic clustering + LLM grouping) ← **This Package**
3. **Stage 3**: Package-level enrichment (aggregation + recommendations)

See `docs/THREE_STAGE_PROCESS.md` for complete details.
