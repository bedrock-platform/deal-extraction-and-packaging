# Three-Stage Semantic Enrichment Process

This document explains the complete three-stage pipeline for transforming raw SSP deal data into semantically enriched, buyer-ready audience packages.

## Overview

The semantic enrichment pipeline consists of three sequential stages:

1. **Stage 1: Individual Deal Enrichment** - Enriches each deal with semantic metadata
2. **Stage 2: Package Creation** - Groups enriched deals into intelligent packages (this package)
3. **Stage 3: Package-Level Enrichment** - Aggregates deal enrichments into package-level metadata

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

Enriched deals with semantic metadata:

```json
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
    "family_safe": true
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
}
```

### Key Characteristics

- **Individual Processing**: Each deal is enriched independently
- **LLM Inference**: Uses Google Gemini to infer semantic metadata
- **Multi-Layered Strategy**: Combines LLM inference with volume context, publisher intelligence, and validation
- **Incremental**: Only processes unenriched deals (`taxonomyTier1 IS NULL`)
- **Idempotent**: Safe to re-run on already-enriched deals

---

## Stage 2: Package Creation (This Package)

### Purpose

Group enriched deals into intelligent, buyer-ready packages using semantic clustering and LLM-based grouping.

### Input

Enriched deals from Stage 1 (with semantic metadata)

### Process

#### Step 1: Semantic Embeddings

Each deal is converted to a text representation:

```
Deal: Premium CTV Auto Inventory | SSP: BidSwitch | Format: video | 
Category: Automotive | Subcategory: Auto Parts & Accessories | 
Topic: Auto Repair | Concepts: auto, luxury, premium | 
Family Safe | Risk: Low | Audience: Auto Intenders, Luxury Shoppers | 
Demographics: 25-54, High Income | Quality: Premium | Volume: High | 
Publishers: Paramount, Disney+
```

This text is embedded using `sentence-transformers` (all-MiniLM-L6-v2) to create a semantic vector representation.

#### Step 2: K-Means Clustering

Deals are clustered by semantic similarity:
- **Adaptive Clustering**: Determines optimal number of clusters based on deal count
- **Target Size**: ~25 deals per cluster (optimal for LLM processing)
- **Splitting**: Large clusters are split into smaller batches
- **Filtering**: Tiny clusters (< 5 deals) are filtered out

**Why Clustering?**
- Scales to thousands of deals
- Pre-groups similar deals for LLM analysis
- Reduces LLM processing time and cost

#### Step 3: LLM Grouping

Each cluster is processed through Google Gemini:
- **Prompt**: Includes all deals in cluster with their enrichment data
- **Analysis**: LLM analyzes semantic relationships:
  - Taxonomy alignment (exact + complementary)
  - Audience synergy
  - Safety alignment
  - Commercial synergies
  - Use case alignment
- **Proposals**: LLM proposes package groupings with:
  - Buyer-friendly package names
  - Deal IDs to include (minimum 3)
  - Reasoning for grouping

**LLM Prompt Criteria**:
1. Semantic Similarity (taxonomy, concepts)
2. Complementary Audiences (synergistic segments)
3. Safety Alignment (consistent risk levels)
4. Commercial Synergies (quality tiers, price ranges)
5. Use Case Alignment (campaign types, verticals)

#### Step 4: Package Proposals

Returns structured proposals:

```json
[
  {
    "package_name": "Premium Auto Intender CTV Package",
    "deal_ids": ["3001", "3002", "3003", "3004"],
    "reasoning": "Combines auto-focused CTV inventory with luxury audience overlap for premium auto campaigns. All deals are family-safe and premium quality tier."
  },
  {
    "package_name": "Family-Safe Entertainment Streaming Package",
    "deal_ids": ["3005", "3006", "3007"],
    "reasoning": "Major streaming platforms (Disney+, ESPN) grouped for family-safe entertainment campaigns. Premium CTV inventory with broad reach."
  }
]
```

### Output

Package proposals with deal groupings

### Key Characteristics

- **Semantic Intelligence**: Not just exact taxonomy matches, but semantic relationships
- **Deal Overlap**: Deals can appear in multiple packages (maximizes diversity)
- **Buyer-Focused**: Package names are descriptive and buyer-friendly
- **Scalable**: Handles thousands of deals through clustering

### Deal Overlap Strategy

Deals can and should appear in multiple packages:
- **Example**: A premium CTV deal can be in both:
  - "Premium CTV Package" (format-based)
  - "Auto Intenders Package" (audience-based)
- **Benefit**: Buyers discover deals through different lenses
- **Goal**: Maximum package diversity while serving distinct buyer needs

---

## Stage 3: Package-Level Enrichment

### Purpose

Aggregate deal-level enrichments into package-level metadata and generate package recommendations.

### Input

Packages with deal IDs (from Stage 2)

### Process

#### 1. Deal Aggregation

For each package, aggregates deal-level enrichments:

- **Taxonomy Aggregation**: Most common taxonomy across deals
  - Tier 1: Most frequent tier1 category
  - Tier 2: Most frequent tier2 category
  - Tier 3: Most frequent tier3 category

- **Safety Aggregation**: Most restrictive rating (worst-case)
  - If any deal is "High", package is "High"
  - If any deal is "Medium", package is at least "Medium"
  - Only "Low" if all deals are "Low" or "Floor"
  - Family-safe only if ALL deals are family-safe

- **Price Aggregation**: MIN/MAX floor prices across deals

- **Volume Aggregation**: SUM of bid request volumes across deals

#### 2. LLM Package Recommendations

LLM generates package-level recommendations:
- **Package Health Score**: Composite score 0-100
- **Use Case Recommendations**: Campaign types this package serves
- **Buyer Targeting Guidance**: Who should buy this package
- **Confidence Score**: Certainty of enrichment quality

### Output

Fully enriched packages ready for buyers:

```json
{
  "package_id": 5001,
  "package_name": "Premium Auto Intender CTV Package",
  "included_deal_ids": [3001, 3002, 3003, 3004],
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
    "primary_audience": ["Auto Intenders", "Luxury Shoppers"],
    "demographic_profile": "25-54, High Income"
  },
  "commercial": {
    "floor_price_min": 4.25,
    "floor_price_max": 6.50,
    "total_daily_avails": 1500000000,
    "quality_tier": "Premium"
  },
  "health_score": 92,
  "use_cases": ["Premium Auto Campaigns", "Brand Awareness"],
  "confidence": 0.85
}
```

### Key Characteristics

- **Aggregation**: Combines deal-level data into package-level insights
- **Worst-Case Safety**: Uses most restrictive safety rating
- **LLM Recommendations**: Generates buyer guidance

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
│ Stage 2: Package Creation (This Package)                   │
│                                                             │
│ Enriched Deals                                              │
│         ↓                                                   │
│ Semantic Embeddings (sentence-transformers)                │
│         ↓                                                   │
│ K-Means Clustering                                          │
│         ↓                                                   │
│ LLM Grouping (Gemini 2.5 Flash)                             │
│         ↓                                                   │
│ Package Proposals (with deal IDs)                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Stage 3: Package-Level Enrichment                          │
│                                                             │
│ Packages with Deal IDs                                      │
│         ↓                                                   │
│ Deal Aggregation (taxonomy, safety, prices, volume)        │
│         ↓                                                   │
│ LLM Package Recommendations                                │
│         ↓                                                   │
│ Fully Enriched Packages (ready for buyers)                 │
└─────────────────────────────────────────────────────────────┘
```

## Why This Architecture?

### Separation of Concerns

- **Stage 1**: Focuses on individual deal intelligence
- **Stage 2**: Focuses on grouping intelligence (this package)
- **Stage 3**: Focuses on package-level intelligence

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
- **Stage 3**: Validates aggregation logic

## Integration Points

### Stage 1 → Stage 2

Stage 2 requires enriched deals with:
- `taxonomy` (tier1, tier2, tier3)
- `safety` (garm_risk_rating, family_safe)
- `audience` (inferred_audience, demographic_hint)
- `commercial` (quality_tier, volume_tier, floor_price)

### Stage 2 → Stage 3

Stage 3 requires packages with:
- `package_name`
- `deal_ids` (array of deal IDs)
- `reasoning` (optional)

### Database Schema

Typical database structure:

**Deals Table** (Stage 1 output):
- Individual deals with enrichment columns
- `taxonomyTier1`, `taxonomyTier2`, `taxonomyTier3`
- `garmRiskRating`, `familySafe`
- `inferredAudience`, `demographicHint`
- `qualityTier`, `volumeTier`

**Packages Table** (Stage 2 output):
- Packages with `includedDealIDs` array
- `name`, `description`
- Basic metadata

**Enriched Packages Table** (Stage 3 output):
- Packages with aggregated enrichment
- Package-level taxonomy, safety, audience
- Health scores, use case recommendations

## Best Practices

1. **Run Stage 1 First**: Always enrich deals individually before grouping
2. **Minimum Deal Count**: Ensure you have enough enriched deals (10+ recommended)
3. **Deal Overlap**: Allow deals to appear in multiple packages
4. **Validation**: Validate package proposals before creating packages
5. **Incremental**: Process new deals/packages incrementally

## Summary

The three-stage pipeline transforms raw SSP deal data into semantically enriched, buyer-ready packages:

1. **Stage 1**: Individual deal enrichment (taxonomy, safety, audience)
2. **Stage 2**: Package creation (semantic clustering + LLM grouping) ← **This Package**
3. **Stage 3**: Package-level enrichment (aggregation + recommendations)

Each stage builds on the previous, creating increasingly sophisticated intelligence for programmatic advertising buyers.
