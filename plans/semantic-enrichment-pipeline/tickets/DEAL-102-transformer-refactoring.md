# Ticket DEAL-102: Transformer Refactoring

**Ticket ID:** DEAL-102  
**Title:** Refactor Transformers to Output Unified Schema  
**Status:** ✅ COMPLETE  
**Priority:** CRITICAL  
**Created:** January 2025  
**Completed:** January 2025  
**Assigned To:** Development Team

---

## Description

Refactor `GoogleAdsTransformer` and `BidSwitchTransformer` to output the unified `UnifiedPreEnrichmentSchema` instead of vendor-specific schemas. This ensures all deals follow the same structure before Stage 1 enrichment.

Current transformers output different field names and structures. This ticket normalizes them to the unified schema.

## Business Value

- **Critical Blocker:** Required for Stage 1 implementation
- **Data Consistency:** All deals follow same structure regardless of source
- **Maintainability:** Single schema makes downstream processing easier
- **Type Safety:** Pydantic validation ensures data quality

## Acceptance Criteria

- [x] `GoogleAdsTransformer.transform()` returns `UnifiedPreEnrichmentSchema` ✅
- [x] `BidSwitchTransformer.transform()` returns `UnifiedPreEnrichmentSchema` ✅
- [x] Field mapping correct:
  - `vendor` → `ssp_name` (Google Ads) ✅
  - `name` → `deal_name` (both) ✅
  - `publisher` (single) → `publishers` (array) (Google Ads) ✅
  - `price` (string) → `floor_price` (float) (both) ✅
  - `creative_type` → `format` (BidSwitch) ✅
- [x] All existing tests pass ✅
- [x] New tests verify unified schema output ✅
- [x] `raw_deal_data` preserved in output ✅
- [x] Orchestrator handles Pydantic models (converts to dicts) ✅

## Implementation Details

### Technical Approach

1. Update `GoogleAdsTransformer.transform()`:
   - Map `vendor` → `ssp_name`
   - Map `entityName` → `deal_name`
   - Convert single `publisher` → `publishers` array
   - Convert `floor_price` string → float
   - Infer `format` from `primary_request_format` or breakdowns
   - Preserve original deal in `raw_deal_data`

2. Update `BidSwitchTransformer.transform()`:
   - Map `ssp_id` → `ssp_name` (using SSP_MAP)
   - Map `display_name` → `deal_name`
   - Map `creative_type` → `format` (normalize values)
   - Convert `price` string → float
   - Preserve original deal in `raw_deal_data`

3. Add schema validation:
   - Validate output against `UnifiedPreEnrichmentSchema`
   - Raise clear errors for validation failures

### Code Changes

- **MODIFY:** `src/google_ads/transformer.py`
  - Update `transform()` method to return `UnifiedPreEnrichmentSchema`
  - Add field normalization logic
  - Add schema validation

- **MODIFY:** `src/bidswitch/transformer.py`
  - Update `transform()` method to return `UnifiedPreEnrichmentSchema`
  - Add field normalization logic
  - Add schema validation

- **MODIFY:** `src/common/base_transformer.py`
  - Update return type hint to `UnifiedPreEnrichmentSchema`

### Dependencies

- [ ] DEAL-101 (Unified Schema Definition) - **BLOCKER**

## Testing

- [ ] Unit tests: Google Ads transformer outputs unified schema
- [ ] Unit tests: BidSwitch transformer outputs unified schema
- [ ] Unit tests: Field mappings correct
- [ ] Unit tests: Type conversions work (string → float)
- [ ] Unit tests: `raw_deal_data` preserved
- [ ] Integration tests: Transformers work with real API responses
- [ ] Regression tests: Existing functionality unchanged

## Related Tickets

- Blocked by: DEAL-101 (Unified Schema Definition)
- Blocks: DEAL-103 (Core LLM Inference Pipeline)

## Reference Materials

- **Vision Document:** `../reference/documentation/VISION.md` - Schema Unification section
- **Stage 1 Strategies:** `../reference/documentation/STAGE1_ENRICHMENT_STRATEGIES.md` - Field mapping requirements

## Notes

- Must maintain backward compatibility during transition
- Consider deprecation warnings for old schema fields
- `format` normalization needs careful mapping:
  - Google Ads: "VIDEO", "DISPLAY" → "video", "display"
  - BidSwitch: "video", "display" → "video", "display"
- Handle missing fields gracefully (use None or defaults)

---

**Template Source:** `../templates/ticket_template.md`
