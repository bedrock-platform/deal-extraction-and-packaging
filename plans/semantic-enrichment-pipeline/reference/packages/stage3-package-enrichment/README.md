# Package Enrichment Python Package

A standalone Python package for enriching audience packages with aggregated deal-level metadata and LLM-generated recommendations.

## Overview

This package implements **Stage 3** of a three-stage semantic enrichment pipeline that transforms raw SSP (Supply-Side Platform) deal data into semantically enriched, buyer-ready audience packages.

## Features

- ✅ **Deal Aggregation** - Aggregates deal-level enrichments into package-level metadata
- ✅ **LLM Recommendations** - Uses Google Gemini to generate package-level use case recommendations
- ✅ **Health Scoring** - Calculates package health scores based on quality, safety, volume, and coverage
- ✅ **Safety Aggregation** - Uses most restrictive safety rating (worst-case approach)
- ✅ **Standalone** - No dependencies on parent project

## The Three-Stage Enrichment Pipeline

### Stage 1: Individual Deal Enrichment

**Before package creation**, each deal must be enriched individually with semantic metadata:

- **IAB Content Taxonomy** (Tier 1, 2, 3 classifications)
- **Brand Safety** (GARM risk rating, family-safe flag)
- **Audience Inference** (inferred segments, demographic hints)
- **Commercial Tiers** (quality tier, volume tier)

**Input**: Raw deals from SSP APIs  
**Output**: Enriched deals with semantic metadata

### Stage 2: Package Creation

**Groups enriched deals into intelligent packages**:

1. Semantic embeddings
2. Clustering (K-means or GMM)
3. LLM-based grouping
4. Package proposals with deal IDs

**Input**: Enriched deals (from Stage 1)  
**Output**: Packages with `included_deal_ids` array

### Stage 3: Package-Level Enrichment (This Package)

**This package** aggregates deal-level enrichments and generates package recommendations:

1. **Deal Aggregation**: Aggregates taxonomy, safety, audience, commercial data
2. **LLM Recommendations**: Generates use cases, verticals, and agent recommendations
3. **Health Scoring**: Calculates package health score
4. **Package Updates**: Returns enriched package data

**Input**: Packages with deal IDs (from Stage 2)  
**Output**: Fully enriched packages ready for buyers

## Installation

### Option 1: Copy Package Directory

```bash
cp -r package_enrichment_package/package_enrichment /path/to/your/project/
```

### Option 2: Install as Package

```bash
cd package_enrichment_package
pip install -e .
```

## Quick Start

### 1. Set Up Google Gemini API Key

```bash
export GEMINI_API_KEY="your-api-key"
```

### 2. Prepare Package and Deals

Your package should have deal IDs, and deals should have enrichment data:

```python
package = {
    "package_id": 5001,
    "name": "Premium Auto Intender CTV Package",
    "included_deal_ids": [3001, 3002, 3003]
}

deals = [
    {
        "deal_id": 3001,
        "deal_name": "Premium CTV Auto",
        "taxonomy_tier1": "Automotive",
        "garm_risk_rating": "Low",
        "family_safe": True,
        "quality_tier": "Premium",
        "floor_price": 5.50,
        # ... more enrichment fields
    },
    # ... more deals
]
```

### 3. Enrich Package

```python
from package_enrichment import PackageEnricher
from pathlib import Path

# Load prompt template
prompt_path = Path("config/package_enrichment_prompt.txt")
with open(prompt_path, 'r') as f:
    prompt_template = f.read()

# Initialize enricher
enricher = PackageEnricher(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)

# Enrich package
enriched = enricher.enrich_package(package, deals)

# Process enriched data
print(f"Taxonomy: {enriched['taxonomy_tier1']}")
print(f"Health Score: {enriched['health_score']}")
print(f"Use Cases: {enriched['recommended_use_cases']}")
```

## Aggregation Rules

### Taxonomy Aggregation

- **Method**: Most common taxonomy across deals
- **Tier 1**: Most frequent tier1 category
- **Tier 2**: Most frequent tier2 category
- **Tier 3**: Most frequent tier3 category

### Safety Aggregation

- **GARM Risk Rating**: Most restrictive rating (worst-case)
  - If any deal is "High", package is "High"
  - If any deal is "Medium", package is at least "Medium"
  - Only "Low" if all deals are "Low" or "Floor"
- **Family Safe**: Only true if ALL deals are family-safe

### Commercial Aggregation

- **Floor Price Min**: MIN across all deals
- **Floor Price Max**: MAX across all deals
- **Total Daily Avails**: SUM of bid request volumes
- **Quality Tier**: Most common quality tier

### Health Score

Composite score 0-100 based on:
- **Quality**: Premium=30, Mid-tier=20, RON=10
- **Safety**: Floor/Low=30, Medium=20, High=10
- **Volume**: High=25, Medium=15, Low=5
- **Coverage**: 100%=15, 80-99%=12, <80%=8

Formula: `(quality_points + safety_points + volume_points + coverage_points) / 4`

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |

### PackageEnricher Parameters

```python
PackageEnricher(
    llm_api_key="your-api-key",      # Required
    prompt_template="...",            # Required
    model_name="gemini-2.5-flash",    # Optional (default)
    temperature=0.3,                  # Optional (default, lower for consistency)
    timeout=90,                       # Optional (default)
    max_retries=3                     # Optional (default)
)
```

## Examples

See the `examples/` directory:

- `basic_usage.py` - Simple package enrichment example
- `enrich_packages_from_json.py` - Load packages and deals from JSON

Run examples:

```bash
cd examples
python basic_usage.py
```

## Requirements

- Python 3.7+
- `langchain-google-genai` - For LLM integration

Install dependencies:

```bash
pip install -r requirements.txt
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - Complete system architecture
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Step-by-step integration
- [Three-Stage Process](docs/THREE_STAGE_PROCESS.md) - Detailed explanation of enrichment pipeline
- [Aggregation Rules](docs/AGGREGATION_RULES.md) - Detailed aggregation logic

## Key Concepts

### Worst-Case Safety

Safety aggregation uses the most restrictive rating:
- Conservative approach ensures buyer safety
- If any deal is risky, package is marked risky
- Family-safe only if ALL deals are family-safe

### Health Scoring

Package health score indicates overall quality:
- Higher scores = better packages
- Based on quality, safety, volume, and enrichment coverage
- Helps buyers identify premium inventory

### LLM Recommendations

LLM generates actionable recommendations:
- **Use Cases**: Specific campaign types (e.g., "Premium auto campaigns")
- **Verticals**: Industries/verticals (e.g., ["Automotive", "Finance"])
- **Agent Recommendation**: Human-readable summary for AI agents

## Support

For questions or issues, refer to the documentation in `docs/` directory.

## License

This package is provided as-is for integration into your projects.
