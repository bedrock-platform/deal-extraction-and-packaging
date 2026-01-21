# Ticket DEAL-101: Unified Schema Definition

**Ticket ID:** DEAL-101  
**Title:** Create Unified Pre-Enrichment Schema  
**Status:** ✅ COMPLETE  
**Priority:** CRITICAL  
**Created:** January 2025  
**Completed:** January 2025  
**Assigned To:** Development Team

---

## Description

Create a unified schema (`UnifiedPreEnrichmentSchema`) that serves as the single "source of truth" for all deals before Stage 1 enrichment. This schema will normalize vendor-specific data (Google Ads, BidSwitch) into a consistent format that Stage 1 can process.

Currently, transformers output vendor-specific schemas:
- Google Ads: `vendor`, `name`, `publisher` (single), `floor_price` (string)
- BidSwitch: `ssp_name`, `name`, `publishers` (array), `floor_price` (float)

This ticket establishes the unified schema using Pydantic for validation and type safety.

## Business Value

- **Critical Blocker:** Stage 1 cannot be implemented without a unified schema
- **Data Consistency:** Ensures all deals follow the same structure regardless of source
- **Type Safety:** Pydantic validation catches schema errors early
- **Maintainability:** Single schema definition makes future changes easier

## Acceptance Criteria

- [x] Pydantic model `UnifiedPreEnrichmentSchema` created in `src/common/schema.py` ✅
- [x] Schema includes all required fields: `deal_id`, `deal_name`, `ssp_name`, `format`, `publishers`, `floor_price`, `raw_deal_data` ✅
- [x] Schema includes optional fields: `inventory_type`, `start_time`, `end_time`, `volume_metrics` ✅
- [x] Schema validation tests pass (valid data accepted, invalid data rejected) ✅
- [x] Schema documentation includes field descriptions and examples ✅
- [x] Schema versioning strategy defined ✅
- [x] Updated to Pydantic v2 syntax (`field_validator`, `model_validator`) ✅

## Implementation Details

### Technical Approach

1. Create `src/common/schema.py` with Pydantic models
2. Define `UnifiedPreEnrichmentSchema` with all required/optional fields
3. Add validation rules (e.g., `format` must be one of: "video", "display", "native", "audio")
4. Create helper functions for schema conversion
5. Add schema versioning support

### Code Changes

- **NEW:** `src/common/schema.py`
  - `UnifiedPreEnrichmentSchema` Pydantic model
  - `EnrichedDeal` Pydantic model (for Stage 1 output)
  - Schema validation utilities
  - Schema versioning helpers

### Dependencies

- [ ] Pydantic installed (`pip install pydantic`)
- [ ] Python 3.8+ (for type hints)

## Testing

- [ ] Unit tests: Valid deals pass validation
- [ ] Unit tests: Invalid deals raise validation errors
- [ ] Unit tests: Optional fields handled correctly
- [ ] Unit tests: Type coercion (string → float for `floor_price`)
- [ ] Integration tests: Schema works with sample Google Ads deals
- [ ] Integration tests: Schema works with sample BidSwitch deals

## Related Tickets

- Blocks: DEAL-102 (Transformer Refactoring)
- Related to: DEAL-103 (Core LLM Inference Pipeline)

## Reference Materials

- **Vision Document:** `../reference/documentation/VISION.md` - Schema unification section
- **Stage 1 Strategies:** `../reference/documentation/STAGE1_ENRICHMENT_STRATEGIES.md` - Input schema requirements

## Notes

- Schema must preserve `raw_deal_data` to maintain access to vendor-specific fields
- Consider adding `schema_version` field for future migrations
- `publishers` should always be a list (even if single publisher)
- `format` field needs normalization (Google Ads uses different values than BidSwitch)

---

**Template Source:** `../templates/ticket_template.md`
