# TSV Field Definitions

This document provides comprehensive definitions for all fields exported in the inventory TSV file.

---

## Identity & Metadata Fields

### Name
- **Type:** String
- **Description:** Display name of the marketplace package/deal
- **Example:** `"Yahoo ROS"`
- **Source:** `entity.entityName` from search API

### ID
- **Type:** String (Numeric)
- **Description:** Unique identifier for the marketplace package/deal
- **Example:** `"549644398148090651"`
- **Source:** `entity.entityId` from search API
- **Use Case:** Primary key for joining with other data sources

### Entity Category
- **Type:** String
- **Description:** Type of entity (typically "Marketplace Package")
- **Example:** `"Marketplace Package"`
- **Source:** `entity.entityCategory` (formatted from `MARKETPLACE_PACKAGE`)

### Description
- **Type:** String
- **Description:** Human-readable description of the package/deal
- **Example:** `"Yahoo O&O ROS"`
- **Source:** `entity.description` from search API

### Publisher
- **Type:** String
- **Description:** Display name of the publisher who created/owns this package
- **Example:** `"Yahoo"`
- **Source:** `entity.publisherSummaries[0].displayName` or hydrated `publisherSummary.displayName`

### Publisher Account ID
- **Type:** String (Numeric)
- **Description:** Google account ID of the publisher
- **Example:** `"334696666"`
- **Source:** `entity.publisherSummaries[0].accountId` or hydrated `publisherSummary.accountId`
- **Use Case:** Joining with publisher metadata from other sources

---

## Package Metadata

### Package Type
- **Type:** String
- **Description:** Type of marketplace package (Public, Private, etc.)
- **Example:** `"Public"`
- **Source:** `entity.marketplacePackageType` (formatted from `MARKETPLACE_PACKAGE_TYPE_PUBLIC`)

### Content Type
- **Type:** String
- **Description:** Type of content in the package (Video, Display, Other, etc.)
- **Example:** `"Other"`
- **Source:** `forecast.contentType` (formatted from `CONTENT_TYPE_*`)

### Created By
- **Type:** String
- **Description:** Publisher name who created this package
- **Example:** `"Yahoo"`
- **Source:** Hydrated from `marketplacePackages/{id}` endpoint → `publisherSummary.displayName`

### Floor Price (USD)
- **Type:** String (Decimal)
- **Description:** Minimum CPM price set for this package (if any)
- **Example:** `"0.75"` or `""` (if not set)
- **Source:** Hydrated from `marketplacePackages/{id}` endpoint → `priorityFloorPrice.units` + `nanos`
- **Note:** Empty string if no floor price is set

---

## Forecast Metrics

### Impressions
- **Type:** String (Numeric)
- **Description:** Filtered weekly forecast impressions (based on applied filters)
- **Example:** `"22300000000"` (22.3 billion)
- **Source:** `forecast.metrics.impressions`
- **Note:** This is the filtered forecast, not total available inventory

### Uniques
- **Type:** String (Numeric)
- **Description:** Filtered weekly forecast unique users
- **Example:** `"92060000"` (92.06 million)
- **Source:** `forecast.metrics.uniqueUsers`

### Total Impressions
- **Type:** String (Numeric)
- **Description:** Total weekly forecast impressions (unfiltered)
- **Example:** `"22310000000"`
- **Source:** `forecast.totalMetrics.impressions`
- **Note:** May be slightly higher than filtered `Impressions` due to rounding

### Total Uniques
- **Type:** String (Numeric)
- **Description:** Total weekly forecast unique users (unfiltered)
- **Example:** `"92060000"`
- **Source:** `forecast.totalMetrics.uniqueUsers`

---

## CPM Pricing

### Avg CPM (USD)
- **Type:** String (Decimal)
- **Description:** Weighted average CPM across all cost histogram buckets
- **Example:** `"1.25"`
- **Source:** Calculated from `costHistogramMetrics` (weighted by impressions)
- **Formula:** `sum(cpm * impressions) / sum(impressions)`

### Min CPM (USD)
- **Type:** String (Decimal)
- **Description:** Minimum CPM value from cost histogram
- **Example:** `"0.00"`
- **Source:** Minimum value from `costHistogramMetrics[].cpmUsdMicros`

### Max CPM (USD)
- **Type:** String (Decimal)
- **Description:** Maximum CPM value from cost histogram
- **Example:** `"3.75"`
- **Source:** Maximum value from `costHistogramMetrics[].cpmUsdMicros`

### Median CPM (USD)
- **Type:** String (Decimal)
- **Description:** Median CPM value from cost histogram
- **Example:** `"1.50"`
- **Source:** Calculated median from `costHistogramMetrics[].cpmUsdMicros`

---

## Primary Breakdown Fields (Flat Columns)

These fields show the **#1 top value** for each breakdown category. Full breakdowns are available in the JSON columns below.

### Primary Device
- **Type:** String
- **Description:** Top device type by impressions
- **Example:** `"Desktop"`
- **Possible Values:** `"Desktop"`, `"Mobile"`, `"Tablet"`, `"Connected TV"`

### Primary Device Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary device
- **Example:** `"16860000000"`

### Primary Device %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary device
- **Example:** `"75.6"`

### Primary Request Format
- **Type:** String
- **Description:** Top request format by impressions
- **Example:** `"Display and Video"`
- **Possible Values:** `"Display and Video"`, `"Display only"`, `"Video only"`, `"Audio and Video"`, `"Audio only"`

### Primary Request Format Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary request format
- **Example:** `"13580000000"`

### Primary Request Format %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary request format
- **Example:** `"60.9"`

### Primary Content Vertical
- **Type:** String
- **Description:** Top content vertical category by impressions
- **Example:** `"Arts & Entertainment"`
- **Possible Values:** Various categories like `"News"`, `"Finance"`, `"Sports"`, etc.

### Primary Content Vertical Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary content vertical
- **Example:** `"17600000000"`

### Primary Content Vertical %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary content vertical
- **Example:** `"78.9"`

### Primary Video Duration
- **Type:** String
- **Description:** Top video duration range by impressions
- **Example:** `"Up to 15s"`
- **Possible Values:** `"Up to 15s"`, `"From 16s to 20s"`, `"From 21s to 30s"`, `"From 31s to 60s"`, etc.

### Primary Video Duration Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary video duration
- **Example:** `"13700000000"`

### Primary Video Duration %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary video duration
- **Example:** `"61.4"`

### Primary Gender
- **Type:** String
- **Description:** Top gender demographic by impressions
- **Example:** `"Male"`
- **Possible Values:** `"Male"`, `"Female"`, `"Unknown"`

### Primary Gender Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary gender
- **Example:** `"13390000000"`

### Primary Gender %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary gender
- **Example:** `"60.0"`

### Primary Age Range
- **Type:** String
- **Description:** Top age range demographic by impressions
- **Example:** `"45-54"`
- **Possible Values:** `"18-24"`, `"25-34"`, `"35-44"`, `"45-54"`, `"55-64"`, `"65+"`, `"Unknown"`

### Primary Age Range Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary age range
- **Example:** `"5035000000"`

### Primary Age Range %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary age range
- **Example:** `"22.6"`

### Primary Country
- **Type:** String
- **Description:** Top country by impressions
- **Example:** `"United States"`
- **Possible Values:** Country names (e.g., `"United States"`, `"Taiwan"`, `"United Kingdom"`)

### Primary Country Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary country
- **Example:** `"14300000000"`

### Primary Country %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary country
- **Example:** `"64.1"`

### Primary Ad Size
- **Type:** String
- **Description:** Top ad size (inventory size) by impressions
- **Example:** `"300x250"`
- **Possible Values:** Various ad dimensions like `"300x250"`, `"320x50"`, `"728x90"`, `"interstitial"`, `"native"`, etc.

### Primary Ad Size Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary ad size
- **Example:** `"15400000000"`

### Primary Ad Size %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary ad size
- **Example:** `"69.1"`

### Primary Domain
- **Type:** String
- **Description:** Top website domain by impressions
- **Example:** `"yahoo.com"`
- **Possible Values:** Domain names (e.g., `"yahoo.com"`, `"mail.yahoo.com"`, `"news.yahoo.com"`)

### Primary Domain Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary domain
- **Example:** `"9190000000"`

### Primary Domain %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary domain
- **Example:** `"41.2"`

### Primary App
- **Type:** String
- **Description:** Top mobile app by impressions
- **Example:** `"Yahoo Mail"`
- **Possible Values:** Mobile app names/IDs (e.g., `"Yahoo Mail"`, `"com.yahoo.mobile.client.android.mail"`)

### Primary App Impressions
- **Type:** String (Numeric)
- **Description:** Impressions for the primary app
- **Example:** `"768000000"`

### Primary App %
- **Type:** String (Decimal)
- **Description:** Percentage of total impressions for primary app
- **Example:** `"3.4"`

---

## Nested JSON Breakdown Fields

These fields contain **complete breakdowns** as JSON strings. Each JSON object maps slice names to impression counts.

### Request_Format_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of request formats with impression counts
- **Example:** `{"Display and Video": "13580000000", "Display only": "8581000000", "Video only": "134100000"}`
- **Format:** `{"slice_name": "impressions", ...}`
- **Use Case:** Analyze format distribution beyond the primary value

### Gender_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of gender demographics with impression counts
- **Example:** `{"Male": "13390000000", "Female": "7472000000", "Unknown": "1440000000"}`
- **Use Case:** Gender targeting analysis

### Age_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of age ranges with impression counts
- **Example:** `{"45-54": "5035000000", "55-64": "4805000000", "65+": "3934000000", "35-44": "1982000000"}`
- **Use Case:** Age targeting analysis

### Device_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of device types with impression counts
- **Example:** `{"Desktop": "16860000000", "Mobile": "5068000000", "Tablet": "372500000"}`
- **Use Case:** Device targeting and optimization

### Country_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of countries with impression counts
- **Example:** `{"United States": "14300000000", "Taiwan": "1332000000", "United Kingdom": "906300000", "Canada": "648900000"}`
- **Use Case:** Geographic targeting, brand safety by region
- **Note:** Contains all countries with impressions > 0 (can be 100+ countries)

### Inventory_Size_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of ad sizes (inventory sizes) with impression counts
- **Example:** `{"300x250": "15400000000", "320x50": "3800000000", "300x600": "2600000000", "728x90": "1360000000"}`
- **Use Case:** Ad size matching, inventory capacity planning
- **Note:** Contains all ad sizes with impressions > 0 (can be 200+ sizes)

### Content_Vertical_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of content verticals with impression counts
- **Example:** `{"Arts & Entertainment": "17600000000", "Internet & Telecom": "16600000000", "News": "8450000000"}`
- **Use Case:** Content category analysis, brand safety filtering

### Video_Duration_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of video duration ranges with impression counts
- **Example:** `{"Up to 15s": "13700000000", "From 16s to 20s": "13600000000", "From 21s to 30s": "13600000000"}`
- **Use Case:** Video ad length optimization

### Domain_Name_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of website domains with impression counts
- **Example:** `{"yahoo.com": "9190000000", "mail.yahoo.com": "5310000000", "news.yahoo.com": "2760000000", "aol.com": "2380000000"}`
- **Use Case:** Brand safety filtering, publisher domain analysis, inventory transparency
- **Note:** Contains top domains (typically top 20 per deal)

### App_ID_Breakdown
- **Type:** JSON String
- **Description:** Complete breakdown of mobile apps with impression counts
- **Example:** `{"Yahoo Mail": "768000000", "com.yahoo.mobile.client.android.mail": "500000000"}`
- **Use Case:** Mobile app targeting, brand safety filtering
- **Note:** Contains top apps (typically top 20 per deal)

---

## Data Types & Notes

### Numeric Fields
- All impression counts are stored as **strings** to preserve precision for very large numbers
- Convert to integers/floats in your analysis: `int(row["Impressions"])`
- CPM values are stored as **decimal strings** (e.g., `"1.25"`)

### JSON Fields
- JSON fields are stored as **strings** containing valid JSON
- Parse in your code: `json.loads(row["Country_Breakdown"])`
- Empty breakdowns are represented as `"{}"` (empty JSON object)

### Empty Values
- Missing values are represented as **empty strings** `""`
- JSON fields default to `"{}"` if no breakdown exists
- Numeric fields default to `"0"` if no data exists

### Data Sources
- **Search API:** Most fields come from `inventoryViews:search` endpoint
- **Hydration API:** `Created By` and `Floor Price` come from `marketplacePackages/{id}` endpoint
- **Calculated:** CPM statistics are calculated from `costHistogramMetrics`

---

## Usage Examples

### Filtering by Primary Values
```python
# Filter deals where Desktop is primary device
desktop_deals = df[df["Primary Device"] == "Desktop"]
```

### Parsing JSON Breakdowns
```python
import json

# Get country breakdown for a specific deal
country_data = json.loads(df.iloc[0]["Country_Breakdown"])
# Returns: {"United States": "14300000000", "Taiwan": "1332000000", ...}

# Find deals with impressions in Taiwan
taiwan_deals = df[df["Country_Breakdown"].str.contains("Taiwan")]
```

### Querying in BigQuery
```sql
-- Extract specific country impressions from JSON
SELECT 
  Name,
  JSON_EXTRACT_SCALAR(Country_Breakdown, '$.United States') as usa_impressions
FROM inventory_table
WHERE JSON_EXTRACT_SCALAR(Country_Breakdown, '$.United States') IS NOT NULL
```

---

**Last Updated:** 2026-01-20  
**TSV Version:** Hybrid Nested Schema (v2)
