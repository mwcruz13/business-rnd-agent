# VoC-to-SOC Radar Extract Pipeline — Implementation Guide

This document describes the two-stage pipeline that transforms raw Voice of Customer (VoC) survey data into signal-rich comment extracts ready for use by the SOC Radar agent.

---

## Pipeline Overview

```
 ┌──────────────────────────┐
 │  Relationship Survey CSV │  ~100k comments
 │  (relationship_insight_  │  Columns: Comment, Question, Theater, Length
 │   data.csv)              │
 └────────────┬─────────────┘
              │
              ▼
 ┌──────────────────────────┐
 │  Stage 1                 │  bu_classify_pipeline.py
 │  BU × JTBD Classification│
 │  ─────────────────────── │
 │  Pass 1: Question → BU   │  30.7%
 │  Pass 2: Keyword → BU    │  41.1%
 │  Pass 3: Remainder → X-BU│  28.2%
 │  + JTBD keyword tagging   │  14 themes
 └────────────┬─────────────┘
              │
              ▼
 ┌──────────────────────────┐
 │  relationship_bu_         │  ~100k rows
 │  classified.csv           │  + BU_List, BU_Method, JTBD_List
 └────────────┬─────────────┘
              │
              ▼
 ┌──────────────────────────┐
 │  Stage 2                 │  soc_extract_signals.py
 │  Signal-Rich Extraction   │
 │  ─────────────────────── │
 │  1. De-duplicate          │
 │  2. Score signal richness │
 │  3. Diversity-aware pick  │
 │     (20 per BU)           │
 └────────────┬─────────────┘
              │
              ▼
 ┌──────────────────────────┐
 │  soc_extracts/            │  Per-BU .txt + .json
 │  ├── soc_voc_compute.txt  │  Ready for SOC Radar
 │  ├── soc_voc_networking…  │  voc_data input
 │  └── extraction_summary…  │
 └──────────────────────────┘
```

---

## Stage 1: BU × JTBD Classification (`bu_classify_pipeline.py`)

### Purpose

The relationship survey CSV contains ~100k comments with no Business Unit column. This script classifies every comment into one or more HPE Business Units **and** one or more JTBD themes using a 3-pass approach.

### Location

```
bmi-consultant-app/backend/scripts/data/bu_classify_pipeline.py
```

### Input

| File | Columns | Rows |
|---|---|---|
| `relationship_insight_data.csv` | `Comment`, `Question`, `Theater`, `Length` | ~99,786 |

The CSV must be placed at `backend/scripts/data/relationship_insight_data.csv` (mounted inside the container at `/app/backend/scripts/data/`).

### Classification Logic

#### Pass 1 — Question-Type Mapping (30.7%)

Direct lookup from the survey's `Question` column to a BU. For example:

| Question pattern | Mapped BU |
|---|---|
| `Top-of-mind questions - Networking` | Networking |
| `Hybrid Cloud service providers Satisfaction…` | Hybrid Cloud |
| `Technical_Support_Text` | Service Delivery |
| `Purchase_Experience_Text` | Quote-to-Cash |

This covers all question types that are inherently BU-specific. The full mapping table is defined in `question_bu_map` (~50 entries).

#### Pass 2 — Keyword Extraction (41.1%)

For generic question types (e.g., `Overall Satisfaction Question`, `IT_suppliers_Comments`, `Products_and_Solutions_Text`), the comment text is scanned against BU-specific keyword dictionaries:

| BU | Example keywords |
|---|---|
| **Networking** | `aruba`, `clearpass`, `switch`, `wireless`, `sd-wan`, `juniper`, `router`, `firewall` |
| **Compute** | `proliant`, `dl380`, `synergy`, `ilo`, `server`, `hpc`, `cray`, `gpu` |
| **Hybrid Cloud** | `greenlake`, `alletra`, `nimble`, `3par`, `storage`, `vmware`, `backup` |
| **Service Delivery** | `support`, `technician`, `tech care`, `onsite`, `rma`, `warranty`, `firmware` |
| **Quote-to-Cash** | `quote`, `pricing`, `order`, `renewal`, `reseller`, `partner`, `sales`, `contract` |

A comment may match multiple BUs (11.9% of comments are multi-BU). Single-match: 29.1%. Multi-match: 11.9%.

#### Pass 3 — Cross-BU Fallback (28.2%)

Comments that match no BU-specific keywords are assigned to `Cross-BU / General HPE`. These are often short or generic sentiment statements.

#### JTBD Classification (Applied to All Comments)

Every comment is independently tagged with JTBD themes via keyword patterns (14 themes):

| Code | Theme | Example triggers |
|---|---|---|
| JTBD01 | Support Resolution | `support`, `escalation`, `ticket`, `SLA` |
| JTBD02 | Purchase/Quote/Renew | `quote`, `renewal`, `RFQ`, `configurator` |
| JTBD03 | Delivery Visibility | `delivery`, `shipment`, `lead time`, `ETA` |
| JTBD04 | Partner Relationship | `partner`, `trust`, `account team`, `loyalty` |
| JTBD05 | Product Reliability | `reliability`, `bug`, `firmware`, `downtime` |
| JTBD06 | Firmware/Access | `firmware`, `download`, `portal`, `paywall` |
| JTBD07 | Channel Navigation | `channel`, `reseller`, `distributor`, `VAR` |
| JTBD08 | Cloud Management UX | `greenlake`, `central`, `portal`, `dashboard` |
| JTBD09 | HPE-Juniper Integration | `juniper`, `merger`, `acquisition` |
| JTBD10 | Pre-Sales Accuracy | `pre-sales`, `over-promise`, `mismatch` |
| JTBD11 | Cost Management | `cost`, `expensive`, `subscription`, `budget` |
| JTBD12 | Professional Services | `professional service`, `deployment`, `consulting` |
| JTBD13 | Strategic Advisory | `advisory`, `strategy`, `roadmap`, `proactive` |
| JTBD14 | Product Continuity | `discontinue`, `end-of-life`, `EOL`, `migration` |

Comments matching no JTBD pattern are tagged `Unclassified`.

### Outputs

| File | Description |
|---|---|
| `relationship_bu_classified.csv` | Full dataset with added columns: `BU_List` (pipe-delimited), `BU_Method`, `JTBD_List` (pipe-delimited) |
| `relationship_bu_jtbd_summary.md` | Cross-tabulation summary: method breakdown, BU distribution, BU×JTBD matrix, theater breakdown |

### Running Stage 1

```bash
cd bmi-consultant-app
docker compose exec -T bmi-backend python3 /app/backend/scripts/data/bu_classify_pipeline.py
```

---

## Stage 2: Signal-Rich Extraction (`soc_extract_signals.py`)

### Purpose

From the classified dataset, extract a diverse sample of the **20 richest comments per BU** — optimized for signal detection by the SOC Radar agent. The focus is on diversity and completeness, not volume.

### Location

```
bmi-consultant-app/backend/scripts/data/soc_extract_signals.py
```

### Input

| File | Produced by |
|---|---|
| `relationship_bu_classified.csv` | Stage 1 (`bu_classify_pipeline.py`) |

### Step 1 — De-duplication

The source survey often contains duplicate comment text across rows (same respondent text at different survey lengths). Before scoring, comments are de-duplicated per BU using a normalized text key:

```
key = lowercase → strip punctuation → first 200 chars
```

This typically removes ~75% of raw row duplicates (e.g., Networking goes from ~6,400 raw rows to ~1,600 unique comments).

### Step 2 — Signal Richness Scoring

Each comment receives a composite score (0–100) based on seven signal dimensions:

| Dimension | Weight | What it detects |
|---|---|---|
| **Competitor mentions** | ×3 | Dell, Cisco, Fortinet, Palo Alto, Nutanix, VMware, etc. |
| **Temporal shifts** | ×3 | `used to`, `switching to`, `deteriorated`, `years ago` |
| **Workaround behavior** | ×4 | `worked around`, `used ChatGPT instead`, `found ways` |
| **Business model friction** | ×4 | `forced subscription`, `paywall`, `locked behind` |
| **Nonconsumption evidence** | ×4 | `can't access`, `locked out`, `not available`, `restricted` |
| **Specificity** | ×2 | Product model numbers (`DL380`, `CX8325`), dollar amounts, time durations |
| **JTBD breadth** | ×3 | Number of JTBD themes the comment touches |

Higher weights emphasize disruption-relevant patterns (workarounds, nonconsumption, business model friction) which are direct inputs to the SOC Radar's 7 signal zones.

### Step 3 — JTBD-to-SOC Zone Mapping

Each JTBD theme maps to one of the SOC Radar's 7 disruption signal zones:

| JTBD Themes | SOC Radar Zone |
|---|---|
| JTBD01 (Support), JTBD02 (Quote), JTBD03 (Delivery), JTBD10 (Pre-Sales), JTBD12 (Prof. Services) | Overserved Customers |
| JTBD04 (Partner), JTBD07 (Channel) | Business Model Anomaly |
| JTBD05 (Reliability), JTBD09 (Juniper) | Enabling Technology |
| JTBD06 (Firmware), JTBD14 (Continuity) | Nonconsumption |
| JTBD08 (Cloud UX), JTBD13 (Advisory) | New-Market Foothold |
| JTBD11 (Cost) | Low-End Foothold |
| *(no direct JTBD mapping)* | Regulatory / Policy Shift |

This mapping ensures that the diversity-aware selection algorithm covers the SOC Radar's analysis zones.

### Step 4 — Diversity-Aware Selection (4 Rounds)

For each BU, the algorithm selects up to 20 comments in four priority rounds:

| Round | Goal | Selection rule |
|---|---|---|
| **Round 1** | JTBD coverage | For each uncovered JTBD theme, pick the highest-scoring comment containing that theme |
| **Round 2** | SOC zone coverage | For each uncovered SOC zone, pick the highest-scoring comment mapping to that zone |
| **Round 3** | Theater coverage | For each uncovered theater (AMS, EMEA, APJ), pick the highest-scoring comment from that theater |
| **Round 4** | Depth fill | Fill remaining slots with highest-scoring comments that add JTBD diversity. **Only comments with at least 1 classified JTBD are eligible** (no Unclassified-only filler) |

This ensures every extract covers all 14 JTBD themes, all available SOC zones (typically 6/7), and all 3 geographic theaters.

### Outputs

| File | Format | Description |
|---|---|---|
| `soc_extracts/soc_voc_{bu}.txt` | Plain text | VoC text block formatted for SOC Radar `voc_data` input. Each comment has a header line with theater, signal score, and JTBD tags. |
| `soc_extracts/soc_extract_{bu}.json` | JSON | Scored metadata for each selected comment (score breakdown, JTBD themes, SOC zones, coverage stats) |
| `soc_extracts/extraction_summary.json` | JSON | Summary statistics per BU (candidate count, avg score, zone coverage, gaps) |

BU file names are generated from the BU label: `soc_voc_networking.txt`, `soc_voc_hybrid_cloud.txt`, `soc_voc_quote_to_cash.txt`, etc.

### Running Stage 2

```bash
cd bmi-consultant-app
docker compose exec -T bmi-backend python3 /app/backend/scripts/data/soc_extract_signals.py
```

### Expected Output

```
Loaded comments per BU:
  Compute                  :    666 candidates
  Cross-BU                 :    111 candidates
  Hybrid Cloud             :   1430 candidates
  Networking               :   1612 candidates
  Quote-to-Cash            :   3987 candidates
  Service Delivery         :   3979 candidates

  EXTRACTION COMPLETE
  BUs extracted: 6
    Compute                  : 20 comments, avg score 22, 6/7 zones
    Cross-BU                 : 20 comments, avg score  9, 6/7 zones
    Hybrid Cloud             : 20 comments, avg score 26, 6/7 zones
    Networking               : 20 comments, avg score 26, 6/7 zones
    Quote-to-Cash            : 20 comments, avg score 25, 6/7 zones
    Service Delivery         : 20 comments, avg score 27, 6/7 zones
```

---

## Using Extracts with the SOC Radar Agent

The `.txt` files in `soc_extracts/` are formatted as direct `voc_data` input for the SOC Radar agent. Each file is a self-contained VoC block for one BU.

### .txt File Format

```
# Voice of Customer — Networking Business Unit
# Source: HPE Relationship Survey (classified by bu_classify_pipeline.py)
# Selection: 20 signal-rich comments from 1612 candidates
# Method: Diversity-aware extraction (JTBD coverage + SOC zone coverage + theater coverage)

--- Comment 1 [Theater: EMEA] [Signal Score: 45] [JTBD: JTBD01_Support_Resolution, ...] ---
<comment text>

--- Comment 2 [Theater: AMS] [Signal Score: 24] [JTBD: ...] ---
<comment text>
```

### SOC Radar Integration

The SOC Radar agent's 4-phase workflow (Scan → Interpret → Prioritize → Recommend) scans VoC text across 7 signal zones:

1. **Nonconsumption** — customers locked out of value
2. **Overserved Customers** — paying for complexity they don't need
3. **Low-End Foothold** — cheaper alternatives gaining traction
4. **New-Market Foothold** — new categories emerging at the fringe
5. **Business Model Anomaly** — channel/model conflicts
6. **Enabling Technology** — technology shifts creating new possibilities
7. **Regulatory / Policy Shift** — external forces reshaping the market

Pass the contents of a `.txt` file as the `voc_data` parameter when invoking the SOC Radar. The agent will extract structured disruption signals from the customer verbatims.

---

## Running the Full Pipeline End-to-End

```bash
# Navigate to the app directory
cd bmi-consultant-app

# Stage 1: Classify comments by BU and JTBD
docker compose exec -T bmi-backend python3 /app/backend/scripts/data/bu_classify_pipeline.py

# Stage 2: Extract signal-rich samples for SOC Radar
docker compose exec -T bmi-backend python3 /app/backend/scripts/data/soc_extract_signals.py

# Verify output
docker compose exec -T bmi-backend ls -la /app/backend/scripts/data/soc_extracts/
```

### Prerequisites

- Docker containers running (`docker compose up -d`)
- Source CSV at `backend/scripts/data/relationship_insight_data.csv`
- Stage 1 must complete before Stage 2 (Stage 2 reads Stage 1's output CSV)

---

## File Inventory

| Path (relative to `backend/scripts/data/`) | Type | Role |
|---|---|---|
| `relationship_insight_data.csv` | Input | Raw relationship survey data |
| `bu_classify_pipeline.py` | Script | Stage 1 — BU × JTBD classification |
| `relationship_bu_classified.csv` | Output | Classified dataset (Stage 1 → Stage 2) |
| `relationship_bu_jtbd_summary.md` | Output | Cross-tabulation summary |
| `soc_extract_signals.py` | Script | Stage 2 — Signal-rich extraction |
| `soc_extracts/soc_voc_{bu}.txt` | Output | VoC text blocks for SOC Radar |
| `soc_extracts/soc_extract_{bu}.json` | Output | Scored metadata per comment |
| `soc_extracts/extraction_summary.json` | Output | Extraction summary statistics |

---

## Design Decisions

1. **De-duplication before scoring** — The source CSV contains duplicate survey rows (same respondent text at different lengths). Without de-duplication, the same comment fills multiple selection slots. The normalized 200-char key catches near-identical entries while allowing genuinely different comments to coexist.

2. **JTBD-quality gate in Round 4** — Comments with no classified JTBD theme (only competitor name-drops like "Cisco — network leader") are excluded from fill slots. This ensures all 20 selected comments carry behavioral evidence, not just brand mentions.

3. **Weighted scoring dimensions** — Workaround behavior, business model friction, and nonconsumption evidence receive 4× weight because they are the strongest disruption signals in Clayton Christensen's framework and map directly to SOC Radar zones.

4. **20 comments per BU** — This target balances signal coverage (14 JTBD themes + 3 theaters + 6-7 SOC zones) against LLM context window constraints. Each extract fits comfortably in a single SOC Radar invocation.

5. **Cross-BU extract** — Comments that don't match any specific BU are still extracted if they score ≥5 and have at least one classified JTBD. These often contain cross-cutting strategic signals (e.g., HPE-wide competitor dynamics).
