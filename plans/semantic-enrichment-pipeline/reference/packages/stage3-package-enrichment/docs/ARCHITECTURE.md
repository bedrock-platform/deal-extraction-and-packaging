# Package Enrichment Architecture

## Overview

This package implements Stage 3 of the semantic enrichment pipeline, aggregating deal-level enrichments into package-level metadata and generating LLM-based recommendations.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│              Input: Package with Deal IDs                    │
│                                                             │
│  Package: {                                                  │
│    package_id: 5001,                                        │
│    name: "Premium Auto CTV Package",                        │
│    included_deal_ids: [3001, 3002, 3003]                   │
│  }                                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 1: Load Constituent Deals                 │
│                                                             │
│  For each deal_id in included_deal_ids:                     │
│    - Load deal enrichment data                              │
│    - Format for aggregation                                 │
│                                                             │
│  Output: List of enriched deals                              │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 2: Deterministic Aggregation               │
│                                                             │
│  Taxonomy: Most common (mode)                               │
│  Safety: Most restrictive (worst-case)                       │
│  Audience: Union (combine all)                              │
│  Commercial: MIN/MAX/SUM/COUNT                              │
│  Health Score: Weighted composite                           │
│                                                             │
│  Output: Aggregated metadata                                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 3: Format for LLM                         │
│                                                             │
│  - Package name, deal count                                 │
│  - Deal enrichments (JSON)                                  │
│  - Prompt template                                          │
│                                                             │
│  Output: Formatted prompt                                   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 4: LLM Inference                           │
│                                                             │
│  LLM (Gemini 2.5 Flash):                                    │
│    - Validates aggregation                                  │
│    - Generates recommendations                              │
│    - Calculates confidence                                  │
│                                                             │
│  Output: LLM enrichment JSON                                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              Step 5: Combine Results                        │
│                                                             │
│  - Use LLM data where available                             │
│  - Fall back to aggregation if LLM fails                   │
│  - Combine into final enriched package                      │
│                                                             │
│  Output: Fully Enriched Package                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Aggregation Module (`aggregation.py`)

**Purpose**: Deterministic aggregation functions

**Key Functions**:
- `aggregate_taxonomy()`: Most common taxonomy
- `aggregate_safety()`: Most restrictive safety rating
- `aggregate_audience()`: Union of audience segments
- `aggregate_commercial()`: MIN/MAX/SUM of commercial data
- `calculate_health_score()`: Composite health score

**Characteristics**:
- **Deterministic**: Same input always produces same output
- **Null-Safe**: Handles missing data gracefully
- **Fallback**: Used when LLM fails

### 2. Enricher Module (`enricher.py`)

**Purpose**: Main orchestration class

**Key Class**: `PackageEnricher`

**Methods**:
- `enrich_package()`: Main entry point

**Process**:
1. Formats deal enrichments
2. Calls aggregation functions
3. Formats prompt for LLM
4. Calls LLM
5. Combines aggregation + LLM results

**LLM Configuration**:
- Model: `gemini-2.5-flash`
- Temperature: `0.3` (lower for consistency)
- Timeout: `90 seconds`
- Retries: `3`

## Data Flow

### Input Format

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
        "bid_request_volume": 50000000
    },
    # ... more deals
]
```

### Output Format

```python
enriched = {
    "package_id": 5001,
    "package_name": "Premium Auto Intender CTV Package",
    "taxonomy_tier1": "Automotive",
    "taxonomy_tier2": "Auto Parts & Accessories",
    "garm_risk_rating": "Low",
    "family_safe": True,
    "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
    "quality_tier": "Premium",
    "floor_price_min": 4.25,
    "floor_price_max": 6.00,
    "total_daily_avails": 150000000,
    "deal_count": 3,
    "health_score": 92.5,
    "recommended_use_cases": ["Premium auto campaigns", "Brand awareness"],
    "recommended_verticals": ["Automotive", "Finance"],
    "agent_recommendation": "High-quality package...",
    "confidence": 0.85
}
```

## Aggregation Logic

### Taxonomy Aggregation

```python
# Count occurrences
tier1_counts = Counter(deal['taxonomy_tier1'] for deal in deals)
dominant_tier1 = tier1_counts.most_common(1)[0][0]
```

### Safety Aggregation

```python
# Most restrictive
risk_order = {'High': 4, 'Medium': 3, 'Low': 2, 'Floor': 1}
garm_risk_rating = max(risk_ratings, key=lambda r: risk_order.get(r, 0))

# All must be true
family_safe = all(deal['family_safe'] for deal in deals)
```

### Commercial Aggregation

```python
# MIN/MAX/SUM
floor_price_min = min(prices)
floor_price_max = max(prices)
total_daily_avails = sum(volumes)
```

### Health Score

```python
# Weighted composite
health_score = (
    quality_points +    # 0-30
    safety_points +     # 0-30
    volume_points +     # 0-25
    coverage_points     # 0-15
) / 4
```

## Error Handling

### LLM Failures

- **JSON Parse Errors**: Logged, use aggregation only
- **API Errors**: Retried up to 3 times
- **Timeout Errors**: Logged, package skipped

### Missing Data

- **Null Values**: Ignored in aggregation
- **Missing Fields**: Treated as `null`
- **Invalid Types**: Sanitized or converted

## Performance Characteristics

### Time Complexity

- **Aggregation**: O(N) where N = number of deals
- **LLM Processing**: O(1) per package (constant time per LLM call)

### Typical Performance

- **Small Package (3-5 deals)**: ~5-10 seconds
- **Medium Package (10-20 deals)**: ~10-15 seconds
- **Large Package (50+ deals)**: ~15-30 seconds

### Bottlenecks

1. **LLM API Calls**: Rate-limited, sequential processing
2. **Large Deals**: More deals = larger prompt = longer LLM processing

## Configuration

### PackageEnricher Parameters

```python
PackageEnricher(
    llm_api_key="...",              # Required: Google Gemini API key
    prompt_template="...",           # Required: LLM prompt template
    model_name="gemini-2.5-flash",  # Optional: LLM model
    temperature=0.3,                # Optional: LLM temperature
    timeout=90,                     # Optional: LLM timeout
    max_retries=3                   # Optional: Max retries
)
```

## Future Enhancements

1. **Parallel Processing**: Process multiple packages in parallel
2. **Caching**: Cache aggregation results for unchanged deals
3. **Incremental Updates**: Update only changed fields
4. **Batch Processing**: Process packages in batches
5. **Alternative LLMs**: Support other LLM providers

## Dependencies

- `langchain-google-genai`: LLM integration
- `collections.Counter`: For aggregation (built-in)

## Testing Strategy

1. **Unit Tests**: Test individual aggregation functions
2. **Integration Tests**: Test full enrichment pipeline
3. **Mock LLM**: Use mock LLM responses for testing
4. **Edge Cases**: Test with missing data, null values, empty arrays
