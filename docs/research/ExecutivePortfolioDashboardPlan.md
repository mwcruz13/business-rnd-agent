# Plan: Executive Portfolio Dashboard ("Innovation Hedge Fund")

Build a new **Portfolio Dashboard** page that visualizes CXIF workflow sessions on a 2×2 quadrant scatter chart (X = Innovation Risk, Y = Expected Return) — lower-left = **Explore/Invent**, upper-right = **Exploit/Shift**. Clicking a project opens a detail panel with hypothesis log, experiment log, and metrics. Inspired by "The Invincible Company" portfolio map.

---

## Phase 1 — Data Layer (Backend)

**Step 1: Add portfolio metadata to WorkflowRun**
- `backend/app/db/models.py` — add `portfolio_json` column (JSON, nullable)
- Stores user-editable fields: `expected_revenue`, `testing_cost`, `risk_score_override`, `return_score_override`, `initiative_name`, `notes`
- No migration tool needed — `Base.metadata.create_all()` handles it (existing pattern)

**Step 2: Create portfolio computation service**
- **New file**: `backend/app/services/portfolio_service.py`
- `compute_risk_score(state_json) → float (0–100)`:
  - From `step7_structured` DVF assumptions: weight quadrants — "Test first"=3, "Monitor"=2, "Deprioritize"=1, "Safe zone"=0
  - Evidence penalty: "None"=+2, "Weak"=+1, "Medium"=0 per assumption
  - Pattern direction: "invent" → +15 base risk, "shift" → +0
  - Normalize to 0–100. If step 7 not reached → estimate from workflow progress
- `compute_return_score(state_json) → float (0–100)`:
  - From `vp_rankings`: map High=3, Medium=2, Low=1 across coverage + differentiation + evidence dimensions
  - Normalize top-recommended VP score. If VP scoring not reached → 50 (neutral)
  - Can be overridden by `expected_revenue` in `portfolio_json`
- `get_portfolio_entries(db_session)` — aggregates all sessions with computed scores + overrides

**Step 3: Add portfolio API endpoints**
- **New file**: `backend/app/routes/portfolio.py`
- `GET /portfolio` — all entries with computed risk/return scores, quadrant position, metadata
- `PATCH /runs/{session_id}/portfolio` — update portfolio_json (revenue, cost, notes, overrides)
- `GET /portfolio/{session_id}/detail` — deep detail: DVF assumptions, experiment cards, VP rankings

---

## Phase 2 — Chart Library

**Step 4: Install recharts** *(parallel with Steps 1–3)*
- Add `recharts` to `frontend-react/package.json` — lightweight (~200KB), best React scatter chart support, custom dot rendering, responsive containers

---

## Phase 3 — Dashboard Page

**Step 5: Create PortfolioDashboardPage** *(depends on Steps 3 & 4)*
- **New file**: `frontend-react/src/pages/PortfolioDashboardPage.jsx`
- HPE Design System: `Page kind="full"` → `PageHeader` (title "Business Model Portfolio", Home breadcrumb) → `PageContent`
- **Quadrant Chart** (main area):
  - `ScatterChart` with `ReferenceLine` at x=50, y=50 creating 4 quadrants
  - X-axis: "Innovation Risk" (0→100), Y-axis: "Expected Return" (0→100)
  - Explore watermark lower-left, Exploit watermark upper-right
  - Custom dot renderer: red marker + project name + "$X million" + "$X / N weeks"
  - Click → selects project → opens detail panel
- **Legend**: color-coded markers + field labels (matching the attached image)
- **Summary bar**: total initiatives, Explore vs Exploit count, total investment

**Step 6: Create ProjectDetailPanel** *(depends on Step 5)*
- **New file**: `frontend-react/src/components/ProjectDetailPanel.jsx`
- Grommet `Layer` side-drawer (right-anchored, same pattern as SignalBrowserPage filters)
- **Tabs**: Hypothesis Log (DVF assumptions table), Experiment Log (cards table), Learning Log (step timeline), Actions (edit metadata form)
- Inline editing of `expected_revenue`, `testing_cost`, `notes` → PATCH endpoint

**Step 7: Add route and navigation** *(depends on Step 5)*
- `frontend-react/src/App.jsx` — add `/portfolio` route + header nav link
- `frontend-react/src/pages/HomePage.jsx` — add Portfolio Dashboard navigation card

---

## Phase 4 — Verification

**Step 8: Backend tests** *(parallel with Steps 5–7)*
- **New file**: `backend/tests/test_portfolio.py`
- Test `compute_risk_score()` / `compute_return_score()` with known data
- Test `GET /portfolio` and `PATCH /runs/{session_id}/portfolio`

**Step 9: Manual verification**
- Visit `http://localhost:8501/portfolio`
- Verify 69 production sessions appear as positioned dots
- Click project → detail panel with correct DVF assumptions and experiment data
- Edit expected_revenue → verify dot repositions on Y-axis

---

## Relevant Files

| Action | File | What |
|--------|------|------|
| Modify | `backend/app/db/models.py` | Add `portfolio_json` column |
| Modify | `backend/app/main.py` | Register portfolio router |
| Modify | `frontend-react/src/App.jsx` | Add /portfolio route + nav |
| Modify | `frontend-react/src/pages/HomePage.jsx` | Add Portfolio nav card |
| Modify | `frontend-react/package.json` | Add recharts |
| Create | `backend/app/services/portfolio_service.py` | Risk/return computation |
| Create | `backend/app/routes/portfolio.py` | Portfolio API endpoints |
| Create | `frontend-react/src/pages/PortfolioDashboardPage.jsx` | Dashboard page |
| Create | `frontend-react/src/components/ProjectDetailPanel.jsx` | Detail panel |
| Create | `backend/tests/test_portfolio.py` | Backend tests |
| Reference | `frontend-react/src/pages/SignalBrowserPage.jsx` | HPE page pattern, Layer side-drawer |
| Reference | `backend/app/nodes/step7_risk_llm.py` | DVFAssumption models |
| Reference | `backend/app/nodes/step5b_scoring_llm.py` | VPScore models |

---

## Decisions

- **Risk score**: Computed from DVF assumption quadrants + evidence strength + pattern direction. Manual override via `portfolio_json`
- **Return score**: Proxy from VP scoring dimensions when no financial data entered. Overridden by user `expected_revenue`
- **Explore/Exploit**: `pattern_direction = "invent"` → Explore, `"shift"` → Exploit. Position by scores, not forced into quadrant
- **Storage**: JSON column on existing WorkflowRun — no new table, no migration
- **Scope excludes**: Historical trend tracking, portfolio comparison over time, financial modeling, PPTX export

---

## Further Considerations

1. **Sessions without risk data** — Most of the 69 sessions may not have reached step 7. Show them at (50, 50) with a hollow/dashed dot indicator? Or cluster them in a "needs data" zone?

2. **Dot color coding** — Color by `pattern_direction` (invent=green, shift=blue), by workflow stage, or by status (active/paused/completed)?

3. **Financial data entry** — The image shows specific dollar amounts. Start with inline editing on the detail panel, or add a bulk-edit table view?
