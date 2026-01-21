# Ticket DEAL-207: Update LLM Prompts for IAB v3.1

**Ticket ID:** DEAL-207  
**Title:** Update LLM Prompts to Reference IAB Content Taxonomy v3.1  
**Status:** ✅ **COMPLETE**  
**Priority:** MEDIUM  
**Phase:** Phase 2 (Stage 1 Enhancements)  
**Created:** January 21, 2025  
**Assigned To:** Development Team

---

## Description

Update the taxonomy enrichment prompt to reference IAB Content Taxonomy v3.1 instead of v2.2, and include examples of new Tier 1 categories. This ensures the LLM understands the v3.1 structure and outputs taxonomy classifications compatible with the updated validator.

**Current State:**
- Taxonomy prompt references "IAB Content Taxonomy 2.2"
- Examples use v2.2 categories
- LLM may output v2.2 category names

**Target State:**
- Taxonomy prompt references "IAB Content Taxonomy 3.0/3.1"
- Examples include new v3.1 categories (e.g., "Attractions")
- LLM outputs v3.1-compatible taxonomy classifications

## Business Value

- **Consistency:** LLM outputs match validator expectations (v3.1)
- **Accuracy:** LLM understands complete v3.1 taxonomy structure
- **Future-Proof:** Aligned with latest IAB taxonomy version
- **Data Quality:** Reduces taxonomy mismatches between LLM and validator

## Acceptance Criteria

- [x] Taxonomy prompt updated to reference v3.1
- [x] Prompt includes examples of new v3.1 categories
- [x] Prompt mentions 37 Tier 1 categories (vs. 25 in v2.2)
- [x] LLM outputs compatible with v3.1 structure (validator handles both)
- [x] No breaking changes to existing enrichment flow (backward compatible)

## Implementation Details

### Technical Approach

1. **Update taxonomy prompt:**
   - Change "IAB Content Taxonomy 2.2" → "IAB Content Taxonomy 3.0/3.1"
   - Update examples to include new categories
   - Mention 37 Tier 1 categories
   - Keep existing examples that are still valid

2. **Add new category examples:**
   - Include examples of new v3.1 categories:
     - "Attractions" (e.g., theme parks, museums)
     - "Beauty & Personal Care"
     - Other new categories from v3.1

3. **Verify compatibility:**
   - Test that LLM outputs validate correctly with v3.1 validator
   - Ensure no regression in taxonomy quality

### Code Changes

- **MODIFY:** `config/enrichment/taxonomy_prompt.txt`
  - Update version reference (2.2 → 3.0/3.1)
  - Add examples of new categories
  - Update category count mention

### Prompt Updates

**Before:**
```
Classify into IAB Content Taxonomy 2.2:
- Tier 1: High-level category (e.g., "Automotive", "Arts & Entertainment", "News & Information")
```

**After:**
```
Classify into IAB Content Taxonomy 3.0/3.1:
- Tier 1: High-level category (37 categories available, e.g., "Automotive", "Arts & Entertainment", "News & Information", "Attractions", "Beauty & Personal Care")
- Note: IAB v3.1 includes 37 Tier 1 categories (expanded from 25 in v2.2)
```

### Dependencies

- [ ] DEAL-205 (Migrate Taxonomy Validator to IAB v3.1) - **BLOCKER**
- [ ] Reference data package available (for category examples)

## Testing

- [ ] Unit tests: Prompt includes v3.1 reference
- [ ] Integration tests: LLM outputs validate with v3.1 validator
- [ ] Manual tests: Verify taxonomy quality maintained/improved
- [ ] Regression tests: Existing enrichment still works

## Migration Notes

### Backward Compatibility

- Existing enriched deals may have v2.2 category names
- Validator (DEAL-205) handles backward compatibility
- LLM will gradually output v3.1 categories as prompt is updated
- No breaking changes to enrichment pipeline

### Version Differences

- **v2.2:** 25 Tier 1 categories
- **v3.1:** 37 Tier 1 categories (12 new categories)
- Some category names may have changed slightly
- Validator handles both versions during transition

## Related Tickets

- Blocks: None
- Blocked by: DEAL-205 (Migrate Taxonomy Validator to IAB v3.1)
- Related to: DEAL-206 (GARM Reference Integration)

## Reference Materials

- **IAB Taxonomy File:** `../../data/iab_taxonomy/iab_content_taxonomy_v3.json`
- **IAB Content Taxonomy 3.1:** Official IAB taxonomy documentation
- **Current Prompt:** `config/enrichment/taxonomy_prompt.txt`
- **Validator:** `src/enrichment/taxonomy_validator.py` (after DEAL-205)

## Notes

- Simple prompt update, low risk
- Can be done after DEAL-205 completes
- May want to test LLM output quality before/after
- Consider A/B testing if taxonomy quality is critical

---

**Template Source:** Based on DEAL-202 format
