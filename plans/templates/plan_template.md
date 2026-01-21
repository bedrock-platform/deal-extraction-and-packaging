# [Plan Title] - Implementation Plan

**Status:** [PLANNING | IN PROGRESS | IN REVIEW | COMPLETE]  
**Created:** [Date]  
**Last Updated:** [Date]  
**Owner:** [Team/Individual]

---

## Executive Summary

[2-3 sentence overview of what this plan accomplishes and why it matters]

**Related Tickets:** See `tickets/` directory for detailed implementation tickets ([PREFIX-###] through [PREFIX-###])

---

## Current State

### [Aspect 1]
- Current behavior/limitation 1
- Current behavior/limitation 2
- Current behavior/limitation 3

### [Aspect 2]
- Current behavior/limitation 1
- Current behavior/limitation 2

### [Aspect 3]
- Current workflow/process

---

## Desired State

### [Aspect 1 - Enhanced]
- Desired behavior/capability 1
- Desired behavior/capability 2
- Desired behavior/capability 3

### [Aspect 2 - Enhanced]
- Desired behavior/capability 1
- Desired behavior/capability 2

### [Aspect 3 - Enhanced]
- Desired workflow/process

---

## Implementation Phases

### Phase 1: [Phase Name]
**Tickets:** [PREFIX-###], [PREFIX-###], [PREFIX-###]  
**Goal:** [What this phase accomplishes]

**Key Changes:**
- Change 1
- Change 2
- Change 3

**See:** `tickets/[PREFIX-###].md` through `tickets/[PREFIX-###].md`

### Phase 2: [Phase Name]
**Tickets:** [PREFIX-###], [PREFIX-###]  
**Goal:** [What this phase accomplishes]

**Key Changes:**
- Change 1
- Change 2

**See:** `tickets/[PREFIX-###].md` through `tickets/[PREFIX-###].md`

### Phase 3: [Phase Name]
**Tickets:** [PREFIX-###], [PREFIX-###]  
**Goal:** [What this phase accomplishes]

**Key Changes:**
- Change 1
- Change 2

**See:** `tickets/[PREFIX-###].md`, `tickets/[PREFIX-###].md`

---

## Technical Overview

### Modified Files

1. **`path/to/file1.py`**
   - Change description (Ticket reference)
   - Change description (Ticket reference)

2. **`path/to/file2.ts`**
   - Change description (Ticket reference)
   - Change description (Ticket reference)

3. **`path/to/file3.md`**
   - Change description (Ticket reference)

### New Functions/Components

```python
def new_function(param1: str, param2: Optional[int] = None) -> tuple[bool, Optional[str]]:
    """
    Description of what this function does.
    
    Args:
        param1: Description
        param2: Description
    
    Returns:
        (success: bool, error_message: Optional[str])
    """
    # Implementation notes
```

**See:** `tickets/[PREFIX-###].md` for implementation details

---

## Example User Flows

### Flow 1: [Flow Name]
```
User: "[User input]"
Agent: [Tool call with parameters]
       → Returns [result]

User: "[Follow-up input]"
Agent: [Tool call with parameters]
       → [Action/result]
```

**Related Tickets:** [PREFIX-###], [PREFIX-###]

### Flow 2: [Flow Name]
```
User: "[User input]"
Agent: [Tool call with parameters]
       → Returns [result]

User: "[Follow-up input]"
Agent: "[Agent response/question]"
User: "[User response]"
Agent: [Tool call with parameters]
       → [Action/result]
```

**Related Tickets:** [PREFIX-###], [PREFIX-###]

---

## Success Criteria

1. ✅ [Criterion 1] ([Ticket reference])
2. ✅ [Criterion 2] ([Ticket reference])
3. ✅ [Criterion 3] ([Ticket reference])
4. ✅ [Criterion 4] ([Ticket reference])
5. ✅ [Criterion 5] ([Ticket reference])

---

## Testing Plan

### Unit Tests
- [Test description] ([Ticket reference])
- [Test description] ([Ticket reference])
- [Test description] ([Ticket reference])

### Integration Tests
- [Test description] ([Ticket reference])
- [Test description] ([Ticket reference])
- [Test description] ([Ticket reference])

### Agent Tests
- [Test description] ([Ticket reference])
- [Test description] ([Ticket reference])
- [Test description] ([Ticket reference])

**See:** Individual ticket files for detailed testing requirements

---

## Implementation Order

Tickets should be implemented in order within each phase, respecting dependencies:

1. **Phase 1:** [PREFIX-###] → [PREFIX-###] → [PREFIX-###]
2. **Phase 2:** [PREFIX-###] → [PREFIX-###] (can start after Phase 1 complete)
3. **Phase 3:** [PREFIX-###], [PREFIX-###] (can be done in parallel after Phase 1 & 2)

**See:** `tickets/README.md` for detailed ticket structure and dependencies

---

## Related Documentation

- **Tickets:** `tickets/` directory - Detailed implementation tickets
- **Tool Documentation:** `tools/[tool-name]/README.md`
- **Agent Documentation:** `mastra/src/agents/[agent-name].ts`
- **API Documentation:** `api/[api-file].py`

---

## Notes

- [Important note 1]
- [Important note 2]
- [Important note 3]

---

## Timeline

| Phase | Tasks | Estimated Hours |
|-------|-------|-----------------|
| Phase 1 | [Task list] | [X] |
| Phase 2 | [Task list] | [X] |
| Phase 3 | [Task list] | [X] |
| **Total** | | **[X]** |

**Buffer:** +[X] hours for unexpected issues  
**Total Estimate:** [X]-[Y] hours

---

## Risk Mitigation

- **Risk 1:** [Mitigation strategy]
- **Risk 2:** [Mitigation strategy]
- **Risk 3:** [Mitigation strategy]

---

## Rollback Plan

- **If Phase X fails:** [Rollback steps]
- **If Phase Y fails:** [Rollback steps]
- **Partial rollback:** [What can be kept]

---

## Expected Results

| Metric | Before | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|--------|--------------|---------------|---------------|
| **[Metric 1]** | [Value] | [Value] | [Value] | [Value] |
| **[Metric 2]** | [Value] | [Value] | [Value] | [Value] |

---

**Plan Document:** `[plan-name].md`  
**Tickets Directory:** `tickets/`  
**Ticket Template:** `../templates/ticket_template.md`

---

**Template Source:** Extracted from `tool_changes/tool_changes.md` and `_archive/formula-driven-dashboard/PLAN.md`  
**Last Updated:** December 23, 2024

