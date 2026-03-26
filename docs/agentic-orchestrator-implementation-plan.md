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

### Phase 5: Deepen Individual Workers Where Needed

Goal: Allow richer agent behavior inside remaining steps (3–8) without affecting the workflow contract.

Examples:

- Steps 3–8 can migrate from rule-based to LLM-backed execution using the same pattern proven in Step 1
- Each worker can incorporate the LLM-as-Judge quality gate for its own SKILL compliance
- Workers can incorporate internal tool usage or structured sub-calls if necessary

Definition of done:

- Internal sophistication can increase per worker
- The orchestration contract and workflow checkpoints remain stable

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

## Working Rule During Refactor

This document is the implementation baseline for the agentic orchestrator refactor. If code changes diverge from this plan, update this document first or in the same change so the design intent stays explicit.