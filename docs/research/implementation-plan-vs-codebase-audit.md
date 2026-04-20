# Implementation Plan vs Codebase — Discrepancy Audit

**Date**: 2026-04-18
**Scope**: Compare `docs/agentic-orchestrator-implementation-plan.md` (Phases 1–6 + Future Release Candidates) against current codebase state.
**Method**: Automated codebase exploration — no code changes made.

---

## Executive Summary

| Phase | Status | Completion |
|-------|--------|:----------:|
| Phase 1 — Orchestrator Skeleton | **COMPLETE** | 100% |
| Phase 2 — Agent Execution Layer | **COMPLETE** | 100% |
| Phase 3 — Sequencing Responsibility | **COMPLETE** | 100% |
| Phase 4 — LLM Step 1/2 + Quality Gates | **MOSTLY COMPLETE** | ~80% |
| Phase 5 — Per-Step Quality Gates & Hardening | **NOT STARTED** | ~5% |
| Phase 6 — Worker Audit Trail | **NOT STARTED** | 0% |
| Future Release Candidates | Documented only | N/A |

Phases 1–3 (the architectural refactor) are fully implemented and working. Phase 4 is largely done but missing two minor items. Phase 5 (the quality hardening pass) and Phase 6 (audit trail) have not been started.

---

## Phase 1: Introduce the Orchestrator Skeleton — COMPLETE ✅

### Plan Summary
Replace linear `START → step1 → step2 → ... → step8 → END` chain with an orchestrator-worker loop.

### What Was Implemented
- **`backend/app/graph.py`**: Full orchestrator-worker topology.
  - `_orchestrator()` node reads `completed_steps`, sets `next_step`
  - `get_next_step()` conditional edge router
  - `build_graph()` creates: `START → orchestrator → [conditional] → worker → orchestrator → ... → END`
  - `determine_next_step()` public API for both graph and workflow service
- **`backend/app/state.py`**: `next_step: str` and `completed_steps: list[str]` added to `BMIWorkflowState`
- Step runners reused as first worker implementation

### Discrepancies
- **`last_completed_step`**: Plan listed this as a candidate field. Not implemented — `completed_steps` list serves the same purpose. This is a reasonable simplification, not a gap.
- **Checkpoint naming divergence**: Plan specified 3 checkpoint boundaries (`checkpoint_1`, `checkpoint_1_5`, `checkpoint_2`). Implementation has **8 boundaries** — one per step (`checkpoint_1` through `checkpoint_8`, with `checkpoint_1_5` at Step 2 and `checkpoint_2` at Step 7). The naming convention is inconsistent (Steps 2 and 7 use legacy names; Steps 3–6 and 8 use sequential names). This is a deliberate expansion beyond the plan, not a regression — all 8 steps now have checkpoint support rather than only 3.

### Verdict: No action required.

---

## Phase 2: Add an Agent Execution Layer Around Workers — COMPLETE ✅

### Plan Summary
Introduce worker abstraction so each milestone executes through an explicit agent-oriented unit.

### What Was Implemented
- **`backend/app/workers/base.py`**: `BaseWorker(abc.ABC)` with:
  - Abstract properties: `name`, `step_number`, `description`
  - Abstract method: `execute(state) → BMIWorkflowState`
  - Concrete `run()` — delegates to `execute()`, appends to `completed_steps`
- **`backend/app/workers/steps.py`**: 8 concrete workers:
  1. `SignalScannerWorker` → `run_step1_llm()`
  2. `PatternMatcherWorker` → `run_step2_llm()`
  3. `CustomerProfileWorker` → `run_step3_llm()`
  4. `ValueDriverWorker` → `run_step4_llm()`
  5. `ValuePropositionWorker` → `run_step5_llm()`
  6. `BusinessModelWorker` → `run_step6_llm()`
  7. `RiskMapWorker` → `run_step7_llm()`
  8. `ExperimentPlanWorker` → `run_step8_deterministic()`
- **`backend/app/workers/registry.py`**: Singleton `WorkerRegistry` with `step_names()`, `get_worker()`, `get_runner()` methods

### Discrepancies
- Plan left module location open ("can later be split into `backend/app/workers/`"). Implementation placed it at `backend/app/workers/` — clean and appropriate.

### Verdict: No action required.

---

## Phase 3: Move Sequencing Responsibility Out of Workflow Loop — COMPLETE ✅

### Plan Summary
Make `backend/app/workflow.py` responsible for persistence and checkpoint control only; graph owns routing.

### What Was Implemented
- `workflow.py` imports `determine_next_step`, `steps_completed_before`, `WORKFLOW_STEP_ORDER`, `WORKFLOW_STEP_RUNNERS` from `graph.py`
- `WORKFLOW_STEP_ORDER` is derived from the worker registry, not hardcoded
- `run_workflow_from_voc_data()` invokes `build_graph().invoke(initial_state)`
- `_start_checkpointed_run()` uses `determine_next_step()` for step-by-step control

### Discrepancies
None observed.

### Verdict: No action required.

---

## Phase 4: LLM-Back Step 1 and Step 2 with Quality Gates — MOSTLY COMPLETE ⚠️

### Plan Summary
Build `judge.py`, update Step 1 feature/step-defs for judge evaluation, fix Step 2 production code, guard legacy test, set default execution mode to LLM.

### What Was Implemented

| Planned Item | Status | Evidence |
|---|:---:|---|
| 4-1: Build `judge.py` | ✅ | `backend/app/llm/judge.py` — `evaluate_step1_quality()`, `JudgeVerdict` (4 dimensions × 1–5 rubric) |
| 4-2: Step 1 `.feature` — judge scenario | ✅ | `step1-signal-scanner.feature` lines 27–32 — full "LLM judge evaluates" scenario |
| 4-3: Step 1 step definitions — judge wiring | ✅ | `judge_verdict` fixture calls `evaluate_step1_quality()`, dimension threshold assertions |
| 4-4a: Step 2 — scan all signals | ✅ | `_find_best_disruptive_signal()` scans all `interpreted_signals`, falls back to `[0]` |
| 4-4b: Step 2 — zone name normalization | ✅ | `_ZONE_NORMALIZATION` dict: 3 mappings (Enabling Tech, Overserved, Regulatory Shift) |
| 4-5: Guard legacy `test_competitor_self_serve_evidence_avoids_generic_slogans` | ❌ | Test not found in codebase — may have been removed entirely instead of guarded |
| 4-6: Set `step1_signal_execution_mode` default to `llm` | ❌ | No `step1_signal_execution_mode` config exists. Only `llm_backend` setting (azure/ollama) in `config.py`. All execution is LLM-only — legacy mode appears to have been removed rather than toggled. |

### Analysis
Items 4-5 and 4-6 were about preserving legacy fallback capability. The implementation chose to remove legacy mode entirely rather than maintain a toggle. This is a strategic decision worth confirming — if legacy mode is genuinely obsolete, this is fine. If anyone relies on the rule-based `SIGNAL_SPECS` path, the escape hatch is gone.

### Verdict: Low-severity. Confirm legacy mode is intentionally removed.

---

## Phase 5: Per-Step Quality Gates and Structured Output Hardening — NOT STARTED ❌

Phase 5 is the largest section of the plan (5A–5D, 12 implementation items). Almost none of it has been implemented.

### 5A — Per-Step Quality Gate Design

| Planned Item | Status | Detail |
|---|:---:|---|
| Generalize `judge.py` → `evaluate_step_quality()` | ❌ | Only `evaluate_step1_quality()` exists. No generic function. |
| Step 2 judge evaluation function | ❌ | Not implemented |
| Step 3 judge evaluation function | ❌ | Not implemented |
| Step 4 judge evaluation function | ❌ | Not implemented |
| Step 5 judge evaluation function | ❌ | Not implemented |
| Step 6 judge evaluation function | ❌ | Not implemented |
| Step 7 judge evaluation function | ❌ | Not implemented |

**Impact**: Steps 2–7 have no LLM-as-Judge quality gate. The plan defines specific rubric dimensions and pass thresholds for each step (all documented in the plan). None of this logic exists in code yet.

### 5B — CXIF Domain Validation Library

| Planned Item | Status | Detail |
|---|:---:|---|
| Create `patterns/cxif-pattern-library.json` | ❌ | File does not exist. |
| Steps 3–6 structural compliance BDD scenarios | ❌ | `.feature` files test heading presence but do NOT validate output vocabulary against a pattern library schema |
| Step 8 — migrate dataclass to Pydantic | ❌ | `ExperimentCard` and `TopAssumption` use `@dataclass(frozen=True)`, not Pydantic `BaseModel` |
| Add `_structured` parallel keys to state | ❌ | No `_structured` keys in `BMIWorkflowState` |

#### 5B-2 — Enrichments to Existing Pattern Libraries

| Planned Item | Status | Detail |
|---|:---:|---|
| Strategyzer: add `assessment_scale` to INVENT patterns | ❌ | Only `assessment_question` field exists; no scale anchors |
| Strategyzer: verify SHIFT examples | Not checked | |
| Strategyzer: add SHIFT category grouping vocabulary | ✅ | 4 category groups present: VP Shifts, Frontstage, Backstage, Profit Formula |
| CXIF library: add `trigger_questions` section | ❌ | Library doesn't exist |

### 5C — BDD Feature Scenarios (Judge)

| Step | Judge BDD Scenario Exists? |
|------|:---:|
| Step 1 | ✅ |
| Step 2 | ❌ |
| Step 3 | ❌ |
| Step 4 | ❌ |
| Step 5 | ❌ |
| Step 6 | ❌ |
| Step 7 | ❌ |

### 5D — Implementation Sequence Items

| ID | Description | Status |
|---|---|:---:|
| 5D-1 | Create `cxif-pattern-library.json` | ❌ |
| 5D-2 | Enrich `strategyzer-pattern-library.json` (assessment_scale, SHIFT examples) | Partial (SHIFT categories only) |
| 5D-3 | Add `CXIFPatternLibrary` loader | ❌ |
| 5D-4 | Structural compliance BDD scenarios for Steps 3–6 | ❌ |
| 5D-5 | Step definitions for structural compliance | ❌ |
| 5D-6 | Generalize `judge.py` → reusable `evaluate_step_quality()` | ❌ |
| 5D-7 | Steps 2–7 judge evaluation functions | ❌ |
| 5D-8 | Judge BDD scenarios for Steps 2–7 | ❌ |
| 5D-9 | Step definitions for judge scenarios | ❌ |
| 5D-10 | Pydantic models for Step 8 output | ❌ |
| 5D-11 | `_structured` parallel keys for Steps 3–7 | ❌ |
| 5D-12 | Full test suite pass | N/A (blocked) |

### Verdict: Phase 5 is the next major body of work. Only 1 of 12 implementation items has any progress (5D-2, partial).

---

## Phase 6: Worker Audit Trail and Observability — NOT STARTED ❌

### Plan Summary
Add `WorkerAuditLog` database table, `AuditLogger` utility, API endpoint, and structured logging for every worker execution.

### What Was Implemented

| Planned Item | Status |
|---|:---:|
| `WorkerAuditLog` table in `db/models.py` | ❌ |
| `AuditLogger` class | ❌ |
| `BaseWorker.run()` audit interception | ❌ |
| `GET /runs/{id}/audit` API endpoint | ❌ |
| Structured JSON log output | ❌ |
| Database migration script | ❌ |

### Verdict: Entirely future work. Blocked on Phase 5 completion per the plan's implementation sequence.

---

## Future Release Candidates — Status Check

| ID | Description | Status |
|---|---|:---:|
| FR-1a | Add 8th Signal Zone — Value Network Shift | ❌ Not started |
| FR-1b | Refine Enabling Technology zone description | ❌ Not started |
| FR-1c | Refine Trajectory filter question | ❌ Not started |
| FR-1d | Signal Lifecycle Stage tracking | ❌ Deferred further (needs persistence layer) |
| FR-2 | Exploit Portfolio Assessment Library | ❌ Not started |

These are correctly deferred — they're gated on Phases 1–6 completion per the plan.

---

## Cross-Cutting Observations

### 1. Checkpoint Naming Inconsistency
The plan specified 3 checkpoints: `checkpoint_1`, `checkpoint_1_5`, `checkpoint_2`. The implementation expanded to 8 (one per step), but used the legacy names for Steps 1, 2, and 7 while using sequential names (`checkpoint_3` through `checkpoint_8`) for the rest. The name `checkpoint_2` landing on Step 7 (not Step 2) is confusing. This works correctly but could cause maintenance confusion.

### 2. Step 8 Quick Win (Not In Original Plan)
During this session, Step 8 received a content-aware experiment selection mechanism (`_select_experiment_path()`, `_score_card_fit()`, expanded `EXPERIMENT_MATRIX` to 44 cards). This is tracked in `docs/release/step8-decomposition-plan.md` and is complementary to the broader implementation plan — it addresses Step 8 monotonicity that the plan didn't specifically target.

### 3. Plan Recommended Implementation Sequence vs Actual
The plan recommended: Phase 4 → Phase 1 → Phase 2 → Phase 3 → Phase 5 → Phase 6.
Actual order was approximately: Phase 1 → Phase 2 → Phase 3 → Phase 4 (partial).
This reordering makes sense — the architectural foundation (Phases 1–3) was a prerequisite for everything else.

### 4. Missing Pattern Library Is the Critical Path
The `cxif-pattern-library.json` is the single most impactful missing artifact. It unblocks:
- Structural compliance BDD for Steps 3–6 (5D-4, 5D-5)
- Judge SKILL compliance validation for Steps 3–6 (5D-7, 5D-8, 5D-9)
- Trigger questions for empathy gate enrichment

### 5. Judge Generalization Is the Key Engineering Task
Currently `evaluate_step1_quality()` is hardcoded to Step 1 (it builds Step-1-specific messages with the SOC Radar SKILL body). Generalizing to `evaluate_step_quality()` requires parameterizing: (a) upstream state extraction, (b) SKILL body selection, (c) rubric dimension set. This is 5D-6 and gates 5D-7 through 5D-9.

---

## Recommended Sequencing for Remaining Work

Based on dependencies and impact:

1. **5D-1**: Create `cxif-pattern-library.json` (unblocks 5D-3, 5D-4, 5D-5)
2. **5D-2**: Complete strategyzer enrichments (assessment_scale)
3. **5D-3**: Add CXIF library loader
4. **5D-4 + 5D-5**: Structural compliance BDD for Steps 3–6
5. **5D-6**: Generalize `judge.py`
6. **5D-7 + 5D-8 + 5D-9**: Per-step judge functions + BDD scenarios
7. **5D-10**: Step 8 Pydantic migration (low priority — deterministic step)
8. **5D-11**: `_structured` parallel keys (optional, can defer)
9. **5D-12**: Full suite validation
10. **Phase 6**: Audit trail (after Phase 5 is solid)
