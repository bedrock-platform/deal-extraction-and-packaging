# Ticket DEAL-301: Unified CLI Orchestrator

**Ticket ID:** DEAL-301  
**Title:** Create Unified CLI Orchestrator for Full Pipeline  
**Status:** TODO  
**Priority:** HIGH  
**Phase:** Phase 3 (Stage 2 & 3 Integration)  
**Created:** January 2025  
**Assigned To:** Development Team

---

## Description

Create a unified CLI orchestrator that executes the complete pipeline: Stage 0 → Stage 1 → Stage 2 → Stage 3. This enables end-to-end execution with a single command (`--full-pipeline`).

Currently, stages run independently. This ticket (Phase 3) connects Stage 2 and Stage 3 into the pipeline flow, building on Phase 1 (Stage 0→1) and Phase 2 (Stage 1 Enhancements).

## Business Value

- **User Experience:** Single command for complete pipeline
- **Automation:** Enables scheduled/automated runs
- **Efficiency:** Reduces manual data handoff between stages
- **Production Ready:** Essential for production deployment

## Acceptance Criteria

- [ ] `--full-pipeline` CLI option added to `deal_extractor.py`
- [ ] Pipeline executes: Stage 0 → Stage 1 → Stage 2 → Stage 3
- [ ] Progress tracking and logging throughout pipeline
- [ ] Error handling: Failures don't block entire pipeline
- [ ] Output files saved at each stage (for debugging)
- [ ] Final output: Enriched packages JSON/TSV
- [ ] Supports `--incremental` flag for delta processing

## Implementation Details

### Technical Approach

1. Update `src/deal_extractor.py`:
   - Add `--full-pipeline` argument
   - Add `--incremental` argument
   - Add pipeline orchestration logic

2. Create `src/common/pipeline.py`:
   - `PipelineOrchestrator` class
   - Methods for each stage:
     - `run_stage_0()` - Deal extraction
     - `run_stage_1()` - Enrichment
     - `run_stage_2()` - Package creation
     - `run_stage_3()` - Package enrichment
   - `run_full_pipeline()` - Orchestrates all stages

3. Add progress tracking:
   - Progress bars or logging
   - Stage completion status
   - Error reporting

4. Add error handling:
   - Continue on individual deal failures
   - Log errors for review
   - Partial results saved

### Code Changes

- **MODIFY:** `src/deal_extractor.py`
  - Add `--full-pipeline` argument
  - Add `--incremental` argument
  - Add pipeline execution logic

- **NEW:** `src/common/pipeline.py`
  - `PipelineOrchestrator` class
  - Stage execution methods
  - Error handling and logging

- **MODIFY:** `src/common/orchestrator.py`
  - Add enrichment pipeline methods
  - Integrate with Stage 2/3 packages

### Dependencies

- [ ] Phase 1 Complete (DEAL-101, DEAL-102, DEAL-103) - **BLOCKER** ✅
- [ ] Phase 2 Complete (DEAL-202, DEAL-203, DEAL-204) - **BLOCKER**
- [ ] DEAL-302 (Stage 1 → Stage 2 Integration) - **BLOCKER**
- [ ] DEAL-303 (Stage 2 → Stage 3 Integration) - **BLOCKER**

## Testing

- [ ] Unit tests: Pipeline orchestrator executes stages
- [ ] Unit tests: Error handling works correctly
- [ ] Integration tests: Full pipeline with sample deals
- [ ] Integration tests: Incremental processing works
- [ ] Manual tests: End-to-end with real deals
- [ ] Performance tests: Pipeline handles 1000+ deals

## Related Tickets

- Blocked by: DEAL-103, DEAL-302, DEAL-303
- Blocks: None (enables full pipeline)

## Reference Materials

- **Vision Document:** `../reference/documentation/VISION.md` - Data Flow: Complete Pipeline section
- **Code Integration Guide:** `../CODE_INTEGRATION.md` - Detailed integration steps
- **Package Creation:** `../reference/packages/stage2-package-creation/docs/INTEGRATION_GUIDE.md` - Stage 2 integration
- **Package Enrichment:** `../reference/packages/stage3-package-enrichment/docs/INTEGRATION_GUIDE.md` - Stage 3 integration

## Notes

- Consider adding `--stage` flag to run individual stages
- Add `--dry-run` flag to validate without executing
- Progress tracking helps with long-running pipelines
- Save intermediate results for debugging and recovery

---

**Template Source:** `../templates/ticket_template.md`
