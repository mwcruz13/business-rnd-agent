# SOC Radar Input Preprocessing — Strategy & Implementation Plan

**Date:** 2026-04-27  
**Release:** 2.3  
**Approach:** BDD-first — define feature file behavioral contract, then implement production code to make tests pass.  
**Baseline:** All existing Step 1a/1b tests passing; no changes to SOC Radar SKILL.md or step1a/step1b prompts.

---

## 1. Problem Statement

The SOC Radar pipeline (steps 1a + 1b) receives `voc_data` as a single unstructured string — no segmentation, no source typing, no cleaning. In practice, analysts paste multi-source material that combines:

| Source Type | Example Structure |
|---|---|
| **Customer VoC** | Numbered comments with product/theater tags, direct quotes |
| **Corporate Policy** | Prose, Q&A format, contractual language |
| **Technology Intelligence** | Technical specs, architecture diagrams, reference links |
| **Industry/Market Analysis** | Analyst forecasts, market data, scenario modeling |

This creates three problems:

1. **Attribution collapse** — `DetectedSignal.source_type` defaults to `"Internal VoC"` regardless of actual source. The LLM cannot reliably distinguish a customer complaint from an IDC forecast from a corporate policy change.
2. **Comment numbering mismatch** — `supporting_comments` expects integer indices, but raw text has inconsistent numbering (some sections numbered, some not, sub-numbering like 2.1/2.2, gaps).
3. **Signal dilution** — URL references `[site.com]`, formatting artifacts (`✅❌`, ASCII tables, `---`), boilerplate, and near-duplicate observations waste context window tokens without adding signal value.

---

## 2. Design Goals

- **Separation of concerns**: Preprocessing is a distinct responsibility from signal scanning. Step 1a's system prompt (~500+ lines including SKILL.md) should not be burdened with segmentation/cleaning instructions.
- **Preserve original input**: Store both `voc_data` (original) and `preprocessed_voc_data` (structured) in state. Original remains available for audit/traceability.
- **Enrich metadata for downstream steps**: Source type, products, theater, date references, **Jobs-to-Be-Done (JTBD)**, and **Business Unit (BU)** tags propagate through the pipeline, enabling richer signal attribution in steps 1a, 1b, and the portfolio dashboard.
- **Consistent observation numbering**: Every discrete observation gets a sequential integer index, providing reliable `supporting_comments` references for step1a.
- **Backward compatible**: If `preprocessed_voc_data` is absent (legacy runs, simple text inputs), step1a falls back to `voc_data` unchanged.

---

## 3. Architecture

### 3.1 Pipeline Position

```
Text Input → ingest → [NEW: preprocess_voc] → step1a_signal_scan → step1b_recommend → ...
```

The new step executes as a worker between ingest and step1a. It is **optional** — if the input is already clean VoC (short, homogeneous), the step produces a lightly cleaned version and moves on.

### 3.2 Two-Phase Hybrid Design

#### Phase 1 — Rule-Based Segmentation & Cleaning (deterministic, no LLM)

| Operation | Description |
|---|---|
| **Segment detection** | Identify source-type boundaries using header patterns: `"From ... we hear:"`, `"From Customer Comments:"`, `"From the technology front"`, markdown `##` headers, `"From the Industry"`, etc. |
| **Cleaning** | Strip URL references `[site.com]`, normalize whitespace/newlines, remove formatting artifacts (`✅❌`, ASCII box-drawing, `---` horizontal rules, empty table headers) |
| **Deduplication** | Flag near-duplicate observations across sections using normalized text similarity (Jaccard on token trigrams, threshold ≥ 0.7). Duplicates are merged, not discarded — the richer version is kept with a cross-reference note |
| **Comment re-indexing** | Assign sequential 1-based integer IDs to every discrete observation, regardless of original numbering |

#### Phase 2 — LLM Observation Extraction & Metadata Tagging (structured output)

A single focused LLM call per segment (or batched for short segments) extracts discrete observations and enriches them with metadata:

**Observation Schema:**

```python
class ObservationMetadata(BaseModel):
    observation_id: int          # Sequential 1-based index (from Phase 1)
    source_type: str             # Customer VoC | Corporate Policy | Technology Intelligence |
                                 # Industry Analysis | Competitive Intelligence | Regulatory Filing
    text: str                    # Cleaned, concise observation (1-3 sentences)
    original_excerpt: str        # Verbatim excerpt from input for traceability
    products: list[str]          # HPE products mentioned (e.g., "ProLiant DL380", "Cray EX")
    theater: str                 # AMS | EMEA | APJ | Global | Unknown
    business_unit: str           # HPE Compute | HPE Storage | HPE Supercomputing | HPE Networking |
                                 # HPE GreenLake | HPE Intelligent Edge | Cross-BU | Unknown
    jtbd: str                    # The customer's Job-to-Be-Done expressed or implied
                                 # (e.g., "Deploy AI training infrastructure on schedule",
                                 #  "Maintain budget predictability for hardware refresh")
    date_references: list[str]   # Dates or time periods mentioned (e.g., "April 2025", "H2 2026")
    sentiment: str               # Positive | Negative | Neutral | Mixed
```

**Why JTBD and BU?**

- **JTBD** (Jobs-to-Be-Done): Anchors each observation to the functional/emotional job the customer is trying to accomplish. This directly feeds Step 3 (CXIF empathy profile) and Step 7 (Precoil EMT assumption mapping) — when the SOC Radar identifies a signal, downstream steps can immediately see *whose job* is being disrupted.
- **BU** (Business Unit): Enables portfolio-level filtering. The portfolio dashboard can show signal exposure per BU, and step 1b recommendations can be tagged to the accountable business unit.

### 3.3 Output Format

The preprocessed output is a structured string that step1a consumes:

```
=== PREPROCESSED INPUT (47 observations from 4 source types) ===

--- Source: Customer VoC (22 observations) ---

[1] [Product: ProLiant DL380 | Theater: EMEA | BU: HPE Compute]
[JTBD: Receive ordered hardware within committed delivery window]
"5-month delay in delivery of full BoQ — customer threatening order cancellation. 
Ordered November 2024, still undelivered as of April 2025."

[2] [Product: ProLiant DL380 | Theater: Unknown | BU: HPE Compute]
[JTBD: Plan deployment schedules with visibility into parts availability]
"Gen12 parts arriving piecemeal without clear communication on pending items or ETAs."

...

--- Source: Corporate Policy (6 observations) ---

[23] [Product: Cross-Product | Theater: Global | BU: Cross-BU]
[JTBD: Maintain pricing stability for budget planning]
"HPE reduced quote validity to 14 days and added terms allowing price adjustments 
until shipment date, driven by DRAM/NAND cost increases."

...

--- Source: Technology Intelligence (8 observations) ---

[29] [Product: N/A | Theater: Global | BU: HPE Compute]
[JTBD: Reduce HBM cost per AI inference token]
"CXL 3.0 enables fabric-scale coherent memory pooling — rack-level shared memory 
with ~200-600ns latency, targeting KV cache overflow and embedding tables as 
primary AI use cases."

...

--- Source: Industry Analysis (11 observations) ---

[37] [Product: N/A | Theater: Global | BU: Cross-BU]
[JTBD: Maintain affordable access to memory components for device manufacturing]
"IDC expects 2026 DRAM and NAND supply growth below historical norms at 16% and 
17% YoY respectively, driven by strategic reallocation of wafer capacity to HBM."

...

=== METADATA SUMMARY ===
Source types: Customer VoC (22), Corporate Policy (6), Technology Intelligence (8), Industry Analysis (11)
Products: ProLiant DL380 (7), Cray EX (5), GreenLake (4), ...
Theaters: EMEA (14), AMS (12), Global (15), Unknown (6)
Business Units: HPE Compute (18), HPE Supercomputing (12), HPE GreenLake (6), Cross-BU (11)
Top JTBDs: "Receive hardware on schedule" (9), "Maintain budget predictability" (6), ...
Date range: November 2024 — 2028 (projected)
Near-duplicates merged: 3
```

### 3.4 State Model Changes

Add to `BMIWorkflowState` in `state.py`:

```python
preprocessed_voc_data: str                    # Structured text output for step1a
preprocessing_metadata: dict[str, object]     # Summary stats, segment counts, dedup info
observation_index: list[dict[str, object]]    # Full ObservationMetadata records (for UI/API)
```

### 3.5 Step 1a Integration

Minimal change — `_build_messages()` reads `preprocessed_voc_data` if present, falls back to `voc_data`:

```python
def _build_messages(state: BMIWorkflowState) -> list[SystemMessage | HumanMessage]:
    voc_data = str(state.get("preprocessed_voc_data") or state.get("voc_data", ""))
    # ... rest unchanged
```

The user prompt is updated to reference observation numbers:

```python
user_prompt = (
    "Analyze the following preprocessed Voice of Customer material.\n"
    "Each observation is numbered [N] with metadata tags.\n"
    "Use these numbers as supporting_comments when citing evidence.\n"
    "Use the Source Type tags to set source_type accurately.\n\n"
    "{voc}"
).format(voc=normalized)
```

---

## 4. Implementation Plan

### Phase 0: State Model & Feature File (BDD contract)

#### 0-1. Add state fields

**File:** `backend/app/state.py`  
**Change:** Add `preprocessed_voc_data`, `preprocessing_metadata`, `observation_index` to `BMIWorkflowState`.

#### 0-2. Create feature file

**File:** `backend/tests/features/preprocess-voc.feature`  
**Scenarios:**

| # | Scenario | Tests |
|---|---|---|
| 1 | Multi-source text is segmented by source type | Given mixed input with 4 source headers → segments detected = 4 |
| 2 | Observations are numbered sequentially across segments | Given 47 discrete observations → IDs 1..47, no gaps |
| 3 | URL references and formatting artifacts are stripped | Given text with `[site.com]`, `✅`, `---` → cleaned output contains none |
| 4 | Near-duplicate observations are merged | Given 2 observations with trigram Jaccard ≥ 0.7 → output count reduced by 1 |
| 5 | JTBD is extracted for customer observations | Given customer comment about delivery delay → JTBD contains "delivery" or "schedule" |
| 6 | BU is tagged from product mention | Given "ProLiant DL380" → BU = "HPE Compute" |
| 7 | Theater is extracted from context | Given "Theater: EMEA" in observation → theater = "EMEA" |
| 8 | Fallback when no preprocessing needed | Given short homogeneous VoC text → preprocessed_voc_data ≈ cleaned voc_data |
| 9 | Step1a consumes preprocessed_voc_data | Given state with preprocessed_voc_data → step1a uses it over raw voc_data |
| 10 | Legacy run without preprocessing | Given state without preprocessed_voc_data → step1a falls back to voc_data |

### Phase 1: Rule-Based Preprocessing (deterministic)

#### 1-1. Create preprocessing module

**File:** `backend/app/nodes/preprocess_voc.py`  

**Functions:**

| Function | Responsibility |
|---|---|
| `detect_segments(text: str) -> list[Segment]` | Regex-based header detection, returns list of `(source_type, start, end, body)` tuples |
| `clean_text(text: str) -> str` | Strip URLs, formatting artifacts, normalize whitespace |
| `reindex_observations(segments: list[Segment]) -> list[RawObservation]` | Split segment bodies into discrete observations, assign sequential IDs |
| `find_near_duplicates(observations: list[RawObservation]) -> list[DuplicatePair]` | Trigram Jaccard similarity, return pairs above threshold |
| `merge_duplicates(observations, duplicates) -> list[RawObservation]` | Keep richer observation, add cross-reference |

**Segment detection patterns:**

```python
SEGMENT_PATTERNS = [
    (r"(?i)from\s+.*?customer\s+comments?\s*:", "Customer VoC"),
    (r"(?i)from\s+.*?policy\s+guidance\s*.*?:", "Corporate Policy"),
    (r"(?i)from\s+the\s+technology\s+front\s*.*?:", "Technology Intelligence"),
    (r"(?i)from\s+the\s+industry\s*.*?:", "Industry Analysis"),
    (r"(?i)from\s+.*?competitive\s*.*?:", "Competitive Intelligence"),
    (r"(?i)##\s+\d+\.\s+", "Customer VoC"),  # Markdown numbered sections within VoC
]
```

**Observation boundary detection:**
- Numbered patterns: `### 2.1`, `[N]`, `N.`, `Comment N:`
- Blockquote boundaries: `> "..."` blocks
- Double-newline paragraph breaks within non-numbered sections
- Source/Product/Theater metadata lines act as observation headers

#### 1-2. BU mapping table

**File:** `backend/app/nodes/preprocess_voc.py` (or separate `backend/app/reference/product_bu_map.py`)

A deterministic product-to-BU lookup used by both Phase 1 (rule-based) and Phase 2 (LLM validation):

```python
PRODUCT_BU_MAP = {
    # HPE Compute
    "ProLiant": "HPE Compute",
    "DL380": "HPE Compute",
    "DL360": "HPE Compute",
    "DL320": "HPE Compute",
    "Apollo": "HPE Compute",
    "Synergy": "HPE Compute",
    "Edgeline": "HPE Compute",
    "PCAI": "HPE Compute",
    # HPE Supercomputing
    "Cray": "HPE Supercomputing",
    "EX2500": "HPE Supercomputing",
    "XD 6500": "HPE Supercomputing",
    "Grace Hopper": "HPE Supercomputing",
    "Direct Liquid Cooling": "HPE Supercomputing",
    "DLC": "HPE Supercomputing",
    # HPE Storage
    "Alletra": "HPE Storage",
    "StoreOnce": "HPE Storage",
    "Primera": "HPE Storage",
    # HPE GreenLake
    "GreenLake": "HPE GreenLake",
    # HPE Networking
    "Aruba": "HPE Networking",
    "FlexFabric": "HPE Networking",
    # GPU/Accelerator (maps to Compute or Supercomputing by context)
    "GPU": "HPE Compute",  # default; override to Supercomputing if HPC context
    "H100": "HPE Compute",
    "H200": "HPE Compute",
    "MI300": "HPE Compute",
}
```

### Phase 2: LLM Metadata Extraction

#### 2-1. LLM extraction node

**File:** `backend/app/nodes/preprocess_voc.py`

**Function:** `extract_observation_metadata(observations: list[RawObservation], llm: BaseChatModel) -> list[ObservationMetadata]`

**System prompt (concise, ~50 lines — not the SOC Radar skill):**

```
You are a preprocessing assistant for a disruption signal radar.
Your job is to extract structured metadata from raw observations.

For each observation, determine:
1. source_type: One of [Customer VoC, Corporate Policy, Technology Intelligence, 
   Industry Analysis, Competitive Intelligence, Regulatory Filing]
2. products: HPE products explicitly mentioned (use official names)
3. theater: AMS, EMEA, APJ, Global, or Unknown
4. business_unit: HPE Compute, HPE Storage, HPE Supercomputing, HPE Networking, 
   HPE GreenLake, HPE Intelligent Edge, Cross-BU, or Unknown
5. jtbd: The functional Job-to-Be-Done the customer/stakeholder is trying to accomplish.
   Frame as: "[Verb] [object] [context]" — e.g., "Deploy AI training cluster on schedule",
   "Maintain budget predictability during hardware refresh cycle".
   For non-customer observations (policy, industry), infer the impacted customer JTBD.
6. date_references: Any dates, quarters, or time periods mentioned
7. sentiment: Positive, Negative, Neutral, or Mixed

Rules:
- JTBD must describe the customer's job, not HPE's action. Wrong: "HPE should fix delivery".
  Right: "Receive ordered hardware within committed delivery window".
- BU assignment: Use product mentions first. If no product, infer from context (e.g., 
  "HPC environment" → HPE Supercomputing). If ambiguous, use Cross-BU.
- Do not invent products or theaters not supported by the text.
- Keep text field to 1-3 sentences — concise but preserving the signal-relevant content.
```

**Pydantic output schema:** `PreprocessingResult` containing `list[ObservationMetadata]`.

**Batching strategy:** If >50 observations, batch by segment (one LLM call per source type). If ≤50, single call.

#### 2-2. Render preprocessed output

**Function:** `render_preprocessed_voc(metadata: list[ObservationMetadata]) -> str`

Produces the formatted string shown in §3.3, grouped by source type, with metadata tags and summary footer.

### Phase 3: Worker Integration

#### 3-1. Create worker

**File:** `backend/app/workers/preprocess_worker.py`

```python
class PreprocessWorker(BaseWorker):
    name = "preprocess_voc"
    step_number = 0  # Runs before step 1
    
    def execute(self, state: BMIWorkflowState) -> BMIWorkflowState:
        voc_data = state.get("voc_data", "")
        llm = get_llm(state.get("llm_backend", ""))
        
        # Phase 1: Rule-based
        segments = detect_segments(voc_data)
        observations = reindex_observations(segments)
        observations = [clean_observation(o) for o in observations]
        duplicates = find_near_duplicates(observations)
        observations = merge_duplicates(observations, duplicates)
        
        # Phase 2: LLM metadata
        metadata = extract_observation_metadata(observations, llm)
        preprocessed = render_preprocessed_voc(metadata)
        
        return {
            **state,
            "preprocessed_voc_data": preprocessed,
            "preprocessing_metadata": {
                "total_observations": len(metadata),
                "segments": len(segments),
                "duplicates_merged": len(duplicates),
                "source_types": _count_by(metadata, "source_type"),
                "business_units": _count_by(metadata, "business_unit"),
            },
            "observation_index": [m.model_dump() for m in metadata],
        }
```

#### 3-2. Register worker

**File:** `backend/app/workers/registry.py`  
**Change:** Insert `PreprocessWorker` at position 0 (before `Step1aWorker`).

#### 3-3. Update graph routing

**File:** `backend/app/graph.py`  
**Change:** Add `preprocess_voc` to `WORKFLOW_STEP_ORDER` before `signal_scan`. Update `determine_next_step()` to route from ingest → preprocess_voc → signal_scan.

#### 3-4. Update step1a to consume preprocessed data

**File:** `backend/app/nodes/step1a_signal_scan_llm.py`  
**Change:** `run_step1a_llm()` reads `preprocessed_voc_data` if present, falls back to `voc_data`. User prompt updated to reference observation numbers and metadata tags.

### Phase 4: Checkpoint & UI

#### 4-1. Add checkpoint

**File:** `backend/app/checkpoints.py`  
**Change:** Add `checkpoint_preprocess` after ingest completion. Allows users to review/edit the preprocessed observations before signal scanning.

#### 4-2. Frontend display

**File:** `frontend-react/src/components/` (new or existing step viewer)  
**Change:** Display preprocessing results: observation count by source type, BU distribution, top JTBDs. Allow editing metadata tags before proceeding.

---

## 5. Test Plan

### BDD Scenarios (feature file)

All scenarios from §4 Phase 0-2 above, plus:

| # | Scenario | Validates |
|---|---|---|
| 11 | Preprocessing handles empty segment gracefully | Edge case: header detected but no content |
| 12 | Preprocessing handles single-source input | No segment headers → treated as single "Unknown" segment |
| 13 | Product-to-BU mapping is correct for known products | Deterministic lookup table |
| 14 | JTBD uses customer framing, not vendor framing | LLM output validation |
| 15 | Preprocessing metadata summary is accurate | Counts match actual observations |
| 16 | Checkpoint allows observation edit | Checkpoint decision flow |

### Unit Tests

| Test | Scope |
|---|---|
| `test_detect_segments_multi_source` | 4 headers → 4 segments with correct source types |
| `test_detect_segments_no_headers` | Plain text → 1 segment, source_type = "Unknown" |
| `test_clean_text_urls` | `[site.com]` removed, `[1]` preserved |
| `test_clean_text_artifacts` | `✅❌---` stripped |
| `test_reindex_sequential` | IDs 1..N with no gaps after dedup |
| `test_near_duplicate_detection` | Known duplicate pair → Jaccard ≥ 0.7 |
| `test_product_bu_map_known` | "ProLiant DL380" → "HPE Compute" |
| `test_product_bu_map_unknown` | "FooBar 9000" → "Unknown" |
| `test_render_preprocessed_format` | Output matches expected structure |

### Integration Tests

| Test | Scope |
|---|---|
| `test_end_to_end_preprocess_to_step1a` | Multi-source input → preprocessing → step1a → signals reference correct observation IDs |
| `test_legacy_run_no_preprocessing` | State without `preprocessed_voc_data` → step1a works unchanged |

---

## 6. Risk & Mitigation

| Risk | Impact | Mitigation |
|---|---|---|
| LLM metadata extraction adds latency | ~10-30s per call | Rule-based Phase 1 handles most work; LLM call is lightweight (50-line prompt, structured output) |
| Segment detection misses new header patterns | Observations in wrong segment | Fallback: unrecognized sections become "Unknown" source type; easily extensible regex table |
| JTBD framing is inconsistent across calls | Downstream steps see varied language | Prompt includes explicit positive/negative examples; BDD scenario validates customer-framing constraint |
| Product-to-BU map incomplete | Unknown BU for valid products | Map is easily extensible; LLM Phase 2 can infer from context as fallback |
| Large inputs exceed LLM context | Truncation/failure | Batching by segment (§4 Phase 2-1); cap at ~100 observations per call |

---

## 7. Files Changed

| File | Change Type |
|---|---|
| `backend/app/state.py` | Modify — add 3 fields |
| `backend/app/nodes/preprocess_voc.py` | **New** — preprocessing module |
| `backend/app/workers/preprocess_worker.py` | **New** — worker class |
| `backend/app/workers/registry.py` | Modify — register worker |
| `backend/app/graph.py` | Modify — add step to routing |
| `backend/app/nodes/step1a_signal_scan_llm.py` | Modify — read preprocessed data |
| `backend/app/checkpoints.py` | Modify — add checkpoint |
| `backend/tests/features/preprocess-voc.feature` | **New** — BDD scenarios |
| `backend/tests/test_bdd_preprocess_voc.py` | **New** — step definitions |
| `frontend-react/src/components/PreprocessReviewPanel.jsx` | **New** — UI for review |
