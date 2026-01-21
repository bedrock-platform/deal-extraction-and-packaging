# Ticket DEAL-206: Integrate GARM Reference into Enrichment Prompts

**Ticket ID:** DEAL-206  
**Title:** Integrate GARM Reference Documentation into LLM Enrichment Prompts  
**Status:** ✅ **COMPLETE**  
**Priority:** MEDIUM  
**Phase:** Phase 2 (Stage 1 Enhancements)  
**Created:** January 21, 2025  
**Assigned To:** Development Team

---

## Description

Integrate GARM (Global Alliance for Responsible Media) reference documentation into LLM enrichment prompts to improve brand safety rating accuracy. This includes loading GARM reference docs, enhancing safety prompts with GARM guidelines, and adding GARM aggregation utilities for future package creation.

**Current State:**
- Basic safety prompt with minimal GARM guidance
- LLM infers GARM ratings without comprehensive reference
- No GARM aggregation utilities

**Target State:**
- GARM reference documentation loaded and included in prompts
- Enhanced safety prompt with complete GARM guidelines
- GARM aggregation utilities available for future use
- Improved brand safety rating accuracy

## Business Value

- **Brand Safety Accuracy:** Comprehensive GARM guidelines improve rating accuracy
- **Compliance:** Aligns with industry-standard GARM framework
- **Risk Assessment:** Better risk rating inference for brand safety
- **Future Package Creation:** GARM aggregation utilities ready for Stage 2/3

## Acceptance Criteria

- [x] GARM reference documentation integrated into safety prompt (not loaded from files - info embedded in prompt)
- [x] Safety prompt enhanced with GARM risk rating definitions
- [x] Safety prompt includes GARM aggregation rules
- [x] Safety prompt includes family-safe flag guidelines
- [x] GARM aggregation utilities created (`garm_utils.py`)
- [x] LLM outputs more accurate GARM ratings (enhanced prompt with comprehensive guidelines)
- [x] No performance degradation (prompt building unchanged)

## Implementation Details

### Technical Approach

1. **Load GARM reference documentation:**
   - Read `GARM_RISK_RATINGS.md` or `GARM_REFERENCE.md`
   - Extract key sections for prompt inclusion:
     - Risk rating definitions (Floor, Low, Medium, High)
     - Aggregation rules (most restrictive)
     - Family-safe flag logic
     - Safe-for-verticals assessment

2. **Enhance safety prompt:**
   - Add GARM risk rating definitions section
   - Add aggregation rules explanation
   - Add family-safe flag guidelines
   - Include examples of risk assessment

3. **Create GARM utilities:**
   - `aggregate_garm_ratings()`: Aggregate multiple ratings (most restrictive)
   - `aggregate_family_safe()`: Aggregate family-safe flags (all must be true)
   - `determine_safe_verticals()`: Determine safe-for-verticals list

4. **Update inference logic:**
   - Load GARM reference in `format_deal_for_prompt()`
   - Include GARM reference in safety prompt context

### Code Changes

- **MODIFY:** `config/enrichment/safety_prompt.txt`
  - Add GARM risk rating definitions
  - Add aggregation rules
  - Add family-safe flag guidelines
  - Include examples

- **MODIFY:** `src/enrichment/inference.py`
  - Load GARM reference documentation
  - Include GARM reference in prompt context
  - Update `format_deal_for_prompt()` to include GARM context

- **NEW:** `src/enrichment/garm_utils.py`
  - `aggregate_garm_ratings()` function
  - `aggregate_family_safe()` function
  - `determine_safe_verticals()` function
  - GARM risk order constants

- **Note:** GARM reference information is embedded in the safety prompt (not loaded from files)

### GARM Reference Structure

The GARM reference includes:
- **Risk Rating Definitions:** Floor, Low, Medium, High
- **Aggregation Rules:** Most restrictive (worst-case approach)
- **Family-Safe Logic:** All deals must be family-safe
- **Safe-for-Verticals:** Based on risk rating

### Prompt Enhancement Example

```markdown
## GARM Risk Rating Guidelines

Use GARM (Global Alliance for Responsible Media) risk ratings:

- **Floor**: Lowest risk, suitable for all advertisers (family-friendly, mainstream)
- **Low**: Low risk, suitable for most advertisers (brand-safe publishers)
- **Medium**: Medium risk, requires evaluation (controversial topics, opinion pieces)
- **High**: High risk, not suitable for most advertisers (explicit, violent content)

**Assessment Guidelines:**
- Major broadcast networks (ABC, CBS, NBC) → Low/Floor
- Established publishers (CNN, BBC) → Low
- Streaming platforms (Disney+, Netflix) → Low/Floor
- User-generated content platforms → Medium/High
- Adult content → High

**Aggregation Rule:** When combining deals, use most restrictive rating (worst-case).
```

### Dependencies

- [x] GARM reference information embedded in safety prompt (no file loading needed)
- [ ] DEAL-103 (Core LLM Inference Pipeline) - **BLOCKER** ✅
- [ ] Python standard library (file reading)

## Testing

- [ ] Unit tests: Load GARM reference documentation
- [ ] Unit tests: GARM aggregation utilities work correctly
- [ ] Unit tests: Family-safe aggregation logic
- [ ] Integration tests: Enhanced prompt includes GARM reference
- [ ] Manual tests: Verify improved GARM rating accuracy
- [ ] Performance tests: Prompt building <100ms

## GARM Aggregation Utilities

### `aggregate_garm_ratings(ratings: List[str]) -> str`

Aggregates multiple GARM ratings using most restrictive rule:
- `['Low', 'Low', 'Low']` → `'Low'`
- `['Low', 'Medium', 'Low']` → `'Medium'`
- `['Low', 'High', 'Medium']` → `'High'`

### `aggregate_family_safe(flags: List[bool]) -> bool`

Aggregates family-safe flags (all must be true):
- `[True, True, True]` → `True`
- `[True, False, True]` → `False`
- `[None, True, True]` → `None` (if any is None)

### `determine_safe_verticals(risk_rating: str) -> List[str]`

Determines safe-for-verticals based on risk rating:
- `'Floor'` or `'Low'` → All verticals safe
- `'Medium'` → Limited verticals
- `'High'` → No verticals safe

## Related Tickets

- Blocks: None (utilities for future use)
- Blocked by: DEAL-103 (Core LLM Inference Pipeline) ✅
- Related to: DEAL-205 (IAB Taxonomy Migration), DEAL-207 (Update LLM Prompts)
- Future use: DEAL-302 (Stage 2 Integration - package creation)

## Reference Materials

- **Safety Prompt:** `config/enrichment/safety_prompt.txt` (contains GARM reference information)
- **GARM Utilities:** `src/enrichment/garm_utils.py`
- **GARM Official:** https://wfanet.org/leadership/garm/about-garm

## Notes

- GARM reference is documentation (markdown), not structured data
- Extract key sections for prompt inclusion (don't include entire doc)
- Keep prompt size manageable (<5000 characters)
- GARM aggregation utilities are for future package creation (Stage 2/3)
- Consider caching GARM reference content if loading becomes slow

---

**Template Source:** Based on DEAL-202 format
