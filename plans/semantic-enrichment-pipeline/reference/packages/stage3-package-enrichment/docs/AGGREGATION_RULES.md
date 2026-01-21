# Aggregation Rules - Detailed Documentation

This document explains the detailed aggregation rules used in Stage 3 package enrichment.

## Overview

Stage 3 aggregates deal-level enrichments into package-level metadata using deterministic rules and LLM inference.

## Aggregation Methods

### 1. Taxonomy Aggregation

**Method**: Most Common (Mode)

**Rules**:
- Count occurrences of each taxonomy tier across all deals
- Select the most frequent value for each tier
- If ties occur, select the first encountered value

**Example**:
```
Deal 1: Tier1="Automotive", Tier2="Auto Parts"
Deal 2: Tier1="Automotive", Tier2="Auto Parts"
Deal 3: Tier1="Entertainment", Tier2="Streaming"
Deal 4: Tier1="Automotive", Tier2="Auto Parts"

Result:
- Tier1: "Automotive" (3 occurrences)
- Tier2: "Auto Parts" (3 occurrences)
```

**Output Fields**:
- `dominant_taxonomy_tier1`
- `dominant_taxonomy_tier2`
- `dominant_taxonomy_tier3`
- `taxonomy_distribution` (counts per category)

### 2. Safety Aggregation

**Method**: Most Restrictive (Worst-Case)

**GARM Risk Rating Rules**:
1. If **any** deal is "High" → Package is "High"
2. Else if **any** deal is "Medium" → Package is "Medium"
3. Else if **all** deals are "Low" or "Floor" → Package is "Low"
4. Else → Package is "Floor" (safest)

**Family Safe Rules**:
- Package is `true` **only if ALL** deals are `true`
- If **any** deal is `false` → Package is `false`
- If **any** deal is `null` → Package is `null`

**Safe For Verticals**:
- Determined based on risk rating and family-safe status
- Low risk + family-safe → More verticals
- High risk → Fewer/no verticals

**Example**:
```
Deal 1: risk="Low", family_safe=true
Deal 2: risk="Low", family_safe=true
Deal 3: risk="Medium", family_safe=false

Result:
- garm_risk_rating: "Medium" (most restrictive)
- family_safe: false (not all are safe)
- safe_for_verticals: ["Automotive", "Finance"] (limited due to Medium risk)
```

**Output Fields**:
- `garm_risk_rating`
- `family_safe`
- `safe_for_verticals`

### 3. Audience Aggregation

**Method**: Union (Combine All)

**Primary Audience Rules**:
- Collect all `inferred_audience` segments from all deals
- Remove duplicates while preserving order
- Return combined list

**Demographic Profile Rules**:
- If all deals have same demographic hint → Use that hint
- If different hints → Combine with comma separation
- If no hints → `null`

**Example**:
```
Deal 1: audience=["Auto Intenders", "Luxury Shoppers"], demo="25-54, High Income"
Deal 2: audience=["Auto Intenders"], demo="25-54, High Income"
Deal 3: audience=["Luxury Shoppers"], demo="30-49, Suburban"

Result:
- primary_audience: ["Auto Intenders", "Luxury Shoppers"] (deduplicated)
- demographic_profile: "25-54, High Income, 30-49, Suburban" (combined)
```

**Output Fields**:
- `primary_audience`
- `demographic_profile`
- `provenance`: "Inferred"

### 4. Commercial Aggregation

**Method**: Statistical Aggregation

**Floor Price Rules**:
- **Min**: MIN across all deals
- **Max**: MAX across all deals
- Handles `null` values (ignores them)

**Total Daily Avails Rules**:
- **Sum**: SUM of all `bid_request_volume` values
- Handles `null` values (treats as 0)

**Quality Tier Rules**:
- **Most Common**: Most frequent quality tier across deals
- If ties → Select first encountered

**Volume Tier Rules**:
- **Most Common**: Most frequent volume tier across deals
- If ties → Select first encountered

**Example**:
```
Deal 1: floor_price=5.50, volume=50000000, quality="Premium", volume_tier="High"
Deal 2: floor_price=6.00, volume=45000000, quality="Premium", volume_tier="High"
Deal 3: floor_price=4.25, volume=55000000, quality="Premium", volume_tier="High"

Result:
- floor_price_min: 4.25
- floor_price_max: 6.00
- total_daily_avails: 150000000
- quality_tier: "Premium" (most common)
- volume_tier: "High" (most common)
```

**Output Fields**:
- `floor_price_min`
- `floor_price_max`
- `total_daily_avails`
- `quality_tier`
- `volume_tier`

### 5. Health Score Calculation

**Method**: Weighted Composite Score

**Formula**:
```
Health Score = (quality_points + safety_points + volume_points + coverage_points) / 4
```

**Scoring Tables**:

**Quality Points**:
| Quality Tier | Points |
|--------------|--------|
| Premium      | 30     |
| Mid-tier     | 20     |
| RON          | 10     |
| Unknown      | 15     |

**Safety Points**:
| Risk Rating | Points |
|-------------|--------|
| Floor       | 30     |
| Low         | 30     |
| Medium      | 20     |
| High        | 10     |
| Unknown     | 15     |

**Volume Points**:
| Volume Tier | Points |
|-------------|--------|
| High        | 25     |
| Medium      | 15     |
| Low         | 5      |
| Unknown     | 10     |

**Coverage Points**:
| Coverage % | Points |
|-----------|--------|
| 100%      | 15     |
| 80-99%    | 12     |
| <80%      | 8      |

**Example**:
```
Package:
- quality_tier: "Premium" → 30 points
- garm_risk_rating: "Low" → 30 points
- volume_tier: "High" → 25 points
- enrichment_coverage: 1.0 (100%) → 15 points

Health Score = (30 + 30 + 25 + 15) / 4 = 25.0
```

**Output Fields**:
- `health_score` (0-100)
- `deal_count`
- `enrichment_coverage` (0.0-1.0)

## LLM-Generated Recommendations

### Recommended Use Cases

**Purpose**: Identify specific campaign types this package serves

**Examples**:
- "Premium auto campaigns"
- "Brand awareness"
- "Retargeting"
- "Performance campaigns"
- "CTV streaming campaigns"

**Generation**: LLM analyzes aggregated data and proposes use cases

### Recommended Verticals

**Purpose**: Identify industries/verticals this package fits

**Examples**:
- ["Automotive", "Finance", "CPG", "Retail"]
- ["Technology", "Healthcare", "Education"]
- ["Entertainment", "Sports", "News"]

**Generation**: LLM analyzes taxonomy, audience, and safety to propose verticals

### Agent Recommendation

**Purpose**: Human-readable summary for AI agents

**Includes**:
- What this package is best for
- Key strengths
- When to use it
- Any limitations

**Example**:
```
"High-quality package for premium auto campaigns. Premium CTV inventory 
from major streaming platforms. Brand-safe for all advertisers. Strong 
volume and competitive pricing."
```

## Aggregation vs LLM Inference

### Deterministic Aggregation (Always Used)

These fields are always calculated using deterministic rules:
- `floor_price_min/max` (MIN/MAX)
- `total_daily_avails` (SUM)
- `deal_count` (COUNT)
- `enrichment_coverage` (percentage)

### LLM Inference (Can Override Aggregation)

These fields use LLM inference but fall back to aggregation:
- `taxonomy_tier1/2/3` (LLM can refine most common)
- `garm_risk_rating` (LLM validates worst-case)
- `family_safe` (LLM validates all-true)
- `quality_tier` (LLM can refine most common)

### LLM-Only Fields

These fields are only generated by LLM:
- `recommended_use_cases`
- `recommended_verticals`
- `agent_recommendation`
- `confidence`

## Error Handling

### Missing Deal Data

- **Null Values**: Ignored in aggregation
- **Missing Fields**: Treated as `null`
- **Empty Arrays**: Treated as empty (not `null`)

### Invalid Data Types

- **Numeric Fields**: Sanitized (converts "N/A" to `null`)
- **String Fields**: Truncated to database limits
- **Boolean Fields**: Preserved as-is

### LLM Failures

- **JSON Parse Errors**: Logged, enrichment continues with aggregation only
- **API Errors**: Retried up to `max_retries` times
- **Timeout Errors**: Logged, package skipped

## Best Practices

1. **Validate Input**: Ensure deals have enrichment data before aggregation
2. **Handle Nulls**: Aggregation functions handle `null` values gracefully
3. **Monitor Health Scores**: Use health scores to identify quality issues
4. **Review Recommendations**: LLM recommendations should be reviewed for accuracy
5. **Fallback Logic**: Always have aggregation fallback if LLM fails

## Summary

Stage 3 aggregation combines deterministic rules with LLM inference:

- **Deterministic**: Prices, volumes, counts (always calculated)
- **Hybrid**: Taxonomy, safety (LLM can refine aggregation)
- **LLM-Only**: Recommendations, use cases, verticals (only from LLM)

This approach ensures reliable aggregation while leveraging LLM intelligence for recommendations.
