# PPTX Generation Improvement Strategy

**Date:** 2026-04-17
**File:** `backend/cli/generate_report_pptx.py`
**Status:** Approved strategy, pending implementation

---

## Problem

The current PPTX generator truncates text mid-sentence using `_trunc(text, N)` with limits as low as 50–65 characters. This renders slide content **inaccurate and useless** — the audience sees incomplete thoughts with trailing "…" ellipses.

### Truncation Audit (HBM-SC Report, 17 slides)

| Slide | Topic | Truncated / Total | Severity |
|-------|-------|-------------------|----------|
| 4 | Customer Profile | 15 / 22 | Critical |
| 7 | Value Proposition Canvas | 12 / 28 | Critical |
| 8 | Business Model Canvas | 9 / 22 | Critical |
| 9 | Fit Assessment | 14 / 23 | Critical |
| 10 | Assumptions | 7 / 17 | High |
| 12–16 | Experiments / Worksheets | 3–5 each | Moderate |

Only **1 of 17 slides** currently has speaker notes. The rest have no fallback for the lost content.

---

## Solution: Three Coordinated Changes

### 1. Speaker Notes — Full Untruncated Content

Every `_slide_*` builder will compose a **complete, formatted text block** from the parsed data and write it via `_notes(slide, full_text)`.

Contents:
- All table rows with all columns, no character limits
- Section headings for readability in presenter Notes view
- Raw markdown prose where applicable (recommendations, ad-libs, etc.)

This is the **lossless backup** — presenters always have full detail available.

### 2. Slide Face — Concise Headlines (Min 16pt Font)

**Minimum font size on all slide text boxes: 16pt.** This ensures legibility in presentations, screen-shares, and printed handouts.

#### Impact on Text Density

With 16pt minimum (up from 8–10pt currently):
- Each card line fits ~6–8 words max (vs. ~12–15 previously)
- This strongly reinforces the headline-only approach

#### `_headline()` Helper

Replace `_trunc(long_text, N)` calls with a new `_headline(text, max_words=8)` that:
- Extracts the **first meaningful clause** (up to first comma, period, em-dash, or semicolon)
- Falls back to first N words if no natural break
- Never ends mid-word or with "…"
- Produces a coherent, self-contained thought

#### Examples

| Before (truncated) | After (headline) |
|---------------------|------------------|
| `AI projects delayed months or quarters because infrastructure doesn't…` | `AI projects delayed by delivery gaps` |
| `Unplanned cost increases (surcharges, price adjustments) erode AI inv…` | `Unplanned surcharges erode AI ROI` |
| `Systems engineered to require less of the components causing glo…` | `Fewer constrained components, faster delivery` |
| `GreenLake consumption model that absorbs commodity price volatil…` | `GreenLake absorbs commodity price volatility` |

#### Font Size Rules

| Element | Current | New Min |
|---------|---------|---------|
| Section label (e.g., "STEP 1 — SOC RADAR") | 10pt | 16pt |
| Section title | 26pt | 26pt (unchanged) |
| Card headline / primary text | 9–11pt | 16pt |
| Card secondary text (relevance, status) | 8–9pt | 16pt |
| Footer | 8pt | 10pt (exception: footer stays small) |
| Speaker notes | N/A | Not constrained (notes pane) |

Because cards now hold fewer words at 16pt, the layout needs adjustment:
- Tables with many columns → show 2–3 key columns only, rest in notes
- Cards with bullet lists → max 3–4 bullet headlines per card
- Long-form blocks (recommendations, ad-libs) → 2-sentence summary on slide, full text in notes

### 3. HPE Spot Illustrations — Visual Accents

**76 isometric illustrations** are available as ~1"×0.87" PNGs in `hpe_spot_illustrations.pptx` (slides 4–6).

#### Extraction Approach

1. **`_load_illustrations(pptx_path)`** — reads the illustrations deck, pairs each image blob with its text label using positional matching (sorted by top→left), returns `dict[str, bytes]`.
2. Called once at the top of `generate_report_pptx()`, cached for the generation run.
3. Returns `{}` if the illustrations file is missing (graceful fallback, no crash).

#### Placement

- **`_place_illustration(slide, illustrations, label, left=11.5, top=0.3, size=0.8)`**
- Places the image in the **top-right corner** of the slide as a branded visual accent
- Size: ~0.8"×0.8" (within HPE guidelines: min 0.7", max 1.25")
- Adjacent to the section label area

#### Slide → Illustration Mapping

| Slide | Primary Illustration | Secondary (optional) | Rationale |
|-------|---------------------|---------------------|-----------|
| Cover | AI | Enterprise | Core topics of the BMI workflow |
| Signals / SOC Radar | Observability | Data | Continuous monitoring + signal intelligence — SOC = Signals of Change, Radar = continuous weak-signal detection for disruption |
| Priority Matrix | Performance | Scalability | Prioritizing impact and speed of signals |
| Pattern Selection | Market Growth | Scalability | Innovation direction and growth patterns |
| Customer Profile | Partnership | Enterprise | Customer empathy and relationship focus |
| Value Driver Tree | Cost Savings | Time Savings | KPIs tied to cost and time outcomes |
| Actionable Insights | Data | Agentic AI | Data-driven insights and intelligent analysis |
| Value Proposition | Services | Cloud | Products, services, cloud delivery models |
| Business Model Canvas | Financial Services | Infrastructure | Revenue/cost structure + operational infrastructure |
| Fit Assessment | Orchestration | Data Governance | Orchestrating problem-solution-market fit + governance rigor |
| Assumptions / Risk Map | Observability | Security | Monitoring assumptions + risk mitigation |
| DVF Tensions | Networking | Orchestration | Interconnected tensions across dimensions |
| Experiments | Quick Setup | Machine Learning | Rapid experimentation + ML-driven testing |
| Experiment Worksheets | Machine Learning | Quick Setup | Per-worksheet: experiment design details |

#### Override Mechanism

A `SLIDE_ILLUSTRATIONS` dict constant at module level allows easy customization:

```python
SLIDE_ILLUSTRATIONS = {
    "cover": ["AI", "Enterprise"],
    "signals": ["Observability", "Data"],
    "priority": ["Performance", "Scalability"],
    # ...
}
```

---

## Files Changed

| File | Change |
|------|--------|
| `backend/cli/generate_report_pptx.py` | All changes (helpers, slide builders, constants) |

### What Won't Change

- Slide layout geometry, colors, card sizes (no visual regression beyond font scaling)
- The `_slide()`, `_rect()`, `_bar()`, `_tb()`, `_multi_tb()` low-level primitives
- The `generate_report_pptx()` orchestrator function signature and flow
- The markdown export (`export_report.py`)
- Feature files, tests, or behavioral contracts
- Frontend export buttons

---

## New Helpers

### `_headline(text, max_words=8)`

```python
def _headline(text: str, max_words: int = 8) -> str:
    """Extract a concise, coherent headline from the first clause of text."""
    # Try natural break points
    for sep in [". ", ", ", " — ", " - ", "; "]:
        idx = text.find(sep)
        if 10 < idx < 80:
            return text[:idx].strip()
    # Fallback: first N words
    words = text.split()[:max_words]
    return " ".join(words)
```

### `_load_illustrations(pptx_path)`

Reads slides 4–6, pairs images with text labels by position, returns `{label: image_blob}`.

### `_place_illustration(slide, illustrations, label, left, top, size)`

Adds a PNG image to the slide from the illustrations dict. No-op if label not found.

---

## Test Plan

1. **Regenerate** the HBM-SC report PPTX inside the container
2. **Audit truncation**: target **0 items** with "…" on the slide face
3. **Audit notes**: every slide (except cover) must have non-empty speaker notes
4. **Audit font sizes**: no text box below 16pt (except footer)
5. **Audit illustrations**: verify ≥1 illustration per slide
6. **Run existing tests**: `pytest` — confirm no regressions
7. **Visual check**: open in PowerPoint and verify legibility + illustration placement

---

## Design Rationale

- **Speaker notes as lossless backup**: Presenters need the full detail for Q&A and preparation. Notes are searchable and printable. This is non-negotiable.
- **Headlines over truncation**: A 6-word coherent summary conveys more than an 80-character sentence chopped at "…". The audience should understand the point at a glance.
- **16pt minimum**: HPE presentation guidelines recommend readable font sizes. 8–10pt is only legible if you zoom in. 16pt works at screen-share distance and on printed slides.
- **Illustrations as accent, not decoration**: One small icon per slide reinforces the topic visually without cluttering the layout. Placed in top-right to avoid interfering with card content.
- **Graceful fallback**: If the illustrations PPTX is missing, the generator still works — just without icons.
