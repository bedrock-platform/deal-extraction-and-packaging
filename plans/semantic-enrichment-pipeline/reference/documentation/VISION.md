# Deal Extraction & Semantic Enrichment Pipeline: Complete Vision

**Version:** 1.0  
**Date:** January 2025  
**Status:** Vision Document - Implementation Roadmap

---

## Executive Summary

This document outlines the complete vision for a three-stage semantic enrichment pipeline that transforms raw SSP deal data into semantically enriched, buyer-ready audience packages. The system extracts deals from multiple vendors (Google Authorized Buyers and BidSwitch), unifies their schemas, enriches them with semantic metadata, and groups them into intelligent packages optimized for programmatic buyers.

**Key Value Propositions:**
- **Multi-Vendor Extraction**: Unified interface for extracting deals from Google Authorized Buyers (Marketplace + Curated) and BidSwitch
- **Schema Unification**: Normalizes vendor-specific data into a consistent schema ready for enrichment
- **Semantic Enrichment**: Transforms sparse deal data into rich semantic metadata using LLM inference
- **Intelligent Packaging**: Groups deals into buyer-ready packages using semantic clustering and constraint-based rules
- **Package-Level Intelligence**: Aggregates deal enrichments into package recommendations and health scores

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DEAL EXTRACTION LAYER                           │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │   Google     │  │  BidSwitch  │  │ Future SSPs  │                │
│  │ Authorized   │  │             │  │               │                │
│  │   Buyers     │  │             │  │               │                │
│  │              │  │             │  │               │                │
│  │ • Marketplace│  │ • OAuth2    │  │ • Extensible  │                │
│  │ • Curated    │  │ • Filtering │  │   Architecture│                │
│  │ • SAPISIDHASH│  │ • Pagination│  │               │                │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                │
│         │                 │                 │                          │
│         └─────────────────┴─────────────────┘                          │
│                           │                                              │
│                    ┌──────▼───────┐                                     │
│                    │ Unified      │                                     │
│                    │ Orchestrator │                                     │
│                    │ (DealExtractor)│                                    │
│                    └──────┬───────┘                                     │
└───────────────────────────┼─────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      SCHEMA UNIFICATION LAYER                         │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Vendor-Specific Transformers                                 │    │
│  │                                                               │    │
│  │  • GoogleAdsTransformer → Unified Schema                     │    │
│  │  • BidSwitchTransformer → Unified Schema                    │    │
│  │                                                               │    │
│  │  Unified Pre-Enrichment Schema:                              │    │
│  │  {                                                           │    │
│  │    "deal_id": str,                                          │    │
│  │    "deal_name": str,                                         │    │
│  │    "ssp_name": str,                                          │    │
│  │    "format": str,                                            │    │
│  │    "publishers": List[str],                                  │    │
│  │    "floor_price": float,                                     │    │
│  │    "inventory_type": str/int,                                │    │
│  │    "start_time": str,                                        │    │
│  │    "end_time": str,                                          │    │
│    │    "volume_metrics": {...},                                │    │
│  │    "raw_deal_data": {...}  # Preserve vendor data            │    │
│  │  }                                                           │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: INDIVIDUAL DEAL ENRICHMENT                 │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Multi-Layered Semantic Inference                            │    │
│  │                                                               │    │
│  │  1. LLM-Based Inference (Google Gemini 2.5 Flash)            │    │
│  │     • IAB Content Taxonomy (Tier 1/2/3)                       │    │
│  │     • Brand Safety (GARM ratings)                            │    │
│  │     • Audience Segments                                      │    │
│  │     • Commercial Profile                                     │    │
│  │                                                               │    │
│  │  2. Volume Context Enhancement                                │    │
│  │     • Index Exchange publisher volume data                   │    │
│  │     • Commercial viability assessment                        │    │
│  │                                                               │    │
│  │  3. Publisher Intelligence                                    │    │
│  │     • Brand recognition and reputation                         │    │
│  │     • Content category inference                             │    │
│  │                                                               │    │
│  │  4. Advanced Strategies (Future)                             │    │
│  │     • Multimodal analysis (inventory_image)                  │    │
│  │     • Temporal validation                                    │    │
│  │     • Market-indexed pricing                                 │    │
│  │     • Hard signal overrides                                  │    │
│  │                                                               │    │
│  │  5. IAB Taxonomy Validation                                  │    │
│  │     • Auto-correction                                        │    │
│  │     • Code-to-name conversion                                │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Output: Enriched Deals with Semantic Metadata                         │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: PACKAGE CREATION                            │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Semantic Clustering & LLM Grouping                          │    │
│  │                                                               │    │
│  │  1. Semantic Embeddings                                       │    │
│  │     • sentence-transformers (all-MiniLM-L6-v2)               │    │
│  │     • Text representation of enriched deals                    │    │
│  │                                                               │    │
│  │  2. Clustering Algorithms                                     │    │
│  │     • K-means (adaptive cluster count)                       │    │
│  │     • GMM (Gaussian Mixture Models)                          │    │
│  │     • Target: ~25 deals per cluster                          │    │
│  │                                                               │    │
│  │  3. Advanced Clustering (Future)                              │    │
│  │     • Constraint-based clustering                            │    │
│  │     • Anti-package filter (LLM)                             │    │
│  │     • Recursive refinement                                   │    │
│  │     • Diversity-aware clustering                             │    │
│  │     • Volume-aware clustering                                 │    │
│  │                                                               │    │
│  │  4. LLM Package Grouping                                      │    │
│  │     • Google Gemini processes clusters                       │    │
│  │     • Generates package proposals                            │    │
│  │     • Deal overlap support                                   │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Output: Package Proposals with Deal IDs                               │
└─────────────────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                  STAGE 3: PACKAGE-LEVEL ENRICHMENT                     │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Deal Aggregation & LLM Recommendations                      │    │
│  │                                                               │    │
│  │  1. Deal Aggregation                                         │    │
│  │     • Taxonomy aggregation (union, intersection)              │    │
│  │     • Safety aggregation (worst-case)                         │    │
│  │     • Audience aggregation (union)                            │    │
│  │     • Commercial aggregation (min/max/avg)                      │    │
│  │                                                               │    │
│  │  2. Health Score Calculation                                  │    │
│  │     • Enrichment coverage                                    │    │
│  │     • Deal count                                             │    │
│  │     • Price range                                            │    │
│  │     • Volume metrics                                         │    │
│  │                                                               │    │
│  │  3. LLM Package Recommendations                               │    │
│  │     • Buyer use cases                                        │    │
│  │     • Targeting recommendations                              │    │
│  │     • Optimization suggestions                                │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                         │
│  Output: Enriched Packages with Recommendations                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 0: Deal Extraction

### Overview

The deal extraction layer provides a unified interface for extracting deals from multiple SSP vendors. Currently supports Google Authorized Buyers and BidSwitch, with an extensible architecture for future vendors.

### Google Authorized Buyers

**Two Deal Sources:**

1. **Marketplace Packages**
   - User-created packages in Authorized Buyers UI
   - Rich forecast/breakdown data (age, gender, country, device, content vertical)
   - Cost histograms (CPM distribution)
   - Package details (email, floor price, created by)
   - **API**: Internal endpoint (`adexchangebuyer.clients6.google.com`)
   - **Auth**: SAPISIDHASH (browser session tokens)

2. **Google Curated Packages**
   - Pre-built packages curated by Google
   - Optimized for specific audiences/verticals
   - Less detailed forecast data than Marketplace
   - **API**: Same internal endpoint, different endpoint path
   - **Auth**: Same SAPISIDHASH authentication

**Key Features:**
- ✅ SAPISIDHASH authentication (manual browser tokens)
- ✅ Automatic pagination (`continuationToken` handling)
- ✅ Token expiration detection
- ✅ Package details hydration (email, floor price, created by)
- ✅ Forecast/breakdown metrics extraction
- ✅ Cost histogram analysis

**Data Structure:**
- Nested objects (`forecast`, `breakdowns`, `metrics`)
- Rich demographic/geographic breakdowns
- Publisher information (name, account ID, logo URL)

### BidSwitch

**Deal Source:**
- Deals Discovery API
- Middleware aggregating deals from underlying SSPs (Sovrn, Sonobi, OpenX, etc.)
- Flat structure (no nested objects)
- Sparse semantic data

**Key Features:**
- ✅ OAuth2 authentication (username/password)
- ✅ Comprehensive filtering (format, country, price, SSP, etc.)
- ✅ Automatic token refresh
- ✅ Pagination support
- ✅ SSP identification (`ssp_id` mapping)

**Data Structure:**
- Flat hierarchy (all fields at top level)
- Minimal semantic fields (`deal_id`, `display_name`, `description`)
- Publisher arrays (often placeholder text)
- Basic forecasting metrics (`bid_requests`, `bid_requests_by_categories`)
- **Hidden Signals** (under-utilized):
  - `inventory_image` (URL to visual representation)
  - `weekly_total_avails`, `weekly_unique_avails` (availability metrics)
  - `auction_type` (1=First Price, 2=Second Price)
  - `ssp_id` (SSP identifier)
  - `bid_requests_ratio` (calculated: bid_requests / days_active)

### Unified Orchestrator

The `DealExtractor` orchestrator provides a unified interface for:
- Multi-vendor extraction
- Vendor-specific filtering
- Unified data export
- Google Sheets integration (optional)

**CLI Usage:**
```bash
# Extract from Google Ads only
python -m src.deal_extractor --vendor google_ads

# Extract from BidSwitch only
python -m src.deal_extractor --vendor bidswitch

# Extract from all vendors
python -m src.deal_extractor --all

# Extract Google Curated packages
python -m src.google_ads.inventory_downloader --google-curated

# Extract both Marketplace and Curated
python -m src.google_ads.inventory_downloader --all
```

---

## Schema Unification

### The Challenge

Different vendors provide data in different formats:
- **Google Ads**: Nested objects, rich breakdowns, detailed metrics
- **BidSwitch**: Flat structure, sparse semantic data, minimal fields

### The Solution: Unified Pre-Enrichment Schema

Before Stage 1 enrichment, all deals must be normalized to a consistent schema:

```json
{
  "deal_id": "string",
  "deal_name": "string",
  "ssp_name": "string",  // "Google Authorized Buyers" or "BidSwitch"
  "format": "string",     // "video", "display", "native", "audio"
  "publishers": ["string"],  // Array of publisher names
  "floor_price": float,
  "inventory_type": "string|int",  // "CTV", "Websites", "Apps", "DOOH" or numeric IDs
  "start_time": "ISO8601",
  "end_time": "ISO8601",
  "description": "string",
  "volume_metrics": {
    "bid_requests": int,
    "impressions": int,
    "uniques": int,
    "bid_requests_ratio": float
  },
  "raw_deal_data": {...}  // Preserve original vendor data for reference
}
```

### Vendor-Specific Transformers

**GoogleAdsTransformer:**
- Extracts nested forecast/breakdown data
- Normalizes publisher info (single publisher → array)
- Maps `vendor` → `ssp_name`
- Infers `format` from `primary_request_format` or breakdowns
- Converts `floor_price` from string to float

**BidSwitchTransformer:**
- Extracts flat structure fields
- Maps `creative_type` → `format`
- Maps `ssp_id` → `ssp_name`
- Preserves `publishers` array
- Calculates `bid_requests_ratio`

### Field Mapping

| Unified Field | Google Ads Source | BidSwitch Source |
|--------------|------------------|------------------|
| `deal_id` | `entityId` | `deal_id` |
| `deal_name` | `entityName` | `display_name` |
| `ssp_name` | `"Google Authorized Buyers"` | `SSP_MAP[ssp_id]` |
| `format` | `primary_request_format` (inferred) | `creative_type` |
| `publishers` | `[publisher]` (single → array) | `publishers` (array) |
| `floor_price` | `floor_price` (string → float) | `price` (string → float) |
| `inventory_type` | Inferred from breakdowns | `inventory_type` (numeric) |

---

## Stage 1: Individual Deal Enrichment

### Purpose

Transform sparse deal data into semantically enriched deals with taxonomy, safety, audience, and commercial metadata.

### Input

Unified pre-enrichment schema deals (from Schema Unification layer)

### Process

**1. Multi-Layered Semantic Inference**

Uses Google Gemini 2.5 Flash to infer semantic metadata from available fields:

- **IAB Content Taxonomy** (Tier 1/2/3)
  - Infers from deal names, publishers, creative type
  - Validates against IAB taxonomy validator
  - Auto-corrects typos/variations

- **Brand Safety** (GARM Alignment)
  - GARM risk rating: Floor/Low/Medium/High
  - Family-safe flag: True/False
  - Safe-for-verticals list

- **Audience Profile**
  - Inferred audience segments (e.g., "Auto Intenders", "Luxury Shoppers")
  - Demographic hints (e.g., "25-54, High Income")
  - Audience provenance: "Inferred" (LLM-derived)

- **Commercial Profile**
  - Quality tier: Premium/Mid-tier/RON
  - Volume tier: High/Medium/Low
  - Floor price analysis

**2. Volume Context Enhancement**

Adds Index Exchange publisher volume data:
- Matches publisher names to Index Exchange CSV data
- Provides commercial context (daily avails, CTV volume, market share)
- Helps LLM assess volume tiers and publisher quality

**3. Publisher Intelligence**

Recognizes publisher brand patterns:
- "Paramount+", "Disney+", "ESPN" → Entertainment/CTV
- "CNN", "BBC", "Reuters" → News/Information
- Maps publishers to content categories and safety ratings

**4. Advanced Strategies (Future Enhancements)**

- **Multimodal Intelligence**: Analyze `inventory_image` URLs with Gemini vision
- **Temporal Validation**: Check temporal relevance (e.g., "WorldCup_2022" active in 2026)
- **Market-Indexed Pricing**: Compare floor prices to market averages
- **Hard Signal Overrides**: Prioritize `ssp_id`, `auction_type`, `inventory_image` over LLM guesses
- **Competitive Clutter Analysis**: Use `bid_requests_ratio` for competitive context

**5. Real-Time Verification (Stage 1.5 - Optional)**

For high-value deals or when additional verification is needed, see [Stage 1.5: Real-Time Verification Layer](#stage-15-real-time-verification-layer-advanced) for:
- Real-time publisher intelligence (web crawling, content analysis)
- Compliance and SPO verification (CMP, ads.txt, sellers.json)
- Market intelligence fusion (competitor spend, performance metrics)

**5. IAB Taxonomy Validation**

- Validates taxonomy against IAB standards
- Auto-corrects typos/variations
- Converts IAB codes to names (e.g., "IAB26" → "Sports")

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

- **Individual Processing**: Each deal enriched independently
- **Incremental**: Only processes unenriched deals
- **Idempotent**: Safe to re-run
- **Multi-Layered**: Combines LLM inference with external data and validation

---

## Stage 1.5: Real-Time Verification Layer (Advanced)

### Purpose

Move beyond **static inference** (predicting based on deal metadata) to **dynamic verification** (validating against the live web). This optional layer adds real-time intelligence by crawling publisher sites, verifying compliance, and fusing platform-native data with external market intelligence.

### Input

Enriched deals from Stage 1 (with semantic metadata)

### Process

**1. Real-Time Publisher Intelligence (The "Web Search" Layer)**

Transforms the "publisher" field from a simple string into a live audit:

- **Content Analysis**
  - Use headless browser or specialized API to fetch publisher's site
  - Extract actual keywords and topics appearing *right now* using NLP
  - Compare live content against inferred taxonomy (validate/update)
  - Detect content pivots (e.g., news site → financial advice)

- **Dynamic Risk Assessment**
  - Perform real-time risk assessments to identify recent content pivots
  - Detect high-risk content (controversial news, unregulated financial advice)
  - Flag publishers that may not be reflected in legacy safety lists
  - Update GARM risk ratings based on current content

- **Visual Site Quality Analysis**
  - Use vision-capable model (Gemini 1.5 Pro) to analyze live screenshots
  - Detect "Made-for-Advertising" (MFA) signals:
    - Ad-heavy layouts
    - Low-quality stock images
    - Poor UX indicators
    - Content-to-ad ratio analysis
  - Visual quality assessment complements text analysis

**Implementation:**
```python
# Example: Real-time publisher verification
def verify_publisher_live(publisher_domain: str) -> Dict:
    """
    Crawl publisher site and perform real-time verification.
    """
    # Fetch site content
    content = crawl_publisher_site(publisher_domain)
    
    # Extract keywords/topics
    live_topics = extract_topics_nlp(content)
    
    # Visual analysis
    screenshot = capture_screenshot(publisher_domain)
    visual_quality = analyze_visual_quality(screenshot)  # Gemini 1.5 Pro
    
    # Risk assessment
    risk_signals = assess_dynamic_risk(content, visual_quality)
    
    return {
        "live_topics": live_topics,
        "visual_quality_score": visual_quality["mfa_score"],
        "is_mfa": visual_quality["is_mfa"],
        "dynamic_risk_rating": risk_signals["risk_level"],
        "content_pivot_detected": risk_signals["pivot_detected"]
    }
```

**2. External Metadata & Compliance Enrichment**

Leverage external "alternative data" to verify trust and legitimacy:

- **Regulatory & Identity Signals**
  - Detect Consent Management Platform (CMP) versions:
    - TCF 2.2 compliance
    - Google Consent Mode v2
    - Privacy regulation compliance
  - Ensure deals are compliant with latest privacy regulations
  - Flag non-compliant publishers for exclusion

- **Supply Path Optimization (SPO)**
  - Cross-reference publisher domains against public `ads.txt` files
  - Verify deal is sourced from direct, authorized seller
  - Detect risky third-tier resellers
  - Validate `sellers.json` entries
  - SPO score: Direct (high) → Authorized Reseller (medium) → Unknown (low)

- **Discovery Weighting**
  - Apply "Product Boost" or weighting system
  - Prioritize "Premium Verified" publishers:
    - Long history of high-quality content
    - Established brand reputation
    - Consistent compliance record
  - De-prioritize new or unknown sites
  - Weighting affects package creation and recommendations

**Implementation:**
```python
# Example: Compliance and SPO verification
def verify_compliance_and_spo(publisher_domain: str) -> Dict:
    """
    Verify compliance and supply path optimization.
    """
    # Check CMP compliance
    cmp_version = detect_cmp_version(publisher_domain)
    is_compliant = check_privacy_compliance(cmp_version)
    
    # Verify ads.txt
    ads_txt = fetch_ads_txt(publisher_domain)
    spo_score = analyze_supply_path(ads_txt)
    
    # Check sellers.json
    sellers_json = fetch_sellers_json(publisher_domain)
    authorized_sellers = validate_sellers(sellers_json)
    
    # Calculate premium weighting
    premium_score = calculate_premium_weighting(
        publisher_domain,
        compliance_history=is_compliant,
        spo_score=spo_score,
        brand_reputation=get_brand_reputation(publisher_domain)
    )
    
    return {
        "cmp_version": cmp_version,
        "is_compliant": is_compliant,
        "spo_score": spo_score,  # "direct", "authorized", "unknown"
        "premium_weighting": premium_score,  # 0.0 - 1.0
        "authorized_sellers": authorized_sellers
    }
```

**3. Platform-Native vs. External Signal Fusion**

Fuse platform-native data (Google, BidSwitch) with market-wide ad intelligence:

- **Competitor Spend Tracking**
  - Integrate with ad intelligence platforms (MediaRadar, Pathmatics)
  - Enrich deals with data showing which big brands are *already* spending
  - "High Demand" signal from major advertisers = quality proxy
  - Brand safety validation (premium brands avoid risky publishers)

- **Conversion Schema Enrichment**
  - Ingest external attribution signals
  - Historical performance data by publisher category:
    - CPA vs. CPM performance
    - Conversion rates by vertical
    - ROI metrics
  - Enrich commercial profile with performance data
  - Guide package recommendations based on historical outcomes

- **Market Intelligence Fusion**
  - Combine platform-native signals with external market data
  - Cross-validate taxonomy and safety ratings
  - Identify market trends (rising/falling publisher categories)
  - Enhance volume tier assessment with market context

**Implementation:**
```python
# Example: Signal fusion
def fuse_market_intelligence(deal: Dict) -> Dict:
    """
    Fuse platform-native data with external market intelligence.
    """
    publisher_domain = extract_domain(deal["publishers"][0])
    
    # Competitor spend tracking
    competitor_data = fetch_competitor_spend(publisher_domain)
    major_brands_spending = competitor_data.get("major_brands", [])
    high_demand_signal = len(major_brands_spending) > 5
    
    # Conversion schema enrichment
    performance_data = fetch_historical_performance(
        publisher_domain,
        category=deal["taxonomy"]["tier1"]
    )
    
    # Market intelligence
    market_trends = fetch_market_trends(
        category=deal["taxonomy"]["tier1"],
        format=deal["format"]
    )
    
    return {
        "competitor_spend": {
            "major_brands": major_brands_spending,
            "high_demand": high_demand_signal,
            "spend_volume": competitor_data.get("total_spend")
        },
        "performance_metrics": {
            "avg_cpa": performance_data.get("avg_cpa"),
            "avg_cpm": performance_data.get("avg_cpm"),
            "conversion_rate": performance_data.get("conversion_rate"),
            "roi": performance_data.get("roi")
        },
        "market_trends": {
            "trend": market_trends.get("trend"),  # "rising", "falling", "stable"
            "market_share": market_trends.get("market_share")
        }
    }
```

### Output

Enhanced deals with real-time verification data:

```json
{
  "deal_id": "3001",
  "deal_name": "Premium CTV Auto Inventory",
  // ... Stage 1 enrichment fields ...
  
  "verification": {
    "publisher_intelligence": {
      "live_topics": ["automotive", "luxury cars", "car reviews"],
      "visual_quality_score": 0.85,
      "is_mfa": false,
      "dynamic_risk_rating": "Low",
      "content_pivot_detected": false,
      "last_verified": "2025-01-20T10:30:00Z"
    },
    "compliance": {
      "cmp_version": "TCF 2.2",
      "is_compliant": true,
      "spo_score": "direct",
      "premium_weighting": 0.9,
      "authorized_sellers": ["direct", "authorized_reseller"]
    },
    "market_intelligence": {
      "competitor_spend": {
        "major_brands": ["BMW", "Mercedes", "Audi", "Tesla"],
        "high_demand": true,
        "spend_volume": 5000000
      },
      "performance_metrics": {
        "avg_cpa": 45.50,
        "avg_cpm": 8.25,
        "conversion_rate": 0.025,
        "roi": 3.2
      },
      "market_trends": {
        "trend": "rising",
        "market_share": 0.15
      }
    }
  }
}
```

### Key Characteristics

- **Optional Layer**: Can be enabled/disabled per deal or batch
- **Real-Time**: Validates against live web content
- **Cost-Conscious**: Caching and rate limiting to manage API costs
- **Incremental**: Only re-verify when needed (configurable refresh intervals)
- **Fusion**: Combines platform-native and external signals

### When to Use

- **High-Value Deals**: Premium packages or high-floor deals
- **Unknown Publishers**: New or unfamiliar publisher domains
- **Risk Assessment**: When brand safety is critical
- **Compliance Requirements**: When regulatory compliance is mandatory
- **Market Intelligence**: When competitor insights are valuable

---

## Stage 2: Package Creation

### Purpose

Group enriched deals into intelligent, buyer-ready packages using semantic clustering and LLM-based grouping.

### Input

Enriched deals from Stage 1 (with semantic metadata)

### Process

**1. Semantic Embeddings**

Converts each deal to text representation:
```
Deal: Premium CTV Auto Inventory | SSP: BidSwitch | Format: video | 
Category: Automotive | Subcategory: Auto Parts & Accessories | 
Topic: Auto Repair | Concepts: auto, luxury, premium | 
Family Safe | Risk: Low | Audience: Auto Intenders, Luxury Shoppers | 
Demographics: 25-54, High Income | Quality: Premium | Volume: High | 
Publishers: Paramount, Disney+
```

Embeds using `sentence-transformers` (all-MiniLM-L6-v2) to create semantic vectors.

**2. Clustering Algorithms**

- **K-means**: Adaptive cluster count based on deal count
- **GMM**: Gaussian Mixture Models (alternative)
- **Target Size**: ~25 deals per cluster (optimal for LLM processing)
- **Splitting**: Large clusters split into smaller batches
- **Filtering**: Tiny clusters (< 5 deals) filtered out

**3. Advanced Clustering (Future Enhancements)**

- **Constraint-Based Clustering**: Enforce business rules (safety, content type)
- **Anti-Package Filter**: LLM identifies incompatible deal pairs
- **Recursive Clustering**: Iterative refinement with tighter constraints
- **Diversity-Aware Clustering**: Ensure package diversity (publishers, formats, geos)
- **Volume-Aware Clustering**: Balance package sizes for viability

**4. LLM Package Grouping**

Each cluster processed through Google Gemini:
- Analyzes semantic similarity
- Proposes package groupings
- Generates package names and descriptions
- Supports deal overlap (deals can appear in multiple packages)

### Output

Package proposals with deal IDs:

```json
{
  "package_name": "Premium Auto Intender CTV Package",
  "deal_ids": [3001, 3002, 3003, 3004],
  "reasoning": "Combines auto-focused CTV inventory from premium publishers...",
  "metadata": {
    "cluster_id": 5,
    "deal_count": 4,
    "avg_quality_tier": "Premium"
  }
}
```

### Key Characteristics

- **Scalable**: Handles thousands of deals
- **Semantic**: Groups by semantic similarity, not just keywords
- **Buyer-Ready**: Packages optimized for programmatic buyers
- **Flexible**: Supports deal overlap for maximum diversity

---

## Stage 3: Package-Level Enrichment

### Purpose

Aggregate deal-level enrichments into package-level metadata and generate package recommendations.

### Input

Packages with deal IDs (from Stage 2) and their constituent enriched deals

### Process

**1. Deal Aggregation**

Aggregates deal-level enrichments using deterministic rules:

- **Taxonomy Aggregation**
  - Union: All taxonomy values from all deals
  - Intersection: Common taxonomy values
  - Primary: Most common taxonomy tier

- **Safety Aggregation**
  - Worst-case: Highest risk rating from all deals
  - Family-safe: True only if all deals are family-safe

- **Audience Aggregation**
  - Union: All audience segments from all deals
  - Demographic hints: Aggregated ranges

- **Commercial Aggregation**
  - Min/max/avg floor prices
  - Volume totals
  - Quality tier distribution

**2. Health Score Calculation**

Calculates package health metrics:
- Enrichment coverage (% of deals with enrichment data)
- Deal count
- Price range (min/max)
- Volume metrics (total avails, unique avails)

**3. LLM Package Recommendations**

Google Gemini generates package-level recommendations:
- Buyer use cases
- Targeting recommendations
- Optimization suggestions
- Package strengths and weaknesses

### Output

Enriched packages with recommendations:

```json
{
  "package_id": "pkg_001",
  "package_name": "Premium Auto Intender CTV Package",
  "deal_ids": [3001, 3002, 3003, 3004],
  "aggregated_taxonomy": {
    "tier1": ["Automotive"],
    "tier2": ["Auto Parts & Accessories", "Auto Repair"],
    "tier3": ["Auto Repair", "Auto Parts"]
  },
  "aggregated_safety": {
    "garm_risk_rating": "Low",
    "family_safe": true
  },
  "aggregated_audience": {
    "inferred_audience": ["Auto Intenders", "Luxury Shoppers", "Car Enthusiasts"],
    "demographic_hint": "25-54, High Income"
  },
  "aggregated_commercial": {
    "min_floor_price": 4.50,
    "max_floor_price": 6.00,
    "avg_floor_price": 5.25,
    "total_volume": 1000000000,
    "quality_tier_distribution": {"Premium": 4}
  },
  "health_score": {
    "enrichment_coverage": 1.0,
    "deal_count": 4,
    "price_range": {"min": 4.50, "max": 6.00},
    "volume_metrics": {"total_avails": 1000000000}
  },
  "recommendations": {
    "use_cases": ["Auto brand awareness", "Luxury auto campaigns"],
    "targeting": "Target 25-54, high-income auto intenders",
    "optimization": "Consider adding more CTV inventory for scale"
  }
}
```

### Key Characteristics

- **Deterministic Aggregation**: Consistent rules for combining deal data
- **LLM Recommendations**: Intelligent package-level insights
- **Health Scoring**: Package quality metrics
- **Buyer-Focused**: Recommendations optimized for programmatic buyers

---

## Data Flow: Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 0: Deal Extraction                                            │
│                                                                     │
│ Google Authorized Buyers          BidSwitch                        │
│ ├── Marketplace Packages          ├── Deals Discovery API         │
│ └── Google Curated Packages       └── OAuth2 Auth                 │
│                                                                     │
│         └──────────────┬──────────────────┘                        │
│                        │                                            │
│                 Unified Orchestrator                                 │
│                 (DealExtractor)                                     │
└────────────────────────┼────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Schema Unification                                                 │
│                                                                     │
│ GoogleAdsTransformer    BidSwitchTransformer                      │
│         └──────────────┬──────────────────┘                        │
│                        │                                            │
│              Unified Pre-Enrichment Schema                          │
│              (deal_id, deal_name, ssp_name, format,                │
│               publishers, floor_price, volume_metrics, ...)        │
└────────────────────────┼────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 1: Individual Deal Enrichment                                │
│                                                                     │
│ • LLM Inference (Gemini 2.5 Flash)                                │
│ • Volume Context Enhancement (Index Exchange)                       │
│ • Publisher Intelligence                                            │
│ • IAB Taxonomy Validation                                           │
│ • Advanced Strategies (Future)                                      │
│                                                                     │
│ Output: Enriched Deals                                             │
│ (taxonomy, safety, audience, commercial metadata)                    │
└────────────────────────┼────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 1.5: Real-Time Verification Layer (Optional)                │
│                                                                     │
│ • Real-Time Publisher Intelligence                                  │
│   - Content analysis (live web crawling)                            │
│   - Dynamic risk assessment                                         │
│   - Visual site quality (MFA detection)                             │
│                                                                     │
│ • Compliance & SPO Enrichment                                      │
│   - CMP version detection (TCF 2.2, Consent Mode v2)              │
│   - ads.txt / sellers.json verification                             │
│   - Premium weighting system                                        │
│                                                                     │
│ • Market Intelligence Fusion                                       │
│   - Competitor spend tracking (MediaRadar, Pathmatics)              │
│   - Conversion schema enrichment (CPA, ROI metrics)                 │
│   - Market trend analysis                                           │
│                                                                     │
│ Output: Verified Deals                                             │
│ (live verification, compliance, market intelligence)                │
└────────────────────────┼────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 2: Package Creation                                          │
│                                                                     │
│ • Semantic Embeddings (sentence-transformers)                     │
│ • Clustering (K-means/GMM)                                         │
│ • Advanced Clustering (Future)                                     │
│ • LLM Package Grouping (Gemini)                                    │
│                                                                     │
│ Output: Package Proposals                                          │
│ (package_name, deal_ids, reasoning)                                │
└────────────────────────┼────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│ Stage 3: Package-Level Enrichment                                  │
│                                                                     │
│ • Deal Aggregation (taxonomy, safety, audience, commercial)        │
│ • Health Score Calculation                                          │
│ • LLM Package Recommendations (Gemini)                            │
│                                                                     │
│ Output: Enriched Packages                                          │
│ (aggregated metadata, health scores, recommendations)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Status

### ✅ Completed

- **Deal Extraction Layer**
  - ✅ Google Authorized Buyers (Marketplace + Curated)
  - ✅ BidSwitch integration
  - ✅ Unified orchestrator
  - ✅ Multi-vendor CLI
  - ✅ Google Sheets export

- **Schema Unification**
  - ✅ GoogleAdsTransformer
  - ✅ BidSwitchTransformer
  - ✅ Unified export format

- **Documentation**
  - ✅ Stage 1 enrichment strategies
  - ✅ Stage 2 advanced clustering strategies
  - ✅ Three-stage process documentation
  - ✅ Integration guides

### 🚧 In Progress / Planned

- **Stage 1: Individual Deal Enrichment**
  - 🚧 LLM inference implementation
  - 🚧 Volume context enhancement
  - 🚧 IAB taxonomy validation
  - 📋 Multimodal intelligence (inventory_image)
  - 📋 Temporal validation
  - 📋 Market-indexed pricing
  - 📋 Hard signal overrides

- **Stage 1.5: Real-Time Verification Layer**
  - 📋 Real-time publisher intelligence (web crawling)
  - 📋 Dynamic risk assessment
  - 📋 Visual site quality analysis (MFA detection)
  - 📋 Compliance verification (CMP, ads.txt, sellers.json)
  - 📋 SPO scoring and premium weighting
  - 📋 Competitor spend tracking integration
  - 📋 Conversion schema enrichment
  - 📋 Market intelligence fusion

- **Stage 2: Package Creation**
  - 🚧 Semantic embeddings
  - 🚧 K-means/GMM clustering
  - 🚧 LLM package grouping
  - 📋 Constraint-based clustering
  - 📋 Anti-package filter
  - 📋 Recursive clustering
  - 📋 Diversity-aware clustering
  - 📋 Volume-aware clustering

- **Stage 3: Package-Level Enrichment**
  - 🚧 Deal aggregation
  - 🚧 Health score calculation
  - 🚧 LLM package recommendations

### 📋 Future Enhancements

- Additional SSP integrations (IndexExchange, OpenX, etc.)
- Database integration
- Web UI dashboard
- Scheduled automation
- Incremental updates (delta downloads)
- Real-time deal monitoring

---

## Key Design Principles

### 1. Extensibility

- Abstract base classes (`BaseSSPClient`, `BaseTransformer`)
- Easy to add new vendors
- Plugin architecture for enrichment strategies

### 2. Data Preservation

- Preserve raw vendor data in `raw_deal_data`
- Maintain vendor-specific fields alongside unified schema
- Enable vendor-specific analysis when needed

### 3. Incremental Processing

- Stage 1: Only process unenriched deals
- Idempotent operations (safe to re-run)
- Resume capability for large datasets

### 4. Scalability

- Clustering for large deal volumes
- Batch processing
- Parallelizable stages

### 5. Buyer-Focused

- Packages optimized for programmatic buyers
- Health scores and recommendations
- Use case suggestions

### 6. Verification & Compliance

- Real-time verification against live web content
- Compliance checking (privacy regulations, SPO)
- Dynamic risk assessment
- Market intelligence fusion

---

## Technical Stack

### Core Technologies

- **Python 3.8+**
- **LLM**: Google Gemini 2.5 Flash
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Clustering**: scikit-learn (K-means, GMM)
- **Data Processing**: pandas
- **API Clients**: requests, OAuth2

### External Data Sources

- **Index Exchange**: Publisher volume data
- **IAB Taxonomy**: Content taxonomy validation
- **Google Sheets**: Data export and sharing
- **Ad Intelligence Platforms** (Future): MediaRadar, Pathmatics for competitor spend tracking
- **Web Crawling APIs**: For real-time publisher verification
- **Compliance APIs**: CMP detection, ads.txt/sellers.json verification

### Authentication

- **Google Authorized Buyers**: SAPISIDHASH (browser session tokens)
- **BidSwitch**: OAuth2 (username/password)

---

## Success Metrics

### Data Quality

- **Enrichment Coverage**: % of deals with complete semantic metadata
- **Taxonomy Accuracy**: % of validated IAB taxonomy classifications
- **Package Coherence**: Semantic similarity scores within packages

### Business Value

- **Package Utilization**: % of packages used by buyers
- **Deal Overlap**: Average deals per package (diversity metric)
- **Buyer Satisfaction**: Feedback on package recommendations

### Performance

- **Processing Time**: Time to enrich X deals
- **LLM Cost**: Cost per deal/package processed
- **Scalability**: Maximum deals processed per run

---

## Next Steps: Implementation Roadmap

### Phase 1: Core Enrichment (Q1 2025)

1. **Implement Stage 1 Enrichment**
   - LLM inference pipeline
   - Volume context enhancement
   - IAB taxonomy validation
   - Basic publisher intelligence

2. **Implement Schema Unification**
   - Unified pre-enrichment schema
   - Field mapping and normalization
   - Validation and error handling

### Phase 2: Package Creation (Q2 2025)

1. **Implement Stage 2 Package Creation**
   - Semantic embeddings
   - K-means/GMM clustering
   - LLM package grouping
   - Basic constraint enforcement

2. **Testing & Validation**
   - Test with real Google Ads and BidSwitch deals
   - Validate package quality
   - Optimize clustering parameters

### Phase 3: Advanced Features (Q3 2025)

1. **Advanced Enrichment Strategies**
   - Multimodal intelligence
   - Temporal validation
   - Market-indexed pricing
   - Hard signal overrides

2. **Real-Time Verification Layer (Stage 1.5)**
   - Real-time publisher intelligence (web crawling)
   - Dynamic risk assessment
   - Visual site quality analysis (MFA detection)
   - Compliance verification (CMP, ads.txt, sellers.json)
   - SPO scoring and premium weighting
   - Competitor spend tracking integration (MediaRadar, Pathmatics)
   - Conversion schema enrichment
   - Market intelligence fusion

3. **Advanced Clustering**
   - Constraint-based clustering
   - Anti-package filter
   - Recursive refinement
   - Diversity/volume awareness

### Phase 4: Package Enrichment (Q4 2025)

1. **Implement Stage 3 Package Enrichment**
   - Deal aggregation
   - Health score calculation
   - LLM package recommendations

2. **Integration & Polish**
   - End-to-end pipeline testing
   - Performance optimization
   - Documentation updates

---

## Conclusion

This vision document outlines a comprehensive three-stage semantic enrichment pipeline (plus optional real-time verification layer) that transforms raw SSP deal data into semantically enriched, buyer-ready audience packages. The system leverages:

- **Multi-vendor extraction** from Google Authorized Buyers (Marketplace + Curated) and BidSwitch
- **Schema unification** to normalize vendor-specific data into consistent pre-enrichment schema
- **Semantic enrichment** using LLM inference and external data sources (Stage 1)
- **Real-time verification** (Stage 1.5 - Optional) moving from static inference to dynamic validation:
  - Real-time publisher intelligence via web crawling
  - Compliance and SPO verification (CMP, ads.txt, sellers.json)
  - Market intelligence fusion (competitor spend, performance metrics)
- **Intelligent packaging** using semantic clustering and constraint-based rules (Stage 2)
- **Package-level intelligence** with aggregated metadata and recommendations (Stage 3)

### Key Innovation: Static → Dynamic Intelligence

The addition of **Stage 1.5: Real-Time Verification Layer** represents a fundamental shift from **static inference** (predicting based on deal metadata) to **dynamic verification** (validating against the live web). This enables:

1. **Live Publisher Audits**: Real-time content analysis and risk assessment
2. **Compliance Assurance**: Automated verification of privacy regulations and supply path optimization
3. **Market Intelligence**: Fusion of platform-native data with external market signals
4. **Quality Validation**: Visual site quality analysis to detect MFA sites and low-quality inventory

The modular architecture enables incremental implementation while maintaining extensibility for future vendors and enhancement strategies. This document serves as the **north star** for implementation planning and development priorities.

---

## References

- **Stage 1 Strategies**: [STAGE1_ENRICHMENT_STRATEGIES.md](STAGE1_ENRICHMENT_STRATEGIES.md)
- **Stage 2 Advanced Clustering**: [STAGE2_ADVANCED_CLUSTERING.md](STAGE2_ADVANCED_CLUSTERING.md)
- **Package Creation**: [../packages/stage2-package-creation/README.md](../packages/stage2-package-creation/README.md)
- **Package Enrichment**: [../packages/stage3-package-enrichment/README.md](../packages/stage3-package-enrichment/README.md)
- **Three-Stage Process**: [../packages/stage2-package-creation/docs/THREE_STAGE_PROCESS.md](../packages/stage2-package-creation/docs/THREE_STAGE_PROCESS.md)
