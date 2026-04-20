# Release Plan: Step 8 Decomposition (v2)

**Date:** 2026-04-18
**Owner:** BMI Workflow Team
**Status:** Draft — awaiting review
**Depends on:** Research findings in `docs/research/step7-8-quality-assessment.md`

---

## Problem Statement

Step 8 currently uses 9 of 44 experiment cards, produces identical recommendations for same-category assumptions, has no LLM reasoning, and generates boilerplate success/failure criteria. Consultants running the workflow across different VoC inputs receive monotonous, undifferentiated output that limits their ability to select the right experiments for each assumption.

---

## Design Principles

1. **The feature file defines behavior** — production code changes to make tests pass, not the other way around.
2. **Single responsibility** — each sub-step does one thing well.
3. **No regression** — existing Step 7 → Step 8 contract (markdown parsing of "Test first" rows) must continue to work during incremental delivery.
4. **Incremental delivery** — each phase is independently shippable and testable.

---

## Phase 0: Quick Win (Immediate)

**Goal:** Replace hardcoded `PATH_BY_CATEGORY` with `EXPERIMENT_MATRIX` + a single LLM call to differentiate card selection per assumption.

**Scope:**
- Modify `step8_pdsa.py` to use `EXPERIMENT_MATRIX` for card selection
- Add an LLM call that receives assumption text + EXPERIMENT_MATRIX candidates and returns the best-fit 3 cards
- Expand coverage from 9 to ~23 cards
- Same-category assumptions will get different experiments based on their content

**Acceptance criteria:**
- Two Desirability "Test first" assumptions produce different experiment card selections
- All selected card names exist in `experiment-library.json`
- Evidence strength ordering is maintained (Weak → Medium → Strong or Weak → Medium → Medium)
- Existing BDD tests pass without modifying `.feature` files

**Estimated effort:** 1 session

---

## Phase 1: Step 8a — Evidence Audit

**Goal:** Before selecting experiments, assess what evidence already exists for each "Test first" assumption based on the VoC data and upstream step outputs.

**New node:** `step8a_evidence_audit.py`

**Input:**
- `assumptions` (Step 7 output — "Test first" rows)
- `voc_data` (original VoC input)
- `customer_profile` (Step 3 output)
- `signal_scan` (Step 1 output)

**Output:** For each assumption, an `evidence_level` field:
- `None` — no relevant evidence found in prior steps
- `Weak` — VoC contains anecdotal or indirect references
- `Medium` — VoC contains direct behavioral observations or multiple corroborating signals

**LLM call:** Yes — the LLM reads the assumption text against the VoC/signal context and classifies the existing evidence level.

**State change:** Adds `assumption_evidence_audit` to state (list of `{assumption, category, existing_evidence_level, evidence_summary}`).

**Acceptance criteria:**
- An assumption about "delivery delays" where the VoC has 14 months of delivery complaints → `Weak` (not `None`)
- An assumption about "CXL adoption" where the VoC has no customer feedback → `None`
- Feature file defines expected audit behavior; step definition validates LLM output structure

**Estimated effort:** 1-2 sessions

---

## Phase 2: Step 8b — Card Selection

**Goal:** Use the full 44-card library to select 3-5 candidate cards per assumption, driven by assumption content, DVF category, and existing evidence level from 8a.

**New node:** `step8b_card_selection.py`

**Input:**
- `assumption_evidence_audit` (from 8a)
- Full 44-card library (loaded from `experiment-library.json`)

**LLM call:** Yes — receives assumption text, category, existing evidence level, and the full card list for that category. Returns ranked card candidates with rationale.

**Output:** For each assumption:
- 3-5 candidate cards (not just 3) with selection rationale
- Primary recommendation (the first card to run)
- Why alternatives were considered

**Key constraint:** Card names must exist in `experiment-library.json`. The LLM selects from a constrained set, not free text.

**State change:** Adds `experiment_card_selections` to state.

**Acceptance criteria:**
- Two Desirability assumptions with different content produce different card selections
- A Feasibility assumption with `Weak` existing evidence skips the Weak tier and starts at Medium
- All card names validate against the library
- At least 15 of 44 cards are reachable across a diverse set of VoC inputs

**Estimated effort:** 2 sessions

---

## Phase 3: Step 8c — Path Sequencing

**Goal:** Build assumption-specific escalation paths using the library's `usually_runs_after`/`usually_runs_next` fields and Precoil's 5 sequencing rules.

**New node:** `step8c_path_sequencing.py`

**Input:**
- `experiment_card_selections` (from 8b)
- Library card definitions (for sequencing metadata)

**Logic:** Primarily rule-based with LLM validation.
1. For each selected primary card, walk `usually_runs_next` to build the path
2. Validate path against 5 sequencing rules (opinion→behavior, cheap→expensive, simulated→real, interest→commitment, first-use→repeat-use)
3. LLM validates the path makes sense for the specific assumption

**Output:** For each assumption:
- Ordered evidence path (3-5 cards)
- Move-to-next criteria specific to the assumption
- Library ceiling warning if the path terminates before Strong evidence

**State change:** Adds `experiment_paths` to state.

**Acceptance criteria:**
- Desirability paths correctly reflect the zero-Strong-card ceiling
- Feasibility paths can reach Strong evidence via Concierge/Wizard of Oz/MVP
- `usually_runs_next` relationships are respected
- Evidence ordering never decreases

**Estimated effort:** 1-2 sessions

---

## Phase 4: Step 8d — Brief & Worksheet Generation

**Goal:** Generate experiment briefs with success/failure criteria specific to the assumption content and VoC context, replacing generic boilerplate.

**Refactored from:** Current `_format_precoil_brief()`, `_format_implementation_plan()`, `_format_worksheet()` functions.

**Input:**
- `experiment_paths` (from 8c)
- `assumption_evidence_audit` (from 8a)
- `customer_profile` (Step 3)
- `value_proposition_canvas` (Step 5)

**LLM call:** Yes — generates context-specific:
- "What You're Trying to Learn" tied to the specific assumption
- Success/failure thresholds grounded in the customer segment and VoC
- Sample size and timebox recommendations scaled to the assumption risk level

**Output:** Formatted markdown briefs, implementation plans, worksheets, and structured card objects (Zone A immutable / Zone B updatable).

**State change:** Updates `experiment_selections`, `experiment_plans`, `experiment_worksheets`, `experiment_cards`.

**Acceptance criteria:**
- Success criteria for a delivery-delay assumption mentions delivery timelines, not generic percentages
- Two different assumptions produce different "What You're Trying to Learn" sections
- Zone A/B enforcement still works
- `update_experiment_card_evidence()` continues to function unchanged

**Estimated effort:** 2 sessions

---

## Phase 5: Step 7 Flexibility (Parallel Track)

**Goal:** Allow Step 7 to produce 2-5 assumptions per category based on VoC complexity.

**Changes:**
- Relax `min_length=3, max_length=3` in `DVFCategory` schema to `min_length=2, max_length=5`
- Update Step 7 prompt to: "Generate 2-5 assumptions per category. Use fewer when the VoC is narrow; use more when it surfaces multiple distinct risks."
- Add a `voc_evidence_strength` field to each assumption so Step 8a doesn't start from scratch

**Acceptance criteria:**
- A narrow firmware VoC produces 2 Viability assumptions (not forced to 3)
- A rich multi-signal VoC produces 4-5 Desirability assumptions
- Step 8a correctly receives variable-length assumption lists
- Feature file behavior is unchanged (the contract is "assumptions are extracted and mapped")

**Estimated effort:** 1 session

---

## Delivery Sequence

```
Phase 0 (Quick Win)     ← Start here, immediate value
    ↓
Phase 1 (8a Evidence Audit)
    ↓
Phase 2 (8b Card Selection)    Phase 5 (Step 7 Flexibility) ← parallel track
    ↓
Phase 3 (8c Path Sequencing)
    ↓
Phase 4 (8d Brief Generation)
```

---

## Migration Strategy

- Phase 0 modifies `step8_pdsa.py` in place — no new nodes
- Phases 1-4 introduce new nodes (`step8a_*.py`, `step8b_*.py`, etc.) that chain together
- The original `step8_pdsa.py` is retained as fallback until Phase 4 is complete
- Graph wiring in `backend/app/graph.py` switches from single Step 8 node to 8a→8b→8c→8d chain
- State schema in `backend/app/state.py` gains new fields: `assumption_evidence_audit`, `experiment_card_selections`, `experiment_paths`
- Existing `experiment_selections`, `experiment_plans`, `experiment_worksheets`, `experiment_cards` fields remain — Phase 4 populates them with richer content

---

## Testing Strategy

Each phase follows BDD-TDD:
1. Write/update `.feature` file for the sub-step behavior
2. Write step definitions with mocks
3. Implement the production node
4. Run full regression: `docker compose exec bmi-backend pytest backend/tests -q`

No `.feature` file behavior is altered to make tests pass. Step definitions (mocks, fixtures) may be adjusted.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| LLM hallucinating card names | Constrain selection to validated list from `experiment-library.json` |
| Regression in Step 8 output format | Existing BDD tests run after each phase |
| Increased latency from multiple LLM calls | 8a and 8b can potentially share a single LLM call; 8c is mostly rule-based |
| Step 7 variable-length output breaking Step 8 parser | Phase 5 includes parser update in `_extract_top_assumptions()` |
