# Ticket DEAL-304: Delta Detection & Incremental Processing

**Ticket ID:** DEAL-304  
**Title:** Implement Delta Detection and Incremental Processing  
**Status:** TODO  
**Priority:** HIGH  
**Phase:** Phase 3 (Stage 2 & 3 Integration)  
**Created:** January 2025  
**Assigned To:** Development Team

---

## Description

Implement delta detection and incremental processing to enable efficient pipeline runs that only process new or modified deals. This reduces processing time and API costs by skipping deals that have already been processed.

Currently, the pipeline processes all deals on every run. This ticket adds the ability to:
1. Track which deals have been processed (state tracking)
2. Detect new or modified deals since last run
3. Process only delta (new/modified deals) when `--incremental` flag is used
4. Update existing packages with new deals instead of recreating everything

## Business Value

- **Cost Efficiency:** Reduces LLM API calls by skipping already-processed deals
- **Performance:** Faster pipeline runs for incremental updates
- **Scalability:** Enables handling of large deal volumes efficiently
- **Production Ready:** Essential for production deployments with frequent updates

## Acceptance Criteria

- [ ] State tracking: Last run timestamp and processed deal IDs stored
- [ ] Delta detection: Compare current deals with last processed state
- [ ] `--incremental` CLI flag added to `deal_extractor.py`
- [ ] Incremental processing: Only new/modified deals processed in Stage 1
- [ ] Package updates: Stage 2 updates existing packages with new deals
- [ ] Package re-enrichment: Stage 3 re-enriches packages with updated deals
- [ ] State persistence: Save state after successful pipeline run
- [ ] Error handling: Failed runs don't corrupt state

## Implementation Details

### Technical Approach

1. **State Tracking:**
   - Create `src/common/state_tracker.py`:
     - `PipelineState` class to track last run timestamp, processed deal IDs
     - Save state to JSON file: `output/pipeline_state.json`
     - Load state on startup
     - Update state after successful pipeline completion

2. **Delta Detection:**
   - Compare current deals with last processed state:
     - New deals: `deal_id` not in processed set
     - Modified deals: `deal_id` exists but `raw_deal_data` hash changed
     - Unchanged deals: Skip processing
   - Return list of deal IDs to process

3. **Incremental Processing Logic:**
   - Stage 1: Only enrich new/modified deals
   - Stage 2: Update existing packages with new deals (don't recreate all packages)
   - Stage 3: Re-enrich packages that received new deals

4. **CLI Integration:**
   - Add `--incremental` flag to `deal_extractor.py`
   - When enabled, use delta detection
   - When disabled (default), process all deals

### Code Changes

- **NEW:** `src/common/state_tracker.py`
  - `PipelineState` class
  - `load_state()` function
  - `save_state()` function
  - `detect_delta()` function

- **MODIFY:** `src/common/pipeline.py`
  - Add delta detection logic
  - Add incremental processing support
  - Integrate state tracking

- **MODIFY:** `src/deal_extractor.py`
  - Add `--incremental` argument
  - Pass incremental flag to pipeline orchestrator

- **MODIFY:** `src/common/orchestrator.py`
  - Add methods for incremental deal extraction
  - Support filtering deals by delta

### State File Format

```json
{
  "last_run_timestamp": "2025-01-21T12:00:00Z",
  "processed_deal_ids": {
    "549644398148090651": {
      "deal_id": "549644398148090651",
      "processed_at": "2025-01-21T12:00:00Z",
      "data_hash": "abc123..."
    }
  },
  "schema_version": "1.0"
}
```

### Delta Detection Algorithm

```python
def detect_delta(current_deals: List[UnifiedPreEnrichmentSchema], state: PipelineState) -> List[str]:
    """
    Detect new or modified deals.
    
    Returns:
        List of deal IDs that need processing
    """
    new_deal_ids = []
    
    for deal in current_deals:
        deal_hash = hash_deal_data(deal.raw_deal_data)
        
        if deal.deal_id not in state.processed_deal_ids:
            # New deal
            new_deal_ids.append(deal.deal_id)
        elif state.processed_deal_ids[deal.deal_id]['data_hash'] != deal_hash:
            # Modified deal
            new_deal_ids.append(deal.deal_id)
    
    return new_deal_ids
```

### Dependencies

- [ ] Phase 1 Complete (DEAL-101, DEAL-102, DEAL-103) - **BLOCKER** ✅
- [ ] Phase 2 Complete (DEAL-202, DEAL-203, DEAL-204) - **BLOCKER** ✅
- [ ] DEAL-301 (Unified CLI Orchestrator) - **BLOCKER** (needs pipeline structure)
- [ ] DEAL-302 (Stage 1 → Stage 2 Integration) - **BLOCKER** (needs package creation)
- [ ] DEAL-303 (Stage 2 → Stage 3 Integration) - **BLOCKER** (needs package enrichment)

## Testing

- [ ] Unit tests: State tracking saves and loads correctly
- [ ] Unit tests: Delta detection identifies new deals
- [ ] Unit tests: Delta detection identifies modified deals
- [ ] Unit tests: Delta detection skips unchanged deals
- [ ] Integration tests: Incremental processing with real deals
- [ ] Integration tests: Package updates with new deals
- [ ] Manual tests: Full incremental pipeline run
- [ ] Edge cases: Empty state file, corrupted state, missing deals

## Related Tickets

- Blocked by: DEAL-301, DEAL-302, DEAL-303
- Related to: DEAL-301 (Unified CLI Orchestrator)

## Reference Materials

- **Vision Document:** `../reference/documentation/VISION.md` - Incremental Processing section
- **Code Integration Guide:** `../CODE_INTEGRATION.md` - State tracking patterns

## Notes

- State file should be versioned for future migrations
- Consider using SQLite for state tracking in production (future enhancement)
- Hash algorithm should be deterministic (use JSON serialization + SHA256)
- Handle edge cases: first run (no state), corrupted state file, missing deals
- Consider adding `--force` flag to override incremental mode

---

**Template Source:** `../templates/ticket_template.md`
