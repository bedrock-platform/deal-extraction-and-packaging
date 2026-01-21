# Package Creation Integration Guide

Step-by-step guide for integrating Package Creation functionality into your Python project.

## Step 1: Copy the Package

Copy the `package_creation` directory to your project:

```bash
cp -r package_creation_package/package_creation /path/to/your/project/
```

Your project structure should look like:

```
your-project/
├── package_creation/
│   ├── __init__.py
│   ├── creator.py
│   ├── embeddings.py
│   └── clustering.py
├── config/
│   └── package_grouping_prompt.txt
├── your_code.py
└── ...
```

## Step 2: Install Dependencies

Install required Python packages:

```bash
pip install sentence-transformers scikit-learn langchain-google-genai numpy
```

Or add to your `requirements.txt`:

```
sentence-transformers>=2.0.0
scikit-learn>=1.0.0
langchain-google-genai>=1.0.0
numpy>=1.20.0
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

## Step 4: Prepare Enriched Deals

Ensure your deals have enrichment data from Stage 1:

```python
deals = [
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
            "family_safe": True
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
    },
    # ... more deals
]
```

## Step 5: Load Prompt Template

Load the package grouping prompt template:

```python
from pathlib import Path

prompt_path = Path("config/package_grouping_prompt.txt")
with open(prompt_path, 'r') as f:
    prompt_template = f.read()
```

## Step 6: Initialize PackageCreator

```python
from package_creation import PackageCreator
import os

creator = PackageCreator(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template
)
```

## Step 7: Create Packages

```python
# Optional: Progress callback
def progress(msg):
    print(f"[Progress] {msg}")

# Create packages
proposals = creator.create_packages(deals, progress_callback=progress)

# Process proposals
for proposal in proposals:
    print(f"Package: {proposal['package_name']}")
    print(f"Deals: {proposal['deal_ids']}")
    print(f"Reasoning: {proposal['reasoning']}")
```

## Step 8: Save Packages

Save package proposals to your database or file system:

```python
import json

# Save to JSON
with open('package_proposals.json', 'w') as f:
    json.dump({
        'metadata': {
            'source': 'Package Creation Package',
            'count': len(proposals),
            'created_at': '2025-01-20T12:00:00Z'
        },
        'proposals': proposals
    }, f, indent=2)

# Or save to database
for proposal in proposals:
    db.insert('packages', {
        'name': proposal['package_name'],
        'deal_ids': proposal['deal_ids'],
        'reasoning': proposal['reasoning']
    })
```

## Step 9: Customize Configuration

Adjust parameters based on your needs:

```python
creator = PackageCreator(
    llm_api_key=os.getenv("GEMINI_API_KEY"),
    prompt_template=prompt_template,
    model_name="gemini-2.5-flash",      # LLM model
    temperature=0.5,                      # LLM temperature (0.0-1.0)
    embedding_model="all-MiniLM-L6-v2",  # Embedding model
    max_deals_per_cluster=25,            # Max deals per cluster
    min_cluster_size=5                   # Min cluster size
)
```

## Step 10: Error Handling

Add error handling for production use:

```python
import json
from package_creation import PackageCreator

try:
    creator = PackageCreator(
        llm_api_key=os.getenv("GEMINI_API_KEY"),
        prompt_template=prompt_template
    )
    
    proposals = creator.create_packages(deals)
    
    if not proposals:
        print("No packages created")
        return
    
    # Process proposals
    for proposal in proposals:
        # Validate proposal
        if not proposal.get('package_name'):
            continue
        if len(proposal.get('deal_ids', [])) < 3:
            continue
        
        # Save proposal
        save_package(proposal)
        
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
from package_creation import PackageCreator

# Database connection
conn = psycopg2.connect(
    host="localhost",
    database="mydb",
    user="user",
    password="password"
)
cursor = conn.cursor()

# Create packages
creator = PackageCreator(...)
proposals = creator.create_packages(deals)

# Save to database
for proposal in proposals:
    cursor.execute("""
        INSERT INTO packages (
            name, deal_ids, reasoning, created_at
        ) VALUES (%s, %s, %s, NOW())
    """, (
        proposal['package_name'],
        proposal['deal_ids'],
        proposal['reasoning']
    ))

conn.commit()
cursor.close()
conn.close()
```

## Testing

Create a test script:

```python
#!/usr/bin/env python3
"""Test Package Creation integration"""

from package_creation import PackageCreator
import os

def test_package_creation():
    """Test package creation with sample deals"""
    
    # Sample deals
    deals = [
        {
            "deal_id": "3001",
            "deal_name": "Premium CTV Auto",
            "taxonomy": {"tier1": "Automotive"},
            "safety": {"garm_risk_rating": "Low"},
            "audience": {"inferred_audience": ["Auto Intenders"]},
            "commercial": {"quality_tier": "Premium"}
        },
        # Add more sample deals...
    ]
    
    # Initialize
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("✗ GEMINI_API_KEY not set")
        return False
    
    prompt_template = load_prompt_template()
    creator = PackageCreator(api_key, prompt_template)
    
    # Create packages
    proposals = creator.create_packages(deals)
    
    if proposals:
        print(f"✓ Created {len(proposals)} packages")
        return True
    else:
        print("✗ No packages created")
        return False

if __name__ == "__main__":
    test_package_creation()
```

## Troubleshooting

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'sentence_transformers'`

**Solution**: Install dependencies:
```bash
pip install sentence-transformers scikit-learn langchain-google-genai numpy
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

### Clustering Errors

**Error**: `Not enough deals for clustering`

**Solution**: Ensure you have at least 5 deals (or adjust `min_cluster_size`).

## Next Steps

- Review [API Reference](API_REFERENCE.md) for complete method documentation
- Check [Architecture](ARCHITECTURE.md) for system design details
- Read [Three-Stage Process](THREE_STAGE_PROCESS.md) for complete pipeline understanding
