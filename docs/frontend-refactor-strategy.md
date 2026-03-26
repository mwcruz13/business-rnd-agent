# Frontend Refactor Strategy & Implementation Plan

## Problem Statement

The current BMI Consultant App frontend is a single Streamlit page that shows all workflow state in one view. It has three critical UX problems:

1. **No step-by-step progression** — The consultant sees the entire workflow state at once (VoC input, signals, patterns, canvases, experiments), which is overwhelming and provides no sense of progress through the 8-step BMI methodology.

2. **JSON-only editing** — When a checkpoint pauses the workflow, the consultant edits a raw JSON text area. This is developer-oriented, not consultant-friendly. A consultant should see labeled fields (e.g., "Pattern Direction", "Selected Patterns") with appropriate input controls (dropdowns, text areas, checklists).

3. **Rigid entry points** — The workflow can only start from Step 1 with VoC data. A consultant cannot pick up from Step 3 (customer profiling) with pre-existing signals and patterns, or re-enter at Step 6 (BMC design) to iterate on business model design.

4. **Limited checkpoints** — Only 3 of 8 steps have human review checkpoints (after Steps 1, 2, 7). The consultant has no opportunity to review or edit outputs from Steps 3–6 or Step 8.

## Requirements

From the user request, five capabilities are required:

| # | Requirement | Description |
|---|---|---|
| R1 | One page per step | Each of the 8 workflow steps gets its own dedicated page with step-specific content |
| R2 | Checkpoint at every step | After each step completes, the consultant can approve, edit, or cancel before advancing |
| R3 | Entry point at each step | The consultant can start the workflow at any step by providing the required inputs |
| R4 | User-friendly edit forms | Each step's checkpoint shows labeled form fields (not raw JSON), with multi-page pagination when forms are large |
| R5 | Inspired by reference template | Follow the React/Grommet/HPE Design System wizard pattern from `one-ai-graphrag/frontend` |

## Technology Decision: React + Grommet (Not Streamlit)

### Why Move Off Streamlit

The current Streamlit app cannot satisfy requirements R1, R3, and R4:

- **R1 (pages)**: Streamlit's multi-page mode creates separate files and sidebar navigation, but provides no wizard-style step progression, shared state management, or controlled page transitions.
- **R3 (entry points)**: Streamlit has no URL routing. Each step page would need duplicated session state initialization logic, and there is no clean way to deep-link into a specific step.
- **R4 (forms)**: Streamlit forms are limited — no dynamic field rendering, no pagination within a form, no conditional field visibility, no custom validation UX. Building the signal table editor, pattern selector, or BMC canvas editor in Streamlit would require extensive workarounds.

### Why React + Grommet

- The reference template (`one-ai-graphrag/frontend`) already implements a multi-step wizard pattern with pagination (the `DomainCreationWizard.jsx` with `StepDetails`, `StepUpload`, `StepRefine`, `StepReview`).
- Grommet + `grommet-theme-hpe` provides HPE-branded components out of the box: `TextInput`, `TextArea`, `Select`, `DataTable`, `CheckBox`, `Tabs`, `Tab`, `Meter`, `Button`.
- React Router enables URL-based navigation (`/steps/1`, `/steps/2`, ..., `/steps/8`).
- React state management (context + hooks) naturally handles the workflow state shared across step pages.
- Vite provides fast development builds with hot module replacement.
- The containerization pattern (Dockerfile with dev/prod stages, docker-compose volume mounts for hot reload) is already proven in the reference.

### What We Reuse From the Reference

| Asset | Source | What we take |
|---|---|---|
| Dockerfile | `one-ai-graphrag/frontend/Dockerfile` | Multi-stage build (dev with Vite, prod with nginx) |
| Vite config | `vite.config.js` | Base configuration, proxy setup for backend API |
| HPE theme | `grommet-theme-hpe` | Theme provider pattern from `App.jsx` |
| Wizard pattern | `DomainCreationWizard.jsx` | Step header, progress indicator, prev/next/submit footer, step content dispatch |
| Form components | `StepDetails.jsx`, `StepRefine.jsx` | Labeled form fields, entity editors, inline validation, pagination controls |
| Error handling | `ErrorBoundary.jsx` | Error boundary wrapper |

### What We Do NOT Reuse

- Keycloak authentication (not needed for BMI app at this stage)
- GraphRAG-specific service layer
- react-router multi-route structure (we use a simpler wizard within a single route)
- @tanstack/react-query (overkill for our sequential workflow — simple fetch calls suffice)

## Architecture Overview

### Frontend Structure

```
frontend/
├── Dockerfile                    # Multi-stage: dev (Vite) + prod (nginx)
├── nginx.conf                    # Production reverse proxy config
├── package.json                  # React, Grommet, Vite, react-router-dom
├── vite.config.js                # Dev server config with backend proxy
├── index.html                    # SPA entry point
├── public/                       # Static assets
└── src/
    ├── main.jsx                  # React entry point
    ├── App.jsx                   # Grommet theme provider + router
    ├── index.css                 # Global styles
    ├── api/
    │   └── workflowApi.js        # Backend API client (fetch-based)
    ├── context/
    │   └── WorkflowContext.jsx   # Shared workflow state (React context)
    ├── components/
    │   ├── ErrorBoundary.jsx     # Error boundary
    │   ├── StepWizard.jsx        # Master wizard: header, progress, footer, step dispatch
    │   ├── StepSidebar.jsx       # Left sidebar with step list + progress indicators
    │   ├── CheckpointActions.jsx # Approve / Edit / Cancel action bar
    │   └── PaginationControls.jsx # Multi-page form pagination
    ├── pages/
    │   ├── HomePage.jsx          # Landing: start new workflow or resume existing
    │   └── WorkflowPage.jsx      # Main wizard page (wraps StepWizard)
    └── steps/
        ├── Step1SignalScan.jsx    # Signal scan output review + form editor
        ├── Step2PatternSelect.jsx # Pattern direction selector + pattern checklist
        ├── Step3CustomerProfile.jsx # Empathy profile review + empathy gate questions
        ├── Step4ValueDrivers.jsx  # Value driver tree + actionable insights editor
        ├── Step5ValueProp.jsx     # Value proposition canvas editor
        ├── Step6BusinessModel.jsx # BMC + fit assessment editor
        ├── Step7RiskMap.jsx       # Assumptions and DVF tensions editor
        └── Step8Experiments.jsx   # Experiment selections + PDSA plan review
```

### State Management

The `WorkflowContext` holds the full `BMIWorkflowState` dict returned by the backend. Each step component reads the fields it needs and provides edit forms that build the `edit_state` payload for the resume API call.

```
WorkflowContext = {
  sessionId: string | null,
  runState: BMIWorkflowState | null,
  currentStep: number (0-7),
  isLoading: boolean,
  error: string | null,
  
  // Actions
  startWorkflow(vocData, inputFormat, llmBackend),
  resumeWorkflow(decision, editState?),
  loadSession(sessionId),
  goToStep(stepIndex),          // For entry-point navigation
  startFromStep(stepIndex, inputState),  // Start pipeline mid-stream
}
```

### How Each Requirement Is Satisfied

#### R1: One Page Per Step

The `StepWizard` component maintains an `activeStep` index (0–7). Each step has a dedicated component in `steps/`. The wizard renders only the active step's component, with a progress sidebar showing all 8 steps and their completion status.

Step components are responsible for:
- Rendering the step's agent output as readable content (markdown, tables, cards)
- Rendering the edit form when the checkpoint is active
- Providing validation logic for the form

#### R2: Checkpoint at Every Step

**Backend change required**: Currently only 3 checkpoints exist (after Steps 1, 2, 7). The backend `CHECKPOINTS_BY_STEP` in `checkpoints.py` must be extended to define a checkpoint after every step:

| Checkpoint | After Step | Required State Fields |
|---|---|---|
| `checkpoint_1` | step1_signal | (none — signals are always produced) |
| `checkpoint_1_5` | step2_pattern | `pattern_direction` |
| `checkpoint_3` | step3_profile | `customer_profile` |
| `checkpoint_4` | step4_vpm | `value_driver_tree`, `actionable_insights` |
| `checkpoint_5` | step5_define | `value_proposition_canvas` |
| `checkpoint_6` | step6_design | `business_model_canvas`, `fit_assessment` |
| `checkpoint_2` | step7_risk | `assumptions` |
| `checkpoint_8` | step8_pdsa | `experiment_selections`, `experiment_plans` |

The `cancel` action will be a new decision type. When the consultant clicks Cancel, the frontend discards the current run state and returns to the home page. The backend run remains in `paused` status (recoverable via session ID).

#### R3: Entry Point at Each Step

The `HomePage` offers two modes:
1. **Start from Step 1** — Upload VoC data, run the full pipeline
2. **Start from Step N** — Select a step, fill in the required upstream state fields, then the backend starts execution from that step index

**Backend change required**: A new API endpoint `POST /runs/start-from-step` that accepts:
```json
{
  "step_index": 2,
  "initial_state": {
    "voc_data": "...",
    "signals": [...],
    "interpreted_signals": [...],
    "pattern_direction": "invent",
    "selected_patterns": ["Market Explorers"]
  }
}
```

This calls `_execute_from_index()` with the provided state and step index, inserting the run into the database and executing from that point.

Each step page shows a "Required Inputs" section when accessed as an entry point — pre-filled forms for upstream outputs that the consultant must provide.

#### R4: User-Friendly Edit Forms

Each step's edit form replaces the raw JSON text area with structured input controls.

**Step 1 — Signal Scan Review**:
- Signals table (DataTable) with columns: signal_id, signal, zone (Select from 7 zones), source_type
- Interpreted signals table: signal, zone, classification (Select from 3 types), confidence
- Priority matrix table: signal, impact (1-3 number input), speed (1-3 number input), auto-computed score + tier
- Agent recommendation (TextArea, editable)
- Coverage gaps shown as read-only info cards
- **Pagination**: If > 5 signals, paginate the signal tables (4 per page like the reference)

**Step 2 — Pattern Direction**:
- Pattern direction (Select: "invent" / "shift")
- Selected patterns (CheckBox list from the Strategyzer library, filtered by direction)
- Pattern rationale (TextArea)
- Agent recommendation (read-only display)

**Step 3 — Customer Profile**:
- Customer profile rendered as styled markdown
- If empathy gate triggers: shows empathy trigger questions as labeled text areas for supplemental VoC
- Edit mode: Jobs (TextArea), Pains (TextArea), Gains (TextArea) — each is a markdown section

**Step 4 — Value Drivers**:
- Value driver tree rendered as markdown
- Actionable insights rendered as markdown
- Edit mode: both as TextArea (markdown content)

**Step 5 — Value Proposition Canvas**:
- VP Canvas rendered as a two-column layout: Customer Profile side / Value Map side
- Edit mode: TextArea for the full canvas markdown

**Step 6 — Business Model Canvas**:
- BMC rendered as a 9-block grid layout
- Fit assessment rendered as styled card
- Edit mode: TextArea for BMC markdown + TextArea for fit assessment

**Step 7 — Risk Map**:
- Assumptions rendered as a table (ID, assumption text, DVF category, evidence strength)
- Edit mode: Editable DataTable rows

**Step 8 — Experiment Plan**:
- Experiment selections rendered as cards
- PDSA experiment plans rendered as structured forms
- Experiment worksheets as read-only markdown
- Edit mode: Experiment selections as Select/CheckBox, plan details as TextArea

**Multi-page pagination**: When a step's form has > 4 editable items (e.g., Step 1 with 6+ signals, Step 7 with many assumptions), `PaginationControls` splits items across pages. The pattern from `StepRefine.jsx` is reused directly:

```jsx
const ITEMS_PER_PAGE = 4;
const totalPages = Math.ceil(items.length / ITEMS_PER_PAGE);
const pageItems = items.slice((page - 1) * ITEMS_PER_PAGE, page * ITEMS_PER_PAGE);
```

#### R5: Reference Template Patterns

The following patterns from the reference are adopted directly:

1. **Wizard layout** (`DomainCreationWizard.jsx`):
   - Fixed header with step number + back button
   - Scrollable content area
   - Fixed footer with Cancel / Next / Approve buttons
   - Progress indicator (Meter component)

2. **Form field layout** (`StepDetails.jsx`):
   - Label + required indicator + help text + input
   - Max-width constrained forms for readability
   - Info boxes for "next step" context

3. **Inline editors** (`StepRefine.jsx`):
   - DataTable for list items with Add/Edit/Delete actions
   - Pagination for large lists
   - Modal/inline edit forms for complex items

4. **Step `canProceed` validation** (`DomainCreationWizard.jsx`):
   - Each step defines its own validation function
   - Next button disabled until validation passes

## Backend Changes Required

### 1. Extend Checkpoints to All 8 Steps

Update `backend/app/checkpoints.py` `CHECKPOINTS_BY_STEP` to define a checkpoint after every step. Add `"cancel"` to `CheckpointDecision`.

### 2. Add Start-From-Step API Endpoint

Add `POST /runs/start-from-step` endpoint in `backend/app/main.py`:
- Accepts `step_index` (0-7) and `initial_state` dict
- Validates that all required upstream state fields are present
- Creates a `WorkflowRun` record
- Calls `_execute_from_index(session_id, initial_state, step_index, pause_at_checkpoints=True)`
- Returns the resulting state (paused at the checkpoint after the specified step)

### 3. Add Step-Level State Introspection Endpoint

Add `GET /runs/{session_id}/step/{step_index}` endpoint that returns the step output for a specific step (from `StepOutput` records). This allows the frontend to show historical step outputs even after the workflow has advanced.

### 4. CORS Configuration

Add CORS middleware to FastAPI for the React frontend dev server (port 8080):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Implementation Plan

### Phase 1: Project Scaffold + Container Setup

**Goal**: New React frontend boots in Docker alongside existing backend.

Tasks:
1. Create `frontend-react/` directory (keeping `frontend/` Streamlit for backward compatibility during migration)
2. Copy and adapt `Dockerfile` from reference (dev stage with Vite, no prod stage yet)
3. Add `bmi-frontend-react` service to `docker-compose.yaml` on port 8080
4. Initialize `package.json` with React 18, Grommet, grommet-theme-hpe, react-router-dom, Vite
5. Create `vite.config.js` with proxy to `http://bmi-backend:8000` for `/api/*`
6. Create `src/main.jsx`, `src/App.jsx` with Grommet theme provider
7. Create `src/api/workflowApi.js` — port the current `frontend/components/api.py` logic to JavaScript fetch
8. Add CORS middleware to backend `main.py`

**Definition of done**: `docker compose up` starts both frontends. React app loads at `localhost:8080` and can reach the backend health endpoint.

### Phase 2: Workflow Context + Home Page

**Goal**: Consultant can start a new workflow from the React UI.

Tasks:
1. Create `src/context/WorkflowContext.jsx` — React context provider with state management
2. Create `src/pages/HomePage.jsx` — VoC input (text paste or file upload), LLM backend selector, "Start Workflow" button
3. Wire `startWorkflow()` to call `POST /runs` via `workflowApi.js`
4. On success, navigate to `/workflow` and store session in context

**Definition of done**: Consultant can paste VoC text, click "Start Workflow", see the workflow start and receive the paused state.

### Phase 3: Step Wizard Shell

**Goal**: Master wizard layout with step sidebar and navigation.

Tasks:
1. Create `src/components/StepWizard.jsx` — wizard container with header, sidebar, content area, footer
2. Create `src/components/StepSidebar.jsx` — 8 steps listed vertically with status indicators (pending, active, completed, paused)
3. Create `src/components/CheckpointActions.jsx` — Approve / Edit / Cancel button row
4. Create `src/components/PaginationControls.jsx` — prev/page indicator/next - ported from reference `StepRefine.jsx`
5. Create `src/pages/WorkflowPage.jsx` — wraps StepWizard with WorkflowContext consumer
6. Add routes: `/` → HomePage, `/workflow` → WorkflowPage

**Definition of done**: Wizard loads after starting a workflow. Sidebar shows all 8 steps. Content area shows placeholder text for the active step.

### Phase 4: Step Components — Read-Only Views

**Goal**: Each step renders its agent output in a consultant-friendly way.

Tasks (can be parallelized across developers):
1. `Step1SignalScan.jsx` — Signals DataTable, interpreted signals DataTable, priority matrix DataTable, coverage gaps cards, recommendation markdown
2. `Step2PatternSelect.jsx` — Direction badge, selected patterns list, rationale text, recommendation markdown
3. `Step3CustomerProfile.jsx` — Customer profile markdown rendered with react-markdown, empathy gate question cards
4. `Step4ValueDrivers.jsx` — Value driver tree markdown, actionable insights markdown
5. `Step5ValueProp.jsx` — VP Canvas markdown (two-column layout)
6. `Step6BusinessModel.jsx` — BMC markdown (9-block grid), fit assessment card
7. `Step7RiskMap.jsx` — Assumptions markdown (structured table rendering)
8. `Step8Experiments.jsx` — Experiment selections cards, PDSA plans markdown, worksheets accordion

**Definition of done**: Running a full workflow shows each step's output rendered properly as the consultant navigates through the wizard.

### Phase 5: Step Components — Edit Forms

**Goal**: Each step's checkpoint provides form-based editing.

Tasks:
1. Step 1 signal editor: DataTable with inline editing for signal fields, zone/classification Select dropdowns
2. Step 2 pattern editor: Direction Select, pattern CheckBox list (filtered by direction from library), rationale TextArea
3. Step 3 profile editor: Jobs/Pains/Gains TextArea sections, supplemental VoC TextArea for empathy gate
4. Step 4 VDT editor: Value driver tree TextArea, actionable insights TextArea
5. Step 5 VPC editor: VP Canvas TextArea (future: structured fields per canvas block)
6. Step 6 BMC editor: BMC TextArea, fit assessment TextArea (future: 9-block structured form)
7. Step 7 assumptions editor: DataTable with inline editable rows (assumption text, DVF category Select, evidence TextArea)
8. Step 8 experiments editor: Experiment selection CheckBox list, plan details TextArea

Each edit form must:
- Pre-populate with current agent output
- Build the `edit_state` dict from form values
- Call `resumeWorkflow("edit", editState)` on submit
- Validate required fields before enabling submit

**Definition of done**: Consultant can edit any step's output via form fields instead of raw JSON.

### Phase 6: Backend — Checkpoints at Every Step

**Goal**: Every step pauses for human review.

Tasks:
1. Add checkpoint definitions for Steps 3, 4, 5, 6, 8 in `checkpoints.py`
2. Add `"cancel"` to `CheckpointDecision`
3. Update `validate_checkpoint_state()` with required fields per new checkpoint
4. Update existing BDD tests to account for new checkpoints (the full-workflow checkpoint test will now pause at every step, not just 3)
5. Verify all 8 steps pause and can be approved/edited/retried

**Definition of done**: Backend pauses at every step. Existing non-checkpoint tests still pass.

### Phase 7: Backend — Start-From-Step API

**Goal**: Consultant can enter the workflow at any step.

Tasks:
1. Add `POST /runs/start-from-step` endpoint
2. Define required upstream state fields per step (e.g., starting at Step 3 requires signals, patterns, direction, VoC data)
3. Validate the provided initial state
4. Wire to `_execute_from_index()`
5. Add `GET /runs/{session_id}/step/{step_index}` for step output retrieval

**Definition of done**: API tests verify starting from Steps 1, 3, 5, and 8 with appropriate pre-filled state.

### Phase 8: Entry Point UI

**Goal**: Homepage allows starting at any step.

Tasks:
1. Add step selector to `HomePage.jsx` (Select: "Start from Step 1", "Start from Step 3", etc.)
2. When a non-Step-1 entry point is selected, show the required upstream fields as a form
3. Pre-populate with example/template values where possible
4. Call `POST /runs/start-from-step` on submit

**Definition of done**: Consultant can start a workflow from Step 3 by providing signals and pattern direction.

### Phase 9: Polish + Decommission Streamlit

**Goal**: React frontend is the primary UI.

Tasks:
1. Loading states and error handling throughout the wizard
2. Responsive layout for different screen widths
3. Session persistence (localStorage for active session ID)
4. "Load Existing Session" on the home page
5. Update `docker-compose.yaml` to make React frontend the default on port 8501
6. Remove or archive the Streamlit `frontend/` directory

**Definition of done**: Full end-to-end workflow works through the React UI. Streamlit is retired.

## Step-to-Field Mapping Reference

For each step, the fields produced and the edit form controls:

| Step | Output Fields | Form Controls |
|---|---|---|
| 1. Signal Scan | `signals`, `interpreted_signals`, `priority_matrix`, `coverage_gaps`, `agent_recommendation` | DataTable (signals, interp, priority), Select (zone, classification), Number (impact, speed), TextArea (recommendation) |
| 2. Pattern Select | `pattern_direction`, `selected_patterns`, `pattern_rationale`, `agent_recommendation` | Select (direction), CheckBox list (patterns), TextArea (rationale) |
| 3. Customer Profile | `customer_profile`, `empathy_gap_questions`, `supplemental_voc` | Markdown display, TextArea (jobs/pains/gains), TextArea (supplemental VoC) |
| 4. Value Drivers | `value_driver_tree`, `actionable_insights` | TextArea × 2 |
| 5. Value Proposition | `value_proposition_canvas` | TextArea (future: structured canvas) |
| 6. Business Model | `business_model_canvas`, `fit_assessment` | TextArea × 2 (future: 9-block grid) |
| 7. Risk Map | `assumptions` | TextArea (future: DataTable with DVF columns) |
| 8. Experiments | `experiment_selections`, `experiment_plans`, `experiment_worksheets` | Read-only cards + TextArea for plan edits |

## Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| Backend checkpoint changes break existing tests | High | Phase 6 updates tests alongside checkpoint additions. Run full suite after each change. |
| Form complexity for Step 1 (many fields per signal) | Medium | Start with TextArea-based editing; upgrade to DataTable inline editing in Phase 5. |
| LLM output format varies, making form pre-population fragile | Medium | Parse markdown outputs defensively. Fall back to TextArea display if structured parsing fails. |
| Streamlit removal disrupts current users | Low | Keep Streamlit running on port 8501 until React is validated. Phase 9 is the last phase. |
| Reference template has Keycloak dependency | None | We do not reuse auth components. |

## Implementation Sequence Summary

```
Phase 1: Scaffold + Docker        → React app boots, reaches backend
Phase 2: Context + Home Page      → Can start workflow
Phase 3: Wizard Shell             → Step navigation works
Phase 4: Read-Only Step Views     → All 8 steps render output
Phase 5: Edit Forms               → All 8 steps have form editing
Phase 6: Backend Checkpoints      → Every step pauses
Phase 7: Backend Start-From-Step  → Entry at any step
Phase 8: Entry Point UI           → Homepage supports mid-stream entry
Phase 9: Polish + Retire Streamlit → React frontend is primary
```

## Working Rule

This document is the implementation baseline for the frontend refactor. If code changes diverge from this plan, update this document first or in the same change so the design intent stays explicit.
