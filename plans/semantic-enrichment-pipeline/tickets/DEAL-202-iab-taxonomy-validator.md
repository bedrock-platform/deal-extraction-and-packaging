# Ticket DEAL-202: IAB Taxonomy Validator

**Ticket ID:** DEAL-202  
**Title:** Implement IAB Taxonomy Validator with Auto-Correction  
**Status:** ✅ **COMPLETE**  
**Priority:** HIGH  
**Phase:** Phase 2 (Stage 1 Enhancements)  
**Created:** January 2025  
**Assigned To:** Development Team

---

## Description

Implement an IAB Content Taxonomy validator that validates and auto-corrects taxonomy tags inferred by the LLM. This ensures taxonomy accuracy by validating against the authoritative IAB 2.2 taxonomy and correcting non-standard or incorrect tags.

The validator uses ChromaDB vector database for fuzzy matching to handle variations in taxonomy naming (e.g., "Automotive" vs "Automotive & Vehicles").

## Business Value

- **Taxonomy Accuracy:** Ensures all taxonomy tags are valid IAB 2.2 tags
- **Auto-Correction:** Automatically fixes common LLM inference errors
- **Data Quality:** Improves downstream package creation quality
- **Compliance:** Ensures taxonomy tags meet industry standards

## Acceptance Criteria

- [ ] ChromaDB vector database initialized with IAB 2.2 taxonomy
- [ ] `TaxonomyValidator` class created
- [ ] `validate_and_correct()` method validates Tier 1, 2, 3 tags
- [ ] Fuzzy matching handles name variations
- [ ] Auto-correction logs changes for review
- [ ] Validator integrates with enrichment pipeline
- [ ] Handles missing or invalid tags gracefully
- [ ] Taxonomy accuracy improves to >80% (manual validation)

## Implementation Details

### Technical Approach

1. Create `src/enrichment/taxonomy_validator.py`:
   - `TaxonomyValidator` class
   - ChromaDB initialization and IAB taxonomy loading
   - `validate_and_correct()` method
   - Fuzzy matching logic

2. Load IAB 2.2 taxonomy into ChromaDB:
   - Tier 1 categories (e.g., "Automotive", "Business", "News")
   - Tier 2 subcategories (e.g., "Automotive > Parts", "Business > Finance")
   - Tier 3 specific categories (e.g., "Automotive > Parts > Tires")

3. Integrate with enrichment pipeline:
   - Validate taxonomy after LLM inference
   - Auto-correct invalid tags
   - Log corrections for review

### Code Changes

- **NEW:** `src/enrichment/taxonomy_validator.py`
  - `TaxonomyValidator` class
  - `validate_and_correct()` method
  - ChromaDB integration

- **NEW:** `data/iab_taxonomy/` directory (optional)
  - IAB 2.2 taxonomy data files
  - Or load from API/online source

- **MODIFY:** `src/enrichment/inference.py`
  - Add taxonomy validation after LLM inference
  - Apply auto-corrections

### Dependencies

- [ ] DEAL-103 (Core LLM Inference Pipeline) - **BLOCKER** ✅
- [ ] ChromaDB installed (`pip install chromadb`)
- [ ] IAB 2.2 taxonomy data available

## Testing

- [ ] Unit tests: Validator corrects invalid tags
- [ ] Unit tests: Fuzzy matching handles variations
- [ ] Unit tests: Missing tags handled gracefully
- [ ] Integration tests: Validator works with enrichment pipeline
- [ ] Manual tests: Verify taxonomy accuracy improvement

## Related Tickets

- Blocked by: DEAL-103 (Core LLM Inference Pipeline)
- Related to: DEAL-203 (Publisher Intelligence), DEAL-204 (Advanced Strategies)

## Reference Materials

- **Vision Document:** `../reference/documentation/VISION.md` - Stage 1: Taxonomy Validation section
- **Stage 1 Strategies:** `../reference/documentation/STAGE1_ENRICHMENT_STRATEGIES.md` - Taxonomy validation strategies
- **IAB Content Taxonomy 2.2:** Official IAB taxonomy documentation

## Notes

- ChromaDB provides semantic similarity search for fuzzy matching
- Consider caching validation results (taxonomy doesn't change frequently)
- Log all corrections for quality review
- May need to handle taxonomy versioning (IAB 2.2 vs future versions)

---

**Template Source:** `../templates/ticket_template.md`
