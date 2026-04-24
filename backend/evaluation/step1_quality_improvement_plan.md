# Step 1 Quality Improvement — Strategy, Implementation Plan & Test Plan

## Problem Statement

The gap analysis (`workflow_step1_prompt_gap_analysis.md`) identified that GPT-4o produces significantly lower-quality SOC Radar analysis than Claude Opus 4.6 when given the same SKILL.md prompt. The root causes are:

1. **SKILL.md is too implicit** — rules are present but enforcement language is soft
2. **Pydantic schemas are too sparse** — fields the SKILL requires are missing from the output contract
3. **Single-pass architecture** — all 4 SOC Radar phases in one LLM call causes GPT-4o to compress/shortcut later phases

## Strategy

Address the problem in two layers:

| Layer | What Changes | Why |
|-------|-------------|-----|
| **Prompt layer** | Strengthen SKILL.md with explicit extraction rules, classification gates, and completeness requirements | Forces the LLM to follow the framework even when it tends to compress |
| **Architecture layer** | Split Step 1 into Step 1a (Scan+Interpret) and Step 1b (Prioritize+Recommend) with expanded Pydantic schemas | Each LLM call gets focused attention; schema enforces completeness mechanically |

The existing sub-step pattern (Step 5a/5b, Step 8a/8b/8c) provides a proven blueprint. Step 1a and 1b will share `step_number=1` but have distinct worker names, checkpoints, and LLM calls.

---

## Part 1: SKILL.md Changes

### 1.1 Phase 1 — Signal Extraction Minimum & Evidence Linking

**Current text** (Phase 1 Rules):
```
- Extract signals directly from the provided material — do not invent signals not supported by the input
```

**Proposed addition** — append these rules to the Phase 1 Rules section:

```markdown
- Extract at least 7 distinct signals when the input contains 10+ observations. Do not collapse
  related phenomena into a single signal — a pricing complaint and a portal access complaint may
  share root causes but represent separate signals with different disruption trajectories
- For each signal, cite the specific input comment numbers (e.g., Comment 3, Comment 12) that
  provide supporting evidence. Every input comment should be cited by at least one signal
- Treat the input as a system of interrelated behaviors, not a flat list of complaints. If multiple
  comments describe downstream effects of a single root cause, extract both the root cause signal
  and the effect signals separately
```

### 1.2 Phase 2 — Classification Gate Enforcement

**Current text** (Phase 2 Rules):
```
- Classify as sustaining or disruptive *before* applying filters. Sustaining signals do not receive disruption filter analysis
```

**Proposed replacement** — strengthen to an explicit gate:

```markdown
- CLASSIFICATION GATE: Before applying disruption filters, output a sustaining/disruptive
  classification for EVERY signal. This is a mandatory prerequisite — no signal may receive
  filter analysis without a classification.
  - Sustaining signals MUST NOT receive disruption filter analysis. They receive ONLY a
    `sustaining_rationale` and `competitive_implication`.
  - Disruptive signals MUST receive the full litmus test AND the 6-filter assessment table.
  - A signal's zone must be consistent with its classification: Nonconsumption and New-Market
    Foothold zones imply disruptive potential; Overserved Customers may be either sustaining
    (execution gap) or disruptive (performance overshoot). Justify explicitly if a signal's
    zone appears to conflict with its classification.
```

### 1.3 Phase 2 — Per-Filter Assessment Enforcement

**Current text** (Phase 2 Output Format):
```
| Filter | Assessment | Confidence |
|--------|------------|------------|
| Asymmetric Motivation | [Yes / No / Unclear] — [1-2 sentence rationale] | [Low / Medium / High] |
```

**Proposed addition** — add to Phase 2 Rules after the existing filter rules:

```markdown
- For each disruptive signal, you MUST produce a 6-row assessment evaluating ALL six disruption
  filters. Each row must include: result (Yes/No/Unclear), a 1-2 sentence rationale specific to
  this signal (not generic), and confidence (Low/Medium/High). Do not list filter names without
  individual assessments.
- When assessing Asymmetric Skills (RPV), provide separate evaluations for Resources, Processes,
  and Values — do not collapse them into a single sentence
- After the filter table, always output: filters_passed count, overall disruptive potential
  (Low/Medium/High), value_network_insight, alternative_explanation, and key_evidence_gap.
  These are mandatory fields, not optional.
```

### 1.4 Phase 3 — Reinforcement Map

**Proposed addition** — add new subsection after "Priority Rationale" in Phase 3 Output Format:

```markdown
### Signal Reinforcement Map
After scoring all signals, identify causal chains or reinforcement patterns:
- If Signal A creates conditions that make Signal B more likely or more impactful, document
  the relationship
- Note which sustaining signals act as accelerants for the disruptive signals
- Identify whether addressing upstream signals in the chain would reduce the urgency of
  downstream signals

Output format:
```
### Reinforcement Map
**Chain:** [Signal X] → [Signal Y] → [Signal Z] → [Downstream consequence]
**Strategic insight:** [1-2 sentences on where intervention is most efficient]
**Accelerants:** [Which sustaining signals weaken the incumbent's ability to respond to
the disruptive chain]
```
```

### 1.5 Phase 3 — Scoring Calibration Rules

**Proposed addition** — append to Phase 3 Rules:

```markdown
- When scoring speed: if VoC comments use past-tense language describing completed switching
  actions (e.g., "we moved to Dell," "contributed to switching"), score speed as 3 — the
  behavioral shift is already underway, not hypothetical
- When scoring impact: if multiple independent comments cite the same signal as a procurement
  decision trigger, score impact as 3 — it is affecting core revenue
- Sustaining signals that are high-urgency (impact=3, speed=3) should be labeled
  "Sustaining — Act" to distinguish from sustaining signals that are lower urgency.
  Do not classify sustaining signals as Disruptive to elevate their priority
```

### 1.6 Phase 4 — RPV and Experiment Structure

**Proposed addition** — append to Phase 4 Rules:

```markdown
- For each Investigate or Act recommendation, the RPV Assessment must evaluate Resources,
  Processes, and Values as separate items, not as a single combined judgment
- Each experiment candidate must include: assumption (starting with "We believe that..."),
  experiment type, what success looks like, and what failure looks like
- Recommended next steps must include at least 2 actions, each with a suggested owner role
  and timeframe
```

---

## Part 2: Architecture Changes — Split Step 1 into 1a/1b

### 2.1 Rationale

The gap analysis (R7) found that GPT-4o allocates insufficient attention to later phases when all 4 phases are requested in a single prompt. The existing sub-step pattern (5a/5b) demonstrates that:

- Sub-steps share `step_number` but have distinct `name` properties
- The graph orchestrator routes them sequentially via `WORKFLOW_STEP_ORDER`
- Each sub-step can have its own checkpoint for human review
- State flows naturally: 1a produces fields that 1b consumes

### 2.2 Sub-Step Design

```
Step 1a: Signal Scan & Interpretation
  Input:  voc_data
  Output: signals, interpreted_signals, coverage_gaps
  LLM:    Phase 1 (Scan) + Phase 2 (Interpret) — focused prompt

Step 1b: Signal Prioritization & Recommendation
  Input:  voc_data, signals, interpreted_signals
  Output: priority_matrix, signal_recommendations, agent_recommendation
  LLM:    Phase 3 (Prioritize) + Phase 4 (Recommend) — focused prompt with 1a output as context
```

### 2.3 New Pydantic Schemas

#### Step 1a Schemas (Scan + Interpret)

```python
# --- step1a_signal_scan_llm.py ---

class DetectedSignal(BaseModel):
    signal_id: str = Field(description="Short snake_case identifier")
    signal: str = Field(description="Concise signal description grounded in source input")
    zone: str = Field(
        description="Primary SOC Radar signal zone. Must be one of: Nonconsumption, "
        "Overserved Customers, Low-End Foothold, New-Market Foothold, "
        "Business Model Anomaly, Enabling Technology, Regulatory / Policy Shift"
    )
    source_type: str = Field(default="Internal VoC")
    observable_behavior: str = Field(description="What is actually happening")
    evidence: list[str] = Field(description="Direct excerpts from the input")
    supporting_comments: list[int] = Field(
        description="Comment numbers from the input that support this signal (e.g., [3, 5, 12])"
    )


class DisruptionFilterAssessment(BaseModel):
    filter_name: str = Field(description="One of the 6 disruption filter names")
    result: str = Field(description="Yes, No, or Unclear")
    confidence: str = Field(description="Low, Medium, or High")
    rationale: str = Field(description="1-2 sentence rationale specific to this signal")


class InterpretedSignal(BaseModel):
    signal_id: str
    signal: str
    zone: str
    classification: str = Field(
        description="Sustaining, Disruptive — New-Market, or Disruptive — Low-End"
    )
    confidence: str = Field(description="Low, Medium, or High")
    # --- Sustaining fields (populated when classification == Sustaining) ---
    sustaining_rationale: str = Field(
        default="",
        description="Why this serves existing customers along known dimensions (sustaining only)"
    )
    competitive_implication: str = Field(
        default="",
        description="Whether and how the incumbent can respond (sustaining only)"
    )
    # --- Disruptive fields (populated when classification starts with Disruptive) ---
    litmus_test: str = Field(
        default="",
        description="Pass or Fail with 1-sentence rationale (disruptive only)"
    )
    filters: list[DisruptionFilterAssessment] = Field(
        default_factory=list,
        description="6-filter assessment table (disruptive only)"
    )
    filters_passed: int = Field(
        default=0,
        description="Count of filters with result=Yes"
    )
    disruptive_potential: str = Field(
        default="",
        description="Low, Medium, or High (disruptive only)"
    )
    value_network_insight: str = Field(
        default="",
        description="Why the incumbent's value network causes them to ignore this signal"
    )
    alternative_explanation: str = Field(
        default="",
        description="At least one reason this might not be disruptive"
    )
    key_evidence_gap: str = Field(
        default="",
        description="What additional data would most change the assessment"
    )


class ScanInterpretResult(BaseModel):
    """Step 1a output — Scan and Interpret phases."""
    signals: list[DetectedSignal]
    interpreted_signals: list[InterpretedSignal]
```

#### Step 1b Schemas (Prioritize + Recommend)

```python
# --- step1b_signal_recommend_llm.py ---

class PriorityEntry(BaseModel):
    signal_id: str
    signal: str
    classification: str = Field(description="Carried from interpretation")
    impact: int = Field(ge=1, le=3)
    speed: int = Field(ge=1, le=3)
    score: int = Field(description="impact * speed")
    tier: str = Field(description="Act, Investigate, Monitor, Sustaining — Act, or Sustaining — Investigate")
    rationale: str = Field(description="2-3 sentences referencing evidence from Interpret phase")


class ReinforcementMap(BaseModel):
    chain: list[str] = Field(description="Ordered list of signal names forming a causal chain")
    strategic_insight: str = Field(description="Where intervention is most efficient")
    accelerants: list[str] = Field(
        default_factory=list,
        description="Sustaining signals that weaken incumbent's ability to respond"
    )


class RPVAssessment(BaseModel):
    resources: str = Field(description="Can the incumbent deploy capital, talent, or technology?")
    processes: str = Field(description="Are incumbent processes aligned or misaligned?")
    values: str = Field(description="Does cost structure make response attractive?")
    assessment: str = Field(
        description="Can respond / Cannot respond without structural change / Would choose not to respond"
    )


class NextStep(BaseModel):
    action: str = Field(description="Specific action description")
    owner: str = Field(description="Suggested owner role")
    timeframe: str = Field(description="e.g., 30 days, 60 days")


class ExperimentCandidate(BaseModel):
    assumption: str = Field(description="Starts with 'We believe that...'")
    experiment_type: str = Field(description="Customer Interview / Smoke Test / Concierge / Prototype / Survey")
    success: str = Field(description="What success looks like")
    failure: str = Field(description="What failure looks like")


class SignalRecommendation(BaseModel):
    signal_id: str
    action_tier: str = Field(description="Act or Investigate")
    what_we_know: str
    what_we_dont_know: list[str]
    rpv_assessment: RPVAssessment
    next_steps: list[NextStep]
    experiment_candidate: ExperimentCandidate


class WatchingBrief(BaseModel):
    signal_id: str
    signal: str
    review_frequency: str = Field(default="Quarterly")
    key_indicator: str
    escalation_trigger: str


class PrioritizeRecommendResult(BaseModel):
    """Step 1b output — Prioritize and Recommend phases."""
    priority_matrix: list[PriorityEntry]
    reinforcement_map: ReinforcementMap
    recommendations: list[SignalRecommendation] = Field(
        default_factory=list,
        description="For Act and Investigate tier signals only"
    )
    watching_briefs: list[WatchingBrief] = Field(
        default_factory=list,
        description="For Monitor tier signals only"
    )
    agent_recommendation: str = Field(description="Summary for the consultant")
```

### 2.4 File Changes Summary

| File | Change |
|------|--------|
| `backend/app/nodes/step1a_signal_scan_llm.py` | **New** — Phase 1+2 LLM logic with `ScanInterpretResult` schema |
| `backend/app/nodes/step1a_signal_scan.py` | **New** — Thin wrapper (like current `step1_signal.py`) |
| `backend/app/nodes/step1b_signal_recommend_llm.py` | **New** — Phase 3+4 LLM logic with `PrioritizeRecommendResult` schema |
| `backend/app/nodes/step1b_signal_recommend.py` | **New** — Thin wrapper |
| `backend/app/nodes/step1_signal_llm.py` | **Deprecate** — Keep for backward compatibility; mark as legacy |
| `backend/app/nodes/step1_signal.py` | **Deprecate** — Keep; delegates to step1a+1b internally |
| `backend/app/workers/steps.py` | **Modify** — Replace `SignalScannerWorker` with `SignalScanWorker` (1a) + `SignalRecommendWorker` (1b) |
| `backend/app/workers/registry.py` | **Modify** — Register both new workers in order |
| `backend/app/checkpoints.py` | **Modify** — Add `checkpoint_1a` and `checkpoint_1b`; update `REQUIRED_UPSTREAM_STATE` |
| `backend/app/state.py` | **Modify** — No new fields needed (existing fields cover both sub-steps) |
| `backend/app/skills/soc-radar/SKILL.md` | **Modify** — Apply prompt changes from Part 1 |

### 2.5 Prompt Design for Each Sub-Step

#### Step 1a System Prompt (Scan + Interpret)

The 1a prompt loads the full SKILL.md but overrides the task scope:

```python
system_prompt = (
    f"{skill_asset.body}\n\n"
    "You are the SOC Radar agent for the BMI consultant workflow.\n"
    "Execute ONLY Phase 1 (Scan) and Phase 2 (Interpret) from the skill above.\n"
    "Do NOT produce prioritization scores or recommendations — those come in a separate pass.\n\n"
    "SIGNAL EXTRACTION RULES:\n"
    "- Extract at least 7 distinct signals when the input contains 10+ observations\n"
    "- Do not collapse related phenomena into a single signal\n"
    "- Cite specific input comment numbers as supporting_comments for every signal\n"
    "- Every input comment should be cited by at least one signal\n\n"
    "CLASSIFICATION GATE:\n"
    "- Classify EVERY signal as Sustaining or Disruptive before any filter analysis\n"
    "- Sustaining signals: provide sustaining_rationale and competitive_implication; "
    "  leave filter fields empty\n"
    "- Disruptive signals: apply litmus test, then assess ALL 6 filters with individual "
    "  result/confidence/rationale per filter\n\n"
    "VALID SIGNAL ZONES: Nonconsumption, Overserved Customers, Low-End Foothold, "
    "New-Market Foothold, Business Model Anomaly, Enabling Technology, "
    "Regulatory / Policy Shift.\n"
    "VALID FILTERS: Asymmetric Motivation, Asymmetric Skills, Trajectory, "
    "Performance Overshoot, Barrier Removal, Business Model Conflict.\n"
)
```

#### Step 1b System Prompt (Prioritize + Recommend)

The 1b prompt receives the 1a output as structured context:

```python
system_prompt = (
    f"{skill_asset.body}\n\n"
    "You are the SOC Radar agent for the BMI consultant workflow.\n"
    "Phase 1 (Scan) and Phase 2 (Interpret) have already been completed.\n"
    "Execute ONLY Phase 3 (Prioritize) and Phase 4 (Recommend).\n\n"
    "PRIORITIZATION RULES:\n"
    "- Score every signal on impact (1-3) and speed (1-3); score = impact * speed\n"
    "- Tier: 7-9 = Act, 4-6 = Investigate, 1-3 = Monitor\n"
    "- Sustaining signals use tiers: Sustaining — Act, Sustaining — Investigate, "
    "  Sustaining — Monitor\n"
    "- Past-tense switching language in VoC (e.g., 'we moved to Dell') = speed 3\n"
    "- Multiple independent comments citing the same procurement trigger = impact 3\n\n"
    "REINFORCEMENT MAP:\n"
    "- After scoring, identify causal chains between signals\n"
    "- Note which sustaining signals act as accelerants\n\n"
    "RECOMMENDATION RULES:\n"
    "- Act/Investigate signals: full RPV assessment (Resources, Processes, Values separately), "
    "  2-3 next steps with owner and timeframe, experiment candidate with success/failure criteria\n"
    "- Monitor signals: watching brief with key indicator and escalation trigger\n"
)

user_prompt = (
    "The following signals were detected and interpreted from Voice of Customer data.\n"
    "Prioritize them and provide recommendations.\n\n"
    f"## Original VoC Data\n{voc_data}\n\n"
    f"## Detected Signals\n{json.dumps(signals, indent=2)}\n\n"
    f"## Interpreted Signals\n{json.dumps(interpreted_signals, indent=2)}\n"
)
```

### 2.6 State Flow

```
┌─────────────────────────────┐
│     voc_data (input)        │
└──────────┬──────────────────┘
           │
    ┌──────▼──────┐
    │  Step 1a    │  Scan + Interpret
    │  LLM Call 1 │
    └──────┬──────┘
           │ writes: signals, interpreted_signals, coverage_gaps
           │
    ┌──────▼──────────┐
    │  Checkpoint 1a  │  (human can review/edit signals)
    └──────┬──────────┘
           │
    ┌──────▼──────┐
    │  Step 1b    │  Prioritize + Recommend
    │  LLM Call 2 │  reads: voc_data, signals, interpreted_signals
    └──────┬──────┘
           │ writes: priority_matrix, signal_recommendations, agent_recommendation
           │
    ┌──────▼──────────┐
    │  Checkpoint 1b  │  (human can review/edit priorities)
    └──────┬──────────┘
           │
    ┌──────▼──────┐
    │  Step 2     │  Pattern Matching
    └─────────────┘
```

### 2.7 Checkpoint & Registry Changes

#### `checkpoints.py` — Replace `step1_signal` entry:

```python
CHECKPOINTS_BY_STEP = {
    "step1a_signal_scan": CheckpointDefinition(
        name="checkpoint_1a",
        after_step_name="step1a_signal_scan",
        step_number=1,
    ),
    "step1b_signal_recommend": CheckpointDefinition(
        name="checkpoint_1b",
        after_step_name="step1b_signal_recommend",
        step_number=1,
        required_state_fields=("signals", "interpreted_signals"),
    ),
    # ... rest unchanged
}

REQUIRED_UPSTREAM_STATE = {
    "step1a_signal_scan": ("voc_data",),
    "step1b_signal_recommend": ("voc_data", "signals", "interpreted_signals"),
    "step2_pattern": ("voc_data", "signals"),  # unchanged — signals already present after 1a
    # ... rest unchanged
}
```

#### `registry.py` — Replace `SignalScannerWorker()`:

```python
workers: list[BaseWorker] = [
    SignalScanWorker(),          # step1a_signal_scan
    SignalRecommendWorker(),     # step1b_signal_recommend
    PatternMatcherWorker(),
    # ... rest unchanged
]
```

### 2.8 Backward Compatibility

- The existing `step1_signal.py` / `step1_signal_llm.py` remain in the codebase
- The `run_step1_eval.py` evaluation script can be updated to call step1a then step1b, or left as-is for single-pass comparison
- The CLI `run` command works unchanged — the graph auto-discovers steps from the registry
- Existing tests that reference `step1_signal` in `completed_steps` or `current_step` will need updates

---

## Part 3: Test Plan

### 3.1 Existing Tests — Required Modifications

The current feature file (`step1-signal-scanner.feature`) defines behavioral contracts that must be preserved. The split requires updating step references but NOT the behavioral expectations.

| Current Test | Impact | Change Needed |
|-------------|--------|---------------|
| `step1_result` fixture calls `run_step(state)` | Needs to call 1a then 1b sequentially | Create a `run_step1_combined(state)` helper or update fixture |
| `current_step == "signal_scan"` assertion | After split, 1b sets `current_step = "signal_recommend"` | Update expected step name |
| Signal/interpreted/priority list assertions | Still valid | No change — fields still produced |
| Zone/filter/classification validators | Still valid | No change |
| LLM judge evaluation | Still valid | May score higher due to improved completeness |

### 3.2 New Feature File — Step 1a

```gherkin
Feature: Step 1a signal scan and interpretation
  Step 1a extracts signals from VoC input and classifies them as sustaining or disruptive.

  Scenario: Step 1a produces signals with comment-level evidence
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1a signal scan node runs
    Then the workflow state contains at least 5 detected signals
    And every signal has at least one supporting comment index
    And every signal zone is a valid SOC Radar zone

  Scenario: Step 1a enforces the classification gate
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1a signal scan node runs
    Then every interpreted signal has a valid classification
    And every sustaining signal has a sustaining rationale
    And every sustaining signal has no disruption filter assessments
    And every disruptive signal has a litmus test result
    And every disruptive signal has exactly 6 filter assessments

  Scenario: Step 1a produces interpreted signals with per-filter detail
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1a signal scan node runs
    Then every disruptive signal filter has a result of Yes, No, or Unclear
    And every disruptive signal filter has a confidence of Low, Medium, or High
    And every disruptive signal has a value network insight
    And every disruptive signal has an alternative explanation
    And every disruptive signal has a key evidence gap
```

### 3.3 New Feature File — Step 1b

```gherkin
Feature: Step 1b signal prioritization and recommendation
  Step 1b scores signals and produces actionable recommendations.

  Scenario: Step 1b produces priority matrix from interpreted signals
    Given a workflow state with Step 1a output from the firmware assessment VoC sample
    When the Step 1b signal recommend node runs
    Then every priority score equals impact times speed
    And every priority tier matches its score range
    And the priority matrix includes both sustaining and disruptive tiers

  Scenario: Step 1b produces a reinforcement map
    Given a workflow state with Step 1a output from the firmware assessment VoC sample
    When the Step 1b signal recommend node runs
    Then the workflow state contains a reinforcement map
    And the reinforcement map has a non-empty causal chain
    And the reinforcement map has a strategic insight

  Scenario: Step 1b produces structured recommendations for Act and Investigate signals
    Given a workflow state with Step 1a output from the firmware assessment VoC sample
    When the Step 1b signal recommend node runs
    Then every Act or Investigate recommendation has an RPV assessment
    And every RPV assessment evaluates resources, processes, and values separately
    And every recommendation has at least 2 next steps with owner and timeframe
    And every experiment candidate starts with "We believe that"
    And every experiment candidate has success and failure criteria

  Scenario: Step 1b produces watching briefs for Monitor signals
    Given a workflow state with Step 1a output from the firmware assessment VoC sample
    When the Step 1b signal recommend node runs
    Then every Monitor signal has a watching brief
    And every watching brief has a key indicator and escalation trigger
```

### 3.4 Integration Test — Full Step 1 (1a + 1b Combined)

```gherkin
Feature: Step 1 end-to-end signal analysis
  Step 1a and 1b together produce the complete SOC Radar analysis.

  Scenario: Combined Step 1 passes LLM judge quality assessment
    Given a workflow state with the firmware assessment VoC sample
    When the Step 1a signal scan node runs
    And the Step 1b signal recommend node runs with Step 1a output
    And the LLM judge evaluates the combined signal analysis
    Then the judge completeness score is at least 4
    And the judge relevance score is at least 4
    And the judge groundedness score is at least 4
    And the judge SKILL compliance score is at least 4

  Scenario: Combined Step 1 produces more signals than single-pass
    Given a workflow state with the Compute BU VoC sample
    When the Step 1a signal scan node runs
    And the Step 1b signal recommend node runs with Step 1a output
    Then the workflow state contains at least 6 detected signals
    And the workflow state contains at least 2 disruptive signals
    And the workflow state contains at least 2 sustaining signals
```

### 3.5 Regression Test — Existing Workflow Pipeline

The existing `step1-signal-scanner.feature` scenarios must continue to pass. Create a backward-compatible `run_step(state)` that internally calls 1a then 1b:

```python
# backend/app/nodes/step1_signal.py (updated)
def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    """Backward-compatible entry point — runs 1a then 1b."""
    from backend.app.nodes.step1a_signal_scan import run_step as run_1a
    from backend.app.nodes.step1b_signal_recommend import run_step as run_1b
    state_after_1a = run_1a(state)
    return run_1b(state_after_1a)
```

### 3.6 Test Execution Order

```
1. Run existing step1 BDD tests (regression — must still pass)
2. Run new step1a feature tests
3. Run new step1b feature tests
4. Run combined step1 integration tests
5. Run full workflow pipeline test (end-to-end)
```

---

## Summary — Does This Require Splitting Step 1?

**Yes**, but in the same way Step 5 is already split into 5a/5b. The changes are:

| Aspect | Impact |
|--------|--------|
| Logical step number | Unchanged — both 1a and 1b report `step_number=1` |
| Downstream steps (2-9) | Unchanged — they consume the same state fields |
| CLI interface | Unchanged — `run --input ... --no-pause-at-checkpoints` still works |
| API interface | Unchanged — graph auto-discovers new step order from registry |
| Checkpoint flow | Enhanced — human can now review signals *before* prioritization |
| Database schema | Unchanged — `StepOutput` already supports sub-step names |
| Total LLM calls for Step 1 | Increases from 1 to 2 |

The split follows an established pattern in the codebase and provides the additional benefit of a human review checkpoint between signal detection and prioritization — allowing a consultant to add, remove, or reclassify signals before the model scores them.
