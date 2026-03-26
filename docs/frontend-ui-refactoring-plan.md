# Frontend UI Refactoring Plan

## Goals

1. **Tab-based card layout** — Each workflow step page gets a Card with Tabs; every logical section becomes its own Tab panel, replacing the current long-scroll single-page approach.
2. **YAML download / upload per step** — A toolbar above each step card offers "Download YAML" and "Upload YAML" buttons so consultants can export/import step content without using the edit mode text fields.
3. **Cognitive-friendly UI** — Progressive disclosure (one section visible at a time via tabs), consistent visual hierarchy, readable typography, and reduced information overload.

---

## Architecture Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Tab component | Grommet `<Tabs>` / `<Tab>` | Already in the Grommet design system; no extra dependency |
| YAML library | `js-yaml` (npm) | Lightweight, well-maintained, covers dump/load |
| Shared toolbar | New `StepToolbar.jsx` component | Reusable Download/Upload bar for all 8 steps |
| YAML field mapping | New `yamlStepFields.js` config | Centralizes per-step field names, labels, and types in one place |
| File handling | Browser `Blob` + `<a>` download / Grommet `FileInput` upload | No backend changes required; purely client-side |

---

## Per-Step Section → Tab Mapping

### Step 1 — Signal Scan (`Step1SignalScan.jsx`)

State fields: `agent_recommendation`, `signals`, `interpreted_signals`, `priority_matrix`, `coverage_gaps`

| Tab | Content | Editable? |
|---|---|---|
| **Recommendation** | `agent_recommendation` — Markdown block | Yes (TextArea) |
| **Signals** | `signals` — DataTable (ID, Signal, Zone, Source) | Yes (DataTable) |
| **Interpreted** | `interpreted_signals` — DataTable (Signal, Zone, Classification, Confidence) | Yes (DataTable) |
| **Priority Matrix** | `priority_matrix` — DataTable (Signal, Impact, Speed, Score, Tier) | Yes (DataTable) |
| **Coverage Gaps** | `coverage_gaps` — JSON pre block | Read-only |

### Step 2 — Pattern Direction (`Step2PatternDirection.jsx`)

State fields: `pattern_direction`, `selected_patterns`, `pattern_rationale`

| Tab | Content | Editable? |
|---|---|---|
| **Direction** | `pattern_direction` — invent/shift badge + Select in edit mode | Yes |
| **Selected Patterns** | `selected_patterns` — Tag list / CheckBox list in edit mode | Yes |
| **Rationale** | `pattern_rationale` — Markdown block / TextArea in edit mode | Yes |

### Step 3 — Customer Profile (`Step3CustomerProfile.jsx`)

State fields: `customer_profile`, `empathy_gap_questions`, `supplemental_voc`

| Tab | Content | Editable? |
|---|---|---|
| **Profile** | `customer_profile` — Markdown | Yes |
| **Empathy Questions** | `empathy_gap_questions` — Markdown | Read-only |
| **Supplemental VoC** | `supplemental_voc` — Markdown / TextArea | Yes |

### Step 4 — Value Drivers (`Step4ValueDrivers.jsx`)

State fields: `value_driver_tree`, `actionable_insights`

| Tab | Content | Editable? |
|---|---|---|
| **Value Driver Tree** | `value_driver_tree` — Markdown | Yes |
| **Actionable Insights** | `actionable_insights` — Markdown | Yes |

### Step 5 — Value Proposition (`Step5ValueProposition.jsx`)

State fields: `value_proposition_canvas`, `fit_assessment`

| Tab | Content | Editable? |
|---|---|---|
| **VP Canvas** | `value_proposition_canvas` — Markdown | Yes |
| **Fit Assessment** | `fit_assessment` — Markdown | Yes |

### Step 6 — Business Model (`Step6BusinessModel.jsx`)

State fields: `business_model_canvas`

| Tab | Content | Editable? |
|---|---|---|
| **Business Model Canvas** | `business_model_canvas` — Markdown | Yes |

> Single-section step. Tabs header still renders for consistency but only one tab is shown.

### Step 7 — Risk Map (`Step7RiskMap.jsx`)

State fields: `assumptions`

| Tab | Content | Editable? |
|---|---|---|
| **Assumptions & Risk Map** | `assumptions` — Markdown | Yes |

> Single-section step. Same treatment as Step 6.

### Step 8 — Experiment Plan (`Step8ExperimentPlan.jsx`)

State fields: `experiment_selections`, `experiment_plans`, `experiment_worksheets`

| Tab | Content | Editable? |
|---|---|---|
| **Selections** | `experiment_selections` — Markdown | Yes |
| **Plans** | `experiment_plans` — Markdown | Yes |
| **Worksheets** | `experiment_worksheets` — Markdown | Yes |

---

## New Files

### 1. `frontend-react/src/utils/yamlStepFields.js`

Centralised per-step YAML field configuration. Each entry maps a step index (0–7) to an array of field descriptors used for download/upload serialization.

```js
// Example structure:
export const STEP_YAML_FIELDS = [
  // Step 0 (Step 1 — Signal Scan)
  [
    { key: 'agent_recommendation', label: 'Agent Recommendation', type: 'text' },
    { key: 'signals', label: 'Signals', type: 'json' },
    { key: 'interpreted_signals', label: 'Interpreted Signals', type: 'json' },
    { key: 'priority_matrix', label: 'Priority Matrix', type: 'json' },
    { key: 'coverage_gaps', label: 'Coverage Gaps', type: 'json' },
  ],
  // Step 1 (Step 2 — Pattern Direction)
  [
    { key: 'pattern_direction', label: 'Pattern Direction', type: 'text' },
    { key: 'selected_patterns', label: 'Selected Patterns', type: 'json' },
    { key: 'pattern_rationale', label: 'Rationale', type: 'text' },
  ],
  // ... one entry per step
];
```

### 2. `frontend-react/src/components/StepToolbar.jsx`

Shared toolbar rendered above the tabs inside each step card. Provides:

- **Download YAML** button — serialises the current step's `runState` fields (via `yamlStepFields`) into a `.yaml` file and triggers a browser download.
- **Upload YAML** button — accepts a `.yaml` file via Grommet `FileInput`, parses it with `js-yaml`, and calls `onEditChange` to populate the edit state.
- Step title + optional status badge.

```
┌──────────────────────────────────────────────────────────┐
│  Step N: <title>                    [⬇ Download] [⬆ Upload] │
├──────────────────────────────────────────────────────────┤
│  [ Tab 1 ] [ Tab 2 ] [ Tab 3 ]                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │  (tab panel content)                                 ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

### 3. `frontend-react/src/components/StepCard.jsx`

Generic wrapper that combines:
- `StepToolbar` (title + download/upload)
- Grommet `<Card>` + `<Tabs>` shell
- Child tab panels injected via render-props or children

Each Step component will use `StepCard` instead of raw `<Box>` wrappers.

---

## Modified Files

| File | Changes |
|---|---|
| `package.json` | Add `js-yaml` dependency |
| `Step1SignalScan.jsx` | Wrap sections in `<StepCard>` + 5 `<Tab>` panels |
| `Step2PatternDirection.jsx` | Wrap in `<StepCard>` + 3 `<Tab>` panels |
| `Step3CustomerProfile.jsx` | Wrap in `<StepCard>` + 3 `<Tab>` panels |
| `Step4ValueDrivers.jsx` | Wrap in `<StepCard>` + 2 `<Tab>` panels |
| `Step5ValueProposition.jsx` | Wrap in `<StepCard>` + 2 `<Tab>` panels |
| `Step6BusinessModel.jsx` | Wrap in `<StepCard>` + 1 `<Tab>` panel |
| `Step7RiskMap.jsx` | Wrap in `<StepCard>` + 1 `<Tab>` panel |
| `Step8ExperimentPlan.jsx` | Wrap in `<StepCard>` + 3 `<Tab>` panels |
| `StepWizard.jsx` | Remove outer heading/session text (moved into `StepToolbar`) |

---

## Implementation Phases

### Phase A — Add `js-yaml` dependency

1. Add `js-yaml` to `frontend-react/package.json` dependencies.
2. Rebuild container (`docker compose up --build frontend-react`).

### Phase B — Create `yamlStepFields.js`

1. Create `frontend-react/src/utils/yamlStepFields.js` with all 8 step field definitions.
2. Export helper functions:
   - `stepFieldsToYaml(stepIndex, runState)` — returns YAML string.
   - `yamlToStepFields(stepIndex, yamlString)` — returns parsed object matching edit state shape.

### Phase C — Create `StepToolbar.jsx` and `StepCard.jsx`

1. `StepToolbar.jsx`:
   - Props: `stepIndex`, `stepLabel`, `runState`, `onImport(parsedFields)`
   - Download handler: calls `stepFieldsToYaml`, creates Blob, triggers `<a>` click download.
   - Upload handler: reads file via FileReader, calls `yamlToStepFields`, invokes `onImport`.
2. `StepCard.jsx`:
   - Props: `stepIndex`, `stepLabel`, `runState`, `onImport`, `children` (Tab panels)
   - Renders `<Card>` → `<StepToolbar>` → `<Tabs>{children}</Tabs>`

### Phase D — Refactor all 8 Step components

For each `StepN*.jsx`:

1. Replace outer `<Box gap="medium">` with `<StepCard stepIndex={N} ...>`.
2. Wrap each `<Section>` block in a `<Tab title="...">` element.
3. Both read-only and edit views use the same tab structure (edit mode swaps content inside each tab panel).
4. Remove the `Section` local component where it was only used as a visual grouper — the Tab title replaces it.

**Order**: Step 6 → Step 7 (simplest, 1 tab) → Step 4 → Step 5 (2 tabs) → Step 2 → Step 3 → Step 8 (3 tabs) → Step 1 (5 tabs, most complex).

### Phase E — Update `StepWizard.jsx`

1. Remove the step title heading and session ID text from the main content area (these move into `StepToolbar`).
2. Keep error/status notifications and checkpoint actions outside the card.

### Phase F — Cognitive UX Polish

1. **Typography**: Ensure tab titles use `size="small"` with `weight="bold"` for active tab — matches HPE design system defaults.
2. **Spacing**: Set consistent `pad="medium"` inside tab panels. Use `gap="small"` between content blocks.
3. **Progressive disclosure**: Tabs naturally show one section at a time — no additional work needed.
4. **Empty states**: Each tab panel shows a clear "No data yet" message when the field is empty.
5. **Visual hierarchy**: Card elevation + tab underline indicator provides clear focus.
6. **Responsive**: On small screens, Grommet `<Tabs>` can overflow horizontally with scroll — no special handling needed for the number of tabs we have (max 5).

### Phase G — Build verification

1. Run `npm run build` inside the container.
2. Manual smoke test: start a workflow, proceed through checkpoints, verify tabs render correctly.
3. Test YAML download/upload round-trip for each step.

---

## Cognitive UX Principles Applied

| Principle | Implementation |
|---|---|
| **Miller's Law** (7 ± 2 chunks) | Max 5 tabs per step; sidebar already limits to 8 steps |
| **Progressive Disclosure** | Tabs show one section at a time instead of scrolling through all |
| **Recognition over Recall** | Tab titles name exact content; Download/Upload buttons are always visible |
| **Consistency** | Every step has the same Card + Toolbar + Tabs layout |
| **Aesthetic-Usability Effect** | Clean card with HPE theme elevation, whitespace, and type scale |
| **Hick's Law** (reduce choices) | Edit mode controls only appear at checkpoints; YAML upload only when relevant |
| **Feedback** | Active tab underline, status badges, loading spinners |

---

## Dependency Graph

```
Phase A (js-yaml)
    └─▶ Phase B (yamlStepFields.js)
            └─▶ Phase C (StepToolbar + StepCard)
                    └─▶ Phase D (refactor 8 Step components)
                            └─▶ Phase E (StepWizard cleanup)
                                    └─▶ Phase F (polish)
                                            └─▶ Phase G (verify)
```

All phases are sequential — each depends on the previous.

---

## Risk & Mitigation

| Risk | Mitigation |
|---|---|
| Grommet `<Tabs>` may not support controlled active index cleanly | Grommet Tabs support `activeIndex` + `onActive` — confirmed in docs |
| YAML parsing edge cases (arrays, nested objects) | `js-yaml` handles all JSON-compatible structures; we only serialize known field shapes |
| Edit mode + tab switching may lose unsaved edits | Edit state is lifted to `StepWizard` level — tab switches don't unmount the form; state persists across tabs |
| DataTable columns inside tabs may need width adjustment | Use `overflow="auto"` on tab panel Box — already present in current code |
| Container rebuild needed for new npm dependency | Phase A explicitly calls out rebuild step |
