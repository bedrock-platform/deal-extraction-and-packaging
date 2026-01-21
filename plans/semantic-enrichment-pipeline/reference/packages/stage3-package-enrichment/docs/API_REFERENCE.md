# Package Enrichment API Reference

Complete API reference for the Package Enrichment Python package.

## PackageEnricher

### Class: `PackageEnricher`

Main class for enriching packages with aggregated deal-level metadata.

#### Constructor

```python
PackageEnricher(
    llm_api_key: str,
    prompt_template: str,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.3,
    timeout: int = 90,
    max_retries: int = 3
)
```

**Parameters:**

- `llm_api_key` (str, required): Google Gemini API key
- `prompt_template` (str, required): LLM prompt template string (uses `{package_name}`, `{deal_count}`, `{deal_enrichments}` placeholders)
- `model_name` (str, optional): LLM model name (default: "gemini-2.5-flash")
- `temperature` (float, optional): LLM temperature (default: 0.3, lower for consistency)
- `timeout` (int, optional): LLM timeout in seconds (default: 90)
- `max_retries` (int, optional): Maximum retries on failure (default: 3)

**Example:**

```python
from package_enrichment import PackageEnricher

enricher = PackageEnricher(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)
```

#### Method: `enrich_package(package, deals, progress_callback=None) -> Optional[Dict]`

Enrich a package using aggregated deal data and LLM.

**Parameters:**

- `package` (Dict): Package dictionary with at least `name` or `package_name`
- `deals` (List[Dict]): List of enriched deal dictionaries
- `progress_callback` (Callable, optional): Optional callback function for progress updates

**Returns:** Enriched package dictionary or None on error

**Example:**

```python
enriched = enricher.enrich_package(package, deals, progress_callback=print)

if enriched:
    print(f"Taxonomy: {enriched['taxonomy_tier1']}")
    print(f"Health Score: {enriched['health_score']}")
    print(f"Use Cases: {enriched['recommended_use_cases']}")
```

**Enriched Package Format:**

```python
{
    "package_id": 5001,
    "package_name": "Premium Auto Intender CTV Package",
    "taxonomy_tier1": "Automotive",
    "taxonomy_tier2": "Auto Parts & Accessories",
    "taxonomy_tier3": "Auto Repair",
    "garm_risk_rating": "Low",
    "family_safe": True,
    "inferred_audience": ["Auto Intenders", "Luxury Shoppers"],
    "demographic_hint": "25-54, High Income",
    "quality_tier": "Premium",
    "floor_price_min": 4.25,
    "floor_price_max": 6.00,
    "total_daily_avails": 1500000000,
    "deal_count": 3,
    "enrichment_coverage": 1.0,
    "health_score": 92.5,
    "recommended_use_cases": ["Premium auto campaigns", "Brand awareness"],
    "recommended_verticals": ["Automotive", "Finance"],
    "agent_recommendation": "High-quality package...",
    "confidence": 0.85,
    "raw_llm_response": "{...}"
}
```

## Aggregation Functions

### `aggregate_taxonomy(deals: List[Dict]) -> Dict`

Aggregate taxonomy data from deals using most common (mode).

**Parameters:**

- `deals`: List of deal dictionaries with taxonomy fields

**Returns:** Dictionary with dominant taxonomy and distribution

**Example:**

```python
from package_enrichment import aggregate_taxonomy

result = aggregate_taxonomy(deals)
# Returns: {
#     'dominant_taxonomy_tier1': 'Automotive',
#     'dominant_taxonomy_tier2': 'Auto Parts & Accessories',
#     'taxonomy_distribution': {...}
# }
```

### `aggregate_safety(deals: List[Dict]) -> Dict`

Aggregate safety data using most restrictive rating (worst-case).

**Parameters:**

- `deals`: List of deal dictionaries with safety fields

**Returns:** Dictionary with garm_risk_rating, family_safe, safe_for_verticals

**Example:**

```python
from package_enrichment import aggregate_safety

result = aggregate_safety(deals)
# Returns: {
#     'garm_risk_rating': 'Medium',  # Most restrictive
#     'family_safe': False,  # Not all are safe
#     'safe_for_verticals': ['Automotive', 'Finance']
# }
```

### `aggregate_audience(deals: List[Dict]) -> Dict`

Aggregate audience data by combining all segments.

**Parameters:**

- `deals`: List of deal dictionaries with audience fields

**Returns:** Dictionary with primary_audience and demographic_profile

**Example:**

```python
from package_enrichment import aggregate_audience

result = aggregate_audience(deals)
# Returns: {
#     'primary_audience': ['Auto Intenders', 'Luxury Shoppers'],
#     'demographic_profile': '25-54, High Income',
#     'provenance': 'Inferred'
# }
```

### `aggregate_commercial(deals: List[Dict]) -> Dict`

Aggregate commercial data using MIN/MAX/SUM.

**Parameters:**

- `deals`: List of deal dictionaries with commercial fields

**Returns:** Dictionary with floor_price_min/max, quality_tier, volume_tier

**Example:**

```python
from package_enrichment import aggregate_commercial

result = aggregate_commercial(deals)
# Returns: {
#     'floor_price_min': 4.25,
#     'floor_price_max': 6.00,
#     'quality_tier': 'Premium',
#     'volume_tier': 'High'
# }
```

### `calculate_health_score(deals, quality_tier, risk_rating, volume_tier, enrichment_coverage) -> Dict`

Calculate package health score (0-100).

**Parameters:**

- `deals`: List of deal dictionaries
- `quality_tier`: Dominant quality tier
- `risk_rating`: GARM risk rating
- `volume_tier`: Volume tier
- `enrichment_coverage`: Percentage of deals enriched (0.0-1.0)

**Returns:** Dictionary with health_score, deal_count, enrichment_coverage

**Example:**

```python
from package_enrichment import calculate_health_score

result = calculate_health_score(
    deals,
    quality_tier="Premium",
    risk_rating="Low",
    volume_tier="High",
    enrichment_coverage=1.0
)
# Returns: {
#     'deal_count': 3,
#     'enrichment_coverage': 1.0,
#     'health_score': 92.5
# }
```

## Deal Format

### Required Fields

```python
{
    "deal_id": int,              # Required: Deal identifier
    "deal_name": str,            # Optional: Deal display name
    "taxonomy_tier1": str,       # Optional: IAB Tier 1
    "taxonomy_tier2": str,       # Optional: IAB Tier 2
    "taxonomy_tier3": str,       # Optional: IAB Tier 3
    "garm_risk_rating": str,     # Optional: GARM rating
    "family_safe": bool,         # Optional: Family-safe flag
    "inferred_audience": List,   # Optional: Audience segments
    "demographic_hint": str,     # Optional: Demographic profile
    "quality_tier": str,         # Optional: Quality tier
    "volume_tier": str,          # Optional: Volume tier
    "floor_price": float,        # Optional: Floor price
    "bid_request_volume": float  # Optional: Volume metric
}
```

### Alternative Format (Nested)

Deals can also use nested structure:

```python
{
    "deal_id": 3001,
    "taxonomy": {
        "tier1": "Automotive",
        "tier2": "Auto Parts & Accessories"
    },
    "safety": {
        "garm_risk_rating": "Low",
        "family_safe": True
    },
    "audience": {
        "inferred_audience": ["Auto Intenders"],
        "demographic_hint": "25-54, High Income"
    },
    "commercial": {
        "quality_tier": "Premium",
        "floor_price": 5.50
    }
}
```

## Error Handling

### Common Exceptions

**ImportError**: Missing dependencies
```python
try:
    from package_enrichment import PackageEnricher
except ImportError as e:
    print(f"Missing dependency: {e}")
```

**ValueError**: Missing API key
```python
try:
    enricher = PackageEnricher(llm_api_key=None, prompt_template="...")
except ValueError as e:
    print(f"Configuration error: {e}")
```

**JSONDecodeError**: LLM response parsing
```python
try:
    enriched = enricher.enrich_package(package, deals)
except json.JSONDecodeError as e:
    print(f"Failed to parse LLM response: {e}")
```

## Progress Callback

Optional callback function for progress updates:

```python
def progress_callback(message: str):
    print(f"[Progress] {message}")

enriched = enricher.enrich_package(
    package, 
    deals, 
    progress_callback=progress_callback
)
```

**Example Output:**
```
[Progress] Calling LLM for package enrichment...
[Progress] LLM response received (3.2s)
```

## Best Practices

1. **Validate Input**: Ensure deals have enrichment data before enrichment
2. **Handle Nulls**: Aggregation functions handle `null` values gracefully
3. **Monitor Health Scores**: Use health scores to identify quality packages
4. **Review Recommendations**: LLM recommendations should be reviewed
5. **Error Handling**: Wrap `enrich_package()` in try/except for error handling

## Performance Tips

1. **Batch Processing**: Process multiple packages in batches
2. **Parallel Processing**: Process packages in parallel (future enhancement)
3. **Caching**: Cache aggregation results for unchanged deals
4. **Timeout**: Adjust timeout based on package size
