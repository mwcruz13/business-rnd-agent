# Project Evolution: From Initial Build to Current State

**Date:** 2026-04-18
**Scope:** Consolidated review of all planning documents, analysis reports, and implementation plans against the current codebase state. Traces the arc from initial scaffold through quality diagnosis, architectural refactor, and feature expansion.

---

## 1. Document Inventory and Chronological Sequence

The project produced 9 major planning/analysis documents across two locations. The chronological sequence, reconstructed from git history and filesystem timestamps:

| # | Date | Document | Type | Location |
|---|------|----------|------|----------|
| 1 | Mar 22 | Step 1 Signal Scan Contract | Output contract spec | `docs/step1-signal-scan-contract.md` |
| 2 | Mar 25 | Step 2 Signal-to-Pattern Mapping Research | Research / pre-implementation | `docs/step2-signal-to-pattern-mapping-research.md` |
| 3 | Mar 26 | Agentic Orchestrator Implementation Plan | Architecture plan (Phases 1–6) | `docs/agentic-orchestrator-implementation-plan.md` |
| 4 | Mar 26 | Signals-to-Business-Model Patterns | Routing rationale | `docs/signals-to-business-model-patterns.md` |
| 5 | Apr 2 | Interactive Experiment Cards Feature | Feature design (Step 8 frontend) | `docs/interactive experiment cards feature.md` |
| 6 | Apr 15 | Diagnosing Steps 3–5: Customer vs Supplier | Root-cause diagnosis | `reports/Diagnosing workflow steps 3 to 5...md` |
| 7 | Apr 15 | Full Workflow Audit: Batch vs Conversational | All-step gap analysis | `reports/Full Workflow Audit...md` |
| 8 | Apr 15 | Converting to Conversational AI Agent | Architecture options (A/B/C) | `reports/Converting BMI Consultant...md` |
| 9 | Apr 15 | BMI Consultant Release 1.0 Plan | Concrete task plan (12 tasks) | `reports/BMI consultant release 1.0 plan.md` |
| 10 | Apr 18 | Step 7–8 Quality Assessment | Research findings | `docs/research/step7-8-quality-assessment.md` |
| 11 | Apr 18 | Step 8 Decomposition Plan | Release plan (Phases 0–5) | `docs/release/step8-decomposition-plan.md` |
| 12 | Apr 18 | Implementation Plan vs Codebase Audit | Gap analysis | `docs/research/implementation-plan-vs-codebase-audit.md` |

---

## 2. The Development Arc

### Phase A: Initial Build (Mar 22)

The app was scaffolded as a LangGraph sequential workflow with 8 steps, a Streamlit frontend, and PostgreSQL persistence. Steps 1–4 had placeholder implementations; Steps 5–8 were added the same day. The initial architecture was a hardcoded linear chain: `START → step1 → step2 → ... → step8 → END`.

Key decisions made at this stage:
- BDD-first discipline: `.feature` files define behavioral contracts, production code makes tests pass
- Docker-only runtime: all code runs inside containers, CLI is the entrypoint
- Checkpoint-based human-in-the-loop after Steps 1, 2, and 7

### Phase B: Architecture and Research (Mar 25–26)

Four documents were produced in rapid succession, establishing the theoretical and architectural foundation:

1. **Step 1 output contract** defined the exact state shape for signal scan results
2. **Step 2 pattern research** analyzed the mapping from Christensen's disruption theory to Osterwalder's business model patterns — this produced the zone-to-pattern affinity matrix
3. **Agentic orchestrator plan** laid out 6 phases to evolve from a linear chain to an orchestrator-worker model with quality gates
4. **Signals-to-patterns routing** documented the theoretical basis for INVENT vs SHIFT direction decisions

On the same day (Mar 26), a large commit delivered:
- Orchestrator-worker graph topology (Plan Phases 1 + 3)
- LLM-backed step nodes for Steps 1–7 (Plan Phase 4, partially)
- Hybrid Step 2 pattern matcher (deterministic affinity + LLM reasoning)
- React frontend with Grommet/HPE theme
- BDD tests for orchestrator routing and pattern affinity

### Phase C: Worker Abstraction and Polish (Mar 27–31)

- **Mar 27**: `BaseWorker` ABC, 8 concrete workers, `WorkerRegistry`, graph rewiring (Plan Phase 2)
- **Mar 30–31**: Frontend scroll bars, LLM backend selector, responsive layout, Ollama structured output support, timeout increases

This completed Plan Phases 1, 2, and 3.

### Phase D: Interactive Experiment Cards (Apr 2)

Two commits delivered the interactive experiment cards feature:
- Strategy document with 6-phase design (card deck UI, Zone A/B, evidence persistence)
- Backend: `_build_card_objects()`, `experiment_cards` state field, PATCH API endpoint, Zone B validation
- Frontend: `ExperimentCard`, `ExperimentCardDeck` components with filter bar and progress indicator
- This work was **not in the original orchestrator plan** — it was a parallel feature track responding to the usability problems identified in Step 8's markdown wall

### Phase E: Quality Diagnosis (Apr 15)

After the initial build was functional, four analysis documents were produced in a single session, each building on the previous:

1. **Steps 3–5 diagnosis** identified the root cause: the CXIF SKILL.md was written for interactive coaching where the human IS the supplier. In batch mode, the LLM defaults to "always customer-centric" for everything, producing VP Canvases where the customer appears to solve their own problems.

2. **Full workflow audit** extended the diagnosis to all 8 steps, producing a severity-ranked table of 12 issues across the entire pipeline. Key findings:
   - Step 1: Phase 4 (Recommend) dropped entirely
   - Step 2: Gold standard — no issues
   - Steps 3–6: Supplier perspective missing, full SKILL.md loaded for single-phase steps, trigger questions unused
   - Step 7: LLM self-assigns quadrants (methodology violation — Map phase requires human judgment)
   - Step 8: 35 of 44 experiment cards unreachable due to hardcoded paths

3. **Conversational agent analysis** evaluated three options:
   - Option A: Full conversational rewrite (8–12 weeks, high risk)
   - Option B: Hybrid — conversational within phases, structured between (4–6 weeks, medium risk)
   - Option C: Fix batch prompts (1–2 days, low risk)
   
   Recommendation: Option C immediately, evaluate Option B for the medium term.

4. **Release 1.0 plan** operationalized Option C into 12 concrete tasks across 5 phases, with exact file paths, code snippets, and test plans.

### Phase F: Release 1.0 Implementation (Apr 15–16)

Between the analysis session and the "last commit before release 1.0" marker on Apr 16, all 12 tasks from the Release 1.0 plan were implemented:

- **Phase 1 (Supplier Perspective)**: Supplier identity added to Steps 4, 5, 6 system prompts. Pydantic field descriptions added. SKILL.md updated with phase-specific perspective rules.
- **Phase 2 (Step 7 Methodology)**: `quadrant` → `suggested_quadrant`. Rendering header marked "Suggested — Review Required". DVFTension structured as a Pydantic model.
- **Phase 3 (Prompt Scoping)**: Phase-specific prompt files created (step3–step7). Trigger questions added to Step 3 system prompt. Empathy gate extended for type diversity. VoC data passed to Steps 5 and 6.
- **Phase 4 (Step 1 + 8)**: SignalRecommendation schema added to Step 1. EXPERIMENT_MATRIX added to Step 8 (alongside PATH_BY_CATEGORY).

### Phase G: Step 7–8 Deepening (Apr 18 — Today)

Today's session produced three new documents and one code change:

1. **Step 7–8 quality assessment** identified the remaining structural problems: 9/44 card coverage, monotonicity, no evidence audit, boilerplate criteria
2. **Step 8 decomposition plan** broke Step 8 into 4 sub-steps (8a Evidence Audit → 8b Card Selection → 8c Path Sequencing → 8d Brief Generation) with a parallel Step 7 flexibility track
3. **Implementation plan vs codebase audit** compared the original Phases 1–6 orchestrator plan against actual code, finding Phases 1–3 complete, Phase 4 ~80%, Phases 5–6 not started
4. **Quick win code change**: Replaced hardcoded PATH_BY_CATEGORY with content-aware `_select_experiment_path()` using word-overlap scoring; expanded EXPERIMENT_MATRIX to 44 cards; fixed the precoil-emt library identity contradiction

---

## 3. Plan Adjustments and Divergences

### 3.1 Execution Order Changed

The orchestrator plan recommended: Phase 4 → Phase 1 → Phase 2 → Phase 3 → Phase 5 → Phase 6.

Actual execution was: Phases 1+3 → Phase 4 (partial) → Phase 2 → Phase 4 (completion via Release 1.0).

This reordering was pragmatic — the architectural foundation (Phases 1–3) had to exist before quality work (Phase 4+) could be layered on.

### 3.2 Release 1.0 Plan Superseded Parts of the Orchestrator Plan's Phase 4

The orchestrator plan's Phase 4 focused narrowly on Step 1 LLM quality and Step 2 production fixes. The Release 1.0 plan expanded the scope to include:
- Supplier perspective fixes for Steps 4, 5, 6 (not in the orchestrator plan)
- Step 7 methodology fix: `suggested_quadrant` (not in the orchestrator plan — it was identified later during the workflow audit)
- Phase-specific prompt files for Steps 3–7 (partially aligns with Phase 5B but was delivered as a Release 1.0 task)
- Trigger questions and empathy gate improvements for Step 3 (not in the orchestrator plan)
- VoC data passthrough to Steps 5 and 6 (not in the orchestrator plan)
- Step 1 Recommend phase restoration (not in the orchestrator plan)

In other words, Release 1.0 addressed prompt-level and schema-level quality issues that the orchestrator plan deferred to Phases 5–6. The orchestrator plan's Phases 5–6 remain relevant for the structural/infrastructure work (CXIF pattern library, generic judge, audit trail) that Release 1.0 did not touch.

### 3.3 Step 8 Decomposition Plan Is New

The step8-decomposition-plan.md (Phases 0–5) was not part of the original orchestrator plan. It emerged from the Step 7–8 quality assessment research conducted today. It represents a new work stream focused specifically on Step 8's deterministic logic, orthogonal to the orchestrator plan's Phase 5 (quality gates across all steps).

### 3.4 Interactive Experiment Cards Were a Parallel Track

The interactive experiment cards feature (Apr 2) was not in any planning document before it was built. It was a user-experience-driven response to Step 8's "wall of markdown" problem. The strategy document was created alongside the implementation, not beforehand.

### 3.5 Legacy Mode Was Removed, Not Toggled

The orchestrator plan's Phase 4 specified guarding the legacy `test_competitor_self_serve_evidence_avoids_generic_slogans` test and adding a `step1_signal_execution_mode` config toggle. Instead, legacy mode was removed entirely. The test no longer exists. There is no `step1_signal_execution_mode` config — all execution is LLM-only.

### 3.6 Checkpoint Boundaries Expanded Beyond Plan

The orchestrator plan specified 3 checkpoint boundaries (after Steps 1, 2, and 7). The implementation expanded to 8 (one per step), with inconsistent naming: Steps 1, 2, 7 use legacy names (`checkpoint_1`, `checkpoint_1_5`, `checkpoint_2`) while Steps 3–6 and 8 use sequential names (`checkpoint_3` through `checkpoint_8`).

---

## 4. What Has Been Accomplished (Summary)

### Architecture (from Orchestrator Plan)
| Item | Status |
|------|--------|
| Phase 1: Orchestrator skeleton (graph topology) | **DONE** |
| Phase 2: Worker abstraction (BaseWorker + 8 workers + registry) | **DONE** |
| Phase 3: Sequencing moved to graph | **DONE** |
| Phase 4: LLM judge for Step 1 | **DONE** |
| Phase 4: Step 2 production fixes (all signals, zone normalization) | **DONE** |
| Phase 5: Per-step quality gates (Steps 2–7) | **NOT STARTED** |
| Phase 5: CXIF pattern library | **NOT STARTED** |
| Phase 5: Generic evaluate_step_quality() | **NOT STARTED** |
| Phase 6: Worker audit trail | **NOT STARTED** |

### Quality Fixes (from Release 1.0 Plan)
| Item | Status |
|------|--------|
| Phase 1: Supplier perspective in Steps 4, 5, 6 | **DONE** |
| Phase 1: SKILL.md perspective rules | **DONE** |
| Phase 2: Step 7 suggested_quadrant | **DONE** |
| Phase 2: DVFTension structured model | **DONE** |
| Phase 3: Phase-specific prompt files | **DONE** |
| Phase 3: Trigger questions in Step 3 | **DONE** |
| Phase 3: Empathy gate type diversity | **DONE** |
| Phase 3: VoC data to Steps 5 and 6 | **DONE** |
| Phase 4: Step 1 Recommend phase | **DONE** |
| Phase 4: Step 8 EXPERIMENT_MATRIX | **DONE** |

### Step 8 Improvements (from Decomposition Plan + Today's Quick Win)
| Item | Status |
|------|--------|
| Phase 0: Content-aware card selection | **DONE** (today) |
| Phase 0: EXPERIMENT_MATRIX expanded to 44 cards | **DONE** (today) |
| Phase 1: Evidence Audit (8a) | **NOT STARTED** |
| Phase 2: Card Selection with LLM (8b) | **NOT STARTED** |
| Phase 3: Path Sequencing (8c) | **NOT STARTED** |
| Phase 4: Brief Generation with LLM (8d) | **NOT STARTED** |
| Phase 5: Step 7 flexibility (2–5 assumptions) | **NOT STARTED** |

### Features (from Interactive Cards Strategy)
| Item | Status |
|------|--------|
| Backend structured card output | **DONE** |
| Evidence persistence API (PATCH endpoint) | **DONE** |
| Frontend ExperimentCard + ExperimentCardDeck | **DONE** |
| Card deck as primary Step 8 view | **DONE** |
| Status tracking and sequencing visualization | **PARTIAL** (progress indicator exists, full sequencing visualization not yet) |
| Export functionality | **NOT STARTED** |

---

## 5. What Remains (Consolidated Backlog)

Three active planning documents define the remaining work. Here they are organized by dependency and priority:

### Tier 1: Structural Quality Infrastructure (from Orchestrator Plan Phase 5)

These are foundational items that the Step 8 decomposition and the per-step judge quality gates both depend on:

| ID | Task | Unblocks |
|----|------|----------|
| **5D-1** | Create `cxif-pattern-library.json` | Structural compliance BDD for Steps 3–6 |
| **5D-2** | Complete strategyzer enrichments (assessment_scale) | Step 2 structural validation |
| **5D-3** | Add CXIF library loader | Step definition access to CXIF vocabulary |
| **5D-6** | Generalize `judge.py` → `evaluate_step_quality()` | Per-step judge functions |

### Tier 2: Per-Step Quality Gates (from Orchestrator Plan Phase 5)

Once the infrastructure is in place:

| ID | Task |
|----|------|
| **5D-4 + 5D-5** | Structural compliance BDD scenarios + step definitions for Steps 3–6 |
| **5D-7** | Steps 2–7 judge evaluation functions |
| **5D-8 + 5D-9** | Judge BDD scenarios + step definitions for Steps 2–7 |

### Tier 3: Step 8 Decomposition (from Step 8 Plan)

Can proceed in parallel with Tier 2:

| Phase | Task |
|-------|------|
| **8a** | Evidence audit — assess existing evidence per assumption |
| **8b** | LLM-powered card selection from full 44-card library |
| **8c** | Path sequencing using library metadata + Precoil rules |
| **8d** | Context-specific brief and worksheet generation |
| **7-flex** | Step 7: Allow 2–5 assumptions per category (parallel track) |

### Tier 4: Audit Trail (from Orchestrator Plan Phase 6)

Depends on Tiers 1–2 being stable:

| Task | Description |
|------|-------------|
| WorkerAuditLog table | DB table for LLM interaction recording |
| AuditLogger class | Utility injected into BaseWorker.run() |
| API endpoint | GET /runs/{id}/audit |
| Structured logging | JSON output for docker logs visibility |

### Tier 5: Cross-Cutting Improvements (from Per-Step Codebase Review)

Six improvement areas identified through a deep review of all 8 step implementations, the frontend, export pipeline, API layer, and session management. These are **not covered** by any of the three planned work streams (quality gates, Step 8 decomposition, audit trail).

#### 5a. Step 7→8 Structured Data Passing (Critical Fragility)

Step 8's `_extract_top_assumptions()` parses Step 7's markdown output by splitting on the heading `"## Importance × Evidence Map"` and then parsing pipe-delimited table rows. If Step 7's rendering changes (heading text, table format, unicode character for ×), Step 8 **silently returns zero assumptions** — producing empty selections, plans, worksheets, and cards with no error raised.

**Fix**: Pass the structured `Step7Output` Pydantic model (or its dict representation) between steps via state, instead of re-parsing markdown. This requires adding a `step7_structured` key to `BMIWorkflowState`.

**Priority**: HIGH — prerequisite for reliable Step 8 decomposition work.

#### 5b. Frontend Display Misalignment (UX Bugs)

| ID | Issue | Severity |
|----|-------|----------|
| F-1 | `fit_assessment` is rendered on Step 5 instead of Step 6. `Step5ValueProposition.jsx` reads it from state, but Step 6 produces it. `Step6BusinessModel.jsx` never renders it. | Medium |
| F-2 | Step 7 has no structured rendering — dumps entire `assumptions` markdown into a single `<ReactMarkdown>` block. No parsed table, no interactive quadrant view, no editable per-assumption placement. The consultant is supposed to *confirm* the LLM's suggested quadrant assignments. | High |
| F-3 | Step 6 is a single-tab view for a 2-artifact step (BMC + Fit Assessment). Compare with Steps 4 and 5, which each have 2 tabs. | Medium |
| F-5 | Step 1 coverage gaps rendered as raw `JSON.stringify()` instead of a formatted table. | Low |
| F-6 | Step 3 "Empathy Questions" tab is read-only — no `editMode` branch, unlike the other two tabs. | Low |
| F-7 | `PaginationControls.jsx` exists but is imported nowhere — dead code. | Trivial |

#### 5c. Export Pipeline Gaps (Data Loss)

| ID | Issue | Severity |
|----|-------|----------|
| E-1 | PPTX and markdown exports **omit Zone B experiment card evidence** (status, owner, what_customers_said, decision). If a consultant captures evidence through interactive cards, none appears in reports. | High |
| E-2 | Markdown export drops `pattern_rationale` (Step 2 LLM reasoning) — variable is read but never written to output. | Medium |
| E-3 | Markdown export omits `empathy_gap_questions` and `supplemental_voc` (Step 3). | Medium |
| E-4 | No partial export — a consultant at a mid-workflow checkpoint has no export option. Export buttons only appear on Step 8 when `run_status === 'completed'`. | Medium |

#### 5d. Session Lifecycle Management

| ID | Issue | Severity |
|----|-------|----------|
| S-1 | No `DELETE /runs/{id}` endpoint or UI. Sessions accumulate forever in PostgreSQL. | Medium |
| S-2 | `state_json` vs `StepOutput` drift: when experiment card evidence is edited post-completion, `WorkflowRun.state_json` is updated but `StepOutput` for Step 8 is not. `GET /runs/{id}/step/8` returns stale data. | Medium |
| S-3 | Export temp files (`tempfile.NamedTemporaryFile(delete=False)`) accumulate on disk — never cleaned up. | Low |
| S-4 | Frontend session list has no search, filter, pagination, or delete. | Low |

#### 5e. State Model Correctness

| ID | Issue | Severity |
|----|-------|----------|
| SM-1 | `signal_recommendations` is written by Step 1 (`step1_signal_llm.py:169`) but not declared in `BMIWorkflowState` and **never consumed by any downstream step**. Step 2 doesn't use it for pattern selection. The experiment candidates could inform Step 8. | Medium |
| SM-2 | `REQUIRED_UPSTREAM_STATE` for `step8_pdsa` includes `experiment_selections` — Step 8's *own output*, not upstream data. `POST /runs/start-from-step` with `step8_pdsa` always fails unless Step 8 has already run once. | Medium (bug) |
| SM-3 | Checkpoint naming inconsistency: Steps 1, 2, 7 use legacy names (`checkpoint_1`, `checkpoint_1_5`, `checkpoint_2`) while Steps 3–6, 8 use sequential names. `checkpoint_2` landing on Step 7 is confusing. | Low |

#### 5f. Missing Enum Constraints on Pydantic Models (Silent LLM Drift)

| Step | Field | Documented Valid Values | Current Type |
|------|-------|------------------------|--------------|
| 4 | `SuccessMeasure.driver_type` | Time, Effort, Volume, Cost, Satisfaction, Revenue | `str` |
| 4 | `FrictionPoint.friction_type` | Delay, Effort, Confusion, Access, Cost | `str` |
| 6 | `BMCBuildingBlock.building_block` | 9 named BMC blocks | `str` |
| 7 | `DVFAssumption.suggested_quadrant` | Test first, Monitor, Deprioritize, Safe zone | `str` |

Without `Literal` or `Enum` constraints, the LLM can return novel values that pass Pydantic validation but break downstream logic. Step 8 depends on `quadrant == "Test first"` being exact — if the LLM returns `"test first"` (lowercase), that assumption is silently excluded from experiment selection.

### Tier 6: Future Release Candidates (from Orchestrator Plan)

Deferred until Phases 1–6 are complete:

| ID | Description |
|----|-------------|
| FR-1a | 8th Signal Zone — Value Network Shift |
| FR-1b–c | Enabling Technology and Trajectory filter refinements |
| FR-2 | Exploit Portfolio Assessment Library |

### Out of Scope (from Release 1.0)

Explicitly deferred to a future "Release 2.0 (Hybrid Conversational)":
- Multiple alternatives mechanism (2–3 VP Canvas or BMC options)
- Conversational loops within steps (Option B from the conversational analysis)
- Library ceiling surfacing in Step 8
- Full RPV Assessment in Step 1

---

## 6. Observations and Review of Today's Analysis

### 6.1 The Implementation Plan Audit Is Accurate But Needs Context

The implementation-plan-vs-codebase-audit.md correctly identified that Phases 5–6 are not started. However, it assessed the situation purely against the orchestrator plan without accounting for the Release 1.0 plan — which delivered substantial quality improvements that the orchestrator plan deferred to Phase 5. Specifically:

- **Prompt scoping** (Phase 5's concern about "full SKILL.md loading") was solved by Release 1.0 Task 3.1 — phase-specific prompt files now exist
- **VoC evidence grounding** (Phase 5's concern about evidence drift) was partially solved by Release 1.0 Task 3.4 — Steps 5 and 6 now receive VoC data
- **Step 7 methodology** was not in the orchestrator plan at all — it was identified by the workflow audit and fixed in Release 1.0

This means the remaining Phase 5 scope is more precisely:
1. CXIF pattern library + structural compliance BDD (the vocabulary validation layer)
2. Generic judge function + per-step judge evaluations (the LLM quality gate layer)
3. Minor hardening (Step 8 Pydantic migration, _structured parallel keys)

### 6.2 The Step 8 Decomposition Plan Overlaps with the Orchestrator Plan's Phase 5

The orchestrator plan's Phase 5D-10 says "Add Pydantic models for Step 8 output." The Step 8 decomposition plan's Phase 2 (8b Card Selection) introduces LLM-powered selection that would naturally use Pydantic structured output. These are the same concern approached from different angles.

Similarly, the orchestrator plan envisions the CXIF pattern library feeding structural compliance checks for Steps 3–6. The Step 8 decomposition plan envisions the experiment library feeding evidence-aware card selection. Both follow the same pattern: **domain vocabulary library → structural validation → LLM-backed reasoning**. The Step 8 work is simply further ahead because the experiment library already exists.

### 6.3 Two Planning Documents Are Now Stale

The **Diagnosing Steps 3–5** document and the **Full Workflow Audit** identified problems that have all been resolved by Release 1.0. These documents are historical — they should not drive new work. The Release 1.0 plan that consumed their findings is also fully implemented.

The **Converting to Conversational AI Agent** analysis remains relevant as a strategic reference. Option B (hybrid conversational) is the identified medium-term direction, and nothing in the current codebase precludes it. But no work toward it has been started.

### 6.4 The Quick Win Went Further Than Planned

The Step 8 decomposition plan's Phase 0 specified expanding from 9 to ~23 cards with a single LLM call for differentiation. The actual implementation:
- Expanded to **44 cards** (all cards in the library), not 23
- Used **word-overlap scoring** instead of an LLM call (simpler, deterministic, faster)
- Also fixed the precoil-emt library identity contradiction (not in any plan)

This means Phase 0 is complete, and the Phase 2 (8b Card Selection with LLM) is the next natural step when the word-overlap scoring proves insufficient for nuanced selection.

### 6.5 The Orchestrator Plan Has a Date-of-Writing Problem

The orchestrator plan was written on Mar 26 — before the Release 1.0 analysis existed (Apr 15). Its Phase 5 "Current State baseline" table describes the codebase as it was in late March, not as it is now. For example:
- It says Step 2 has "Partial — post-hoc validation only." This was true in March but Step 2 has since been validated as the gold standard.
- It says Steps 3–6 have "No" quality gate. Release 1.0 improved all of them with supplier perspective, prompt scoping, and empathy gate improvements — though none of these are LLM-as-Judge quality gates.
- It doesn't mention `suggested_quadrant`, DVFTension structured model, or phase-specific prompt files, because those didn't exist yet.

The orchestrator plan should be updated to reflect the current baseline before Phase 5 work begins.

---

## 8. Per-Step Implementation Scorecard

A deep review of all 8 step implementations, their prompts, Pydantic models, and BDD coverage produced the following quality summary:

| Step | Purpose | Prompt | Model | BDD Scenarios | Critical Gaps |
|------|---------|--------|-------|:-------------:|---------------|
| 1 — Signal Scan | SOC Radar signals | Strong (in-code) | Strong (5 models) | 3 + judge | `signal_recommendations` missing from TypedDict; no retry on LLM failure; prompt lives in code, not in `prompts/` |
| 2 — Pattern Match | Hybrid shortlist + LLM | Strong (.md) | Good | 3 + 8 affinity | No fallback-path BDD test; `signal_recommendations` orphaned |
| 3 — Empathy Profile | CXIF jobs/pains/gains | Strong (.md) | Good | 4 | Gate only checks empty sections, not quality; no `min_length` on lists |
| 4 — Value Drivers | VDT + Context Analysis | Strong (.md) | Strong | 2 | Thinnest test coverage; VoC truncation silent; no enum constraints |
| 5 — Value Proposition | VPC Design | Strong (.md) | Good | 2 | No cross-reference validation (pain_addressed/gain_addressed are free-text); no quality gate |
| 6 — Business Model | BMC + Fit Assessment | Strong (.md) | Good | 2 | No building-block count enforcement; VoC truncation silent; `fit_assessment` not rendered in frontend |
| 7 — Risk Map | DVF Assumptions | Very Strong (.md) | Very Strong | 2 | Markdown format fragility for Step 8 parsing; `suggested_quadrant` not enum-constrained |
| 8 — PDSA Plans | Experiment cards | N/A (deterministic) | Good (dataclass) | 3 | `_extract_top_assumptions` fragile; EXPERIMENT_MATRIX sync risk with library; dead code in `_format_precoil_brief` |

### Top 5 Systemic Issues

1. **Step 7→8 markdown coupling** — the most critical fragility point. A single heading change in Step 7's rendering breaks all of Step 8 silently.
2. **No LLM retry/fallback** on Steps 1, 3–7. A single LLM failure crashes the entire workflow with no partial state save. Only Step 2 has a `try/except` with fallback.
3. **Judge coverage is Step 1 only** — Steps 2–8 have no automated quality assessment.
4. **`signal_recommendations` is orphaned** — Step 1 generates it (with `experiment_candidate`), no step consumes it, and it's not in the TypedDict.
5. **Test coverage skew**: Steps 2 + pattern-affinity have 11 scenarios; Steps 4, 5, 6, 7 have only 2 each.

---

## 9. Recommended Next Actions

### Priority A: Pre-requisites (address before or alongside quality gate work)

1. **Fix Step 7→8 structured data passing** (Tier 5a) — add `step7_structured` key to `BMIWorkflowState` and pass the Pydantic model dict instead of re-parsing markdown. This is a prerequisite for reliable Step 8 decomposition.

2. **Add `Literal` constraints to Pydantic models** (Tier 5f) — constrain `suggested_quadrant`, `driver_type`, `friction_type`, `building_block` to their documented values. Prevents silent LLM drift, especially the `"Test first"` case-sensitivity issue.

3. **Fix `REQUIRED_UPSTREAM_STATE` bug** (Tier 5e, SM-2) — remove `experiment_selections` from Step 8's required upstream state. One-line fix.

4. **Add `signal_recommendations` to `BMIWorkflowState`** (Tier 5e, SM-1) — declare the field so type checkers can validate it. Design decision needed: should Step 2 or Step 8 consume the experiment candidates?

### Priority B: Planned work streams (unchanged)

5. **Update the orchestrator plan's Phase 5 baseline table** to reflect Release 1.0 improvements.

6. **Proceed with 5D-1 (cxif-pattern-library.json)** — critical-path artifact for structural compliance BDD.

7. **Proceed with 5D-6 (generalize judge.py)** — key engineering task for per-step quality gates.

8. **Treat Step 8 decomposition Phases 1–4 as a parallel track.**

### Priority C: UX and data completeness

9. **Fix frontend display misalignment** (Tier 5b) — move `fit_assessment` from Step 5 to Step 6, add Fit Assessment tab to Step 6, format Step 1 coverage gaps as a table.

10. **Build structured Step 7 rendering** (Tier 5b, F-2) — parsed assumption table with editable quadrant assignment. Critical for the consultant's confirm/override workflow.

11. **Fix export data loss** (Tier 5c) — add Zone B evidence to PPTX/markdown exports, include `pattern_rationale` and `empathy_gap_questions` in markdown export.

12. **Enable partial export** (Tier 5c, E-4) — allow report generation at any checkpoint, not just after Step 8 completion.

### Priority D: Lifecycle and housekeeping

13. **Add session delete endpoint and UI** (Tier 5d, S-1).

14. **Fix `StepOutput` drift** (Tier 5d, S-2) — update `StepOutput` when experiment card evidence is edited.

15. **Clean up export temp files** (Tier 5d, S-3) — use context manager or `BackgroundTask` deletion in FastAPI.

16. **Defer Phase 6 (audit trail)** until Phase 5 quality gates are stable.

17. **Archive the diagnosis and audit documents** (Diagnosing Steps 3–5, Full Workflow Audit) as historical references.
