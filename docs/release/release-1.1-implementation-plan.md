# Release 1.1 Implementation Plan

**Date:** 2026-04-18
**Approach:** BDD-first — review and edit feature files to define the behavioral contract, then implement production code to make tests pass (RED → GREEN).
**Baseline:** 106 tests across 18 feature files, all passing.

---

## Strategy

The project-evolution-and-plan-review.md identified 4 priority bands (A–D) of improvements. This plan operationalizes them into a phased implementation sequence where **each phase starts with feature file edits** that define the behavioral contract, followed by production code changes to make the new scenarios pass.

**Key principle:** Feature files define *what* the system must do. Step definitions define *how* to test it (mocks, fixtures, assertions). Production code makes tests pass. We never alter feature files to accommodate code — we alter code to satisfy features.

---

## Phase 0: Quick Fixes (no feature file changes needed)

These are correctness bugs that can be fixed immediately. They don't change behavior visible in feature files — they fix state model declarations and checkpoint configuration.

### 0-1. Fix `REQUIRED_UPSTREAM_STATE` for Step 8

**Problem:** `step8_pdsa` requires `experiment_selections` — its own output, not upstream data. `start-from-step` with step 8 always fails unless Step 8 has already run.

**File:** `backend/app/checkpoints.py`
**Change:** Remove `experiment_selections` from the `step8_pdsa` tuple in `REQUIRED_UPSTREAM_STATE`.

**Verification:** The existing `start-from-step.feature` scenarios test steps 1, 3, and boundary cases. We add no new scenario — the fix is internal correctness. Verify by running `pytest backend/tests/test_bdd_start_from_step.py -q` (no regression).

### 0-2. Add `signal_recommendations` to `BMIWorkflowState`

**Problem:** Step 1 writes `signal_recommendations` to state but the TypedDict doesn't declare it. Type checkers can't validate it.

**File:** `backend/app/state.py`
**Change:** Add `signal_recommendations: list[dict[str, object]]` to `BMIWorkflowState`.

**Verification:** No feature change needed. Existing Step 1 tests pass unchanged.

### 0-3. Normalize checkpoint naming

**Problem:** Steps 1, 2, 7 use legacy names (`checkpoint_1`, `checkpoint_1_5`, `checkpoint_2`) while Steps 3–6, 8 use sequential names. `checkpoint_2` on Step 7 is confusing.

**Files:** `backend/app/checkpoints.py`, `backend/tests/features/workflow-checkpoints.feature`, `backend/tests/test_bdd_workflow_checkpoints.py`

**Change:**
- Rename in `CHECKPOINTS_BY_STEP`:
  - `checkpoint_1` → `checkpoint_1` (keep — already correct)
  - `checkpoint_1_5` → `checkpoint_2` (Step 2)
  - `checkpoint_2` → `checkpoint_7` (Step 7)
- Update `workflow-checkpoints.feature` scenario: change `checkpoint_1_5` → `checkpoint_2` and the old `checkpoint_2` → `checkpoint_7`.
- Update step definitions to match.

**Note:** This is a feature file change, but it's correcting the contract to match the intended naming, not altering behavior. The checkpoint-decisions.feature is unaffected (it tests decision values, not checkpoint names).

---

## Phase 1: Enum Constraints and Structured Data Passing (Priority A)

These changes harden the data contracts between steps. Feature files are updated to assert that output values use valid vocabulary.

### 1-1. Feature file edits: Step 7 enum constraint

**File:** `backend/tests/features/step7-risk.feature`

**Add new scenario:**
```gherkin
Scenario: Step 7 assumptions use only valid quadrant values
  Given a workflow state with completed Step 6 design outputs
  When the Step 7 risk mapper node runs
  Then every assumption quadrant is one of "Test first, Monitor, Deprioritize, Safe zone"
```

**Production code change:** In `backend/app/nodes/step7_risk_llm.py`, change `DVFAssumption.suggested_quadrant` from `str` to `Literal["Test first", "Monitor", "Deprioritize", "Safe zone"]`.

**Step definition:** Parse the importance-evidence matrix rows and assert each quadrant value is in the allowed set. This reuses the existing markdown parsing pattern from `test_bdd_step7_risk.py`.

### 1-2. Feature file edits: Step 4 enum constraints

**File:** `backend/tests/features/step4-vpm.feature`

**Add new scenario:**
```gherkin
Scenario: Step 4 outputs use valid driver and friction types
  Given a workflow state with a completed Step 3 empathy profile
  When the Step 4 VPM synthesizer node runs
  Then every success measure driver type is one of "Time, Effort, Volume, Cost, Satisfaction, Revenue"
  And every friction point friction type is one of "Delay, Effort, Confusion, Access, Cost"
```

**Production code changes:**
- `SuccessMeasure.driver_type`: `str` → `Literal["Time", "Effort", "Volume", "Cost", "Satisfaction", "Revenue"]`
- `FrictionPoint.friction_type`: `str` → `Literal["Delay", "Effort", "Confusion", "Access", "Cost"]`

**Step definitions:** Parse the markdown tables for value driver tree and friction points, assert each type value is in the allowed set.

### 1-3. Feature file edits: Step 6 BMC building block constraint

**File:** `backend/tests/features/step6-design.feature`

**Add new scenario:**
```gherkin
Scenario: Step 6 business model canvas contains all 9 BMC building blocks
  Given a workflow state with a completed Step 5 value proposition canvas
  When the Step 6 design canvas node runs
  Then the business model canvas contains all 9 standard BMC building blocks
  And the desirability section contains "Customer Segments, Value Proposition, Channels, Customer Relationships"
  And the feasibility section contains "Key Partnerships, Key Activities, Key Resources"
  And the viability section contains "Revenue Streams, Cost Structure"
```

**Production code change:** In `backend/app/nodes/step6_design_llm.py`, add a `Literal` constraint on `BMCBuildingBlock.building_block` with the 9 valid names. Add post-processing validation that all 9 blocks are present (3 desirability + 3 feasibility + 2 viability = 8, plus the shared "Value Proposition" = 9). If the LLM omits a block, raise a `ValueError` that triggers a retry rather than silently producing an incomplete BMC.

### 1-4. Step 7→8 structured data passing

**File:** `backend/tests/features/step7-risk.feature`

**Add new scenario:**
```gherkin
Scenario: Step 7 stores structured assumption data alongside markdown
  Given a workflow state with completed Step 6 design outputs
  When the Step 7 risk mapper node runs
  Then the workflow state contains structured step 7 output
  And the structured output has 3 DVF categories with 3 assumptions each
  And every structured assumption has a suggested quadrant
```

**File:** `backend/tests/features/step8-pdsa.feature`

**Edit existing Given step** for all 3 scenarios: The fixture that creates "a workflow state with completed Step 7 risk outputs" must now include a `step7_structured` key containing the structured dict alongside the markdown `assumptions` key.

**Add new scenario:**
```gherkin
Scenario: Step 8 reads structured data instead of parsing markdown
  Given a workflow state with completed Step 7 risk outputs
  When the Step 8 PDSA experiment designer node runs
  Then the experiment cards reference assumptions from the structured step 7 output
  And the experiment card count matches the number of test-first assumptions in structured output
```

**Production code changes:**
1. `backend/app/state.py`: Add `step7_structured: dict[str, object]` to `BMIWorkflowState`.
2. `backend/app/nodes/step7_risk_llm.py`: After building the markdown, also store the `Step7Output` model dict in state under `step7_structured`.
3. `backend/app/nodes/step8_pdsa.py`: Rewrite `_extract_top_assumptions()` to prefer `state.get("step7_structured")` over markdown parsing. Fall back to markdown parsing for backward compatibility with existing sessions.

**Risk:** This changes Step 8's data source. The existing 3 Step 8 scenarios must still pass — they validate the same outputs regardless of data source. The markdown fallback ensures backward compatibility.

---

## Phase 2: Test Coverage Equalization (Steps 4, 5, 6, 7)

Steps 4–7 each have only 2 BDD scenarios. Steps 1, 2, 3, and 8 have 3–4+. This phase brings the thin steps up to parity with focused structural validation scenarios.

### 2-1. Feature file edits: Step 4 additional scenarios

**File:** `backend/tests/features/step4-vpm.feature`

**Add:**
```gherkin
Scenario: Step 4 value driver tree includes measurable targets
  Given a workflow state with a completed Step 3 empathy profile
  When the Step 4 VPM synthesizer node runs
  Then the value driver tree includes at least 3 success measures
  And every success measure has a non-empty baseline and target

Scenario: Step 4 context analysis grounds problem statements in VoC
  Given a workflow state with a completed Step 3 empathy profile
  When the Step 4 VPM synthesizer node runs
  Then the actionable insights include at least 1 problem statement
  And the actionable insights include at least 1 friction point
```

**Step definitions:** Parse the markdown tables for success measures (count rows, check baseline/target columns non-empty) and context analysis (check problem statement and friction point sections).

**Production code:** No changes expected — these scenarios validate existing behavior.

### 2-2. Feature file edits: Step 5 additional scenarios

**File:** `backend/tests/features/step5-define.feature`

**Add:**
```gherkin
Scenario: Step 5 value proposition canvas distinguishes supplier products from customer needs
  Given a workflow state with completed Step 4 outputs
  When the Step 5 define model node runs
  Then the value proposition canvas includes at least 2 products or services
  And the value proposition canvas includes at least 2 pain relievers
  And the value proposition canvas includes at least 2 gain creators
```

**Step definitions:** Parse the markdown tables under "Products & Services", "Pain Relievers", and "Gain Creators" sections and count rows.

**Production code:** No changes expected — these scenarios validate existing behavior.

### 2-3. Feature file edits: Step 6 additional scenario

**File:** `backend/tests/features/step6-design.feature`

Already covered by Phase 1-3 (BMC building block count). One additional scenario:

**Add:**
```gherkin
Scenario: Step 6 fit assessment includes all three fit levels
  Given a workflow state with a completed Step 5 value proposition canvas
  When the Step 6 design canvas node runs
  Then the fit assessment includes a problem-solution fit section
  And the fit assessment includes a product-market fit section
  And the fit assessment includes a business-model fit section
```

**Step definitions:** Assert presence of the three section headings in the `fit_assessment` markdown.

**Production code:** No changes expected.

### 2-4. Feature file edits: Step 7 additional scenario

**File:** `backend/tests/features/step7-risk.feature`

Already covered by Phase 1-1 (quadrant enum) and Phase 1-4 (structured output). One additional scenario:

**Add:**
```gherkin
Scenario: Step 7 DVF tensions identify cross-category conflicts
  Given a workflow state with completed Step 6 design outputs
  When the Step 7 risk mapper node runs
  Then the assumptions include at least 1 DVF tension
  And each DVF tension references two assumptions from different categories
```

**Step definitions:** Parse the DVF Tensions table, assert each tension row has `categories_in_conflict` spanning at least 2 different DVF categories. Use the structured output (from Phase 1-4) if available, fall back to markdown parsing.

**Production code:** No changes expected — the existing `Step7Output` model already enforces `min_length=1` for `dvf_tensions`.

---

## Phase 3: Export and State Correctness

These scenarios test the reporting pipeline and state model — areas not currently covered by any feature file.

### 3-1. New feature file: `export-report.feature`

**File:** `backend/tests/features/export-report.feature`

```gherkin
Feature: Report export
  The export pipeline must produce complete reports that include all
  workflow artifacts, including experiment card evidence.

  Scenario: Markdown export includes all step outputs
    Given a completed workflow run with all 8 steps
    When the markdown report is generated
    Then the report includes a Step 1 signal scan section
    And the report includes a Step 2 pattern rationale
    And the report includes a Step 3 customer profile section
    And the report includes a Step 6 fit assessment section
    And the report includes a Step 8 experiment selections section

  Scenario: Markdown export includes experiment card evidence
    Given a completed workflow run with experiment card evidence captured
    When the markdown report is generated
    Then the report includes experiment card status and evidence fields
    And the report includes the evidence decision for each card

  Scenario: Markdown export works for partial runs
    Given a workflow run paused at step 3
    When the markdown report is generated
    Then the report includes steps 1 through 3 only
    And the report does not include step 4 or later sections
```

**Step definitions:** Call `build_report()` from `export_report.py` with mock state dicts. Assert section presence via substring matching. For the evidence scenario, construct a state dict with Zone B fields populated. For the partial scenario, construct a state dict with only steps 1–3 fields.

**Production code changes:**
1. `backend/cli/export_report.py`: Add `pattern_rationale` to the report output. Add `empathy_gap_questions` and `supplemental_voc` when present. Add Zone B evidence fields to `_render_experiment_cards()`.
2. Enable partial export by checking which step fields are present rather than assuming all 8.

### 3-2. Feature file edit: `start-from-step.feature`

**Add scenario testing the Phase 0-1 fix:**
```gherkin
Scenario: Starting at step 8 with complete upstream state succeeds
  Given initial state with upstream fields for step 8
  When the workflow is started from step 8
  Then the run status is "paused"
  And the pending checkpoint is "checkpoint_8"
```

**Step definition:** The fixture creates a state dict with all fields through step 7 (`assumptions` but NOT `experiment_selections`). This validates the Phase 0-1 fix.

---

## Phase 4: Step 7→8 Resilience Hardening

This phase strengthens the Step 8 parser and the LLM error handling across steps.

### 4-1. Feature file edits: Step 8 graceful degradation

**File:** `backend/tests/features/step8-pdsa.feature`

**Add:**
```gherkin
Scenario: Step 8 produces empty artifacts when no test-first assumptions exist
  Given a workflow state with Step 7 output containing zero test-first assumptions
  When the Step 8 PDSA experiment designer node runs
  Then the workflow state contains empty experiment selections
  And the workflow state contains empty experiment cards
  And the workflow current step is "pdsa_plan"
```

**Step definition:** Create a Step 7 fixture where all 9 assumptions have `suggested_quadrant` as "Monitor" or "Deprioritize" — none are "Test first". Step 8 should produce empty but valid output without errors.

**Production code:** Verify `_build_outputs()` handles the empty-assumptions path cleanly. If it raises, fix the production code.

### 4-2. Feature file edits: Step 8 backward compatibility

**File:** `backend/tests/features/step8-pdsa.feature`

**Add:**
```gherkin
Scenario: Step 8 falls back to markdown parsing when structured data is absent
  Given a workflow state with Step 7 markdown output but no structured data
  When the Step 8 PDSA experiment designer node runs
  Then the workflow state contains experiment selections
  And the workflow state contains structured experiment cards
```

**Step definition:** Create a fixture with `assumptions` (markdown) but no `step7_structured` key. Validates the fallback path from Phase 1-4.

---

## Phase 5: LLM Error Resilience (New Feature)

This is a new behavioral concern — currently no feature file covers LLM failure scenarios.

### 5-1. New feature file: `llm-error-handling.feature`

**File:** `backend/tests/features/llm-error-handling.feature`

```gherkin
Feature: LLM error handling
  When the LLM fails or returns invalid output, the workflow must
  handle the error gracefully rather than crashing silently.

  Scenario: Step node retries on LLM structured output failure
    Given a workflow state with VoC data "Customers need faster onboarding"
    And the LLM is configured to fail on the first call then succeed
    When the Step 1 signal scanner node runs
    Then the workflow state contains a signals list
    And the LLM was called exactly 2 times

  Scenario: Step node raises a clear error after max retries exhausted
    Given a workflow state with VoC data "Customers need faster onboarding"
    And the LLM is configured to always fail
    When the Step 1 signal scanner node runs expecting failure
    Then the error message indicates an LLM failure
    And the error message names the step that failed
```

**Step definitions:** Use mock/patch on the `structured_llm.invoke()` call to simulate failure. The first scenario mocks a transient failure (raises once, succeeds on retry). The second scenario mocks a permanent failure (always raises).

**Production code changes:** Add a retry wrapper (max 2 attempts) around `structured_llm.invoke()` in each step's `_llm.py` file. On final failure, raise a descriptive error with the step name.

**Design note:** This is infrastructure that affects all LLM-backed steps (1, 3, 4, 5, 6, 7). The feature file tests Step 1 as the representative case. The retry wrapper should be a shared utility, not duplicated per step.

---

## Implementation Sequence

| Order | Phase | Feature Files Touched | New Scenarios | Production Files Touched |
|:-----:|-------|----------------------|:-------------:|-----------------------------|
| 1 | Phase 0 | `start-from-step.feature` (verify only), `workflow-checkpoints.feature` | 0 | `checkpoints.py`, `state.py` |
| 2 | Phase 1 | `step7-risk.feature`, `step4-vpm.feature`, `step6-design.feature`, `step8-pdsa.feature` | 6 | `step7_risk_llm.py`, `step4_vpm_llm.py`, `step6_design_llm.py`, `step8_pdsa.py`, `state.py` |
| 3 | Phase 2 | `step4-vpm.feature`, `step5-define.feature`, `step6-design.feature`, `step7-risk.feature` | 5 | None expected (validate existing behavior) |
| 4 | Phase 3 | New `export-report.feature`, `start-from-step.feature` | 4 | `export_report.py` |
| 5 | Phase 4 | `step8-pdsa.feature` | 2 | `step8_pdsa.py` (error path only) |
| 6 | Phase 5 | New `llm-error-handling.feature` | 2 | All `step*_llm.py` files (retry wrapper) |

**Projected test count after all phases:** 106 (current) + 19 (new scenarios) = ~125 tests.

---

## What This Plan Does NOT Cover

These items from the project-evolution-and-plan-review.md are **explicitly deferred** from Release 1.1:

| Item | Reason |
|------|--------|
| **Frontend display fixes** (Tier 5b: F-1 through F-7) | Frontend changes don't need backend BDD coverage. Separate UI work stream. |
| **Session delete endpoint** (Tier 5d: S-1) | API lifecycle feature — separate work stream. |
| **PPTX export fixes** (Tier 5c: E-1 partially) | PPTX generation has its own audit tool. Markdown export is covered in Phase 3. |
| **CXIF pattern library** (Tier 1: 5D-1) | Requires domain research to define the vocabulary. Separate work stream per orchestrator plan Phase 5. |
| **Generalize judge.py** (Tier 1: 5D-6) | Depends on CXIF pattern library. Sequenced after 5D-1. |
| **Step 8 decomposition Phases 1–4** (Tier 3) | Parallel track per project evolution review. |
| **Audit trail** (Tier 4) | Deferred until quality gates are stable. |
| **Conversational hybrid** (Out of Scope) | Release 2.0 territory. |

---

## BDD Discipline Checklist

Before starting each phase:

- [ ] Read the existing `.feature` file(s) being modified
- [ ] Write/edit scenarios first — define the behavioral contract
- [ ] Run tests to confirm new scenarios FAIL (RED)
- [ ] Write step definitions with appropriate mocks and fixtures
- [ ] Implement production code to make tests PASS (GREEN)
- [ ] Run the full test suite to confirm no regressions
- [ ] Commit with a descriptive message referencing the phase number

**Critical rule:** If an existing test breaks because of a production code change, fix the production code — do not modify the existing scenario's behavioral assertion. Step definition infrastructure (fixtures, mocks, delay scaling) may be adjusted.
