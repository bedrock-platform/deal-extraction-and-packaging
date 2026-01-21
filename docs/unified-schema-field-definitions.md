# Unified Schema & Enrichment Field Definitions

## Overview

This document describes the unified schema used throughout the deal extraction, packaging, and enrichment pipeline. The schema supports multiple vendors (Google Authorized Buyers, Google Curated, BidSwitch) and includes both pre-enrichment and post-enrichment fields.

### Schema Versions

- **UnifiedPreEnrichmentSchema**: Normalized schema for all deals before Stage 1 enrichment
- **EnrichedDeal**: Schema for deals after Stage 1 enrichment (with semantic metadata from Phase 1 & Phase 2)

### Multi-Vendor Support

The unified schema normalizes vendor-specific data into a consistent format:
- **Google Authorized Buyers** (Marketplace)
- **Google Curated** (Packages)
- **BidSwitch**
- Future vendors...

---

## Part 1: Pre-Enrichment Schema (UnifiedPreEnrichmentSchema)

These fields are present in the unified TSV before enrichment. All vendors are normalized to this schema.

### Required Fields

#### `deal_id` (string, required)
- **Description**: Unique deal identifier
- **Example**: `"549644398148090651"`
- **Source**: Vendor-specific (e.g., Google entityId, BidSwitch deal ID)
- **Use Case**: Primary key for deal identification and deduplication

#### `deal_name` (string, required)
- **Description**: Human-readable deal name
- **Example**: `"Yahoo ROS"`, `"Premium CTV RON US - Political Accepted 2026"`
- **Source**: Vendor deal name
- **Use Case**: Display name for UI, search/filter operations

#### `source` (string, required)
- **Description**: Source vendor identifier
- **Example**: `"Google Authorized Buyers"`, `"Google Curated"`, `"BidSwitch"`
- **Source**: Normalized from vendor data
- **Use Case**: Vendor attribution, filtering by source

#### `ssp_name` (string, required)
- **Description**: SSP (Supply-Side Platform) name
- **Example**: `"Google Authorized Buyers"`, `"BidSwitch"`
- **Source**: Normalized from vendor data
- **Use Case**: SSP-level reporting and filtering

#### `format` (enum, required)
- **Description**: Creative format type
- **Valid Values**: `"video"`, `"display"`, `"native"`, `"audio"`
- **Example**: `"video"`, `"display"`
- **Source**: Vendor format field (normalized)
- **Use Case**: Format-based filtering and reporting

#### `publishers` (list[string], required, default: [])
- **Description**: List of publisher names/domains
- **Example**: `["yahoo.com", "news.com"]`
- **Source**: Vendor publisher data (may be single string or list)
- **Use Case**: Publisher-level filtering, publisher intelligence (Phase 2)

#### `floor_price` (float, required, >= 0)
- **Description**: Bid floor price (minimum bid)
- **Example**: `2.50`, `0.10`
- **Source**: Vendor pricing data
- **Use Case**: Pricing analysis, floor price filtering

#### `raw_deal_data` (dict, required)
- **Description**: Original vendor data preserved as JSON for reference
- **Example**: `{"entityId": "123", "vendor": "Google", ...}`
- **Source**: Complete vendor API response
- **Use Case**: Debugging, vendor-specific data access, future transformations

### Optional Fields

#### `inventory_type` (string | int, optional)
- **Description**: Inventory type classification
- **Valid Values**: `"apps"`, `"websites"`, `"ctv"`, `"dooh"` or numeric ID
- **Example**: `"ctv"`, `"websites"`
- **Source**: Vendor inventory type field
- **Use Case**: Inventory type filtering and reporting

#### `start_time` (string, optional)
- **Description**: Deal start time in ISO 8601 format
- **Example**: `"2026-01-01T00:00:00Z"`
- **Source**: Vendor deal timing data
- **Use Case**: Temporal signal extraction (Phase 2), deal availability filtering

#### `end_time` (string, optional)
- **Description**: Deal end time in ISO 8601 format
- **Example**: `"2026-12-31T23:59:59Z"`
- **Source**: Vendor deal timing data
- **Use Case**: Temporal signal extraction (Phase 2), deal availability filtering

#### `description` (string, optional)
- **Description**: Deal description text
- **Example**: `"Premium CTV inventory for US market"`
- **Source**: Vendor deal description
- **Use Case**: LLM enrichment context, search/filter operations

#### `volume_metrics` (object, optional)
- **Description**: Volume metrics object with nested fields
- **Structure**:
  - `bid_requests` (int, optional): Total bid requests
  - `impressions` (int, optional): Total impressions
  - `uniques` (int, optional): Unique users
  - `bid_requests_ratio` (float, optional): Bid requests per day
- **Example**: `{"bid_requests": 1000000, "impressions": 500000}`
- **Source**: Vendor volume data
- **Use Case**: Volume-based filtering and reporting
- **Note**: Flattened in TSV as `volume_metrics_bid_requests`, `volume_metrics_impressions`, etc.

#### `inventory_scale` (int, optional)
- **Description**: Unified inventory scale metric (vendor-agnostic)
- **Example**: `1000000`
- **Source**: Normalized from `bid_requests` (BidSwitch) or `impressions` (Google)
- **Use Case**: Cross-vendor volume comparison
- **Note**: See `inventory_scale_type` for metric type

#### `inventory_scale_type` (string, optional)
- **Description**: Type of `inventory_scale` metric
- **Valid Values**: `"bid_requests"`, `"impressions"`
- **Example**: `"bid_requests"` (BidSwitch), `"impressions"` (Google)
- **Source**: Determined during normalization
- **Use Case**: Understanding which metric `inventory_scale` represents

#### `schema_version` (string, optional, default: "1.0")
- **Description**: Schema version for future migrations
- **Example**: `"1.0"`
- **Source**: Schema definition
- **Use Case**: Schema evolution and migration tracking

---

## Part 2: Enrichment Fields (EnrichedDeal)

These fields are added during Stage 1 enrichment (Phase 1 & Phase 2). They extend `UnifiedPreEnrichmentSchema` with semantic metadata inferred by LLM and validation components.

### Taxonomy Fields (IAB Content Taxonomy 2.2)

Taxonomy classification using IAB Content Taxonomy 2.2, validated and auto-corrected by Phase 2 Taxonomy Validator.

#### `taxonomy.tier1` (string, optional)
- **Description**: Tier 1 category (top-level classification)
- **Example**: `"Automotive"`, `"News & Politics"`, `"Technology"`
- **Source**: LLM inference + Taxonomy Validator (Phase 2)
- **Use Case**: High-level content categorization, filtering
- **Validation**: Auto-corrected against IAB Tier 1 categories if similarity > 0.8

#### `taxonomy.tier2` (string, optional)
- **Description**: Tier 2 subcategory (mid-level classification)
- **Example**: `"Auto Parts & Accessories"`, `"Political News"`
- **Source**: LLM inference + Taxonomy Validator (Phase 2)
- **Use Case**: More specific content categorization
- **Validation**: Auto-corrected against IAB Tier 2 mappings if similarity > 0.8

#### `taxonomy.tier3` (string, optional)
- **Description**: Tier 3 specific topic (granular classification)
- **Example**: `"Auto Repair"`, `"Election Coverage"`
- **Source**: LLM inference
- **Use Case**: Granular content targeting

### Safety Fields (Brand Safety / GARM)

Brand safety metadata aligned with GARM (Global Alliance for Responsible Media) standards.

#### `safety.garm_risk_rating` (string, optional)
- **Description**: GARM risk rating classification
- **Valid Values**: `"Floor"`, `"Low"`, `"Medium"`, `"High"`
- **Example**: `"Low"`, `"Medium"`
- **Source**: LLM inference based on deal content
- **Use Case**: Brand safety filtering, risk assessment

#### `safety.family_safe` (boolean, optional)
- **Description**: Family-safe flag (suitable for all audiences)
- **Example**: `true`, `false`
- **Source**: LLM inference
- **Use Case**: Family-safe inventory filtering

#### `safety.safe_for_verticals` (list[string], optional)
- **Description**: List of verticals this deal is safe for
- **Example**: `["Finance", "Healthcare", "Education"]`
- **Source**: LLM inference
- **Use Case**: Vertical-specific brand safety filtering

### Audience Fields

Audience profile metadata inferred from deal characteristics.

#### `audience.inferred_audience` (list[string], optional, default: [])
- **Description**: Inferred audience segments
- **Example**: `["Tech Enthusiasts", "Business Professionals", "25-54"]`
- **Source**: LLM inference + Publisher Intelligence (Phase 2)
- **Use Case**: Audience targeting, demographic analysis
- **Enhancement**: Phase 2 Publisher Intelligence adds publisher-specific audience insights

#### `audience.demographic_hint` (string, optional)
- **Description**: Demographic hints (age range, income level, etc.)
- **Example**: `"25-54, High Income"`, `"18-34, Urban"`
- **Source**: LLM inference
- **Use Case**: Demographic targeting

#### `audience.audience_provenance` (string, optional, default: "Inferred")
- **Description**: Source/provenance of audience data
- **Example**: `"Inferred"`, `"Publisher Intelligence"`
- **Source**: Enrichment pipeline
- **Use Case**: Data quality tracking

### Commercial Fields

Commercial profile metadata for deal quality and pricing assessment.

#### `commercial.quality_tier` (string, optional)
- **Description**: Quality tier classification
- **Valid Values**: `"Premium"`, `"Mid-tier"`, `"RON"` (Run of Network)
- **Example**: `"Premium"`, `"RON"`
- **Source**: LLM inference based on deal characteristics
- **Use Case**: Quality-based filtering and prioritization

#### `commercial.volume_tier` (string, optional)
- **Description**: Volume tier classification
- **Valid Values**: `"High"`, `"Medium"`, `"Low"`
- **Example**: `"High"`, `"Medium"`
- **Source**: LLM inference based on volume metrics
- **Use Case**: Volume-based filtering and planning

#### `commercial.floor_price` (float, optional)
- **Description**: Floor price (may differ from pre-enrichment floor_price)
- **Example**: `2.50`
- **Source**: LLM inference or preserved from pre-enrichment
- **Use Case**: Pricing analysis

### Semantic Concepts

#### `concepts` (list[string], optional, default: [])
- **Description**: Semantic concepts/keywords extracted from deal
- **Example**: `["CTV", "Premium", "US Market", "Political"]`
- **Source**: LLM inference
- **Use Case**: Search, keyword matching, concept-based filtering

### Metadata Fields

#### `enrichment_timestamp` (string, optional)
- **Description**: When enrichment was performed (ISO 8601 format)
- **Example**: `"2026-01-21T05:27:43Z"`
- **Source**: Enrichment pipeline (automatically set)
- **Use Case**: Tracking enrichment freshness, debugging

#### `schema_version` (string, optional, default: "1.0")
- **Description**: Schema version (inherited from pre-enrichment)
- **Example**: `"1.0"`
- **Source**: Schema definition
- **Use Case**: Schema evolution tracking

---

## Phase 2 Enhancements

Phase 2 added three key enhancements to the enrichment pipeline:

### 1. Taxonomy Validator (`DEAL-202`)
- **Purpose**: Validates and auto-corrects IAB Content Taxonomy classifications
- **Method**: Fuzzy string matching using `difflib.SequenceMatcher`
- **Impact**: Improves taxonomy accuracy by correcting LLM inference errors
- **Fields Affected**: `taxonomy.tier1`, `taxonomy.tier2`

### 2. Publisher Intelligence (`DEAL-203`)
- **Purpose**: Recognizes publisher brands and enhances enrichment context
- **Method**: Brand alias matching and publisher knowledge base lookup
- **Impact**: Adds publisher-specific context to LLM prompts, improving audience inference
- **Fields Affected**: `audience.inferred_audience`, enrichment quality

### 3. Temporal Signal Extraction (`DEAL-204`)
- **Purpose**: Analyzes temporal patterns (start_time/end_time) for seasonal relevance
- **Method**: Date parsing, seasonal keyword detection, temporal mismatch detection
- **Impact**: Adds temporal context to LLM prompts, improves seasonal deal identification
- **Fields Affected**: Enrichment quality (via enhanced prompts), `concepts` (temporal keywords)

---

## TSV Export Structure

When exported to TSV, nested objects are flattened:

### Pre-Enrichment TSV Columns
- `deal_id`, `deal_name`, `source`, `ssp_name`, `format`, `publishers` (JSON array), `floor_price`
- `inventory_type`, `start_time`, `end_time`, `description`
- `volume_metrics_bid_requests`, `volume_metrics_impressions`, `volume_metrics_uniques`, `volume_metrics_bid_requests_ratio`
- `inventory_scale`, `inventory_scale_type`
- `raw_deal_data` (JSON string)
- `schema_version`

### Enriched TSV Columns (Additional)
- `taxonomy_tier1`, `taxonomy_tier2`, `taxonomy_tier3`
- `safety_garm_risk_rating`, `safety_family_safe`, `safety_safe_for_verticals` (JSON array)
- `audience_inferred_audience` (JSON array), `audience_demographic_hint`, `audience_audience_provenance`
- `commercial_quality_tier`, `commercial_volume_tier`, `commercial_floor_price`
- `concepts` (JSON array)
- `enrichment_timestamp`

---

## Usage Examples

### Filtering by Taxonomy
```python
# Filter for Automotive deals
filtered = [deal for deal in deals if deal.taxonomy and deal.taxonomy.tier1 == "Automotive"]
```

### Brand Safety Filtering
```python
# Filter for family-safe, low-risk deals
safe_deals = [
    deal for deal in deals
    if deal.safety
    and deal.safety.family_safe
    and deal.safety.garm_risk_rating in ["Floor", "Low"]
]
```

### Volume-Based Filtering
```python
# Filter for high-volume, premium deals
premium_high_volume = [
    deal for deal in deals
    if deal.commercial
    and deal.commercial.quality_tier == "Premium"
    and deal.commercial.volume_tier == "High"
]
```

### Cross-Vendor Volume Comparison
```python
# Compare inventory scale across vendors
for deal in deals:
    if deal.inventory_scale:
        print(f"{deal.deal_name}: {deal.inventory_scale} {deal.inventory_scale_type}")
```

---

## Related Documentation

- **[field-definitions.md](./field-definitions.md)**: Legacy Google Ads Marketplace TSV structure (historical reference)
- **[authentication-architecture.md](./authentication-architecture.md)**: Authentication setup and configuration
- **[../plans/semantic-enrichment-pipeline/PLAN.md](../plans/semantic-enrichment-pipeline/PLAN.md)**: Enrichment pipeline architecture and phases

---

## Schema Evolution

### Version 1.0 (Current)
- Initial unified schema
- Phase 1 enrichment fields
- Phase 2 enhancements (Taxonomy Validator, Publisher Intelligence, Temporal Signals)

### Future Versions
- Schema migrations will be tracked via `schema_version` field
- Breaking changes will be documented in release notes
