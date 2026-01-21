# Package Enrichment Package - Overview for Dev Agents

This document provides a quick overview for AI dev agents integrating this package.

## What This Package Does

Enriches audience packages with aggregated deal-level metadata and LLM-generated recommendations:
- **Deal Aggregation**: Aggregates taxonomy, safety, audience, commercial data
- **LLM Recommendations**: Generates use cases, verticals, and agent recommendations
- **Health Scoring**: Calculates package quality scores

## Package Structure

```
package_enrichment/
├── enricher.py              # Main PackageEnricher class
└── aggregation.py           # Aggregation utilities
```

## Dependencies

- Python 3.7+
- `langchain-google-genai` library

## Quick Integration

```python
from package_enrichment import PackageEnricher
import os

# Load prompt template
with open('config/package_enrichment_prompt.txt', 'r') as f:
    prompt_template = f.read()

# Initialize enricher
enricher = PackageEnricher(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)

# Enrich package with deals
enriched = enricher.enrich_package(package, deals)
```

## Key Methods

### PackageEnricher

- `enrich_package(package, deals, progress_callback=None)` - Enrich package with aggregated deal data

### Aggregation Functions

- `aggregate_taxonomy(deals)` - Most common taxonomy
- `aggregate_safety(deals)` - Most restrictive safety rating
- `aggregate_audience(deals)` - Union of audience segments
- `aggregate_commercial(deals)` - MIN/MAX/SUM of commercial data
- `calculate_health_score(...)` - Composite health score

## Configuration

Set environment variable:
- `GEMINI_API_KEY` (required)

Or pass directly:
```python
enricher = PackageEnricher(
    llm_api_key="your-api-key",
    prompt_template="..."
)
```

## Input Format

Package with deal IDs:
```python
package = {
    "package_id": 5001,
    "name": "Premium Auto CTV Package",
    "included_deal_ids": [3001, 3002, 3003]
}
```

Enriched deals:
```python
deals = [
    {
        "deal_id": 3001,
        "taxonomy_tier1": "Automotive",
        "garm_risk_rating": "Low",
        "family_safe": True,
        "quality_tier": "Premium",
        "floor_price": 5.50
    }
]
```

## Output Format

Enriched package:
```python
{
    "package_id": 5001,
    "taxonomy_tier1": "Automotive",
    "garm_risk_rating": "Low",
    "health_score": 92.5,
    "recommended_use_cases": ["Premium auto campaigns"],
    "recommended_verticals": ["Automotive", "Finance"]
}
```

## Documentation Files

- `README.md` - User-facing documentation
- `docs/THREE_STAGE_PROCESS.md` - Complete 3-stage pipeline explanation
- `docs/AGGREGATION_RULES.md` - Detailed aggregation logic
- `docs/INTEGRATION_GUIDE.md` - Step-by-step integration
- `docs/API_REFERENCE.md` - Complete API reference
- `docs/ARCHITECTURE.md` - System architecture

## Example Files

- `examples/basic_usage.py` - Simple example
- `examples/enrich_packages_from_json.py` - Load from JSON

## Integration Checklist

- [ ] Copy `package_enrichment/` directory to project
- [ ] Install `langchain-google-genai`
- [ ] Set up Google Gemini API key
- [ ] Prepare packages with deal IDs (from Stage 2)
- [ ] Prepare enriched deals (from Stage 1)
- [ ] Load prompt template
- [ ] Initialize PackageEnricher
- [ ] Call `enrich_package()` with package and deals
- [ ] Process enriched package data

## Common Patterns

### Basic Usage
```python
enricher = PackageEnricher(api_key, prompt_template)
enriched = enricher.enrich_package(package, deals)
```

### With Progress Callback
```python
def progress(msg):
    print(f"[Progress] {msg}")

enriched = enricher.enrich_package(package, deals, progress_callback=progress)
```

### Error Handling
```python
try:
    enriched = enricher.enrich_package(package, deals)
except ValueError as e:
    logger.error(f"Configuration error: {e}")
except json.JSONDecodeError as e:
    logger.error(f"LLM response parsing error: {e}")
```

## The Three-Stage Process

This package is **Stage 3** of a three-stage pipeline:

1. **Stage 1**: Individual deal enrichment (taxonomy, safety, audience)
2. **Stage 2**: Package creation (semantic clustering + LLM grouping)
3. **Stage 3**: Package-level enrichment (aggregation + recommendations) ← **This Package**

See `docs/THREE_STAGE_PROCESS.md` for complete details.

## Aggregation Rules Summary

- **Taxonomy**: Most common (mode)
- **Safety**: Most restrictive (worst-case)
- **Audience**: Union (combine all)
- **Commercial**: MIN/MAX/SUM
- **Health Score**: Weighted composite (0-100)

See `docs/AGGREGATION_RULES.md` for detailed rules.
