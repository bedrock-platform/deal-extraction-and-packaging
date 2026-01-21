# Semantic Enrichment Pipeline - Implementation Plan

**Status:** Phase 1 ✅ COMPLETE | Phase 2 ✅ COMPLETE | Phase 3 PLANNING | Phase 4 DEFERRED  
**Created:** January 2025  
**Last Updated:** January 21, 2025  
**Owner:** Development Team

---

## Executive Summary

This plan implements the complete semantic enrichment pipeline that transforms raw SSP deal data into semantically enriched, buyer-ready audience packages. The pipeline consists of: Stage 0 (Deal Extraction), Stage 1 (Individual Deal Enrichment), Stage 2 (Package Creation), Stage 3 (Package Enrichment), and Stage 1.5 (Verification Layer - deferred until after Stage 2 is operational).

**Related Tickets:** See `tickets/` directory for detailed implementation tickets

---

## Phase-to-Stage Mapping

**Important:** Phases are aligned with pipeline stages for clarity. Each phase completes a stage before moving to the next.

| Phase | Pipeline Stage(s) | Weeks | Status | Tickets |
|-------|-------------------|-------|--------|---------|
| **Phase 1** | Stage 0 + Stage 1 Core | 1-4 | ✅ **100% COMPLETE** | DEAL-101 ✅, DEAL-102 ✅, DEAL-103 ✅ |
| **Phase 2** | Stage 1 Enhancements | 5-8 | ✅ **100% COMPLETE** | DEAL-202 ✅, DEAL-203 ✅, DEAL-204 ✅, DEAL-205 ✅, DEAL-206 ✅, DEAL-207 ✅ |
| **Phase 3** | Stage 2 + Stage 3 Integration | 9-12 | TODO | DEAL-301, DEAL-302, DEAL-303, DEAL-304, DEAL-305 |
| **Phase 4** | Stage 1.5 Verification Layer | 13-16 | DEFERRED | TBD (after Stage 2 is operational) |

**Pipeline Flow:** Stage 0 → Stage 1 → Stage 2 → Stage 3 → Stage 1.5 (deferred)

**Note:** Stage 1.5 (Real-Time Verification) is **deferred until after Stage 2 (Package Creation) is working**. This allows us to focus on completing the essential pipeline (Stage 0→1→2→3) before adding verification enhancements. Stage 1.5 will be implemented in Phase 4 after package creation is operational.

---

## Current State

### Stage 0: Deal Extraction
- ✅ Fully implemented and operational (Phase 1 - Pre-existing)
- ✅ Multi-vendor extraction (Google Authorized Buyers + BidSwitch)
- ✅ Unified orchestrator (`DealExtractor`)
- ✅ Data export (JSON, TSV, Google Sheets)
- ✅ Transformers output unified schema (Phase 1 - DEAL-102 ✅)

### Stage 1: Individual Deal Enrichment
- ✅ **Core Implementation Complete** (Phase 1 - DEAL-103 ✅)
- ✅ LLM inference pipeline (Gemini 2.5 Flash)
- ✅ Unified enrichment (1 API call, ~4x speedup)
- ✅ Error handling with graceful degradation
- ✅ **Core Enhancements Complete** (Phase 2 - DEAL-202 ✅, 203 ✅, 204 ✅)
- ✅ Taxonomy validation (Phase 2 - DEAL-202 ✅)
- ✅ Publisher intelligence (Phase 2 - DEAL-203 ✅)
- ✅ Temporal signal extraction (Phase 2 - DEAL-204 ✅)
- ✅ **Reference Data Integration** (Phase 2 - DEAL-205 ✅, 206 ✅, 207 ✅)
- ✅ IAB v3.1 taxonomy migration (Phase 2 - DEAL-205 ✅)
- ✅ GARM reference integration (Phase 2 - DEAL-206 ✅)
- ✅ LLM prompt updates for v3.1 (Phase 2 - DEAL-207 ✅)

### Stage 2: Package Creation
- ✅ **Standalone package exists** (`reference/packages/stage2-package-creation/`)
- ✅ **Code Implementation:**
  - `PackageCreator` class (`package_creation/creator.py`)
  - Semantic embeddings (`package_creation/embeddings.py`)
  - Clustering (K-means, GMM) (`package_creation/clustering.py`)
  - LLM grouping (Gemini integration)
- ✅ Examples and documentation
- ❌ **NOT INTEGRATED** with main codebase
- ❌ Expects Stage 1 output (enriched deals)
- ⚠️ **Integration Required:** Import `PackageCreator` and adapt Stage 1 output format

### Stage 3: Package-Level Enrichment
- ✅ **Standalone package exists** (`reference/packages/stage3-package-enrichment/`)
- ✅ **Code Implementation:**
  - `PackageEnricher` class (`package_enrichment/enricher.py`)
  - Deal aggregation (`package_enrichment/aggregation.py`)
  - Health scoring
  - LLM recommendations (Gemini integration)
- ✅ Examples and documentation
- ❌ **NOT INTEGRATED** with main codebase
- ❌ Expects Stage 2 output (packages with deal IDs)
- ⚠️ **Integration Required:** Import `PackageEnricher` and match package/deal formats

### Stage 1.5: Real-Time Verification Layer
- ⏳ **DEFERRED** until after Stage 2 (Package Creation) is operational
- **Rationale:** Focus on completing essential pipeline (Stage 0→1→2→3) before adding verification enhancements
- **Proposed Components:**
  - ads.txt verification (supply path validation via HTTP GET requests)
  - Contextual verification (Gemini Search tool for real-time category validation)
  - E-E-A-T scoring (authority scoring based on search visibility)
  - Dynamic risk detection (real-time brand safety updates)
- **Timing:** Phase 4 (after Stage 2 is working)
- **Tickets:** To be created after Stage 2 integration is complete

### Schema Unification
- ⚠️ **PARTIALLY IMPLEMENTED**
- ✅ Transformers exist (`GoogleAdsTransformer`, `BidSwitchTransformer`)
- ✅ Basic field mapping
- ❌ No unified schema definition
- ❌ No schema validation layer
- ❌ No normalization layer

### Stage Integration
- ❌ **NOT CONNECTED**
- ❌ Stages run independently
- ❌ Manual data handoff required
- ❌ No unified pipeline execution

---

## Desired State

### Unified Schema Layer
- ✅ Single "source of truth" schema (`UnifiedPreEnrichmentSchema`)
- ✅ Pydantic/Dataclass validation
- ✅ All transformers output validated unified schema
- ✅ Schema versioning and migration support

### Stage 1: Individual Deal Enrichment
- ✅ LLM inference pipeline (Google Gemini 2.5 Flash) - Phase 1 ✅
- ✅ Unified enrichment (taxonomy, safety, audience, commercial) - Phase 1 ✅
- ✅ GARM risk rating assignment - Phase 1 ✅
- ⏳ IAB taxonomy validation and auto-correction - Phase 2
- ⏳ Publisher intelligence - Phase 2
- ⏳ Temporal signal extraction - Phase 2


### Stage Integration
- ⏳ **Partial Integration** (Phase 1 - Stage 0 → Stage 1 complete)
- ✅ Stage 0 → Stage 1 flow working
- ❌ **Stage 1 → Stage 2 integration** (Phase 3 - DEAL-302)
- ❌ **Stage 2 → Stage 3 integration** (Phase 3 - DEAL-303)
- ❌ **Full pipeline orchestration** (Phase 3 - DEAL-301)
- ❌ Delta detection (only process new deals) (Phase 3 - DEAL-304)
- ❌ Incremental processing support (Phase 3)
- ❌ Unified CLI (`--full-pipeline`) (Phase 3)
- ❌ Industry-standard package naming taxonomy (Phase 3 - DEAL-305)
- ⏳ **Stage 1.5 Verification** (Phase 4 - DEFERRED until after Stage 2 is operational)

### Production Readiness
- ✅ Database integration for state tracking
- ✅ Monitoring and logging
- ✅ Performance optimization
- ✅ Cost management (LLM API usage)

---


## Implementation Phases

**Note:** Phases are aligned with pipeline stages for clarity. Each phase completes a stage before moving to the next.

### Phase 1: Foundation & Stage 1 Core (Weeks 1-4)
**Pipeline Stage:** Stage 0 (pre-existing) + Stage 1 Core  
**Tickets:** DEAL-101 ✅, DEAL-102 ✅, DEAL-103 ✅  
**Status:** ✅ **100% COMPLETE**  
**Goal:** Establish unified schema and implement core Stage 1 LLM inference pipeline

**Note:** DEAL-104 (Stepwise Taxonomy Inference) and DEAL-105 (GARM Risk Rating Assignment) were originally planned but consolidated into DEAL-103's unified enrichment approach, which handles all enrichment types (taxonomy, safety, audience, commercial) in a single optimized API call.

**Key Changes:**
- **Stage 0:** Deal Extraction (pre-existing, documented) ✅
- Create `UnifiedPreEnrichmentSchema` (Pydantic model) ✅
- Refactor transformers to output unified schema ✅
- Implement core LLM inference engine (Gemini 2.5 Flash) ✅
- **OPTIMIZED:** Unified enrichment (1 API call instead of 4) - ~4x speedup ✅
- Error handling with graceful degradation ✅
- GARM risk rating assignment ✅

**Performance Optimization (Jan 2025):**
- Unified enrichment combines all 4 enrichment types (taxonomy, safety, audience, commercial) into a single LLM API call
- Reduces processing time from ~30-40s per deal to ~8-12s per deal
- For 800 deals: ~2-3 hours (down from 6-8 hours)

**See:** `tickets/DEAL-101.md` through `tickets/DEAL-103.md`

### Phase 2: Stage 1 Enhancements (Weeks 5-8)
**Pipeline Stage:** Stage 1 Enhancements  
**Tickets:** DEAL-202, DEAL-203, DEAL-204  
**Status:** TODO  
**Goal:** Enhance Stage 1 LLM inference with external market data and validation

**Key Changes:**
- IAB taxonomy validator (ChromaDB vector database)
- Auto-correction logic for non-standard tags
- Publisher intelligence patterns
- Temporal signal extraction (seasonal patterns, temporal validation)

**See:** `tickets/DEAL-202.md` through `tickets/DEAL-204.md`

### Phase 3: Stage 2 & 3 Integration (Weeks 9-12)
**Pipeline Stage:** Stage 2 (Package Creation) + Stage 3 (Package Enrichment)  
**Tickets:** DEAL-301, DEAL-302, DEAL-303, DEAL-304, DEAL-305  
**Status:** TODO  
**Goal:** Integrate standalone Stage 2 and 3 packages into unified pipeline

**Key Changes:**
- Stage 1 → Stage 2 integration (enriched deals → embeddings)
- Stage 2 → Stage 3 integration (packages → aggregation)
- Unified CLI orchestrator (`--full-pipeline`)
- Delta detection and incremental processing
- Industry-standard package naming taxonomy (North Star)
- Error handling and recovery

**See:** `tickets/DEAL-301.md` through `tickets/DEAL-305.md`

### Phase 4: Stage 1.5 Verification Layer (Weeks 13-16) - DEFERRED
**Pipeline Stage:** Stage 1.5 (Real-Time Verification)  
**Tickets:** TBD (to be created after Stage 2 is operational)  
**Status:** DEFERRED  
**Goal:** Add verification layer for supply path validation and contextual verification

**Deferral Rationale:**
- Stage 1.5 is deferred until after Stage 2 (Package Creation) is working
- Focus on completing essential pipeline (Stage 0→1→2→3) first
- Verification layer adds value but is not critical for initial package creation
- Can be implemented after package creation proves successful

**Proposed Components:**
- **ads.txt Verification:** HTTP GET requests to verify supply path (DIRECT vs RESELLER)
- **Contextual Verification:** Gemini Search tool integration for real-time category validation
- **E-E-A-T Scoring:** Authority scoring based on search visibility
- **Dynamic Risk Detection:** Real-time brand safety updates from web search

**Implementation Approach:**
- ads.txt verification: High ROI, low complexity (HTTP requests)
- Contextual verification: Medium complexity (requires Gemini Search tool integration)
- Will be evaluated after Stage 2 is operational

**See:** To be documented in Phase 4 tickets (after Stage 2 completion)

---

## Technical Overview

### Modified Files

1. **`src/common/schema.py`** (NEW)
   - `UnifiedPreEnrichmentSchema` Pydantic model (DEAL-101)
   - Schema validation utilities (DEAL-101)

2. **`src/google_ads/transformer.py`**
   - Refactor to output unified schema (DEAL-102)
   - Field normalization (DEAL-102)

3. **`src/bidswitch/transformer.py`**
   - Refactor to output unified schema (DEAL-102)
   - Field normalization (DEAL-102)

4. **`src/enrichment/`** (NEW DIRECTORY)
   - `llm_client.py` - Gemini client wrapper (DEAL-103) ✅
   - `inference.py` - LLM inference pipeline with unified enrichment (DEAL-103) ✅
   - `enricher.py` - Batch processing orchestrator (DEAL-103) ✅
   - `taxonomy_validator.py` - IAB taxonomy validation (DEAL-202)
   - `publisher_intelligence.py` - Brand recognition (DEAL-203)

5. **`src/common/orchestrator.py`**
   - Add enrichment pipeline methods (Phase 1 ✅)
   - Add Stage 2/3 integration (Phase 3 - DEAL-302, DEAL-303)
   - Delta detection logic (Phase 3 - DEAL-304)
   - Industry-standard package naming taxonomy (Phase 3 - DEAL-305)

6. **`src/deal_extractor.py`**
   - Add `--enrich` flag (Phase 1 ✅)
   - Add `--full-pipeline` CLI option (Phase 3 - DEAL-301)
   - Add `--incremental` flag for delta processing (Phase 3 - DEAL-304)

### New Functions/Components

```python
# src/common/schema.py
class UnifiedPreEnrichmentSchema(BaseModel):
    """Unified schema for all deals before Stage 1 enrichment."""
    deal_id: str
    deal_name: str
    ssp_name: str
    format: str  # "video", "display", "native", "audio"
    publishers: List[str]
    floor_price: float
    inventory_type: Optional[Union[str, int]]
    start_time: Optional[str]
    end_time: Optional[str]
    volume_metrics: Optional[Dict[str, Any]]
    raw_deal_data: Dict[str, Any]  # Preserve original vendor data

# src/enrichment/inference.py
def enrich_deal(
    deal: UnifiedPreEnrichmentSchema,
    llm_client: GeminiClient,
    volume_context: Optional[VolumeContext] = None
) -> EnrichedDeal:
    """
    Enrich a single deal with semantic metadata using LLM inference.
    
    OPTIMIZED: Uses unified enrichment (1 API call instead of 4) for ~4x speedup.
    
    Process:
    1. Single unified LLM call returns all enrichment types:
       - IAB Content Taxonomy (Tier 1 → Tier 2 → Tier 3)
       - GARM risk rating assignment
       - Audience inference
       - Commercial tier assessment
    2. Fallback to individual calls if unified enrichment fails
    """
    # Implementation (unified enrichment with fallback)

# src/enrichment/taxonomy_validator.py
class TaxonomyValidator:
    """IAB taxonomy validator with auto-correction."""
    def validate_and_correct(
        self, 
        tier1: str, 
        tier2: str, 
        tier3: str
    ) -> Tuple[str, str, str]:
        """
        Validate taxonomy against IAB 2.2 and auto-correct.
        Uses ChromaDB vector database for fuzzy matching.
        """
        # Implementation
```

**See:** Individual ticket files for detailed implementation

---

## Example User Flows

### Flow 1: Full Pipeline Execution
```
User: python -m src.deal_extractor --full-pipeline --vendor google_ads
Agent: Stage 0: Extracting deals from Google Authorized Buyers...
       → Extracted 500 deals
       
Agent: Schema Unification: Normalizing deals to unified schema...
       → 500 deals normalized, 0 validation errors
       
Agent: Stage 1: Enriching deals with semantic metadata...
       → Enriched 500 deals (100% coverage)
       
Agent: Stage 2: Creating packages from enriched deals...
       → Created 25 packages
       
Agent: Stage 3: Enriching packages with recommendations...
       → Enriched 25 packages
       
Agent: Pipeline complete! Output saved to output/enriched_packages_2025-01-20.json
```

**Related Tickets:** DEAL-301, DEAL-302, DEAL-303

### Flow 2: Incremental Processing
```
User: python -m src.deal_extractor --full-pipeline --incremental
Agent: Delta Detection: Checking for new deals...
       → Found 50 new deals (450 already processed)
       
Agent: Stage 1: Enriching 50 new deals...
       → Enriched 50 deals
       
Agent: Stage 2: Updating packages with new deals...
       → Updated 10 existing packages, created 2 new packages
       
Agent: Stage 3: Re-enriching updated packages...
       → Re-enriched 12 packages
```

**Related Tickets:** DEAL-304


---

## Success Criteria

1. ✅ Unified schema validates all vendor outputs (DEAL-101)
2. ✅ Stage 1 enriches 100+ deals successfully (DEAL-103)
3. ✅ Taxonomy accuracy >80% (manual validation) (DEAL-202)
4. ✅ End-to-end pipeline processes 1000+ deals (DEAL-301)
5. ✅ Package creation generates coherent packages (DEAL-302)
6. ✅ Package enrichment provides actionable recommendations (DEAL-303)
7. ✅ Incremental processing handles delta detection (DEAL-304)
8. ✅ Package names follow industry-standard DSP-searchable taxonomy (DEAL-305)

---

## Testing Plan

### Unit Tests
- Unified schema validation (DEAL-101)
- LLM inference pipeline (DEAL-103)
- Taxonomy validator auto-correction (DEAL-202)
- Publisher intelligence patterns (DEAL-203)
- Stage integration (DEAL-301, DEAL-302, DEAL-303)
- Delta detection and incremental processing (DEAL-304)
- Package naming taxonomy compliance (DEAL-305)

### Integration Tests
- Stage 0 → Stage 1 flow (Phase 1 ✅)
- Stage 1 → Stage 2 flow (Phase 3 - DEAL-302)
- Stage 2 → Stage 3 flow (Phase 3 - DEAL-303)
- Full pipeline end-to-end (Phase 3 - DEAL-301)
- Incremental processing (Phase 3 - DEAL-304)

### Manual Tests
- Full pipeline with real Google Ads deals (Phase 3 - DEAL-301)
- Full pipeline with real BidSwitch deals (Phase 3 - DEAL-301)
- Package creation quality validation (Phase 3 - DEAL-302)
- Package naming taxonomy compliance (Phase 3 - DEAL-305)
- Package enrichment quality validation (Phase 3 - DEAL-303)
- Incremental processing with delta detection (Phase 3 - DEAL-304)

**See:** Individual ticket files for detailed testing requirements

---

## Implementation Order

Tickets should be implemented in order within each phase, respecting dependencies:

1. **Phase 1:** DEAL-101 → DEAL-102 → DEAL-103 (Stage 0 + Stage 1 Core) ✅ ~95% COMPLETE
2. **Phase 2:** DEAL-202 → DEAL-203 → DEAL-204 (Stage 1 Enhancements) - Requires Phase 1
3. **Phase 3:** DEAL-301 → DEAL-302 → DEAL-303 → DEAL-304 → DEAL-305 (Stage 2 & 3 Integration) - Requires Phase 1 & 2 ✅
4. **Phase 4:** Stage 1.5 Verification Layer (TBD tickets) - DEFERRED until after Stage 2 is operational

**See:** `tickets/README.md` for detailed ticket structure and dependencies

---

## Related Documentation

### Reference Materials

**Documentation:**
- **Vision Document:** `reference/documentation/VISION.md` - Complete vision for three-stage pipeline
- **Stage 1 Strategies:** `reference/documentation/STAGE1_ENRICHMENT_STRATEGIES.md` - Detailed enrichment strategies
- **Stage 2 Advanced Clustering:** `reference/documentation/STAGE2_ADVANCED_CLUSTERING.md` - Advanced clustering approaches

**Code Packages (To Be Integrated):**

**Package Creation (Stage 2):** `reference/packages/stage2-package-creation/`
- **Documentation:**
  - [README](reference/packages/stage2-package-creation/README.md)
  - [API Reference](reference/packages/stage2-package-creation/docs/API_REFERENCE.md)
  - [Architecture](reference/packages/stage2-package-creation/docs/ARCHITECTURE.md)
  - [Integration Guide](reference/packages/stage2-package-creation/docs/INTEGRATION_GUIDE.md)
  - [Clustering Methods](reference/packages/stage2-package-creation/docs/CLUSTERING_METHODS.md)
- **Code Files:**
  - [`package_creation/creator.py`](reference/packages/stage2-package-creation/package_creation/creator.py) - `PackageCreator` class
  - [`package_creation/embeddings.py`](reference/packages/stage2-package-creation/package_creation/embeddings.py) - Embeddings generation
  - [`package_creation/clustering.py`](reference/packages/stage2-package-creation/package_creation/clustering.py) - Clustering algorithms
  - [`examples/basic_usage.py`](reference/packages/stage2-package-creation/examples/basic_usage.py) - Usage example

**Package Enrichment (Stage 3):** `reference/packages/stage3-package-enrichment/`
- **Documentation:**
  - [README](reference/packages/stage3-package-enrichment/README.md)
  - [API Reference](reference/packages/stage3-package-enrichment/docs/API_REFERENCE.md)
  - [Architecture](reference/packages/stage3-package-enrichment/docs/ARCHITECTURE.md)
  - [Aggregation Rules](reference/packages/stage3-package-enrichment/docs/AGGREGATION_RULES.md)
  - [Integration Guide](reference/packages/stage3-package-enrichment/docs/INTEGRATION_GUIDE.md)
- **Code Files:**
  - [`package_enrichment/enricher.py`](reference/packages/stage3-package-enrichment/package_enrichment/enricher.py) - `PackageEnricher` class
  - [`package_enrichment/aggregation.py`](reference/packages/stage3-package-enrichment/package_enrichment/aggregation.py) - Aggregation functions
  - [`examples/basic_usage.py`](reference/packages/stage3-package-enrichment/examples/basic_usage.py) - Usage example

---

## Notes

- **Critical Blocker:** Schema unification must be completed before Stage 1 implementation
- **Integration Strategy:** Move Stage 2/3 code into main `src/` directory to avoid "package hell"
- **Stage 1.5 Deferred:** Real-time verification layer (ads.txt verification, contextual verification via Gemini Search) deferred until after Stage 2 (Package Creation) is operational. Will be implemented in Phase 4.
- **Cost Management:** Monitor LLM API usage; implement caching for repeated enrichments
- **Performance:** Consider parallel processing for Stage 1 enrichment (batch LLM calls)

---

## Timeline

| Phase | Tasks | Estimated Hours | Weeks |
|-------|-------|-----------------|-------|
| Phase 1 | Stage 0 (pre-existing) + Schema unification, Core Stage 1 LLM inference | 120 | 1-4 | ✅ ~95% |
| Phase 2 | Stage 1 Enhancements: Taxonomy validator, Publisher intelligence, Temporal signals | 100 | 5-8 | TODO |
| Phase 3 | Stage 2 & 3 Integration: Package creation, Package enrichment, End-to-end orchestrator | 120 | 9-12 | TODO |
| Phase 4 | Stage 1.5 Verification Layer (ads.txt, contextual verification) | 80 | 13-16 | DEFERRED |
| **Total** | | **420** | **16 weeks** | |

**Buffer:** +60 hours for unexpected issues  
**Total Estimate:** 340-400 hours (8.5-10 weeks full-time, 12 weeks part-time)

---

## Risk Mitigation

- **Risk 1: Schema Changes Break Existing Code**
  - **Mitigation:** Use Pydantic for validation, version schema, maintain backward compatibility
  
- **Risk 2: LLM API Costs Exceed Budget**
  - **Mitigation:** Implement caching, batch processing, monitor usage, set rate limits
  
- **Risk 3: External API Dependencies Fail**
  - **Mitigation:** Graceful degradation, fallback to static data, retry logic, circuit breakers
  
- **Risk 4: Stage Integration Complexity**
  - **Mitigation:** Incremental integration, thorough testing, rollback plan for each stage
  
- **Risk 5: Web Crawling Blocked/Rate Limited**
  - **Mitigation:** Use API services where possible, implement delays, respect robots.txt

---

## Rollback Plan

- **If Phase 1 fails:** Keep Stage 0 extraction, revert schema changes, maintain vendor-specific transformers
- **If Phase 2 fails:** Fall back to basic LLM inference without external data, disable temporal signal extraction
- **If Phase 3 fails:** Keep stages separate, maintain manual data handoff, add integration later
- **Partial rollback:** Each phase is independent; can rollback individual phases without affecting others

---

## Expected Results

| Metric | Before | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|--------|---------------|---------------|---------------|
| **Deals Enriched** | 0 | 100+ | 500+ | 1000+ |
| **Taxonomy Accuracy** | N/A | 70% | 85% | 85% |
| **Pipeline Integration** | Stage 0 only | Stage 0→1 | Stage 0→1 | Stage 0→1→2→3 |
| **Package Quality** | N/A | N/A | N/A | Coherent |

---

**Plan Document:** `PLAN.md`  
**Tickets Directory:** `tickets/`  
**Ticket Template:** `../templates/ticket_template.md`
