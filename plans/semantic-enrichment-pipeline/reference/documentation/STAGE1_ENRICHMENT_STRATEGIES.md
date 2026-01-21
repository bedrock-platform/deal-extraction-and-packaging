# Stage 1: Individual Deal Enrichment - Handling Sparse BidSwitch Data

## Overview

This document details how Stage 1 enrichment handles sparse BidSwitch deal data and enriches it with semantic information using multi-layered inference strategies.

## The Problem: Sparse BidSwitch Data

BidSwitch deals include minimal semantic fields:

**Available Fields:**
- `deal_id`, `display_name`, `description` (often null)
- `publishers` (array of strings, often placeholder text)
- `creative_type` (e.g., "video", "display", "native", "audio")
- `inventory_highlights` (array of strings, often empty)
- `price` (bid floor as decimal string)
- Basic forecasting metrics (`bid_requests`, `bid_requests_by_categories`)
- **Hidden Signals** (often under-utilized):
  - `inventory_image` (URL to visual representation of inventory)
  - `weekly_total_avails`, `weekly_unique_avails` (availability metrics, often null)
  - `auction_type` (1=First Price, 2=Second Price)
  - `ssp_id` (SSP identifier, e.g., 7=Sovrn)
  - `bid_requests_ratio` (calculated: bid_requests / days_active)
  - `start_time`, `end_time` (temporal signals)

**Missing Fields:**
- ❌ IAB Content Taxonomy (Tier 1, 2, 3)
- ❌ Brand Safety ratings (GARM risk rating, family-safe flag)
- ❌ Audience segments (inferred audiences, demographic hints)
- ❌ Content categories
- ❌ Publisher metadata (domains, categories, quality indicators)
- ❌ Volume tier classifications
- ❌ Quality tier classifications

## The Solution: Multi-Layered Semantic Inference

Stage 1 uses a combination of strategies to infer semantic metadata from sparse BidSwitch data:

### 1. LLM-Based Inference (Primary Strategy)

The codebase uses Google Gemini 2.5 Flash to infer semantic metadata from sparse fields.

**Input Format:**
```python
deal_data = {
    "deal_id": deal.get("dealId"),
    "deal_name": deal.get("displayName") or raw_data.get("display_name", ""),
    "ssp_name": deal.get("sourceSsp"),
    "inventory_type": deal.get("inventoryType"),  # 1=Apps, 2=Websites, 3=CTV, 4=DOOH
    "creative_type": deal.get("creativeType"),
    "country": extract_country_from_deal(deal),
    "publishers": deal.get("publishers") or raw_data.get("publishers", []),
    "bidfloor": extract_bidfloor(deal),
    "description": raw_data.get("description") or raw_data.get("display_name", ""),
    # ⚠️ Currently NOT included but should be (see Advanced Strategies):
    # "inventory_image_url": deal.get("inventory_image"),
    # "auction_type": deal.get("auction_type"),
    # "ssp_id": deal.get("ssp_id"),
    # "weekly_total_avails": deal.get("weekly_total_avails"),
    # "weekly_unique_avails": deal.get("weekly_unique_avails"),
    # "bid_requests_ratio": calculate_bid_requests_ratio(deal),
}
```

**LLM Infers:**
- **IAB Taxonomy** (Tier 1/2/3) from deal names, publishers, and creative type
- **Brand Safety** (GARM ratings) from publisher reputation and inventory type
- **Audience Segments** from publisher brands and content type
- **Quality Tiers** from bid floor prices and publisher names
- **Volume Tiers** from commercial context

### 2. Volume Context Enhancement (Critical Addition)

Adds Index Exchange volume data to provide commercial context for better LLM inference.

**Implementation:**
```python
# Get volume context from Index Exchange inventory research data
volume_lookup = get_volume_lookup()
volume_context = ""
if volume_lookup:
    try:
        volume_context = "\n\n" + volume_lookup.format_volume_context(deal_data)
    except Exception as e:
        # Silently fail if volume lookup fails (non-critical)
        pass
```

**Volume Lookup Process:**
The `VolumeLookup` class matches publisher names from BidSwitch deals to Index Exchange CSV data:

```python
def format_volume_context(self, package_data: Dict[str, any]) -> str:
    """
    Format volume context for LLM prompt.
    
    Maintains backward compatibility with existing enrichment pipeline.
    
    Args:
        package_data: Package data dictionary
        
    Returns:
        Formatted volume context string
    """
    context_parts = []
    
    # Try to get volume from publishers field
    publishers = package_data.get('publishers', [])
    if isinstance(publishers, str):
        publishers = [p.strip() for p in publishers.split(',')]
    
    if publishers:
        for pub_name in publishers[:3]:  # Limit to top 3
            volume_data = self.get_publisher_volume(pub_name)
            if volume_data and volume_data.get('volume'):
                line = f"Publisher '{volume_data['name']}': {volume_data['volume']:,} daily avails"
                if volume_data.get('stv_volume'):
                    line += f" (CTV: {volume_data['stv_volume']:,})"
                if volume_data.get('percent'):
                    line += f" ({volume_data['percent']})"
                context_parts.append(line)
```

**Example Output:**
```
Commercial Liquidity Context:
  • Publisher 'Paramount+': 2,500,000,000 daily avails (CTV: 1,800,000,000) (12.5%)
  • Publisher 'Disney+': 1,800,000,000 daily avails (CTV: 1,500,000,000) (9.0%)
```

**Benefits:**
- Helps LLM assess volume tiers (High/Medium/Low)
- Provides commercial viability indicators
- Indicates publisher quality/reputation
- Enables better quality tier inference

### 3. Publisher Name Intelligence

Publisher names provide semantic signals that the LLM uses for inference:

**Publisher Patterns:**
- **"Paramount+", "Disney+", "ESPN"** → Entertainment/CTV
- **"CNN", "BBC", "Reuters"** → News/Information
- **"Tubi", "Pluto TV"** → Streaming/CTV
- **"Forbes", "Wall Street Journal"** → Finance/Business

**LLM Uses Publisher Names To Infer:**
- **Content Taxonomy**: 
  - "Paramount+" → "Arts & Entertainment" → "Television" → "Streaming"
  - "CNN" → "News & Information" → "Television" → "News"
- **Brand Safety**: 
  - Major broadcasters (CNN, BBC) → Low risk
  - Premium publishers → Low risk
- **Audience**: 
  - "Disney+" → "Cord-cutters", "Streaming subscribers", "Family audiences"
  - "CNN" → "News consumers", "Informed citizens"

### 4. Creative & Inventory Type Inference

The codebase infers inventory type from sparse fields:

**Inference Logic:**
```python
# Infer inventory type from deal metadata
inventory_highlights = deal.get("inventory_highlights", [])
inventory_highlights_str = " ".join(str(h).lower() for h in inventory_highlights)
creative_type_lower = creative_type_raw.lower()

# Check for CTV indicators
if "ctv" in inventory_highlights_str or "connected tv" in inventory_highlights_str:
    inventory_type_id = 3  # CTV
elif creative_type_lower == "video" and "ctv" in deal.get("display_name", "").lower():
    inventory_type_id = 3  # CTV
elif creative_type_lower == "video":
    inventory_type_id = 3  # CTV (default for video)
else:
    inventory_type_id = 2  # Websites (default)
```

**Mapping:**
- `creative_type == "video"` + CTV indicators → CTV inventory
- `creative_type == "display"` → Website inventory
- `creative_type == "native"` → Website/Mobile inventory
- Inventory type + publisher names → Content taxonomy

### 5. Bid Floor Price Analysis

Bid floor prices indicate quality and help infer commercial tiers:

**Price-to-Quality Mapping:**
- **High floor prices ($10+)** → Premium inventory
- **Mid-range prices ($2-$10)** → Mid-tier inventory
- **Low floor prices ($0.50-$2)** → Mid-tier/RON inventory
- **Very low prices (<$0.50)** → RON inventory

**LLM Uses Bid Floor To Infer:**
- **Quality Tiers**: Premium/Mid-tier/RON
- **Commercial Viability**: Higher floors = more premium
- **Publisher Reputation**: Premium publishers command higher floors

**⚠️ Current Limitation**: Floor prices are analyzed in isolation. See [Advanced Strategies](#advanced-strategies) for market-indexed pricing analysis.

### 6. IAB Taxonomy Validation & Auto-Correction

After LLM inference, the taxonomy is validated and auto-corrected using IAB taxonomy validator:

**Validation Process:**
```python
# Validate and auto-correct taxonomy values using IAB validator
taxonomy_raw = enrichment.get("taxonomy", {})
tier1_raw = taxonomy_raw.get("tier1") or ""
tier2_raw = taxonomy_raw.get("tier2") or ""
tier3_raw = taxonomy_raw.get("tier3") or ""

# Get validator instance
validator = get_taxonomy_validator()

# Convert IAB codes to names if needed (e.g., "IAB26" → "Sports")
def convert_code_to_name(code_or_name: str, tier: int = 1) -> Tuple[str, Optional[str]]:
    """
    Convert IAB code to name if it's a code, otherwise return as-is.
    Handles formats like "IAB26", "26", "IAB3 Business".
    """
    if not code_or_name or not validator:
        return (code_or_name or "", None)
    
    # Check if it's an IAB code format
    if code_or_name.upper().startswith("IAB"):
        parts = code_or_name.upper().replace("IAB", "").strip().split(None, 1)
        numeric_id = parts[0]
        
        if numeric_id.isdigit():
            entry = validator.get_by_id(numeric_id)
            if entry:
                tier_name = entry.get("name", code_or_name)
                return (tier_name, parts[1].strip() if len(parts) > 1 else None)
    elif code_or_name.isdigit():
        entry = validator.get_by_id(code_or_name)
        if entry:
            return (entry.get("name", code_or_name), None)
    
    return (code_or_name, None)

# Auto-correct taxonomy
if validator and tier1_raw:
    corrected_tier1, corrected_tier2, corrected_tier3 = validator.auto_correct_taxonomy(
        tier1_raw, tier2_raw, tier3_raw
    )
```

**Validation Ensures:**
- ✅ Valid IAB taxonomy classifications
- ✅ Auto-correction of typos/variations
- ✅ Fallback to closest valid category if needed
- ✅ Conversion of IAB codes to names (e.g., "IAB26" → "Sports")

## Complete Enrichment Flow

```
┌─────────────────────────────────────────────────────────────┐
│ BidSwitch Deal (Sparse)                                    │
│                                                             │
│ • deal_name: "Sovrn_N365_Adform"                           │
│ • publishers: ["CNN", "BBC"]                               │
│ • creative_type: "video"                                  │
│ • inventory_type: 3 (CTV)                                  │
│ • bidfloor: 5.50                                           │
│ • bid_requests: 339489613748                               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 1: Extract & Format Deal Data                          │
│                                                             │
│ • Normalize field names                                     │
│ • Extract publishers list                                   │
│ • Parse bid floor price                                     │
│ • Infer inventory type                                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 2: Add Volume Context                                  │
│                                                             │
│ • Lookup publisher volumes from Index Exchange              │
│ • Format volume context for LLM                             │
│                                                             │
│ Example:                                                    │
│   Publisher 'CNN': 500M daily avails                       │
│   Publisher 'BBC': 300M daily avails                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 3: LLM Inference (Google Gemini 2.5 Flash)            │
│                                                             │
│ Input: Deal data + Volume context                           │
│                                                             │
│ LLM Infers:                                                 │
│ • Taxonomy: "News & Information" → "Television" → "News"   │
│ • Safety: "Low" (major broadcasters)                         │
│ • Audience: ["News consumers", "Informed citizens"]         │
│ • Quality: "Premium" (high floor + major publishers)       │
│ • Volume: "High" (based on volume context)                 │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Step 4: Validate & Auto-Correct Taxonomy                    │
│                                                             │
│ • IAB taxonomy validation                                   │
│ • Auto-correct typos/variations                             │
│ • Convert IAB codes to names                                │
│ • Fallback to closest valid category                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ Enriched Deal (Rich Semantic Metadata)                      │
│                                                             │
│ {                                                           │
│   "deal_id": "Sovrn_N365_Adform",                          │
│   "deal_name": "Sovrn_N365_Adform",                        │
│   "ssp_name": "BidSwitch",                                  │
│   "format": "video",                                         │
│   "taxonomy": {                                             │
│     "tier1": "News & Information",                          │
│     "tier2": "Television",                                  │
│     "tier3": "News"                                         │
│   },                                                        │
│   "safety": {                                               │
│     "garm_risk_rating": "Low",                               │
│     "family_safe": true                                     │
│   },                                                        │
│   "audience": {                                             │
│     "inferred_audience": ["News consumers"],                 │
│     "demographic_hint": "25-54, High Income"                │
│   },                                                        │
│   "commercial": {                                            │
│     "quality_tier": "Premium",                              │
│     "volume_tier": "High",                                  │
│     "floor_price": 5.50                                     │
│   },                                                        │
│   "publishers": ["CNN", "BBC"]                              │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
```

## Key Strategies Summary

### 1. Multi-Signal Inference
- Combines deal name, publishers, creative type, inventory type, and bid floor
- Uses all available signals for robust inference

### 2. External Data Enhancement
- Volume context from Index Exchange provides commercial signals
- Helps LLM assess volume tiers and publisher quality

### 3. Publisher Intelligence
- Recognizes publisher brand patterns
- Maps publishers to content categories and safety ratings

### 4. Type Inference
- Infers inventory type from creative type and deal metadata
- Maps inventory types to content taxonomy

### 5. Price Analysis
- Uses bid floor prices to infer quality tiers
- Higher floors indicate premium inventory

### 6. Validation & Correction
- Validates taxonomy against IAB standards
- Auto-corrects typos and variations
- Ensures data quality

## Integration with Pipeline

**Stage 1 Input:**
- Raw BidSwitch deals (sparse data)

**Stage 1 Output:**
- Enriched deals with taxonomy, safety, audience, commercial metadata

**Stage 2 Input:**
- Enriched deals from Stage 1

**Stage 3 Input:**
- Packages with deal IDs + enriched deals

## Best Practices

1. **Always Add Volume Context**: Volume context significantly improves LLM inference quality
2. **Validate Taxonomy**: Always validate and auto-correct taxonomy after LLM inference
3. **Handle Missing Publishers**: Use deal names and creative types when publishers are missing
4. **Infer Inventory Type**: Don't rely solely on API fields; infer from multiple signals
5. **Price Analysis**: Use bid floor prices as quality indicators
6. **Publisher Matching**: Use fuzzy matching for publisher names (handles variations)

## Limitations

1. **Sparse Data**: Some deals have minimal information (null descriptions, placeholder publishers)
2. **Publisher Matching**: Publisher name variations can cause volume lookup failures
3. **LLM Variability**: LLM inference may vary slightly between runs
4. **Missing Volume Data**: Not all publishers have volume data in Index Exchange

## Advanced Strategies (Recommended Enhancements)

The following strategies leverage "hidden signals" in BidSwitch data that are currently under-utilized:

### 7. Multimodal Intelligence (`inventory_image`)

**The Opportunity:** BidSwitch API provides `inventory_image` URLs that show visual representations of the inventory.

**Current State:** ❌ Not utilized - images are stored in `raw_deal_data` but not analyzed

**Proposed Enhancement:**
- Pass `inventory_image` URL to **Gemini 2.0 Flash/Pro** (multimodal)
- LLM can visually assess:
  - High-quality news site vs. "Made-for-Advertising" (MFA) site
  - Specialized content (sports blog, tech site) vs. generic content
  - Visual quality indicators (professional design, brand presence)
- Adds **"Visual Quality Tier"** that text alone cannot capture

**Example:**
```python
# Enhanced deal_data for LLM
deal_data = {
    # ... existing fields ...
    "inventory_image_url": deal.get("inventory_image"),  # NEW
}

# LLM prompt enhancement:
# "Analyze the inventory_image URL to assess visual quality and content type.
#  Distinguish between premium publishers and MFA sites."
```

**Benefits:**
- Catches MFA sites that text analysis might miss
- Provides visual quality signals for brand safety
- Enhances taxonomy inference (e.g., "professional news site" vs. "blog")

### 8. Availability & Reach Metrics

**The Opportunity:** Fields like `weekly_total_avails` and `weekly_unique_avails` are often null but critical when populated.

**Current State:** ⚠️ Extracted but not used for enrichment

**Proposed Enhancement:**
- Calculate **"Scarcity vs. Scale"** ratio:
  - High unique avails + low bid floor → "High Reach / Efficiency" package
  - Low unique avails + high floor → "Elite / Premium" inventory
- Use for Stage 3 (Package-Level Enrichment) volume aggregation
- Helps distinguish between broad-reach and premium inventory

**Example Logic:**
```python
if weekly_unique_avails and bidfloor:
    if weekly_unique_avails > 10_000_000 and bidfloor < 2.0:
        reach_tier = "High Reach / Efficiency"
    elif weekly_unique_avails < 1_000_000 and bidfloor > 5.0:
        reach_tier = "Elite / Premium"
    else:
        reach_tier = "Standard"
```

### 9. Auction Type & Floor Dynamics

**The Opportunity:** `auction_type` (1=First Price, 2=Second Price) provides commercial signals.

**Current State:** ⚠️ Extracted but not used for commercial tiering

**Proposed Enhancement:**
- First Price auctions (`auction_type: 1`) are more competitive
- A $3.82 floor in First Price auction for "Sports" (World Cup) is a stronger premium signal than RON floor
- Use auction type to adjust commercial tier assessment

**Example:**
```python
# Enhanced commercial tiering
if auction_type == 1:  # First Price
    # More competitive, floor price is stronger signal
    if bidfloor > 3.0:
        commercial_tier = "Premium"  # High confidence
elif auction_type == 2:  # Second Price
    # Less competitive, floor price is weaker signal
    if bidfloor > 3.0:
        commercial_tier = "Mid-tier"  # Lower confidence
```

### 10. Temporal & Event Layer

**The Opportunity:** Deal names often contain temporal/event references (e.g., "WorldCup_2022") but `start_time` may be later.

**Current State:** ❌ Not checked - temporal relevance not validated

**Proposed Enhancement:**
- Check for **Temporal Relevance**:
  - If deal name contains past event ("World Cup 2022") but is active in 2026 → "Legacy" or "Reused ID"
  - Should be flagged as "Evergreen Sports Content" or "Audience Extension" rather than "Live Sports"
- Prevents inaccurate enrichment (e.g., enriching as "Live Sports" when it's legacy content)

**Example:**
```python
import re
from datetime import datetime

def check_temporal_relevance(deal_name: str, start_time: str) -> str:
    """Check if deal name matches temporal context."""
    # Extract year from deal name
    year_match = re.search(r'20\d{2}', deal_name)
    if year_match:
        deal_year = int(year_match.group())
        start_year = datetime.fromisoformat(start_time.replace('Z', '+00:00')).year
        
        if deal_year < start_year - 1:
            return "legacy"  # Past event, likely reused ID
        elif deal_year == start_year:
            return "current"  # Current event
        else:
            return "future"  # Future event
    return "unknown"
```

### 11. Cross-Referencing Publisher Strings

**The Opportunity:** Many "Publisher" strings in BidSwitch are IDs or parent companies (e.g., "Sovrn", "contact sovrn").

**Current State:** ⚠️ Basic publisher matching, but parent company mapping not utilized

**Proposed Enhancement:**
- Build lookup table for parent companies → inventory profiles
- If publisher says "contact sovrn", use `ssp_id` and `inventory_highlights` as primary anchor
- Map SSP IDs to typical inventory profiles:
  - `ssp_id: 7` (Sovrn) + `creative_type: "display"` → High confidence for "Display/Web" inventory
  - Use SSP reputation for brand safety inference

**Example:**
```python
SSP_INVENTORY_PROFILES = {
    7: {  # Sovrn
        "typical_inventory": "Websites",
        "quality_tier": "Mid-tier",
        "brand_safety": "Moderate"
    },
    52: {  # Sonobi
        "typical_inventory": "Websites",
        "quality_tier": "Mid-tier",
        "brand_safety": "Moderate"
    },
    # ...
}

# Use SSP profile when publisher is placeholder
if publishers == ["contact sovrn"] or publishers == ["Please reach out for list of publishers"]:
    ssp_profile = SSP_INVENTORY_PROFILES.get(ssp_id, {})
    # Use SSP profile as anchor for inference
```

### 12. Competitive "Clutter" Analysis

**The Opportunity:** Use `bid_requests_ratio` (bid_requests / days_active) to assess competitive context.

**Current State:** ⚠️ Calculated but not used for enrichment

**Proposed Enhancement:**
- High `bid_requests_ratio` + low floor → "Broad Reach" (low relevance, high competition)
- High `bid_requests_ratio` + high floor + specific keywords → "Contextual Premium"
- Low `bid_requests_ratio` + high floor → "Niche Premium"

**Example:**
```python
# Competitive context analysis
if bid_requests_ratio:
    if bid_requests_ratio > 100_000_000 and bidfloor < 1.0:
        competitive_context = "Broad Reach / High Competition"
        quality_tier = "RON"  # Low relevance
    elif bid_requests_ratio > 100_000_000 and bidfloor > 3.0 and inventory_highlights:
        competitive_context = "Contextual Premium"
        quality_tier = "Premium"  # High relevance
    elif bid_requests_ratio < 10_000_000 and bidfloor > 5.0:
        competitive_context = "Niche Premium"
        quality_tier = "Premium"  # Exclusive
```

### 13. Market-Indexed Floor Price Analysis

**The Opportunity:** Move from absolute floor price analysis to market-relative analysis.

**Current State:** ❌ Floor prices analyzed in isolation

**Proposed Enhancement:**
- Provide LLM with **comparison context**: Current market floor prices for that category
- Task: "Determine if this floor price ($3.82) is Premium or Standard for 'Sports' in the US market"
- Adds `value_score` to metadata (e.g., "Above Market Average", "Market Standard", "Below Market")

**Example Prompt Enhancement:**
```python
market_context = f"""
Current Market Floor Prices (US Market):
- Sports (General): $2.50 - $4.00
- Sports (Premium/CTV): $5.00 - $10.00
- News: $1.50 - $3.00
- Entertainment: $2.00 - $5.00
"""

# LLM task:
# "Given the deal floor price of ${bidfloor} for category '{taxonomy_tier1}',
#  determine if this is Premium, Standard, or Below Market for this category."
```

### 14. Hard Signal Override Strategy

**The Opportunity:** Use `ssp_id`, `auction_type`, and `inventory_image` as **Hard Signals** that override LLM "guesses".

**Current State:** ❌ LLM inference treated as primary, hard signals not prioritized

**Proposed Enhancement:**
- **Hard Signals** (high confidence, override LLM):
  - `ssp_id: 7` (Sovrn) + `creative_type: "display"` → "Display/Web" inventory (high confidence)
  - `inventory_image` visual analysis → Visual quality tier (high confidence)
  - `auction_type: 1` (First Price) + high floor → Premium intent (high confidence)
- **Soft Signals** (LLM inference):
  - Taxonomy from deal name
  - Audience segments
  - Brand safety (when not visually verifiable)

**Example:**
```python
# Hard signal priority
if ssp_id == 7 and creative_type == "display":
    inventory_type = "Websites"  # Hard signal, override LLM
    confidence = "high"

if inventory_image:
    visual_quality = analyze_image(inventory_image)  # Hard signal
    if visual_quality == "MFA":
        brand_safety = "High Risk"  # Override LLM inference
```

## Comparison: Current vs. Proposed Enrichment

| Feature | Current Enrichment | Proposed "Better" Enrichment |
| --- | --- | --- |
| **Taxonomy** | IAB Tier 1-3 (Inferred) | **Contextual Taxonomy** (Event-based + Site Quality) |
| **Brand Safety** | GARM Rating (Inferred) | **Verification** (LLM analyzes `inventory_image` + `publisher` reputation) |
| **Commercial** | Floor Price (Absolute) | **Market Indexing** (Is this price high/low for this specific niche?) |
| **Audience** | Inferred Segments | **Intent Mapping** (Distinguishes between "Interested in Sports" vs "In-Market for World Cup Gear") |
| **Quality Tier** | Floor Price Only | **Multi-Signal** (Floor + Auction Type + Competitive Context) |
| **Volume Tier** | Index Exchange Only | **Availability Metrics** (`weekly_unique_avails` + `bid_requests_ratio`) |
| **Temporal Relevance** | Not Checked | **Event Validation** (Legacy deals vs. current events) |

## Is the API Being Leveraged to the Fullest?

**Not yet.** Currently treating BidSwitch data as a flat text file. Should begin treating `ssp_id`, `auction_type`, and `inventory_image` as **Hard Signals** that override LLM "guesses."

**Example:** If `ssp_id: 7` (Sovrn) and `creative_type: "display"`, you have high-confidence anchor for "Display/Web" inventory regardless of what the description says.

## Future Enhancements

- [x] Document advanced strategies (multimodal, temporal, market indexing)
- [ ] Implement multimodal intelligence (`inventory_image` analysis)
- [ ] Add temporal relevance checking
- [ ] Implement market-indexed floor price analysis
- [ ] Use auction type for commercial tiering
- [ ] Leverage availability metrics for reach/scarcity analysis
- [ ] Build SSP parent company lookup table
- [ ] Implement competitive clutter analysis
- [ ] Add hard signal override strategy
- [ ] Add more external data sources (publisher reputation databases)
- [ ] Improve publisher name matching (fuzzy matching, aliases)
- [ ] Cache LLM responses for identical deals
- [ ] Add confidence scores to inferred fields
- [ ] Support additional SSPs with similar sparse data
