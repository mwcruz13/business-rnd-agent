# Step 8 Redesign — Strategy, Implementation Plan, and Test Plan

**Date:** 2026-04-21
**Owner:** BMI Workflow Team
**Scope authorized:** Strict phased decomposition (Phases 1-4) + Phase 5 (Step 7 flexibility) + new Step 9 Artifact Designer.
**Builds on:** [docs/release/step8-decomposition-plan.md](step8-decomposition-plan.md)

---

## 1. Strategy

### Problem
Today's `step8_pdsa.py` is fully deterministic. It mechanically picks the weakest experiment per DVF category regardless of whether the VoC already contains evidence that could validate the assumption. Worksheets emit boilerplate ("A runnable artifact tailored for problem interviews"), forcing the consultant to fabricate the actual artifact.

### Approach
Decompose Step 8 into four sequential nodes (8a → 8b → 8c → 8d) so each LLM/rule call has a single responsibility, and add a new Step 9 that produces the concrete artifact (interview script, landing-page copy, prototype spec, mock-sale call sheet, etc.).

Step 7 is also relaxed to allow 2-5 assumptions per DVF category and to record the LLM's `voc_evidence_strength` per assumption so Step 8a doesn't start cold.

### Design principles
1. Behavior is owned by `.feature` files; production code is what changes to make tests pass.
2. Each node has a single responsibility and a typed, validated output schema.
3. Card names selected by the LLM are **constrained to the canonical 44-card library** — Step 8b/8c reject any card not present in `experiment-library.json`.
4. Evidence ordering can never decrease across the path (Weak → Medium → Strong, with same-tier repeats allowed when the library has no Strong card).
5. Existing `experiment_selections / experiment_plans / experiment_worksheets / experiment_cards` state contract is preserved — Step 8d populates them with richer content. Step 9 introduces a **new** state field `experiment_artifacts`.
6. Existing `update_experiment_card_evidence()` Zone A/B contract is unchanged.

---

## 2. Implementation Plan

### Phase 5 — Step 7 schema flexibility
**Files touched:**
- `backend/app/nodes/step7_risk_llm.py` — change `DVFCategory.assumptions` from `min_length=3, max_length=3` to `min_length=2, max_length=5`; add `voc_evidence_strength: Literal["None","Weak","Medium"]` field on `DVFAssumption`; update prompt and renderer.

**State change:** `step7_structured.categories[*].assumptions[*]` gains `voc_evidence_strength`.

### Phase 1 — Step 8a Evidence Audit (`step8a_evidence_audit.py`)
**Input:** `step7_structured`, `voc_data`, `customer_profile`, `signals` (Step 1 output), `interpreted_signals`.
**LLM call:** classifies each Test-first assumption against VoC/signal context.
**Output state field:** `assumption_evidence_audit: list[{assumption, category, existing_evidence_level, evidence_summary}]`.
- `existing_evidence_level ∈ {None, Weak, Medium}` (never auto-assigns Strong).
- Falls back to `voc_evidence_strength` from Step 7 when LLM is unavailable.

### Phase 2 — Step 8b Card Selection (`step8b_card_selection.py`)
**Input:** `assumption_evidence_audit`, full 44-card library.
**LLM call:** receives assumption text + category + existing evidence level + the **full** category card list. Returns 3-5 ranked cards with rationale.
**Constraints:** card names validated against `experiment-library.json`; selection must skip evidence tiers below `existing_evidence_level`.
**Output state field:** `experiment_card_selections: list[{assumption, category, existing_evidence_level, candidates: [{card_name, evidence_strength, rationale}], primary_card_name}]`.

### Phase 3 — Step 8c Path Sequencing (`step8c_path_sequencing.py`)
**Input:** `experiment_card_selections`, library card definitions.
**Logic:** rule-based using `usually_runs_next` graph + 5 Precoil sequencing rules. LLM call only validates path coherence per assumption (lightweight).
**Output state field:** `experiment_paths: list[{assumption, category, ordered_cards: [{card_name, evidence_strength, move_to_next_when, ceiling_warning?}]}]`.

### Phase 4 — Step 8d Brief & Worksheet Generation (`step8d_brief_generation.py`)
**Refactored from:** existing `_format_*` functions in `step8_pdsa.py`.
**Input:** `experiment_paths`, `assumption_evidence_audit`, `customer_profile`, `value_proposition_canvas`.
**LLM call:** generates assumption-specific success/failure thresholds, sample size scaled to risk, and "What You're Trying to Learn" tied to the actual assumption.
**Output state fields:** `experiment_selections`, `experiment_plans`, `experiment_worksheets`, `experiment_cards` — same shapes as today, richer content.
**Preserved:** Zone A/B `update_experiment_card_evidence()` contract.

### Step 9 — Artifact Designer (`step9_artifact.py`)
**Input:** `experiment_cards` (from 8d), `customer_profile`, `value_proposition_canvas`, `voc_data`.
**LLM call:** for each primary card, generate the concrete artifact:
  - `Problem Interviews` → 8-12 open-ended questions, intro script, segmentation criteria.
  - `Solution Interviews` → solution stimulus + 6-10 reaction questions.
  - `Surveys / Questionnaires` → 8-15 ranked + open questions, screening logic.
  - `Landing Page` → headline, sub-headline, value bullets, CTA copy, success metric definition.
  - `Fake Door` → button copy, modal explanation, capture form fields.
  - `Wizard of Oz` / `Concierge Test` → manual workflow script + ops checklist.
  - `Mock Sale` / `Letter of Intent` → pitch script, pricing slide, LoI template.
  - `Pre-Order Test` → checkout flow copy + refund policy + threshold.
  - Any card → fallback: structured "what to build" spec with audience, channel, instrumentation.
**Output state field:** `experiment_artifacts: list[{card_id, card_name, artifact_type, artifact_markdown}]`.
**Worksheet integration:** Step 9 also rewrites the `Asset needed` line in each worksheet to point at the generated artifact (by id reference).

### Wiring
- `backend/app/state.py` — add 4 new fields: `assumption_evidence_audit`, `experiment_card_selections`, `experiment_paths`, `experiment_artifacts`.
- `backend/app/workers/steps.py` — replace `ExperimentPlanWorker` with `EvidenceAuditWorker`, `CardSelectionWorker`, `PathSequencingWorker`, `BriefGenerationWorker`, `ArtifactDesignerWorker`.
- `backend/app/workers/registry.py` — register the 5 new workers in order, removing the old one.
- `backend/app/graph.py` — no change (orchestrator drives via registry).
- `backend/app/nodes/step8_pdsa.py` — keep `update_experiment_card_evidence()` and helper formatters (consumed by 8d). Delete `run_step` once 8d ships and update the export-report CLI.
- `backend/cli/main.py` — extend output sections to include `experiment_artifacts`.
- `backend/cli/export_report.py` — render artifacts.

---

## 3. Test Plan (BDD-TDD)

Each phase ships with a `.feature` file driving production code via pytest-bdd. Mocks for the LLM live in step definitions only.

### Phase 5 — `step7-risk.feature` updates
- Scenario: a narrow VoC produces 2 Viability assumptions (not forced to 3).
- Scenario: a rich VoC produces 5 Desirability assumptions.
- Scenario: each assumption carries a `voc_evidence_strength` ∈ {None, Weak, Medium}.

### Phase 1 — new `step8a-evidence-audit.feature`
- Scenario: Test-first assumption about delivery delays + VoC containing 14 months of delivery complaints → `existing_evidence_level = Weak` with non-empty `evidence_summary`.
- Scenario: Test-first assumption about CXL adoption + VoC silent on CXL → `existing_evidence_level = None`.
- Scenario: All Test-first assumptions are audited.
- Scenario: Audit output is well-formed and persisted in state under `assumption_evidence_audit`.

### Phase 2 — new `step8b-card-selection.feature`
- Scenario: two Desirability Test-first assumptions with different content produce different primary cards.
- Scenario: a Feasibility assumption with `existing_evidence_level=Weak` skips Weak cards and starts at Medium.
- Scenario: every selected card name validates against `experiment-library.json`.
- Scenario: selections include 3-5 ranked candidates per assumption with rationale.
- Scenario: across a diverse VoC fixture set, ≥15 of 44 cards are reachable.

### Phase 3 — new `step8c-path-sequencing.feature`
- Scenario: Desirability path correctly terminates at Medium evidence (library has no Strong Desirability card).
- Scenario: Feasibility path can reach Strong evidence via Concierge / Wizard of Oz / MVP.
- Scenario: every consecutive pair satisfies `usually_runs_next` OR a documented sequencing exception.
- Scenario: evidence ordering never decreases.

### Phase 4 — `step8-pdsa.feature` updates
- Scenario: success criteria for a delivery-delay assumption mentions delivery timelines (not generic percentages).
- Scenario: two different assumptions produce different "What You're Trying to Learn" sections.
- Scenario: existing Zone A/B enforcement still works.
- Scenario: existing experiment-card structure (id, status, evidence) preserved.
- Existing scenarios continue to pass.

### Step 9 — new `step9-artifact-designer.feature`
- Scenario: a Problem Interviews card produces a script with 8-12 open-ended questions and an intro paragraph.
- Scenario: a Landing Page card produces a headline + 3-5 value bullets + CTA copy + a success metric definition.
- Scenario: a Mock Sale card produces a pitch script and a pricing artifact.
- Scenario: an unknown / fallback card produces a structured "what to build" spec.
- Scenario: each `experiment_artifact` references a `card_id` from `experiment_cards`.
- Scenario: worksheet `Asset needed` line is updated to reference the generated artifact id.

### Regression
- `docker compose exec -T bmi-backend pytest backend/tests -q` must pass at the end of each phase.
- `test_graph.py`, `test_cli.py`, `test_workflow.py`, `test_bdd_step8_pdsa.py` must continue to pass at every phase boundary; `step8_pdsa` deterministic helpers stay until 8d replaces them.

---

## 4. Migration & rollback

- Phases 1-3 add new state fields and new nodes without removing the old `step8_pdsa` worker. Rollback = revert worker registration.
- Phase 4 swaps the old worker out. Rollback = re-register `ExperimentPlanWorker`.
- Step 9 is purely additive. Rollback = drop registration.
- Phase 5 schema relaxation is backward compatible (3 assumptions still valid).
