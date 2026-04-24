# Plan: Multi-Alternative VP Portfolio Cascade

## TL;DR
Transform Step 5 from generating a single Value Proposition Canvas into a **VP Portfolio system** that ideates multiple alternative value propositions (configurable, default 3), scores them with LLM-driven criteria, lets the consultant select which to pursue at a checkpoint, and cascades the selected VPs through Steps 6-8 — each producing per-VP Business Model Canvases, risk maps, and experiment plans.

## Rationale (Strategyzer VPD + Invincible Company)
- Strategyzer's Value Proposition Design explicitly prescribes: "Prototype multiple alternatives — do not refine a single direction early."
- The Invincible Company emphasizes a **portfolio approach** where teams test 3-5 competing value propositions for desirability before committing.
- The CXIF SKILL.md already states: "Generate alternatives, not a single refined direction."
- Current Step 5 violates this by emitting a single Value Map. The ad-lib prototypes hint at alternatives but aren't distinct VPs.

## Architecture Change

**Current flow:**
```
Step 4 → Step 5 (1 VP) → [CP5] → Step 6 (1 BMC + Fit) → ... → Step 8 (1 experiment plan)
```

**New flow:**
```
Step 4 → Step 5a (N VP alternatives) → Step 5b (rank + recommend) → [CP5: consultant selects] → Step 6 (BMC per selected VP) → [CP6] → Step 7 (risk map per selected VP) → [CP7] → Step 8 (experiments per VP + comparative desirability tests)
```

---

## Phase 1: Step 5 Split (Core Change)

### Step 5a — VP Ideation (Diverge)

**Node:** `step5a_ideation_llm.py` (new file)

**Purpose:** Generate N distinct VP alternatives, each exploring a different but pattern-coherent way to address customer needs. Patterns are not decoration — they are strategic design constraints that shape every element of the Value Map.

---

#### Why Patterns Are the Primary Design Constraint

Each pattern in the Strategyzer library carries a **strategic imperative** (e.g., "Unlock Markets", "Kill Costs", "Access Customers") and **trigger questions** that test whether the pattern applies. When Step 2 selects 1-2 patterns, it locks three design dimensions:

1. **Desirability (frontstage):** The pattern selects WHICH customer segment to target and WHICH jobs/pains/gains to prioritize from the empathy profile. Market Explorers → non-consumers; Gravity Creators → existing users with switching costs; Channel Kings → underserved-by-distribution segment.

2. **Feasibility (backstage):** The pattern determines WHAT operating model is required — what activities, resources, and partnerships the supplier MUST build. Activity Differentiators → new activity configurations; Resource Castles → moat-building IP/brand; Scalers → delegation/licensing. Pain relievers can ONLY promise what the pattern's operating model can deliver.

3. **Viability (financial):** The pattern shapes WHICH revenue mechanics and cost structures are viable. Revenue Differentiators → recurring/freemium/bait-hook; Cost Differentiators → resource-light; Margin Masters → high-end pricing.

**Consequence for VP alternatives:** Each alternative must be internally coherent with the selected pattern(s). You cannot promise "premium specialist support" (pain reliever) if your pattern is Market Explorers/Democratizers (which demands low-touch, self-serve delivery).

---

#### Ideation Strategy: Pattern-Constrained Divergence

With 1-2 selected patterns, each typically having 2-4 flavors, the ideation space is:

**Axis 1 — Pattern Flavor Application** (primary divergence axis):
- Each selected pattern has distinct flavors (e.g., Market Explorers has Visionaries, Repurposers, Democratizers). Each flavor implies a different VP:
  - **Visionaries:** VP targets unproven needs with bold new offering
  - **Repurposers:** VP repurposes existing tech/infrastructure for new context
  - **Democratizers:** VP makes expensive capability accessible to underserved segment
- If 2 patterns are selected, explore **cross-pattern combinations** (e.g., Market Explorers × Revenue Differentiators → Democratizers + Freemium)

**Axis 2 — Customer Job Focus** (secondary divergence axis):
- The empathy profile contains multiple customer jobs, pains, gains. Different alternatives can emphasize different primary jobs from the profile while staying pattern-coherent.
- Example: same Democratizer pattern applied to "manage firmware independently" (autonomy job) vs. "keep infrastructure stable proactively" (reliability job) → two different VP designs

**Axis 3 — Context Scenario** (tertiary divergence axis):
- Different customer contexts/situations where the pattern applies differently. The actionable insights and VoC data surface multiple contexts.

**Non-negotiable constraint:** All axes must satisfy the pattern's strategic imperative. If pattern = Market Explorers, every alternative MUST target an untapped/underserved market. The divergence is in HOW, not WHETHER.

---

#### Pattern-Coherence Validation Rules (embedded in prompt)

Each VP alternative must pass these coherence checks:

1. **Segment-Pattern Alignment:** The target customer segment is consistent with the pattern's strategic imperative (e.g., Democratizers → underserved non-consumers, not existing premium customers)
2. **Pain Reliever Deliverability:** Every pain reliever can be delivered by the operating model the pattern implies (e.g., if pattern requires self-serve, don't promise specialist intervention)
3. **Gain Creator Realism:** Gain creators align with what the pattern's financial model can sustain (e.g., Cost Differentiators can't promise premium white-glove gains)
4. **No Cross-Pattern Contradiction:** If 2 patterns are selected, the VP doesn't satisfy one while violating the other
5. **Trigger Question Affirmation:** The VP design answers the pattern's trigger question affirmatively (the same test Step 2 used to select the pattern)

---

#### Pattern Context Injection (what the prompt receives)

The 5a prompt must receive **rich pattern context**, not just pattern names. Load from `strategyzer-pattern-library.json`:

- `pattern.name` — e.g., "Market Explorers"
- `pattern.strategic_imperative` — e.g., "Unlock Markets"
- `pattern.description` — Full description of the pattern's business model innovation
- `pattern.trigger_question` — e.g., "How could we tap into new, untapped, or underserved markets?"
- `pattern.assessment_question` — e.g., "How large and attractive is the untapped market potential?"
- `pattern.flavors[]` — Each flavor with name, description, trigger_question, examples
- `pattern.category` — Frontstage/Backstage/Profit Formula (indicates which BMC dimension it primarily reshapes)

This requires a new loader function: `load_pattern_details(pattern_names: list[str]) -> list[dict]` in `backend/app/patterns/` that extracts full pattern + flavor data from the JSON.

---

#### New Pydantic Schemas

```
VPAlternative:
  name: str                          # Descriptive VP name (e.g., "Democratized Self-Serve Assessment")
  pattern_flavor_applied: str        # Which flavor(s) this VP explores (e.g., "Democratizers")
  strategic_rationale: str           # WHY this VP is coherent with the pattern's imperative
  target_segment: str                # WHO this VP serves (must align with pattern)
  primary_job_focus: str             # Which customer job from empathy profile is primary
  context_scenario: str              # Customer context/situation being addressed
  products_services: list[ProductService]
  pain_relievers: list[PainReliever]
  gain_creators: list[GainCreator]
  ad_lib_prototype: AdLibPrototype
  pattern_coherence_note: str        # How this VP answers the pattern's trigger question

VPIdeationOutput:
  pattern_context: str               # Selected patterns + direction summary
  ideation_rationale: str            # How alternatives were derived from pattern × empathy matrix
  alternatives: list[VPAlternative]  # N items (configurable via num_vp_alternatives, default 3)
  diversity_check: str               # Self-assessment: how alternatives differ across axes
```

---

#### Prompt Architecture

**System prompt components:**
1. CXIF skill asset (`step5a_vp_ideation.md`)
2. Pattern-as-design-constraint framing (the 3-dimension framework above)
3. Pattern coherence validation rules
4. Value Proposition Canvas mechanics from Strategyzer VPD (Products & Services types, Pain Reliever types, Gain Creator types, Ad-Lib format)

**User prompt components:**
1. Pattern direction + full pattern details (loaded from JSON, not just names)
2. Customer empathy profile (jobs, pains, gains)
3. Actionable insights + value driver tree
4. VoC evidence (for grounding)
5. `num_vp_alternatives` (how many to generate)
6. Explicit instruction: "Each alternative must explore a DIFFERENT flavor or job-focus while remaining coherent with the pattern's strategic imperative"

**State writes:** `vp_alternatives` (structured list of dicts from VPIdeationOutput)

### Step 5b — VP Scoring (Converge)

**Node:** `step5b_scoring_llm.py` (new file)

**Purpose:** Evaluate and rank each VP alternative on desirability criteria aligned with Strategyzer VPD.

**Scoring Criteria:**
1. **Customer need coverage** — How many high-severity pains and essential gains addressed?
2. **Evidence grounding** — How much upstream VoC evidence supports this direction?
3. **Pattern fit** — How well does this VP leverage the selected patterns?
4. **Differentiation** — How distinct from status quo / incumbent solutions?
5. **Testability** — Can we quickly de-risk the core desirability assumptions?

**New Pydantic Schemas:**
- `VPScore`: alternative_name, coverage_score (High/Medium/Low), evidence_score, pattern_fit_score, differentiation_score, testability_score, overall_recommendation ("Recommended"/"Worth exploring"/"Deprioritize"), rationale
- `VPScoringOutput`: rankings (list[VPScore]), recommended_indices (list[int]), comparative_summary (str)

**State writes:** `vp_rankings`, `vp_recommended` (list[int])

### Backward Compatibility Bridge

After Step 5b and checkpoint selection:
- `value_proposition_canvas` (the original field) is populated with a **combined markdown** showing all selected VP alternatives, each clearly labeled — ensuring Steps 6-8 can read it.
- OR, the old field becomes a "primary VP" pointer while `vp_portfolio` carries the full set.

Decision: the combined markdown approach is simpler and avoids breaking the Step 6 prompt contract immediately.

---

## Phase 2: Checkpoint 5 Enhancement

**Checkpoint behavior:**
- Renders a comparison table: VP name | Job Focus | Context | Coverage | Evidence | Pattern Fit | Recommendation
- LLM recommendation highlighted
- Consultant can: approve recommended set, select different subset, edit alternatives, or retry
- Stores `selected_vp_indices: list[int]` in state

**Required state field for resume:** `selected_vp_indices`

---

## Phase 3: Step 6 Adaptation

**Changes to `step6_design_llm.py`:**
- Read `vp_alternatives` + `selected_vp_indices` from state
- For each selected VP, generate a per-VP BMC (9 blocks) + Fit Assessment
- Alternatively: single LLM call that produces portfolio-level BMC if selected count is small (≤3)

**State writes:**
- `business_model_canvas` — Markdown with clearly labeled sections per VP alternative
- `fit_assessment` — Markdown with per-VP fit rows

---

## Phase 4: Step 7 Adaptation

**Changes to `step7_risk_llm.py`:**
- Read per-VP BMC + Fit Assessment
- For each selected VP, extract DVF assumptions and build importance-evidence matrix
- Tag each assumption with which VP it belongs to

**State writes:**
- `assumptions` — Markdown with per-VP assumption sections
- `step7_structured` — Structured data with VP-keyed assumptions

---

## Phase 5: Step 8 Adaptation

**Changes to `step8_pdsa_llm.py`:**
- For each selected VP's "Test first" assumptions → select experiment cards, generate plans
- ADD: **Comparative desirability experiments** that discriminate between VP alternatives (e.g., A/B landing page tests, preference interviews)
- Experiment plans explicitly reference which VP they're testing

**State writes:**
- `experiment_selections`, `experiment_plans`, `experiment_worksheets` — Include VP attribution
- New optional: `comparative_experiments` — Experiments designed to choose between VPs

---

## Phase 6: State & Infrastructure

### New BMIWorkflowState fields (`state.py`)
- `num_vp_alternatives: int` — Configurable (default 3)
- `vp_alternatives: list[dict]` — Step 5a structured output
- `vp_rankings: list[dict]` — Step 5b scoring output
- `vp_recommended: list[int]` — LLM recommended indices
- `selected_vp_indices: list[int]` — Consultant selection at checkpoint 5

### Graph changes (`graph.py`)
- Add `step5a_ideation` and `step5b_scoring` as separate worker nodes
- Remove old `step5_define` worker
- Update orchestrator routing: step5a → step5b → checkpoint_5 → step6

### Checkpoint changes (`checkpoints.py`)
- Update checkpoint_5 to require `selected_vp_indices`
- Update `REQUIRED_UPSTREAM_STATE` for step6 to include `vp_alternatives`, `selected_vp_indices`

---

## Phase 7: BDD / Tests

### Feature file updates (behavior IS changing)
- `step5-define.feature` → becomes `step5a-ideation.feature` + `step5b-scoring.feature`
- New scenarios: "Step 5a generates N distinct VP alternatives", "Step 5b ranks alternatives with scoring criteria", "Consultant selects VP alternatives at checkpoint 5"
- Update step6/7/8 features to reflect portfolio-aware behavior

### Step definition updates
- New test fixtures for multi-VP state
- Assertions on alternative count, diversity, scoring criteria

---

## Relevant Files

**New files:**
- `backend/app/nodes/step5a_ideation_llm.py` — VP ideation node
- `backend/app/nodes/step5b_scoring_llm.py` — VP scoring node
- `backend/app/prompts/step5a_vp_ideation.md` — Prompt asset for ideation
- `backend/app/prompts/step5b_vp_scoring.md` — Prompt asset for scoring
- `backend/tests/features/step5a-ideation.feature` — BDD for 5a
- `backend/tests/features/step5b-scoring.feature` — BDD for 5b

**Modified files:**
- `backend/app/nodes/step5_define_llm.py` — Deprecate or remove (replaced by 5a+5b)
- `backend/app/state.py` — Add new state fields
- `backend/app/graph.py` — Add 5a/5b nodes, update routing, remove old step5
- `backend/app/checkpoints.py` — Update checkpoint 5 definition, REQUIRED_UPSTREAM_STATE
- `backend/app/nodes/step6_design_llm.py` — Portfolio-aware BMC generation
- `backend/app/nodes/step7_risk_llm.py` — Portfolio-aware assumption extraction
- `backend/app/nodes/step8_pdsa_llm.py` — Portfolio-aware experiments + comparative tests
- `backend/tests/features/step5-define.feature` — Replace with 5a/5b features
- `backend/tests/features/step6-design.feature` — Update for portfolio
- `backend/tests/features/step7-risk.feature` — Update for portfolio
- `backend/tests/features/step8-pdsa.feature` — Update for portfolio
- `backend/tests/test_bdd_step5_define.py` — Replace with 5a/5b step defs
- `backend/tests/test_bdd_step6_design.py` — Update assertions
- `backend/tests/test_bdd_step7_risk.py` — Update assertions
- `backend/tests/test_bdd_step8_pdsa.py` — Update assertions
- `frontend/streamlit_app.py` — VP comparison UI at checkpoint 5
- `backend/cli/export_report.py` — Portfolio-aware report export

---

## Verification

1. **Unit:** `docker compose exec bmi-backend pytest backend/tests/test_bdd_step5a_ideation.py -q` — 5a generates N alternatives with distinct job/pain/gain focus
2. **Unit:** `docker compose exec bmi-backend pytest backend/tests/test_bdd_step5b_scoring.py -q` — 5b produces rankings with all 5 criteria
3. **Regression:** `docker compose exec bmi-backend pytest backend/tests -q` — all existing step 6/7/8 tests still pass
4. **Integration:** `docker compose exec bmi-backend pytest backend/tests/test_workflow.py -q` — end-to-end run through all steps with portfolio
5. **Manual:** Streamlit frontend shows VP comparison table at checkpoint 5, consultant can select alternatives
6. **Quality:** Verify LLM output diversity — alternatives should address different job clusters, not minor variations of the same VP

---

## Decisions
- Step 5 splits into two nodes (5a Ideation + 5b Scoring) for SRP and output quality
- N is configurable via `num_vp_alternatives` state field (default 3)
- Checkpoint 5 becomes a mandatory selection point with LLM recommendation + consultant override
- Steps 6-8 operate on selected VP portfolio (not all generated alternatives)
- Backward compatibility: `value_proposition_canvas` field kept as combined markdown for gradual migration
- Feature files ARE updated (this is a legitimate behavior change, not a test fix)

## Implementation Order & Dependencies
1. Phase 6 (State) — no dependencies, unblocks everything
2. Phase 1 (Step 5a+5b) — depends on Phase 6
3. Phase 2 (Checkpoint 5) — depends on Phase 1 + 6
4. Phase 3 (Step 6) — depends on Phase 1 + 2 + 6, parallel with Phase 4
5. Phase 4 (Step 7) — depends on Phase 3 + 6, parallel with Phase 3
6. Phase 5 (Step 8) — depends on Phase 4
7. Phase 7 (Tests) — write BDD features FIRST per phase, then implement (BDD-TDD cycle)

## Further Considerations
1. **LLM cost:** Each VP alternative in Steps 6-8 means ~3x LLM calls. Consider: batch single-call approach for ≤3 VPs vs. parallel per-VP calls for >3.
2. **Report export:** `export_report.py` needs portfolio-aware rendering — show all VP tracks or just the selected ones?
3. **Frontend complexity:** The Streamlit VP comparison UI is a significant addition. Consider a phased frontend rollout (backend first, then UI).
