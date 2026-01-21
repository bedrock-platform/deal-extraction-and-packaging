# Package Creation Python Package

A standalone Python package for creating intelligent audience packages from enriched deals using semantic clustering and LLM-based grouping.

## Overview

This package implements **Stage 2** of a three-stage semantic enrichment pipeline that transforms raw SSP (Supply-Side Platform) deal data into semantically enriched, buyer-ready audience packages.

## Features

- ✅ **Semantic Clustering** - Groups similar deals using sentence-transformers embeddings
- ✅ **GMM Clustering** - Gaussian Mixture Model for better handling of overlapping clusters (recommended)
- ✅ **Soft Assignments** - Probabilistic clustering supports deal overlap strategy
- ✅ **LLM-Based Grouping** - Uses Google Gemini to propose intelligent package groupings
- ✅ **Scalable Processing** - Handles thousands of deals through batch clustering
- ✅ **Buyer-Focused** - Creates packages with descriptive names and clear value propositions
- ✅ **Deal Overlap Support** - Allows deals to appear in multiple packages for maximum diversity

## The Three-Stage Enrichment Pipeline

### Stage 1: Individual Deal Enrichment

**Before package creation**, each deal must be enriched individually with semantic metadata:

- **IAB Content Taxonomy** (Tier 1, 2, 3 classifications)
- **Brand Safety** (GARM risk rating, family-safe flag)
- **Audience Inference** (inferred segments, demographic hints)
- **Commercial Tiers** (quality tier, volume tier)

**Input**: Raw deals from SSP APIs (BidSwitch, Index Exchange, etc.)  
**Output**: Enriched deals with semantic metadata

**Example enriched deal**:
```json
{
  "deal_id": "3001",
  "deal_name": "Premium CTV Auto Inventory",
  "taxonomy": {
    "tier1": "Automotive",
    "tier2": "Auto Parts & Accessories",
    "tier3": "Auto Repair"
  },
  "safety": {
    "garm_risk_rating": "Low",
    "family_safe": true
  },
  "audience": {
    "inferred_audience": ["Auto Intenders", "Luxury Shoppers"]
  },
  "commercial": {
    "quality_tier": "Premium",
    "volume_tier": "High"
  }
}
```

### Stage 2: Package Creation (This Package)

**This package** groups enriched deals into intelligent packages:

1. **Semantic Embeddings**: Converts each deal into a text representation and creates embeddings using `sentence-transformers`
2. **Clustering**: Groups deals by semantic similarity using GMM (recommended) or K-means (~25 deals per cluster)
3. **LLM Grouping**: Processes each cluster through Google Gemini to propose package groupings
4. **Package Proposals**: Returns buyer-friendly packages with reasoning

**Input**: Enriched deals (from Stage 1)  
**Output**: Package proposals with deal groupings

**Example package proposal**:
```json
{
  "package_name": "Premium Auto Intender CTV Package",
  "deal_ids": ["3001", "3002", "3003", "3004"],
  "reasoning": "Combines auto-focused CTV inventory with luxury audience overlap for premium auto campaigns. All deals are family-safe and premium quality tier."
}
```

### Stage 3: Package-Level Enrichment

**After packages are created**, they receive aggregated enrichment:

- **Taxonomy Aggregation**: Most common taxonomy across deals
- **Safety Aggregation**: Most restrictive rating (worst-case)
- **Price Aggregation**: MIN/MAX floor prices
- **Volume Aggregation**: SUM of bid request volumes
- **LLM Recommendations**: Package-level use case recommendations

**Input**: Packages with deal IDs (from Stage 2)  
**Output**: Fully enriched packages ready for buyers

## Installation

### Option 1: Copy Package Directory

```bash
cp -r package_creation_package/package_creation /path/to/your/project/
```

### Option 2: Install as Package

```bash
cd package_creation_package
pip install -e .
```

## Quick Start

### 1. Set Up Google Gemini API Key

```bash
export GEMINI_API_KEY="your-api-key"
```

### 2. Prepare Enriched Deals

Your deals should have enrichment data from Stage 1:

```python
deals = [
    {
        "deal_id": "3001",
        "deal_name": "Premium CTV Auto Inventory",
        "ssp_name": "BidSwitch",
        "format": "video",
        "taxonomy": {"tier1": "Automotive", ...},
        "safety": {"garm_risk_rating": "Low", ...},
        "audience": {"inferred_audience": [...], ...},
        "commercial": {"quality_tier": "Premium", ...},
        "publishers": ["Paramount", "Disney+"]
    },
    # ... more deals
]
```

### 3. Create Packages

```python
from package_creation import PackageCreator
from pathlib import Path

# Load prompt template
prompt_path = Path("config/package_grouping_prompt.txt")
with open(prompt_path, 'r') as f:
    prompt_template = f.read()

# Initialize creator
creator = PackageCreator(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template,
    clustering_method="gmm",  # Use GMM clustering (recommended)
    use_soft_assignments=False  # Set True for deal overlap via probabilities
)

# Create packages
proposals = creator.create_packages(deals)

# Process proposals
for proposal in proposals:
    print(f"Package: {proposal['package_name']}")
    print(f"Deals: {proposal['deal_ids']}")
    print(f"Reasoning: {proposal['reasoning']}")
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |

### PackageCreator Parameters

```python
PackageCreator(
    llm_api_key="your-api-key",           # Required
    prompt_template="...",                 # Required
    model_name="gemini-2.5-flash",        # Optional (default)
    temperature=0.5,                       # Optional (default)
    embedding_model="all-MiniLM-L6-v2",   # Optional (default)
    max_deals_per_cluster=25,             # Optional (default)
    min_cluster_size=5                    # Optional (default)
)
```

## How Package Creation Works

### Step 1: Semantic Embeddings

Each deal is converted to a text representation combining:
- Deal name, SSP, format
- Taxonomy (Tier 1, 2, 3)
- Concepts
- Safety ratings
- Audience segments
- Commercial tiers
- Publishers

This text is embedded using `sentence-transformers` (all-MiniLM-L6-v2) to create a semantic vector.

### Step 2: Clustering (K-Means or GMM)

Deals are clustered by semantic similarity using either K-means or GMM:

**GMM Clustering (Recommended)**:
- **Soft Clustering**: Probabilistic assignments support deal overlap
- **Non-Spherical Clusters**: Better handles elliptical/elongated shapes
- **Auto-Selection**: Uses BIC to automatically find optimal number of components
- **Adaptive Clustering**: Determines optimal number of components based on deal count
- **Target Size**: ~25 deals per cluster (optimal for LLM)
- **Splitting**: Large clusters are split into smaller batches
- **Filtering**: Tiny clusters (< 5 deals) are filtered out

**K-Means Clustering**:
- **Hard Clustering**: Each deal belongs to one cluster
- **Faster**: Quicker than GMM for large datasets
- **Spherical Clusters**: Assumes roughly spherical cluster shapes

**Why Clustering?**
- Scales to thousands of deals
- Pre-groups similar deals for LLM analysis
- Reduces LLM processing time and cost
- GMM better supports deal overlap strategy

### Step 3: LLM Grouping

Each cluster is processed through Google Gemini:
- LLM analyzes semantic relationships between deals
- Groups by taxonomy alignment, audience synergy, safety alignment
- Creates buyer-friendly package names
- Requires minimum 3 deals per package
- Allows deal overlap across packages

### Step 4: Package Proposals

Returns structured proposals:
```json
{
  "package_name": "Premium Auto Intender CTV Package",
  "deal_ids": ["3001", "3002", "3003"],
  "reasoning": "Combines auto-focused CTV inventory..."
}
```

## Examples

See the `examples/` directory:

- `basic_usage.py` - Simple package creation example
- `create_packages_from_json.py` - Load deals from JSON file

Run examples:

```bash
cd examples
python basic_usage.py
```

## Requirements

- Python 3.7+
- `sentence-transformers` - For semantic embeddings
- `scikit-learn` - For K-means and GMM clustering
- `langchain-google-genai` - For LLM integration
- `numpy` - For array operations

Install dependencies:

```bash
pip install -r requirements.txt
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - Complete system architecture
- [API Reference](docs/API_REFERENCE.md) - Complete API documentation
- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Step-by-step integration
- [Three-Stage Process](docs/THREE_STAGE_PROCESS.md) - Detailed explanation of enrichment pipeline
- [Clustering Methods](docs/CLUSTERING_METHODS.md) - GMM vs K-means comparison and usage guide

## Key Concepts

### Deal Overlap

Deals can appear in multiple packages to maximize diversity:
- A premium CTV deal can be in both "Premium CTV Package" AND "Auto Intenders Package"
- This allows buyers to discover deals through different lenses
- Each package serves a distinct buyer need

### Semantic Intelligence

Packages are not just grouped by exact taxonomy matches:
- Complementary relationships (e.g., "auto intenders" + "luxury shoppers")
- Use case alignment (e.g., "brand awareness" packages)
- Audience synergies (e.g., "cord-cutters" + "streaming subscribers")

### Buyer-Focused

Package names are descriptive and buyer-friendly:
- ✅ GOOD: "Premium Auto Intender CTV Package"
- ❌ BAD: "IAB2 Video Package"

## Support

For questions or issues, refer to the documentation in `docs/` directory.

## License

This package is provided as-is for integration into your projects.
