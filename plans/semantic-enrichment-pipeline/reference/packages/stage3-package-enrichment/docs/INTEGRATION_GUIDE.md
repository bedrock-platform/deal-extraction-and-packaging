# Package Enrichment Integration Guide

Step-by-step guide for integrating Package Enrichment functionality into your Python project.

## Step 1: Copy the Package

Copy the `package_enrichment` directory to your project:

```bash
cp -r package_enrichment_package/package_enrichment /path/to/your/project/
```

Your project structure should look like:

```
your-project/
├── package_enrichment/
│   ├── __init__.py
│   ├── enricher.py
│   └── aggregation.py
├── config/
│   └── package_enrichment_prompt.txt
├── your_code.py
└── ...
```

## Step 2: Install Dependencies

Install required Python packages:

```bash
pip install langchain-google-genai
```

Or add to your `requirements.txt`:

```
langchain-google-genai>=1.0.0
```

## Step 3: Set Up Google Gemini API Key

Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey).

Set environment variable:

```bash
export GEMINI_API_KEY="your-api-key"
```

Or in your code:

```python
import os
os.environ["GEMINI_API_KEY"] = "your-api-key"
```

## Step 4: Prepare Package and Deals

Ensure your package has deal IDs and deals have enrichment data:

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
        "taxonomy_tier2": "Auto Parts & Accessories",
        "garm_risk_rating": "Low",
        "family_safe": True,
        "inferred_audience": ["Auto Intenders"],
        "quality_tier": "Premium",
        "floor_price": 5.50,
        "bid_request_volume": 50000000
    },
    # ... more deals
]
```

## Step 5: Load Prompt Template

Load the package enrichment prompt template:

```python
from pathlib import Path

prompt_path = Path("config/package_enrichment_prompt.txt")
with open(prompt_path, 'r') as f:
    prompt_template = f.read()
```

## Step 6: Initialize PackageEnricher

```python
from package_enrichment import PackageEnricher
import os

enricher = PackageEnricher(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)
```

## Step 7: Enrich Package

```python
# Optional: Progress callback
def progress(msg):
    print(f"[Progress] {msg}")

# Enrich package
enriched = enricher.enrich_package(package, deals, progress_callback=progress)

if enriched:
    print(f"Taxonomy: {enriched['taxonomy_tier1']}")
    print(f"Health Score: {enriched['health_score']}")
    print(f"Use Cases: {enriched['recommended_use_cases']}")
```

## Step 8: Save Enriched Package

Save enriched package to your database or file system:

```python
import json

# Save to JSON
with open('enriched_package.json', 'w') as f:
    json.dump(enriched, f, indent=2)

# Or save to database
db.update('packages', {
    'package_id': enriched['package_id'],
    'taxonomy_tier1': enriched['taxonomy_tier1'],
    'health_score': enriched['health_score'],
    'recommended_use_cases': enriched['recommended_use_cases']
})
```

## Step 9: Customize Configuration

Adjust parameters based on your needs:

```python
enricher = PackageEnricher(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template,
    model_name="gemini-2.5-flash",  # LLM model
    temperature=0.3,                # LLM temperature (0.0-1.0)
    timeout=90,                     # LLM timeout (seconds)
    max_retries=3                   # Max retries on failure
)
```

## Step 10: Error Handling

Add error handling for production use:

```python
import json
from package_enrichment import PackageEnricher

try:
    enricher = PackageEnricher(
        llm_api_key=os.getenv("GEMINI_API_KEY"),
        prompt_template=prompt_template
    )
    
    enriched = enricher.enrich_package(package, deals)
    
    if not enriched:
        print("Enrichment failed")
        return
    
    # Process enriched data
    save_enriched_package(enriched)
    
except ValueError as e:
    print(f"Configuration error: {e}")
except json.JSONDecodeError as e:
    print(f"LLM response parsing error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    import traceback
    traceback.print_exc()
```

## Database Integration Example

```python
import psycopg2
from package_enrichment import PackageEnricher

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)
cursor = conn.cursor()

# Load package and deals
package = load_package_from_db(cursor, package_id)
deal_ids = package['included_deal_ids']
deals = load_deals_from_db(cursor, deal_ids)

# Enrich package
enricher = PackageEnricher(...)
enriched = enricher.enrich_package(package, deals)

# Save to database
cursor.execute("""
    UPDATE packages SET
        taxonomy_tier1 = %s,
        garm_risk_rating = %s,
        health_score = %s,
        recommended_use_cases = %s,
        recommended_verticals = %s
    WHERE package_id = %s
""", (
    enriched['taxonomy_tier1'],
    enriched['garm_risk_rating'],
    enriched['health_score'],
    json.dumps(enriched['recommended_use_cases']),
    json.dumps(enriched['recommended_verticals']),
    enriched['package_id']
))

conn.commit()
cursor.close()
conn.close()
```

## Testing

Create a test script:

```python
#!/usr/bin/env python3
"""Test Package Enrichment integration"""

from package_enrichment import PackageEnricher
import os

def test_package_enrichment():
    """Test package enrichment with sample data"""
    
    # Sample package and deals
    package = {
        "package_id": 5001,
        "name": "Test Package",
        "included_deal_ids": [3001, 3002]
    }
    
    deals = [
        {
            "deal_id": 3001,
            "taxonomy_tier1": "Automotive",
            "garm_risk_rating": "Low",
            "family_safe": True,
            "quality_tier": "Premium",
            "floor_price": 5.50
        },
        {
            "deal_id": 3002,
            "taxonomy_tier1": "Automotive",
            "garm_risk_rating": "Low",
            "family_safe": True,
            "quality_tier": "Premium",
            "floor_price": 6.00
        }
    ]
    
    # Initialize
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("✗ GEMINI_API_KEY not set")
        return False
    
    prompt_template = load_prompt_template()
    enricher = PackageEnricher(api_key, prompt_template)
    
    # Enrich package
    enriched = enricher.enrich_package(package, deals)
    
    if enriched:
        print(f"✓ Enriched package successfully")
        print(f"  Taxonomy: {enriched['taxonomy_tier1']}")
        print(f"  Health Score: {enriched['health_score']}")
        return True
    else:
        print("✗ Enrichment failed")
        return False

if __name__ == "__main__":
    test_package_enrichment()
```

## Troubleshooting

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'langchain_google_genai'`

**Solution**: Install dependencies:
```bash
pip install langchain-google-genai
```

### API Key Errors

**Error**: `ValueError: GEMINI_API_KEY environment variable not set`

**Solution**: Set environment variable:
```bash
export GEMINI_API_KEY="your-api-key"
```

### LLM Response Errors

**Error**: `json.JSONDecodeError`

**Solution**: LLM may return invalid JSON. Check prompt template and add error handling.

### Missing Deal Data

**Error**: Aggregation returns `None` values

**Solution**: Ensure deals have enrichment data from Stage 1.

## Next Steps

- Review [API Reference](API_REFERENCE.md) for complete method documentation
- Check [Architecture](ARCHITECTURE.md) for system design details
- Read [Three-Stage Process](THREE_STAGE_PROCESS.md) for complete pipeline understanding
- See [Aggregation Rules](AGGREGATION_RULES.md) for detailed aggregation logic
