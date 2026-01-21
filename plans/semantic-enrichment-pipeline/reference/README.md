# Reference Materials

This directory contains all reference documentation and code packages for the Semantic Enrichment Pipeline implementation.

## Directory Structure

```
reference/
├── documentation/           # Vision and strategy documents
│   ├── VISION.md           # Complete vision document
│   ├── STAGE1_ENRICHMENT_STRATEGIES.md
│   └── STAGE2_ADVANCED_CLUSTERING.md
├── packages/               # Existing code implementations
│   ├── stage2-package-creation/    # Stage 2: Package Creation
│   └── stage3-package-enrichment/  # Stage 3: Package Enrichment
└── README.md               # This file
```

## Documentation

### Vision & Strategy
- **[VISION.md](documentation/VISION.md)** - Complete vision document for the three-stage pipeline (plus Stage 1.5)
- **[STAGE1_ENRICHMENT_STRATEGIES.md](documentation/STAGE1_ENRICHMENT_STRATEGIES.md)** - Detailed strategies for Stage 1 enrichment
- **[STAGE2_ADVANCED_CLUSTERING.md](documentation/STAGE2_ADVANCED_CLUSTERING.md)** - Advanced clustering strategies for Stage 2

## Code Packages

### Stage 2: Package Creation

**Location:** `packages/stage2-package-creation/`

**Main Entry Point:**
- [`package_creation/creator.py`](packages/stage2-package-creation/package_creation/creator.py) - `PackageCreator` class

**Key Modules:**
- [`package_creation/embeddings.py`](packages/stage2-package-creation/package_creation/embeddings.py) - Semantic embeddings
- [`package_creation/clustering.py`](packages/stage2-package-creation/package_creation/clustering.py) - K-means and GMM clustering

**Documentation:**
- [README](packages/stage2-package-creation/README.md)
- [API Reference](packages/stage2-package-creation/docs/API_REFERENCE.md)
- [Architecture](packages/stage2-package-creation/docs/ARCHITECTURE.md)
- [Integration Guide](packages/stage2-package-creation/docs/INTEGRATION_GUIDE.md)
- [Clustering Methods](packages/stage2-package-creation/docs/CLUSTERING_METHODS.md)

**Examples:**
- [Basic Usage](packages/stage2-package-creation/examples/basic_usage.py)
- [Create Packages from JSON](packages/stage2-package-creation/examples/create_packages_from_json.py)

### Stage 3: Package Enrichment

**Location:** `packages/stage3-package-enrichment/`

**Main Entry Point:**
- [`package_enrichment/enricher.py`](packages/stage3-package-enrichment/package_enrichment/enricher.py) - `PackageEnricher` class

**Key Modules:**
- [`package_enrichment/aggregation.py`](packages/stage3-package-enrichment/package_enrichment/aggregation.py) - Deal aggregation functions

**Documentation:**
- [README](packages/stage3-package-enrichment/README.md)
- [API Reference](packages/stage3-package-enrichment/docs/API_REFERENCE.md)
- [Architecture](packages/stage3-package-enrichment/docs/ARCHITECTURE.md)
- [Aggregation Rules](packages/stage3-package-enrichment/docs/AGGREGATION_RULES.md)
- [Integration Guide](packages/stage3-package-enrichment/docs/INTEGRATION_GUIDE.md)

**Examples:**
- [Basic Usage](packages/stage3-package-enrichment/examples/basic_usage.py)
- [Enrich Packages from JSON](packages/stage3-package-enrichment/examples/enrich_packages_from_json.py)

## How to Use

### For Planning
- Refer to `documentation/VISION.md` for complete architecture and goals
- Review `documentation/STAGE1_ENRICHMENT_STRATEGIES.md` for enrichment strategies
- Check `documentation/STAGE2_ADVANCED_CLUSTERING.md` for advanced clustering approaches

### For Implementation
- **Stage 1:** Use `documentation/STAGE1_ENRICHMENT_STRATEGIES.md` as implementation guide
- **Stage 2:** Integrate `packages/stage2-package-creation/` - see [Code Integration Guide](../CODE_INTEGRATION.md)
- **Stage 3:** Integrate `packages/stage3-package-enrichment/` - see [Code Integration Guide](../CODE_INTEGRATION.md)

### For Integration
- See [CODE_INTEGRATION.md](../CODE_INTEGRATION.md) for detailed integration steps
- Review package examples for usage patterns
- Check package documentation for API details

---

**See Also:**
- [Main Plan](../PLAN.md)
- [Code Integration Guide](../CODE_INTEGRATION.md)
- [Tickets](../tickets/)
