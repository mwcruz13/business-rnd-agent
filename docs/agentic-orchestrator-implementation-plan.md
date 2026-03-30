# Agentic Orchestrator Implementation Plan

## Purpose

This document is the working implementation reference for refactoring the BMI Consultant App internals from a sequential LangGraph step chain into a LangGraph orchestrator plus agent-oriented worker model, without changing the external workflow contract or losing checkpoint behavior.

It is based on:

- The current runtime structure in `backend/app/graph.py`, `backend/app/workflow.py`, and `backend/app/checkpoints.py`
- The architecture recommendation in the standalone BMI strategy document
- The LangGraph orchestrator-worker and routing patterns reviewed from the attached LangGraph reference
- The existing workflow-level BDD contracts that already protect checkpoint and completion behavior

## Strategy

1. Preserve the public workflow surface.
   The API, CLI, persisted workflow state shape, and checkpoint behavior remain stable while the internal execution model changes.

2. Introduce orchestration inside the graph, not in the outer workflow loop.
   The current step sequencing logic is split between `backend/app/graph.py` and `backend/app/workflow.py`. The refactor will move milestone routing into the LangGraph orchestration layer.

3. Keep checkpoints at business milestone boundaries.
   Human review remains after the same milestones already enforced today:
   - after Step 1 signal scanning
   - after Step 2 pattern selection
   - after Step 7 risk mapping

4. Refactor incrementally.
   The first architectural change will reuse the existing step implementations as workers behind a new orchestrator graph. Deeper agent behavior can then be introduced per worker without destabilizing the workflow contract.

## Target Architecture

### High-Level Shape

The runtime will move from a fixed chain:

`START -> step1 -> step2 -> step3 -> ... -> step8 -> END`

to a routed graph with a controlling orchestrator:

`START -> orchestrator -> worker_for_next_step -> orchestrator -> ... -> END`

### Roles

- `orchestrator`
  - Reads workflow state
  - Decides the next milestone worker to run
  - Detects completion
  - Keeps routing explicit and deterministic at the milestone level

- `step worker`
  - Encapsulates one BMI milestone
  - Uses the corresponding skill/prompt logic
  - Produces normalized state updates only
  - Does not own checkpoint persistence

- `workflow service`
  - Starts and resumes runs
  - Persists step outputs and checkpoint records
  - Applies checkpoint decisions and validation
  - Remains the durable boundary for pause/resume behavior

## Design Constraints

### Constraint 1: Do Not Break the Current Contract

The following must remain stable unless a separate behavior change is intentionally approved:

- `run_workflow_from_voc_data`, `run_workflow_from_path`, `run_workflow_from_csv_text`, `resume_workflow`
- persisted run state and checkpoint records
- current checkpoint names and their required state validation
- workflow-level BDD scenarios for completion, transitions, retry, and pattern propagation

### Constraint 2: Agent-Oriented Does Not Mean Unbounded Autonomy

The BMI workflow still has fixed business milestones. The orchestrator will route among known milestone workers rather than allowing open-ended agent loops.

### Constraint 3: Retry Must Preserve Current Semantics

- `approve` advances to the next milestone
- valid `edit` advances to the next milestone using edited state
- `retry` reruns the current milestone from the saved pre-checkpoint state

## Step 1 and Step 2 LLM Quality Architecture

This section was added after validating the end-to-end Step 1 LLM flow against real VoC input and Azure OpenAI gpt-4o. The core finding: LLM outputs cannot be tested with exact text matching, fixed signal counts, or deterministic ordering. The behavioral contract must test analytical quality, not string reproduction.

### Problem Statement

The previous Step 1 multi-signal BDD scenario contained assertions tightly coupled to the legacy rule-based `SIGNAL_SPECS` implementation:

- Exact signal text matching (LLM paraphrases naturally)
- Fixed minimum signal count of 6 (real text may yield fewer or more)
- First-position ordering assumptions (LLM sorts differently)
- Assumption that disruptive signals always exist (they may not)

These assertions tested implementation details, not the behavioral contract that a consultant cares about: *did the agent follow the SOC Radar SKILL faithfully and produce a useful, grounded analysis?*

### Two-Layer Assertion Architecture

#### Layer 1: Structural Compliance (deterministic, no LLM needed)

These are hard constraints that production code must always satisfy regardless of whether the execution mode is legacy or LLM:

- Output contains `signals`, `interpreted_signals`, `priority_matrix`, `agent_recommendation`
- Every signal zone name is a valid SOC Radar zone (from the pattern library)
- Every disruption filter name is a valid SOC Radar filter (from the pattern library)
- Every priority score equals impact × speed and falls in the 1–9 range
- Every tier matches its score range: Act (7–9), Investigate (4–6), Monitor (1–3)
- Classifications are valid values: Sustaining, Disruptive — New-Market, Disruptive — Low-End

These assertions remain in the Step 1 `.feature` file as standard BDD scenarios.

#### Layer 2: Quality Evaluation (LLM-as-Judge)

A separate judge LLM call evaluates the analytical quality of the Step 1 output. The judge receives three inputs:

1. The **original VoC text** (what the agent was given)
2. The **SOC Radar SKILL.md** body (the instructions the agent was supposed to follow)
3. The **Step 1 structured output** (the signals, interpretations, priorities, and recommendation the agent produced)

The judge evaluates four dimensions and returns a structured verdict:

| Dimension | Question | Pass threshold |
|---|---|---|
| **Completeness** | Does the scan cover the key themes present in the source text? Are there obvious signals missing? | >= 3 / 5 |
| **Relevance** | Is every signal grounded in the source text? Are there hallucinated signals with no basis in the input? | >= 4 / 5 |
| **Groundedness** | Does each signal reference observable behavior from the source, not analyst opinion or speculation? | >= 4 / 5 |
| **SKILL compliance** | Did the output follow the SOC Radar phases — Scan (detect + classify), Interpret (disruption filters + confidence), Prioritize (impact × speed scoring)? | >= 3 / 5 |

The judge also returns a brief `rationale` per dimension explaining the score.

#### Module Location

- `backend/app/llm/judge.py` — the judge function: builds the evaluation prompt, calls the LLM with a structured output schema, returns the verdict
- Step 1 `.feature` file — structural assertions stay; a new scenario invokes the judge for quality assessment
- Step definitions — the judge scenario calls the real Step 1, then calls the judge, then asserts score thresholds

#### Feature Scenario Shape

```gherkin
Scenario: Step 1 produces a quality-assessed signal scan from firmware assessment VoC
  Given a workflow state with the firmware assessment VoC sample
  When the Step 1 signal scanner node runs
  And the LLM judge evaluates the signal scan against the SOC Radar SKILL
  Then the judge completeness score is at least 3
  And the judge relevance score is at least 4
  And the judge groundedness score is at least 4
  And the judge SKILL compliance score is at least 3
```

### Step 2 Production Code Fixes

Step 2 (`backend/app/nodes/step2_pattern.py`) has two implementation issues that break when Step 1 runs in LLM mode:

1. **Only reads `interpreted_signals[0]`** — The first signal in the list determines the pattern direction. When the LLM returns signals in a different order (e.g., sustaining first, disruptive later), step 2 misses the disruptive signal entirely.

   Fix: Scan all interpreted signals to find the highest-priority disruptive signal for direction routing, rather than relying on position `[0]`.

2. **Zone name mismatch** — The SKILL.md instructs the LLM to use abbreviated zone names (`Enabling Tech`, `Overserved`) while the pattern library and Step 2 routing logic use full names (`Enabling Technology`, `Overserved Customers`).

   Fix: Normalize zone names from LLM output to canonical pattern-library names before routing. The normalization map:
   - `Enabling Tech` → `Enabling Technology`
   - `Overserved` → `Overserved Customers`
   - `Regulatory Shift` → `Regulatory / Policy Shift`

These are production code fixes (Step 2 implementation), not feature file changes. The Step 2 feature scenarios remain unchanged.

### Legacy Test Handling

The standalone pytest function `test_competitor_self_serve_evidence_avoids_generic_slogans` in the Step 1 step definitions directly references `signal_id == "competitor_self_serve"`, which is a legacy `SIGNAL_SPECS` implementation detail. This test should be guarded to run only when `step1_signal_execution_mode == "legacy"`.

## Implementation Plan

### Phase 1: Introduce the Orchestrator Skeleton

Goal: Change the internal graph topology while keeping current worker logic intact.

Planned changes:

1. Add orchestrator routing fields to `BMIWorkflowState`.
   Candidate fields:
   - `next_step`
   - `completed_steps`
   - `last_completed_step`

2. Replace the linear graph in `backend/app/graph.py` with:
   - one `orchestrator` node
   - one worker node per milestone step
   - conditional routing from orchestrator to the selected worker
   - a route back from each worker to the orchestrator
   - termination when orchestrator determines the workflow is complete

3. Reuse current step runners as the first worker implementation.
   This keeps business behavior stable while the topology changes.

Definition of done:

- The graph is no longer a hardcoded linear chain
- Existing step outputs still populate the same workflow state keys
- Existing workflow-level BDD tests still pass

### Phase 2: Add an Agent Execution Layer Around Workers

Goal: Turn step workers into explicit agent-oriented execution units without changing milestone outputs.

Planned changes:

1. Introduce a worker abstraction in backend app code with responsibilities such as:
   - identifying the worker name
   - building worker input from workflow state
   - invoking the skill-backed execution logic
   - returning normalized state updates

2. Map one worker to each BMI milestone:
   - signal worker
   - pattern worker
   - profile worker
   - vpm worker
   - define worker
   - design worker
   - risk worker
   - pdsa worker

3. Keep each worker focused on a single responsibility.
   Prompt loading, state shaping, and worker execution should be separated cleanly so deeper agent behavior can be added later without rewriting orchestration.

Definition of done:

- Each milestone executes through an explicit worker abstraction
- Worker interfaces are consistent across steps
- Checkpoint behavior remains unchanged

### Phase 3: Move Sequencing Responsibility Out of the Workflow Loop

Goal: Make `backend/app/workflow.py` responsible for persistence and checkpoint control, not step sequencing.

Planned changes:

1. Reduce direct dependence on `WORKFLOW_STEP_ORDER` iteration for normal execution.

2. Keep workflow service responsibilities focused on:
   - starting a run
   - resuming a run after checkpoint review
   - persisting step snapshots
   - creating checkpoint records
   - restoring the right state for approve, edit, and retry

3. Retain a milestone ordering source for checkpoint and resume calculations, but do not use it as the primary execution engine.

Definition of done:

- The graph owns routing decisions
- The workflow service owns persistence and checkpoint durability
- Resume behavior still lands on the correct milestone after approve, edit, and retry

### Phase 4: LLM-Back Step 1 and Step 2 with Quality Gates

Goal: Make Step 1 and Step 2 production-ready with LLM execution and quality assurance before deepening any other workers.

Planned changes:

1. Build `backend/app/llm/judge.py` implementing the LLM-as-Judge evaluation module.

2. Update the Step 1 `.feature` file:
   - Keep Scenario 1 (structural compliance) unchanged
   - Replace Scenario 2 (multi-signal with exact text matching) with the judge-based quality evaluation scenario

3. Update the Step 1 step definitions to wire the judge scenario.

4. Fix Step 2 production code:
   - Scan all interpreted signals for disruptive routing (not just `[0]`)
   - Add zone name normalization for LLM-abbreviated names

5. Guard the legacy-only `test_competitor_self_serve_evidence_avoids_generic_slogans` test.

6. Set `step1_signal_execution_mode` default to `llm`.

Definition of done:

- Step 1 runs via real LLM and passes structural compliance assertions
- The LLM-as-Judge quality evaluation passes with approved thresholds
- Step 2 correctly routes pattern direction from LLM-produced signals
- All existing checkpoint and workflow BDD tests still pass
- Legacy mode remains available via configuration

### Phase 5: Per-Step Quality Gates and Structured Output Hardening

Goal: Every LLM-backed step (1–7) gets an LLM-as-Judge quality gate and confirmed Pydantic structured output, so the entire pipeline has measurable, auditable analytical quality from signal scan to risk map.

#### Current State (baseline before Phase 5 work)

| Step | Structured Output? | Pydantic Root Model | Quality Gate? |
|------|:---:|---|:---:|
| 1 — Signal Scan | Yes | `SignalScanResult` | Yes — `judge.py` (completeness, relevance, groundedness, SKILL compliance) |
| 2 — Pattern Matcher | Yes | `PatternReasonerOutput` | Partial — post-hoc validation only (selected patterns must exist in shortlist) |
| 3 — Customer Profile | Yes | `CustomerEmpathyProfile` | Partial — empathy gate (structural completeness check on jobs/pains/gains) |
| 4 — Value Drivers | Yes | `Step4Output` | No |
| 5 — Value Proposition | Yes | `ValuePropositionCanvas` | No |
| 6 — Design Canvas | Yes | `Step6Output` | No |
| 7 — Risk Map | Yes | `Step7Output` | No |
| 8 — Experiment Plan | No (deterministic) | N/A — dataclasses | N/A (no LLM call) |

**Structured output**: Steps 1–7 already use `with_structured_output()`. Step 8 is deterministic and does not need it.

**Quality gates**: Only Step 1 has the full LLM-as-Judge pattern. Steps 2–7 need per-step judge evaluations.

#### 5A — Per-Step Quality Gate Design

Each step gets its own judge evaluation function in `backend/app/llm/judge.py` (or a new `judge_steps.py` if the module grows too large). All judges follow the same pattern proven in Step 1:

1. **Judge receives three inputs**: (a) upstream state the step was given, (b) the SKILL/prompt instructions the step should have followed, (c) the step's structured output.
2. **Judge scores four dimensions** on a 1–5 rubric with rationale per dimension.
3. **Judge returns a `JudgeVerdict`** (same Pydantic schema — reusable across all steps).
4. **BDD scenario per step** asserts minimum thresholds.

##### Step 2 — Pattern Matcher Judge

| Dimension | Question | Pass Threshold |
|---|---|---|
| **Relevance** | Are the selected patterns appropriate for the detected signal direction and zone? | >= 4 |
| **Groundedness** | Does the rationale cite specific signal evidence and pattern descriptions? | >= 4 |
| **SKILL compliance** | Did the step follow the hybrid approach — affinity shortlist first, then LLM reasoning? | >= 3 |
| **Coherence** | Is the pattern selection internally consistent (no contradictory patterns)? | >= 3 |

SKILL context: `prompts/step2_pattern_matcher.md` + `strategyzer-pattern-library.json`

##### Step 3 — Customer Profile Judge

| Dimension | Question | Pass Threshold |
|---|---|---|
| **Completeness** | Does the profile cover functional, social, and emotional job types with corresponding pains and gains? | >= 3 |
| **Relevance** | Are the jobs, pains, and gains traceable to the VoC input and Step 1 signals? | >= 4 |
| **Groundedness** | Does each job/pain/gain reference observable customer behavior, not consultant speculation? | >= 4 |
| **SKILL compliance** | Does the profile follow the CXIF empathy structure (segment → jobs → pains → gains)? | >= 3 |

SKILL context: `cxif-bmi-coach/SKILL.md`

##### Step 4 — Value Driver Judge

| Dimension | Question | Pass Threshold |
|---|---|---|
| **Completeness** | Does the output include a value driver tree, context analysis, and WHO-DOES-BECAUSE-BUT statement? | >= 3 |
| **Relevance** | Are success measures and friction points traceable to the customer profile? | >= 4 |
| **Groundedness** | Are problem statements grounded in identified pains and jobs, not generic business jargon? | >= 3 |
| **SKILL compliance** | Does the output follow the CXIF Measure and Define phases? | >= 3 |

SKILL context: `cxif-bmi-coach/SKILL.md`

##### Step 5 — Value Proposition Judge

| Dimension | Question | Pass Threshold |
|---|---|---|
| **Completeness** | Does the canvas include products/services, pain relievers, gain creators, and ad-lib prototypes? | >= 3 |
| **Relevance** | Do pain relievers map to identified customer pains? Do gain creators map to identified gains? | >= 4 |
| **Groundedness** | Are the VP elements traceable to the value driver tree and problem statements? | >= 3 |
| **SKILL compliance** | Does the output follow the CXIF Value Proposition Canvas structure? | >= 3 |

SKILL context: `cxif-bmi-coach/SKILL.md`

##### Step 6 — Design Canvas Judge

| Dimension | Question | Pass Threshold |
|---|---|---|
| **Completeness** | Does the BMC cover desirability, feasibility, and viability blocks? Does fit assessment include all three fit types? | >= 3 |
| **Relevance** | Do the BMC building blocks connect to the value proposition? Do fit rows reference canvas elements? | >= 4 |
| **Coherence** | Is the BMC internally consistent — do channel, revenue, and cost blocks align with the value proposition? | >= 3 |
| **SKILL compliance** | Does the output follow the CXIF Business Model Canvas and fit assessment structure? | >= 3 |

SKILL context: `cxif-bmi-coach/SKILL.md`

##### Step 7 — Risk Map Judge

| Dimension | Question | Pass Threshold |
|---|---|---|
| **Completeness** | Does the output include assumptions across all three DVF categories with an importance × evidence matrix? | >= 3 |
| **Relevance** | Are assumptions traceable to specific BMC building blocks and fit assessment gaps? | >= 4 |
| **Groundedness** | Are assumptions stated as testable hypotheses, not vague concerns? | >= 4 |
| **SKILL compliance** | Does the output follow the Precoil EMT format (DVF categories, quadrant assignment, tension check)? | >= 3 |

SKILL context: `precoil-emt/agent.md` + `precoil-emt-pattern-library.json`

#### 5B — CXIF Domain Validation Library and Structured Output Hardening

##### Problem

Steps 1, 2, 7, and 8 each have a **domain vocabulary validation library** (`.json` under `patterns/`) that defines the canonical terms the LLM output must use. This enables deterministic structural compliance checks in BDD tests — e.g., "every signal zone is a valid SOC Radar zone", "selected patterns are verified library entries", "assumptions include all DVF categories".

Steps 3–6 (all CXIF-based) have **no such library**. The LLM is told to follow the CXIF SKILL.md, but there's no structured reference to validate against. If the LLM invents a pain type like "annoyance" instead of using the canonical "Functional / Social / Emotional / Ancillary", nothing catches it.

| Step | Has Pattern Library? | Domain |
|------|:---:|---|
| 1 — Signal Scan | Yes — `soc-radar-pattern-library.json` | SOC Radar zones, filters, classifications, tiers |
| 2 — Pattern Matcher | Yes — `strategyzer-pattern-library.json` | INVENT + SHIFT verified pattern names |
| 3 — Customer Profile | **No** | CXIF empathy (job/pain/gain types, importance/severity/relevance scales) |
| 4 — Value Drivers | **No** | CXIF measure/define (driver types, friction types, insight format) |
| 5 — Value Proposition | **No** | CXIF value map (product types, reliever/creator types, relevance scales) |
| 6 — Design Canvas | **No** | CXIF design (BMC building blocks, fit dimensions, fit statuses) |
| 7 — Risk Map | Yes — `precoil-emt-pattern-library.json` | DVF categories, quadrants, assumption format |
| 8 — Experiments | Yes — `experiment-library.json` | 44 experiment cards |

##### Solution: `cxif-pattern-library.json`

Create a single CXIF domain validation library at `patterns/cxif-pattern-library.json` that codifies the canonical vocabulary from `cxif-bmi-coach/SKILL.md`. This serves Steps 3, 4, 5, and 6 the same way the SOC Radar library serves Step 1.

**Contents** (extracted from the SKILL.md tables and rules):

```json
{
  "metadata": {
    "title": "CXIF Pattern Library for Steps 3-6",
    "scope": "Domain vocabulary for Empathize, Measure, Define, and Design phases",
    "source": "cxif-bmi-coach/SKILL.md"
  },

  "empathy_profile": {
    "job_types": ["Functional", "Social", "Emotional", "Supporting"],
    "pain_types": ["Functional", "Social", "Emotional", "Ancillary"],
    "gain_types": ["Functional", "Social", "Emotional", "Financial"],
    "importance_scale": ["High", "Medium", "Low"],
    "severity_scale": ["Severe", "Moderate", "Light"],
    "relevance_scale": ["Essential", "Expected", "Desired", "Unexpected"],
    "min_jobs": 3,
    "min_pains": 3,
    "min_gains": 3
  },

  "value_driver_tree": {
    "driver_types": ["Cost", "Revenue", "Time", "Effort", "Volume", "Satisfaction"],
    "friction_types": ["Pain", "Gap", "Delay", "Error"],
    "journey_phases": ["Awareness", "Evaluation", "Purchase", "Delivery", "Support", "Renewal"],
    "insight_format": "WHO DOES BECAUSE BUT",
    "problem_priority_scale": ["High", "Medium", "Low"]
  },

  "value_proposition_canvas": {
    "product_service_types": ["Physical/Tangible", "Digital", "Intangible", "Financial"],
    "pain_reliever_types": ["Functional", "Social", "Emotional", "Ancillary"],
    "gain_creator_types": ["Functional", "Social", "Emotional", "Financial"],
    "relevance_scale_products": ["Core", "Nice-to-have"],
    "relevance_scale_relievers": ["Substantial", "Nice-to-have"],
    "relevance_scale_creators": ["Substantial", "Nice-to-have"],
    "min_ad_lib_prototypes": 2,
    "ad_lib_template": "OUR [products] HELP [segment] WHO WANT TO [jobs] BY [reducing] [pain] AND [improving] [gain]"
  },

  "business_model_canvas": {
    "building_blocks": {
      "desirability": ["Customer Segments", "Value Proposition", "Channels", "Customer Relationships"],
      "feasibility": ["Key Partnerships", "Key Activities", "Key Resources"],
      "viability": ["Revenue Streams", "Cost Structure"]
    },
    "all_block_names": [
      "Customer Segments", "Value Proposition", "Channels",
      "Customer Relationships", "Key Partnerships", "Key Activities",
      "Key Resources", "Revenue Streams", "Cost Structure"
    ],
    "fit_dimensions": ["Desirability", "Feasibility", "Viability"],
    "fit_status_values": ["Validated", "Assumed", "Unknown"],
    "problem_solution_fit_values": ["Strong", "Partial", "Weak"]
  }
}
```

##### Structural Compliance Checks (new BDD scenarios)

With the library in place, each CXIF step gets a structural compliance scenario (deterministic, no LLM judge needed) — the same layer that Step 1 already has:

- **Step 3**: Every job type is in `empathy_profile.job_types`, every pain type is in `empathy_profile.pain_types`, every gain type is in `empathy_profile.gain_types`, every importance is in `importance_scale`, etc.
- **Step 4**: Every driver type is in `value_driver_tree.driver_types`, every friction type is in `friction_types`, insight follows WHO-DOES-BECAUSE-BUT format.
- **Step 5**: Every product type is in `value_proposition_canvas.product_service_types`, every pain reliever type is in `pain_reliever_types`, minimum 2 ad-lib prototypes.
- **Step 6**: Every BMC block name is in `business_model_canvas.all_block_names`, fit status values are in `fit_status_values`, all three fit dimensions present.

These checks run fast (no LLM call), catch vocabulary drift early, and complement the LLM-as-Judge quality evaluation.

##### Additional Hardening

1. **Step 8 — Add Pydantic schemas**: Replace the `dataclass`-based `ExperimentCard` and `TopAssumption` with Pydantic `BaseModel` classes. Add a root `Step8Output` model. This doesn't change behavior (Step 8 is deterministic) but makes the pipeline uniformly typed for serialization, validation, and the future audit trail.

2. **Promote structured dict storage where currently markdown**: Steps 3–7 store rendered markdown strings in state keys (e.g., `customer_profile`, `value_driver_tree`). Optionally, add a parallel `_structured` key (e.g., `customer_profile_structured`) containing the Pydantic `.model_dump()` dict. This preserves backward compatibility (the markdown string is still there) while giving downstream steps and audit trail typed access to the structured data. This is optional per step and can be done incrementally.

##### 5B-2 — Enrichments to Existing Pattern Libraries

**Source documents** (added to `assistant/docs/`):
- `Customer Jobs Pains Gains Trigger Questions.txt`
- `The Business Model Shifts Library.txt`
- `The Invent Pattern Library.txt`
- `Knowledge Document - Exploit Portfolio Business Model Disruption Risk Assessment.txt`

**Strategyzer library enrichments** (`strategyzer-pattern-library.json`):

1. **INVENT patterns — add `assessment_scale`**: The Invent Pattern Library document provides 7-point scale anchors for each pattern's `assessment_question`. The current library has the question but not the scale meaning. Add an `assessment_scale` field to each INVENT pattern:
   ```json
   "assessment_scale": {
     "negative_anchor": "There is little untapped potential and the market is shrinking",
     "positive_anchor": "The market potential is large, not yet occupied, and growing"
   }
   ```
   This enables structural validation that LLM-generated assessments use the correct scale language.

2. **SHIFT patterns — verify examples**: The Business Model Shifts document confirms examples (Hilti, Netflix, TED, Intel Inside, Apple Genius Bar, Fujifilm, Bharti Airtel, Microsoft, Dow Corning Xiameter, Adobe, Apple iMac). Cross-check that existing `example` fields match.

3. **SHIFT patterns — add category grouping vocabulary**: The Shifts document organizes patterns under "Value Proposition Shifts" (3 patterns), "Frontstage Driven Shifts" (3 patterns), "Backstage Driven Shifts" (3 patterns), "Profit Formula Driven Shifts" (3 patterns). These categories provide a structural validation dimension for Step 2 output.

**CXIF library enrichments** (`cxif-pattern-library.json` — new):

4. **Add `trigger_questions` section**: The Customer Jobs Pains Gains Trigger Questions document provides canonical question sets:
   - Jobs: 4 trigger questions + 2 context trigger questions
   - Pains: 9 trigger questions (organized by pain type)
   - Gains: 9 trigger questions (organized by gain type)

   These serve two purposes:
   - Step 3's empathy gate: when the gate fires trigger questions for incomplete profiles, the canonical questions provide the reference vocabulary
   - Judge SKILL compliance: the judge can verify that empathy analysis addresses the dimensions covered by trigger questions

**Future enrichment candidate** (not part of Phase 5):

5. **Exploit Portfolio Assessment library**: The Exploit Portfolio document defines a structured 10-item Performance assessment and 10-item Trend assessment, each with 7-point scales and BMC-aligned anchors. This could enrich Steps 6 and 7 in a future phase:
   - Step 6 (Design Canvas): validate BMC blocks against performance assessment dimensions
   - Step 7 (Risk Map): trend assessment dimensions identify where threats concentrate and can inform assumption prioritization
   This is documented here for future reference but is out of scope for Phase 5.

#### 5C — BDD Feature Scenarios

Each step gets one new scenario in its `.feature` file following the Step 1 judge pattern:

```gherkin
# step2-pattern-matcher.feature
Scenario: Step 2 produces a quality-assessed pattern selection
  Given a workflow state with interpreted signals from Step 1
  When the Step 2 pattern matcher node runs
  And the LLM judge evaluates the pattern selection against the pattern matcher SKILL
  Then the judge relevance score is at least 4
  And the judge groundedness score is at least 4
  And the judge SKILL compliance score is at least 3
  And the judge coherence score is at least 3

# step3-customer-profile.feature
Scenario: Step 3 produces a quality-assessed customer empathy profile
  Given a workflow state with a consultant-approved pattern direction
  When the Step 3 customer profile node runs
  And the LLM judge evaluates the empathy profile against the CXIF SKILL
  Then the judge completeness score is at least 3
  And the judge relevance score is at least 4
  And the judge groundedness score is at least 4
  And the judge SKILL compliance score is at least 3

# step4-vpm.feature
Scenario: Step 4 produces a quality-assessed value driver output
  Given a workflow state with a completed Step 3 empathy profile
  When the Step 4 VPM synthesizer node runs
  And the LLM judge evaluates the value drivers against the CXIF SKILL
  Then the judge completeness score is at least 3
  And the judge relevance score is at least 4
  And the judge groundedness score is at least 3
  And the judge SKILL compliance score is at least 3

# step5-define.feature
Scenario: Step 5 produces a quality-assessed value proposition canvas
  Given a workflow state with completed Step 4 outputs
  When the Step 5 define model node runs
  And the LLM judge evaluates the value proposition against the CXIF SKILL
  Then the judge completeness score is at least 3
  And the judge relevance score is at least 4
  And the judge groundedness score is at least 3
  And the judge SKILL compliance score is at least 3

# step6-design.feature
Scenario: Step 6 produces a quality-assessed design canvas
  Given a workflow state with a completed Step 5 value proposition canvas
  When the Step 6 design canvas node runs
  And the LLM judge evaluates the design canvas against the CXIF SKILL
  Then the judge completeness score is at least 3
  And the judge relevance score is at least 4
  And the judge coherence score is at least 3
  And the judge SKILL compliance score is at least 3

# step7-risk.feature
Scenario: Step 7 produces a quality-assessed risk map
  Given a workflow state with completed Step 6 design outputs
  When the Step 7 risk mapper node runs
  And the LLM judge evaluates the risk map against the Precoil EMT SKILL
  Then the judge completeness score is at least 3
  And the judge relevance score is at least 4
  And the judge groundedness score is at least 4
  And the judge SKILL compliance score is at least 3
```

#### 5D — Implementation Sequence

1. **5D-1**: Create `patterns/cxif-pattern-library.json` — the CXIF domain validation library with canonical vocabulary for Steps 3–6, including the `trigger_questions` section from the Customer Jobs Pains Gains source document.
2. **5D-2**: Enrich `strategyzer-pattern-library.json` — add `assessment_scale` to each INVENT pattern, verify SHIFT examples, add SHIFT category grouping vocabulary.
3. **5D-3**: Add a `CXIFPatternLibrary` loader (or extend `PatternLibraryLoader`) to expose CXIF vocabulary programmatically.
4. **5D-4**: Add structural compliance BDD scenarios to Steps 3–6 `.feature` files (deterministic — no LLM needed at test time).
5. **5D-5**: Implement step definitions for structural compliance using the CXIF library as the validation source.
6. **5D-6**: Generalize `judge.py` — extract a reusable `evaluate_step_quality()` function that accepts step-specific rubric, SKILL context, upstream state, and step output. Keep `evaluate_step1_quality()` as a convenience wrapper.
7. **5D-7**: Implement Steps 2–7 judge evaluation functions (one per step), each with a step-specific rubric and dimension set.
8. **5D-8**: Add judge BDD scenarios to each step's `.feature` file.
9. **5D-9**: Add step definitions in each step's test module to wire the judge call.
10. **5D-10**: Add Pydantic models for Step 8 output (optional — deterministic step).
11. **5D-11**: Optionally add `_structured` parallel keys for Steps 3–7.
12. **5D-12**: Run full test suite — all existing + new structural + new judge scenarios must pass.

#### Definition of Done

- Every LLM-backed step (1–7) has an LLM-as-Judge quality gate with documented rubric
- Judge dimensions and thresholds are defined per step in the plan and enforced in BDD scenarios
- All steps use `with_structured_output()` with Pydantic models (Steps 1–7 confirmed, Step 8 optional)
- `cxif-pattern-library.json` exists under `patterns/` and codifies the CXIF domain vocabulary for Steps 3–6
- Every CXIF step (3–6) has structural compliance BDD scenarios that validate output against the CXIF library (same pattern as Step 1 against SOC Radar library)
- All 8 steps now have a domain validation library: SOC Radar (Step 1), Strategyzer (Step 2), CXIF (Steps 3–6), Precoil EMT (Step 7), Experiment Library (Step 8)
- All existing BDD tests pass without modification
- New structural compliance + judge scenarios pass against both Azure and Ollama backends

## Proposed Module Direction

The refactor should preserve the current code organization and evolve it rather than replace it wholesale.

- `backend/app/graph.py`
  - becomes the orchestrator graph definition

- `backend/app/workflow.py`
  - remains the run lifecycle and persistence boundary

- `backend/app/checkpoints.py`
  - remains the checkpoint definition and validation boundary

- `backend/app/state.py`
  - gains orchestration fields required for routed execution

- `backend/app/nodes/`
  - can temporarily host worker node functions during Phase 1

- `backend/app/skills/`
  - remains the packaged skill asset area and can support richer worker execution over time

If the worker abstraction grows enough to deserve its own area, it can later be split into a dedicated module such as `backend/app/agents/` or `backend/app/workers/`, but that should follow the first topology refactor, not precede it.

## Checkpoint Preservation Plan

The checkpoint contract must remain exactly aligned with the current runtime.

### Checkpoint Boundaries

- `checkpoint_1` after Step 1
- `checkpoint_1_5` after Step 2
- `checkpoint_2` after Step 7

### Resume Rules

- `approve`
  - resume from the next milestone after the checkpointed step

- `edit`
  - merge approved edits into the post-step state
  - validate required checkpoint fields
  - resume from the next milestone

- `retry`
  - restore the saved pre-step state
  - rerun the same milestone worker

### Persistence Rules

- step snapshots remain persisted per milestone execution
- pending checkpoints remain explicit in stored run state
- final completed runs remain persisted with `run_status = completed`

## Test Plan

### Primary Acceptance Tests

The existing workflow-level BDD tests remain the acceptance contract for the refactor:

1. full orchestrator completion from input to Step 8 artifacts
2. mandatory checkpoint transition flow
3. checkpoint 1.5 validation failure when consultant selection is missing
4. retry reruns the current milestone instead of advancing
5. selected pattern propagation survives the workflow to downstream artifacts

### Step 1 Quality Tests

Step 1 BDD tests are organized into two layers:

1. **Structural compliance scenario** (no LLM needed at test time):
   - Output shape: `signals`, `interpreted_signals`, `priority_matrix`, `agent_recommendation` all present
   - Zone names, filter names, classifications, scores, and tiers are valid per the SOC Radar pattern library
   - VoC data is preserved in state

2. **LLM-as-Judge quality scenario** (requires real LLM call):
   - Completeness >= 3/5
   - Relevance >= 4/5
   - Groundedness >= 4/5
   - SKILL compliance >= 3/5
   - Judge rationale is captured for debugging

### Additional Targeted Tests

Add or expand tests for:

1. orchestrator routing decisions
2. worker return-to-orchestrator transitions
3. completion routing to `END`
4. retry routing returning to the same milestone worker
5. no checkpoint boundary being skipped by the new graph topology
6. Step 2 correctly identifies disruptive signals regardless of sort order
7. Step 2 zone normalization maps LLM abbreviations to canonical names

### Runtime Validation

Per repo rules, run tests inside the containerized backend environment and use the existing CLI-backed workflow execution path where appropriate.

## Implementation Sequence

Recommended execution order:

1. update the plan if a design constraint changes
2. implement Phase 4: LLM-as-Judge module, Step 1 feature update, Step 2 fixes
3. run Step 1 and Step 2 BDD tests plus judge quality evaluation
4. implement Phase 1 graph topology refactor
5. run workflow-level BDD tests
6. implement Phase 2 worker abstraction layer
7. rerun workflow-level BDD tests plus targeted routing tests
8. implement Phase 3: simplify workflow service sequencing logic
9. rerun the full relevant backend test set inside the container
10. implement Phase 5: deepen individual workers where needed

### Phase 6: Worker Audit Trail and Observability

Goal: Provide production-grade visibility into worker decisions so that every LLM interaction can be inspected, audited, and debugged after the fact.

#### Problem Statement

Today the only audit trail is the final state snapshot persisted per step in `StepOutput` and the checkpoint decision records in `CheckpointRecord`. There is no record of:

- What prompt was sent to the LLM
- What raw response the LLM returned
- Which model/deployment was actually used at execution time
- Token usage (input/output) and latency
- Whether structured output parsing required retries
- Quality judge scores (where applicable)

This makes production debugging, cost tracking, and compliance auditing impossible.

#### Design

1. **`WorkerAuditLog` database table** — one row per worker execution, storing:
   - `session_id`, `step_name`, `step_number`
   - `llm_backend`, `model_name`, `model_deployment` — the actual model identity used
   - `prompt_text` — the full prompt sent to the LLM
   - `raw_response` — the raw LLM response before structured parsing
   - `structured_output` — the parsed structured output (JSON)
   - `input_tokens`, `output_tokens`, `total_tokens` — token usage
   - `latency_ms` — wall-clock execution time
   - `retry_count` — number of structured output parse retries
   - `error_message` — if the step failed, the error detail
   - `judge_scores` — quality evaluation scores (JSON, nullable)
   - `created_at` — timestamp

2. **`AuditLogger` utility** — a lightweight logger that workers call to record LLM interactions. Injected into workers via the `BaseWorker.run()` method so no `_llm.py` business logic needs to change.

3. **Interception point**: `BaseWorker.run()` wraps `execute()` with timing, catches errors, and delegates audit persistence. The `_llm.py` functions optionally return metadata (token counts, raw response) via an extended return protocol.

4. **API endpoint**: `GET /runs/{id}/audit` — returns the audit trail for a given run, ordered by step number.

5. **Structured logging**: In addition to DB persistence, emit structured log lines (JSON) to stdout for each worker execution so `docker logs` provides real-time visibility.

#### Definition of Done

- Every worker execution (LLM and deterministic) produces an audit record
- Audit records capture prompt, response, model identity, tokens, and latency
- Audit trail is queryable via API
- Structured log output enables `docker logs -f` monitoring
- Existing tests still pass — audit logging is additive, not behavior-changing
- Migration script creates the `WorkerAuditLog` table

#### Test Plan

- BDD scenario: a completed step produces an audit record with required fields
- BDD scenario: audit trail for a full run contains 8 records in step order
- BDD scenario: API endpoint returns audit records for a given session
- Unit test: AuditLogger correctly captures timing and error states
- Regression: all existing 81+ tests pass without modification

## Future Release Candidates

Items below are validated as theoretically sound but deferred until the current implementation plan (Phases 1–6) is complete. They are captured here so they don't get lost and can be prioritized in a subsequent release cycle.

### FR-1: SOC Radar Pattern Library — Christensen Fidelity Refinements

**Source**: `assistant/docs/soc-radar-fixes.md.html` — review of the SOC Radar pattern library against Christensen's canon (*The Innovator's Dilemma*, *The Innovator's Solution*, *Seeing What's Next*).

#### FR-1a: Add 8th Signal Zone — Value Network Shift

Add a "Value Network Shift" zone to capture signals where entrants use new channels, partnerships, or customer relationships that incumbents cannot replicate without cannibalizing their core business. This is a Christensen non-negotiable for disruption (IDS Ch. 3).

**Rationale**: Currently implied within "Business Model Anomaly" but not elevated as a distinct detection zone. Christensen treats value networks (channels, partnerships, customer relationships) as separable from business model structure (cost/revenue).

**Impact (cross-cutting)**:
- `soc-radar-pattern-library.json` — `count: 7→8`, add zone object, update `agent_usage_guidance`
- `step1_signal_llm.py` — add zone to `DetectedSignal.zone` Field description, system prompt zone list, `_VALID_ZONES` set
- `pattern_affinity.py` — add "Value Network Shift" row to both `_ZONE_INVENT_AFFINITY` and `_ZONE_SHIFT_AFFINITY` matrices; classify in `_AMBIGUOUS_ZONES`
- `test_bdd_step1_signal_scanner.py` — add "Value Network Shift" to `valid_zones` set
- `soc-radar/SKILL.md` — update all zone enumeration references from 7 to 8
- **Design decision needed**: disambiguate "Value Network Shift" from narrowed "Business Model Anomaly" (BMA focuses on cost/revenue structure; VNS focuses on channels/partnerships/customer relationships)

#### FR-1b: Refine Enabling Technology Zone Description

Update description to encode Christensen's principle that technology alone is sustaining — disruptive potential only emerges when paired with a business model shift (SWN Ch. 4).

**Proposed text**: *"Technologies that reduce barriers to entry or change the cost curve. Disruptive potential emerges when paired with a business model shift; technology alone typically enables sustaining innovation."*

**Impact**: JSON-only edit. No code or test changes.

#### FR-1c: Refine Trajectory Filter Question

Add directionality to the Trajectory disruption filter — the entrant must be improving *from the low-end or non-consumption base* (ID Ch. 4). Without this, the filter falsely flags sustaining innovations improving from the high end.

**Proposed text**: *"Is the entrant improving from the low-end or non-consumption base at a rate that will meet mainstream needs?"*

**Impact**: JSON-only edit. No code or test changes.

#### FR-1d (Deferred further): Signal Lifecycle Stage Tracking

Add a `Signal_Lifecycle_Stage` field to evidence capture to track zone migration over time (e.g., "Nonconsumption → New-Market Foothold"). Conceptually sound per Christensen (IDS Ch. 2: *"Disruption is a process, not an event"*) but requires a signal persistence layer (database, not workflow state) that is beyond current architecture scope.

### FR-2: Exploit Portfolio Assessment Library

**Source**: `Knowledge Document - Exploit Portfolio Business Model Disruption Risk Assessment.txt`

Add a pattern library for portfolio-level business model disruption risk assessment, enabling Steps 6–7 to evaluate not just individual BMC fit but portfolio-wide risk exposure across the Explore/Exploit spectrum. Requires design work to determine integration points with the CXIF pipeline.

## Working Rule During Refactor

This document is the implementation baseline for the agentic orchestrator refactor. If code changes diverge from this plan, update this document first or in the same change so the design intent stays explicit.