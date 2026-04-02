# Strategy and Implementation Plan: Interactive Experiment Cards for Step 8

## 1. Problem Diagnosis

The current Step 8 output has five structural problems that make it unusable as a working consultant tool:

| Problem | Impact |
|---------|--------|
| **Wall of markdown** | 3 worksheets dumped sequentially (~200 lines each) with no visual separation. A consultant scrolls endlessly instead of working on one card at a time. |
| **No state separation** | Pre-filled "before" fields (assumption, design, criteria) are mixed with empty "after" fields ("To be filled after experiment"). There is no visual or functional distinction between what the AI prepared and what the consultant needs to complete. |
| **Not interactive** | The `ReactMarkdown` rendering is read-only. To record experiment results, the consultant must click "Edit" and modify raw markdown — finding the right line in a 600-line blob. No one will do this. |
| **Generic boilerplate** | Phrases like "The lowest-cost environment that still produces credible evidence" and "The stakeholders closest to the risk described in the assumption" are tautological filler. They occupy space without adding decision value. |
| **No progression awareness** | There is no way to see at a glance which experiments are Planned, Running, or Completed, nor how they relate to each other in the evidence sequence. |

## 2. Design Reference: The Strategyzer Test Card

The Strategyzer Test Card (David Bland & Alex Osterwalder, *Testing Business Ideas*) is a deliberately compact, two-sided visual artifact:

**Front — BEFORE the experiment:**
1. **Assumption:** "I believe that..."
2. **Test:** "To verify that, I will..." (experiment type + how)
3. **Metric:** "And measure..." (primary metric + threshold)
4. **Criteria:** "I am right if..." (success) / "I am wrong if..." (failure)

**Back — AFTER the experiment:**
5. **Observation:** "We observed..." (what customers said and did)
6. **Learnings:** "From that we learned that..." (insight synthesis)
7. **Decision:** "Therefore, we will..." (escalate / refine / stop + next experiment)

The power of this design is disciplined compression. Every field has exactly one job. The front is the hypothesis; the back is the evidence. A consultant can read and act on one card in under 2 minutes.

## 3. Proposed Design: Interactive Experiment Card Deck

Replace the three-tab markdown dump with a **card-deck UI** where each experiment is a self-contained, interactive Strategyzer-style test card.

### 3.1 Card Layout (per experiment)

Each card has two visual halves, inspired by the Strategyzer front/back but rendered as a single expandable card with clearly differentiated zones:

**Zone A — Hypothesis (pre-filled by AI, read-only by default):**

| Field | Source | Editable? |
|-------|--------|-----------|
| Assumption | Verbatim from Step 7 risk map | Yes (via edit mode) |
| Category badge | D / V / F with color coding | No |
| Evidence strength target | Weak / Medium / Strong | No |
| Experiment card name | From 44-card library | Yes (dropdown from library) |
| What it tests | From card library | No |
| Test audience | Inferred from assumption context | Yes |
| Sample size | Default from card type | Yes |
| Primary metric | From category-based defaults | Yes |
| Success looks like | Pre-filled threshold | Yes |
| Failure looks like | Pre-filled threshold | Yes |

**Zone B — Evidence (empty, editable, the consultant's working space):**

| Field | Purpose |
|-------|---------|
| Status | Dropdown: Planned → Running → Evidence Captured → Decision Made |
| Date started / Date completed | Date pickers |
| Owner | Text field |
| What customers said | Free text |
| What customers did | Free text |
| What surprised us | Free text |
| Confidence change | Selector: Increased / Decreased / Unchanged |
| Decision | Selector: Continue to next test / Refine and rerun / Stop |
| Next experiment | Auto-suggested from sequencing, editable |
| Notes | Free text for anything not covered above |

### 3.2 Card Deck Navigation

Instead of scrolling through markdown, the UI presents:

1. **Card strip / horizontal scroll** — Each experiment is a card shown side-by-side. One card is expanded (active), others are collapsed to a summary bar showing: assumption (truncated), category badge, status pill.
2. **Sequencing connector** — A thin visual line between cards shows the evidence progression path (weak → medium → strong). This comes from `usually_runs_next` in the card library.
3. **Status filtering** — A small filter row at the top: "All | Planned | Running | Completed" lets the consultant focus on active work.

### 3.3 How This Maps to the Backend

The backend currently produces three flat markdown strings:
- `experiment_selections` — selection rationale per assumption
- `experiment_plans` — Precoil brief + implementation plan + evidence sequence
- `experiment_worksheets` — the worksheet per experiment

**Proposed backend change:** Instead of (or in addition to) flat markdown, produce a **structured JSON array** of experiment card objects:

```python
# New state field: experiment_cards (list of dicts)
{
    "experiment_cards": [
        {
            "id": "exp-001",
            "assumption": "I believe HPE customers will trust automated tools...",
            "category": "Desirability",
            "evidence_strength": "Weak",
            "card_name": "Problem Interviews",
            "what_it_tests": "Whether the problem is real, frequent, painful",
            "best_used_when": "You need to confirm whether a problem is real...",
            "test_audience": "Operational buyers, onboarding stakeholders...",
            "sample_size": 8,
            "timebox": "1 week",
            "primary_metric": "Qualified customer signals...",
            "secondary_metrics": "Response quality, follow-up interest...",
            "success_looks_like": "At least 6 of 8 participants describe...",
            "failure_looks_like": "Fewer than 3 participants recognize...",
            "ambiguous_looks_like": "Mixed signals across segments...",
            "sequencing": {
                "usually_runs_after": ["Desk Research", "Search Trends"],
                "next_if_positive": "Landing Page",
                "next_if_mixed": "Landing Page"
            },
            "selection_rationale": "This is the cheapest credible test...",
            # --- Evidence fields (empty, filled by consultant) ---
            "status": "planned",
            "owner": null,
            "date_started": null,
            "date_completed": null,
            "evidence": {
                "what_customers_said": null,
                "what_customers_did": null,
                "what_surprised_us": null,
                "confidence_change": null,
                "decision": null,
                "next_experiment": null,
                "notes": null
            }
        },
        # ... more cards
    ]
}
```

This structured output enables the frontend to render interactive cards without parsing markdown.

### 3.4 Preserving the Existing Output

The markdown rendering (Selections, Plans, Worksheets tabs) stays as a **"Full Report"** export tab for consultants who want the narrative form. The card deck becomes the **primary interaction view**. This avoids breaking existing behavior.

## 4. Implementation Plan

### Phase 1: Backend — Structured Card Output
**Files:** `backend/app/nodes/step8_pdsa.py`

| Task | Description |
|------|-------------|
| 1.1 | Add a `_build_card_objects()` function that produces a list of experiment card dicts (structured data, not markdown) from the same `top_assumptions` and `cards` data |
| 1.2 | Add `experiment_cards` to the `run_step()` return state alongside the existing markdown fields |
| 1.3 | Register `experiment_cards` in the state schema and DB step_outputs model |
| 1.4 | Ensure the existing `_build_outputs()` path is unchanged — backward compatibility |

### Phase 2: Backend — Evidence Persistence API
**Files:** `backend/app/main.py`

| Task | Description |
|------|-------------|
| 2.1 | Add `PATCH /runs/{session_id}/experiment-cards/{card_id}` endpoint that accepts partial updates to the evidence fields of a single experiment card |
| 2.2 | Validate that only Zone B fields (evidence, status, owner, dates) are updatable via PATCH; Zone A fields require a full step restart |
| 2.3 | Persist updated cards back to `step_outputs` for the session |

### Phase 3: Frontend — Experiment Card Component
**Files:** New component `ExperimentCard.jsx`

| Task | Description |
|------|-------------|
| 3.1 | Create `ExperimentCard` component with Zone A (hypothesis, read-only) and Zone B (evidence, editable form fields) |
| 3.2 | Zone A renders: assumption text, category badge (colored D/V/F), evidence strength bar, experiment card name, metrics, success/failure criteria |
| 3.3 | Zone B renders: status dropdown, date pickers, owner field, 4 evidence text areas, confidence selector, decision selector, next-experiment suggestion |
| 3.4 | Use Grommet `Card`, `CardBody`, `FormField`, `Select`, `TextArea`, `DateInput`, `Box` with `background` color differentiation between Zone A and Zone B |

### Phase 4: Frontend — Card Deck View
**Files:** New component `ExperimentCardDeck.jsx`, modified `Step8ExperimentPlan.jsx`

| Task | Description |
|------|-------------|
| 4.1 | Create `ExperimentCardDeck` component that renders a horizontal card strip with expand/collapse behavior |
| 4.2 | Add a status filter bar (All / Planned / Running / Completed) |
| 4.3 | Add a sequencing connector line between cards showing the evidence progression |
| 4.4 | Add a "Save Evidence" button per card that calls the PATCH endpoint |
| 4.5 | Add the card deck as a new primary tab in `Step8ExperimentPlan`, keeping existing Selections/Plans/Worksheets tabs as "Full Report" |

### Phase 5: Frontend — Status Tracking and Sequencing Visualization
**Files:** `ExperimentCardDeck.jsx`, potentially `StepSidebar.jsx`

| Task | Description |
|------|-------------|
| 5.1 | Render a mini progress indicator showing: "2 of 3 experiments completed" |
| 5.2 | When a card's status changes to "Decision Made" and the decision is "Continue to next test," auto-highlight the sequenced next card |
| 5.3 | Add a Step 8 badge in the sidebar showing experiment progress (e.g., "2/3") |

### Phase 6: Export
**Files:** `ExperimentCardDeck.jsx` or `StepToolbar.jsx`

| Task | Description |
|------|-------------|
| 6.1 | Add "Export as PDF" that renders the cards in a print-friendly Strategyzer test card layout (one card per page, front/back) |
| 6.2 | The existing YAML download already works for the markdown fields; extend it to include the structured `experiment_cards` data |

## 5. Test Plan

| Layer | What to test |
|-------|-------------|
| **Backend unit** | `_build_card_objects()` produces correct structured output for 1, 2, and 3 assumptions; card fields match library data |
| **Backend unit** | PATCH endpoint validates: only Zone B fields update; unknown card IDs return 404; invalid status values rejected |
| **Backend integration** | Full Step 8 run produces both `experiment_cards` (structured) and existing markdown fields (backward compat) |
| **Frontend unit** | `ExperimentCard` renders Zone A as read-only, Zone B as editable form fields |
| **Frontend unit** | Status dropdown transitions: Planned → Running → Evidence Captured → Decision Made (no backward jumps unless Reset) |
| **Frontend integration** | PATCH save persists evidence; page reload restores the saved evidence |
| **BDD** | Existing Step 8 feature file behavior must not change — the markdown output paths remain identical |

## 6. Sequencing and Priority

| Priority | Phase | Rationale |
|----------|-------|-----------|
| **P0** | Phase 1 + Phase 3 | Structured backend data + card component = the minimum to demonstrate value. A consultant can see cards instead of markdown. |
| **P1** | Phase 2 + Phase 4 | Evidence persistence + deck navigation = the minimum to make it a working tool. A consultant can record experiment results. |
| **P2** | Phase 5 | Status tracking = quality-of-life improvement for multi-experiment management. |
| **P3** | Phase 6 | Export = nice-to-have for stakeholder reporting. |

## 7. What This Does Not Change

- The 44-card experiment library and Precoil EMT pattern library remain untouched.
- The LLM is not involved in Step 8 — it remains a deterministic, code-driven step. The card output is generated from the same `_extract_top_assumptions` + `_get_category_path` logic that exists today.
- The existing markdown output stays available as a "Full Report" tab for backward compatibility and for users who prefer the narrative form.
- The feature file behavioral contract for Step 8 is unaffected — the same state fields are produced.
