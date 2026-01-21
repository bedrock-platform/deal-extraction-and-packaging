# Data Directory

This directory contains data files used by the enrichment pipeline.

## IAB Taxonomy

### `iab_taxonomy/iab_content_taxonomy_v3.json`

**Purpose:** IAB Content Taxonomy v3.1 JSON file used by the Taxonomy Validator for validating and auto-correcting taxonomy classifications.

**Usage:** Loaded automatically by `TaxonomyValidator` class in `src/enrichment/taxonomy_validator.py`.

**Size:** ~191 KB (704 taxonomy entries)

**Structure:**
- 37 Tier 1 categories
- 323 Tier 2 categories  
- 275 Tier 3 categories

**Source:** Official IAB Content Taxonomy v3.1 from IAB Tech Lab.

**Note:** This file should be committed to the repository as it's required for taxonomy validation.
