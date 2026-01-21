# Three-Stage Semantic Enrichment Process

This document explains the complete three-stage pipeline for transforming raw SSP deal data into semantically enriched, buyer-ready audience packages.

## Overview

The semantic enrichment pipeline consists of three sequential stages:

1. **Stage 1: Individual Deal Enrichment** - Enriches each deal with semantic metadata
2. **Stage 2: Package Creation** - Groups enriched deals into intelligent packages
3. **Stage 3: Package-Level Enrichment** (This Package) - Aggregates deal enrichments into package metadata

---

## Stage 1: Individual Deal Enrichment

### Purpose

Enrich each individual deal with semantic metadata before grouping into packages.

### Input

Raw deals from SSP APIs (BidSwitch, Index Exchange, etc.) with basic metadata:
- Deal name, ID, SSP
- Inventory type, creative type
- Publishers, geo targeting
- Floor prices, volume metrics

### Process

Each deal is processed through an LLM (Google Gemini 2.5 Flash) to infer:

1. **IAB Content Taxonomy**
   - Tier 1: Top-level category (e.g., "Automotive", "Entertainment")
   - Tier 2: Subcategory (e.g., "Auto Parts & Accessories")
   - Tier 3: Specific topic (e.g., "Auto Repair")

2. **Brand Safety (GARM Alignment)**
   - GARM risk rating: Floor/Low/Medium/High
   - Family-safe flag: True/False
   - Safe-for-verticals list

3. **Audience Profile**
   - Inferred audience segments (e.g., "Auto Intenders", "Luxury Shoppers")
   - Demographic hints (e.g., "25-54, High Income")
   - Audience provenance: "Inferred" (LLM-derived)

4. **Commercial Profile**
   - Quality tier: Premium/Mid-tier/RON
   - Volume tier: High/Medium/Low
   - Floor price analysis

**📖 For detailed information on how Stage 1 handles sparse BidSwitch data, see:**
**[Stage 1 Enrichment Strategies](../../STAGE1_ENRICHMENT_STRATEGIES.md)**

This document covers:
- Multi-layered semantic inference strategies
- Volume context enhancement from Index Exchange
- Publisher name intelligence
- Creative/inventory type inference
- Bid floor price analysis
- IAB taxonomy validation and auto-correction
- Complete enrichment flow diagram

### Output

Enriched deals with semantic metadata (see Stage 2 documentation for format).

---

## Stage 2: Package Creation

### Purpose

Group enriched deals into intelligent, buyer-ready packages using semantic clustering and LLM-based grouping.

### Input

Enriched deals from Stage 1 (with semantic metadata)

### Process

1. **Semantic Embeddings**: Converts each deal into embeddings using `sentence-transformers`
2. **Clustering**: Groups deals by similarity (K-means or GMM)
3. **LLM Grouping**: Processes clusters through Google Gemini to propose package groupings
4. **Package Proposals**: Returns buyer-friendly packages with deal IDs

### Output

Package proposals with deal groupings:

```json
{
  "package_name": "Premium Auto Intender CTV Package",
  "deal_ids": [3001, 3002, 3003, 3004],
  "reasoning": "Combines auto-focused CTV inventory..."
}
```

---

## Stage 3: Package-Level Enrichment (This Package)

### Purpose

Aggregate deal-level enrichments into package-level metadata and generate package recommendations.

### Input

Packages with deal IDs (from Stage 2) and their constituent enriched deals

### Process

#### 1. Deal Aggregation

For each package, aggregates deal-level enrichments:

**Taxonomy Aggregation**:
- **Method**: Most common taxonomy across deals
- **Tier 1**: Most frequent tier1 category
- **Tier 2**: Most frequent tier2 category
- **Tier 3**: Most frequent tier3 category

**Safety Aggregation**:
- **GARM Risk Rating**: Most restrictive rating (worst-case)
  - If any deal is "High", package is "High"
  - If any deal is "Medium", package is at least "Medium"
  - Only "Low" if all deals are "Low" or "Floor"
- **Family Safe**: Only true if ALL deals are family-safe
- **Safe For Verticals**: Determined based on risk rating and family-safe status

**Audience Aggregation**:
- **Primary Audience**: Combines audience segments from all deals (deduplicated)
- **Demographic Profile**: Aggregates demographic hints

**Commercial Aggregation**:
- **Floor Price Min**: MIN across all deals
- **Floor Price Max**: MAX across all deals
- **Total Daily Avails**: SUM of bid request volumes
- **Quality Tier**: Most common quality tier

#### 2. Health Score Calculation

Calculates package health score (0-100):

```
Health Score = (quality_points + safety_points + volume_points + coverage_points) / 4
```

Where:
- **Quality Points**: Premium=30, Mid-tier=20, RON=10
- **Safety Points**: Floor/Low=30, Medium=20, High=10
- **Volume Points**: High=25, Medium=15, Low=5
- **Coverage Points**: 100%=15, 80-99%=12, <80%=8

#### 3. LLM Package Recommendations

LLM generates package-level recommendations:
- **Recommended Use Cases**: Specific campaign types (e.g., "Premium auto campaigns", "Brand awareness")
- **Recommended Verticals**: Industries/verticals (e.g., ["Automotive", "Finance", "CPG"])
- **Agent Recommendation**: Human-readable summary explaining:
  - What this package is best for
  - Key strengths
  - When to use it
  - Any limitations

#### 4. Package Enrichment

Combines aggregated data with LLM recommendations into final enriched package.

### Output

Fully enriched packages ready for buyers:

```json
{
  "package_id": 5001,
  "package_name": "Premium Auto Intender CTV Package",
  "taxonomy_tier1": "Automotive",
  "taxonomy_tier2": "Auto Parts & Accessories",
  "taxonomy_tier3": "Auto Repair",
  "garm_risk_rating": "Low",
  "family_safe": true,
  "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
  "demographic_hint": "25-54, High Income",
  "quality_tier": "Premium",
  "floor_price_min": 4.25,
  "floor_price_max": 6.50,
  "total_daily_avails": 1500000000,
  "deal_count": 4,
  "enrichment_coverage": 1.0,
  "health_score": 92,
  "recommended_use_cases": ["Premium auto campaigns", "Brand awareness"],
  "recommended_verticals": ["Automotive", "Finance"],
  "agent_recommendation": "High-quality package for premium auto campaigns...",
  "confidence": 0.85
}
```

### Key Characteristics

- **Aggregation**: Combines deal-level data into package-level insights
- **Worst-Case Safety**: Uses most restrictive safety rating
- **LLM Recommendations**: Generates buyer guidance
- **Health Scoring**: Provides quality indicator

---

## Complete Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Stage 1: Individual Deal Enrichment                         │
│                                                             │
│ Raw Deals (BidSwitch, Index Exchange, etc.)                │
│         ↓                                                   │
│ LLM Enrichment (Gemini 2.5 Flash)                          │
│         ↓                                                   │
│ Enriched Deals (with taxonomy, safety, audience, etc.)    │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 2: Package Creation                                   │
│                                                             │
│ Enriched Deals                                              │
│         ↓                                                   │
│ Semantic Embeddings (sentence-transformers)                │
│         ↓                                                   │
│ Clustering (K-means or GMM)                                 │
│         ↓                                                   │
│ LLM Grouping (Gemini 2.5 Flash)                             │
│         ↓                                                   │
│ Package Proposals (with deal IDs)                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Package-Level Enrichment (This Package)            │
│                                                             │
│ Packages with Deal IDs                                      │
│         ↓                                                   │
│ Deal Aggregation (taxonomy, safety, prices, volume)         │
│         ↓                                                   │
│ Health Score Calculation                                    │
│         ↓                                                   │
│ LLM Package Recommendations                                 │
│         ↓                                                   │
│ Fully Enriched Packages (ready for buyers)                  │
└─────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

### Separation of Concerns

- **Stage 1**: Focuses on individual deal intelligence
- **Stage 2**: Focuses on grouping intelligence
- **Stage 3**: Focuses on package-level intelligence (this package)

### Scalability

- **Stage 1**: Processes deals individually (parallelizable)
- **Stage 2**: Uses clustering to scale to thousands of deals
- **Stage 3**: Processes packages individually (parallelizable)

### Incremental Processing

Each stage can be run independently:
- Run Stage 1 on new deals
- Run Stage 2 when you have enough enriched deals
- Run Stage 3 on new packages

### Quality Control

- **Stage 1**: Validates taxonomy against IAB taxonomy
- **Stage 2**: Validates package proposals (minimum deals, deal IDs exist)
- **Stage 3**: Validates aggregation logic and health scores

## Integration Points

### Stage 2 → Stage 3

Stage 3 requires packages with:
- `package_id` or `id`
- `name` or `package_name`
- `included_deal_ids` or `includedSupplyDealIDs` (array of deal IDs)

And deals with enrichment data:
- `taxonomy_tier1/2/3` or `taxonomy` dict
- `garm_risk_rating` or `safety` dict
- `inferred_audience` or `audience` dict
- `quality_tier`, `volume_tier`, `floor_price` or `commercial` dict

### Database Schema

Typical database structure:

**Packages Table** (Stage 2 output):
- Packages with `includedDealIDs` array
- `name`, `description`
- Basic metadata

**Enriched Packages Table** (Stage 3 output):
- Packages with aggregated enrichment
- Package-level taxonomy, safety, audience
- Health scores, use case recommendations
- `recommendedUseCases`, `recommendedVerticals`
- `healthScore`, `dealCount`, `confidence`

## Best Practices

1. **Run Stages Sequentially**: Complete Stage 1 → Stage 2 → Stage 3
2. **Validate Deals**: Ensure deals have enrichment data before Stage 3
3. **Monitor Health Scores**: Use health scores to identify quality packages
4. **Review Recommendations**: LLM recommendations guide buyer targeting
5. **Incremental**: Process new packages incrementally

## Summary

The three-stage pipeline transforms raw SSP deal data into semantically enriched, buyer-ready packages:

1. **Stage 1**: Individual deal enrichment (taxonomy, safety, audience)
2. **Stage 2**: Package creation (semantic clustering + LLM grouping)
3. **Stage 3**: Package-level enrichment (aggregation + recommendations) ← **This Package**

Each stage builds on the previous, creating increasingly sophisticated intelligence for programmatic advertising buyers.
