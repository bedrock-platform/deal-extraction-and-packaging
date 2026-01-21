# Ticket DEAL-303: Stage 2 → Stage 3 Integration

**Ticket ID:** DEAL-303  
**Title:** Integrate Stage 2 Packages with Stage 3 Package Enrichment  
**Status:** TODO  
**Priority:** HIGH  
**Phase:** Phase 3 (Stage 2 & 3 Integration)  
**Created:** January 2025  
**Assigned To:** Development Team

---

## Description

Integrate Stage 2 package proposals with Stage 3 package enrichment. This connects the package creation output to the existing `package_enrichment_package` to generate package-level recommendations and health scores.

Stage 3 expects packages with deal IDs and their constituent enriched deals. This ticket ensures Stage 2 output matches Stage 3 input requirements and integrates the package enrichment logic.

## Business Value

- **Pipeline Continuity:** Enables Stage 2 → Stage 3 flow
- **Package Intelligence:** Generates recommendations and health scores
- **Reuses Existing Code:** Leverages existing `package_enrichment_package` implementation

## Acceptance Criteria

- [ ] Stage 2 package format matches Stage 3 input requirements
- [ ] `PackageEnricher` integrated into main pipeline
- [ ] Packages include deal IDs and enriched deal data
- [ ] Package enrichment executes after Stage 2 completion
- [ ] Enriched packages include recommendations and health scores
- [ ] Error handling: Failed enrichment doesn't block pipeline

## Implementation Details

### Technical Approach

1. Review `package_enrichment_package` input requirements:
   - Check expected package format
   - Verify enriched deal format
   - Understand aggregation rules

2. Create adapter layer (`src/integration/stage3_adapter.py`):
   - Converts Stage 2 packages → Stage 3 input format
   - Matches package deal IDs with enriched deals
   - Handles missing deals gracefully

3. Integrate `PackageEnricher` into pipeline:
   - Import `PackageEnricher` from `reference/packages/stage3-package-enrichment/package_enrichment/enricher.py`
   - Initialize with LLM API key (Gemini 2.5 Flash)
   - Use existing `enrich_package()` method
   - Execute package enrichment after Stage 2

4. Update pipeline orchestrator:
   - Add `run_stage_3()` method
   - Connect Stage 2 output → Stage 3 input
   - Handle package enrichment results

### Code Changes

- **NEW:** `src/integration/stage3_adapter.py`
  - `convert_to_stage3_format()` function
  - Package and deal matching utilities

- **MODIFY:** `src/common/pipeline.py`
  - Add `run_stage_3()` method
  - Integrate `PackageEnricher`

- **MODIFY:** `src/common/orchestrator.py`
  - Add package enrichment methods

### Dependencies

- [ ] DEAL-302 (Stage 1 → Stage 2 Integration) - **BLOCKER**
- [ ] Phase 4: Stage 2 integration complete
- [ ] `package_enrichment_package` available (already exists)
- [ ] `langchain-google-genai` installed (for PackageEnricher)

## Testing

- [ ] Unit tests: Stage 3 adapter converts packages correctly
- [ ] Unit tests: Package enrichment executes with packages
- [ ] Integration tests: Stage 2 → Stage 3 flow works end-to-end
- [ ] Integration tests: Enriched packages include recommendations
- [ ] Manual tests: Verify recommendation quality and health scores

## Related Tickets

- Blocked by: DEAL-302 (Stage 1 → Stage 2 Integration)
- Blocks: DEAL-301 (Unified CLI Orchestrator)

## Reference Materials

- **Vision Document:** `../reference/documentation/VISION.md` - Stage 3: Package-Level Enrichment section
- **Package Enrichment Documentation:**
  - [README](../reference/packages/stage3-package-enrichment/README.md)
  - [API Reference](../reference/packages/stage3-package-enrichment/docs/API_REFERENCE.md)
  - [Aggregation Rules](../reference/packages/stage3-package-enrichment/docs/AGGREGATION_RULES.md)
  - [Integration Guide](../reference/packages/stage3-package-enrichment/docs/INTEGRATION_GUIDE.md)
- **Package Enrichment Code:**
  - [`enricher.py`](../reference/packages/stage3-package-enrichment/package_enrichment/enricher.py) - `PackageEnricher` class (main integration point)
  - [`aggregation.py`](../reference/packages/stage3-package-enrichment/package_enrichment/aggregation.py) - `aggregate_taxonomy()`, `aggregate_safety()`, `aggregate_audience()`, `aggregate_commercial()`, `calculate_health_score()`
  - [Example Usage](../reference/packages/stage3-package-enrichment/examples/basic_usage.py) - Shows how to use `PackageEnricher`

---

**Template Source:** `../../templates/ticket_template.md`
