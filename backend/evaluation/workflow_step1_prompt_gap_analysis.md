# Workflow Step 1 — Prompt Gap Analysis

## Overview

This analysis compares two SOC Radar signal detection reports generated from the same 20 Compute BU Voice of Customer comments (HPE Relationship Survey) using the same `soc-radar/SKILL.md` prompt.

| Report | Model | File |
|--------|-------|------|
| **Workflow Step 1** | GPT-4o (via `step1_signal_llm.py`) | `workflow_step1_compute_relationship_signal_report.json` |
| **Manual SOC Radar** | Claude Opus 4.6 (interactive) | `soc_radar_compute_report.json` |

Input: `soc_extracts/soc_voc_compute.txt` — 20 signal-rich comments from 246 candidates, Compute BU, Relationship Survey.

---

## 1. Signal Detection Depth

| Dimension | GPT-4o | Claude Opus 4.6 |
|-----------|--------|------------------|
| Signals detected | **4** | **10** |
| Unique comments cited as evidence | 9 of 20 | All 20 of 20 |
| Signal zones covered | 4 of 7 | 6 of 7 |
| Coverage gaps identified | 3 zones | 1 zone |

### Signals GPT-4o Missed

| Signal | Zone | Comments | Strategic Significance |
|--------|------|----------|----------------------|
| AI replacing HPE support | New-Market Foothold | 15 | Highest-priority disruptive signal (6/6 filters passed) |
| Dell as systemic alternative | Low-End Foothold | 3, 5, 12, 14, 18 | Cross-cutting competitive pattern across 6 of 20 comments |
| Acquired-product degradation | Business Model Anomaly | 10 | Reputational pattern affecting future M&A (Juniper integration risk) |
| Gen12 quality regression | Enabling Technology | 7, 16 | Sustaining execution gap accelerating Dell migration |
| Digital experience fragmentation | Nonconsumption | 7, 15, 16, 20 | Creates the nonconsumption conditions enabling AI bypass (Signal 5) |
| Partner/customer defection threshold | Overserved Customers | 2, 9, 12 | 25-year partners actively switching — urgency indicator |

### Root Cause

GPT-4o collapsed related but distinct phenomena into single signals. For example, firmware paywall and iLO monetization were identified separately (correctly), but the *downstream effects* — self-service fragmentation, AI bypass, partner defection — were not extracted as independent signals. Claude treated the VoC as a system of interrelated signals rather than a flat list of complaints.

---

## 2. Sustaining vs. Disruptive Classification

| Dimension | GPT-4o | Claude Opus 4.6 |
|-----------|--------|------------------|
| Disruptive signals | 3 (all "Low-End") | 5 (3 Low-End, 2 New-Market) |
| Sustaining signals | 1 | 5 |
| New-Market disruption detected | **No** | **Yes** — Signals 5, 7, 9 |

### Critical Gap: New-Market Disruption Missed Entirely

GPT-4o classified all 3 disruptive signals as "Disruptive — Low-End" and missed the new-market disruption pattern. The SKILL.md explicitly requires classifying each signal as new-market or low-end before applying filters. Claude correctly identified that AI support bypass (Signal 5) and digital fragmentation (Signal 9) create *nonconsumption* — customers who cannot access HPE's support at all — which is the textbook new-market disruption mechanism from *Seeing What's Next*.

### Zone-Classification Contradiction

GPT-4o classified `support_quality_decline` as **Sustaining** but assigned its zone as **"Nonconsumption"** — a contradiction. Nonconsumption is a disruption zone; sustaining signals serve existing customers along known dimensions. Claude handled this more precisely: it classified SLA failures (Signal 3) as Sustaining (execution gap) while correctly separating the *nonconsumption created by portal fragmentation* (Signal 9) as a distinct Disruptive — New-Market signal.

---

## 3. Disruption Filter Application

| Dimension | GPT-4o | Claude Opus 4.6 |
|-----------|--------|------------------|
| Filter detail per signal | 3 filter names listed, no per-filter assessment | 6 filters assessed individually with confidence ratings |
| Filter pass counts | Not computed | Explicitly scored (3–6 per signal) |
| RPV (Asymmetric Skills) assessed | Not broken into R/P/V | Resources, Processes, Values analyzed separately |
| Disruptive potential rating | Not computed | Low / Medium / High per signal |

### Example: Identical Filter Lists

GPT-4o assigned the same 3 filters ("Asymmetric Motivation, Barrier Removal, Business Model Conflict") to all 3 disruptive signals without differentiation. The SKILL.md requires a per-filter assessment table with Yes/No/Unclear, rationale, and confidence level for each of 6 filters. Claude produced the full 6-filter table for every disruptive signal, with signal-specific rationale.

### Example: Signal 5 (AI Bypass) — Not Detected by GPT-4o

Claude assessed all 6 filters for the AI bypass signal and found all 6 passed — the only signal to achieve a perfect score. This made it the highest-priority disruptive signal. GPT-4o did not detect this signal at all.

---

## 4. Priority Scoring Calibration

| Signal | GPT-4o Score | Claude Score | Delta | Issue |
|--------|-------------|-------------|-------|-------|
| Firmware paywall | 4 (Investigate) | 9 (Act) | **-5** | Under-scored despite past-tense switching language |
| iLO monetization | 4 (Investigate) | 6 (Investigate) | -2 | Conservative but aligned on tier |
| Support decline | 3 (Monitor) | 9 (Sustaining-Act) | **-6** | GPT-4o missed urgency of SLA failures |
| Quote response | 9 (Act) | 9 (Sustaining-Act) | 0 | Same score but different classification |
| AI bypass | Not detected | 9 (Act) | — | Highest-priority signal missed entirely |

### Scoring Rationale Gaps

GPT-4o under-scored the firmware paywall (impact=2, speed=2) despite VoC comments using past-tense language:
- *"the paywall of firmware updates **contributed to switching** to Dell"* (Comment 3)
- *"we **started moving** toward them as primary vendor"* (Comment 12)

These describe completed actions, not future risks. Claude scored speed=3 for exactly this reason and provided per-signal rationale explaining each score.

### Misclassification of Quote Response

GPT-4o's single Act-tier signal (`competitive_quote_response`) is classified as **Disruptive — Low-End**. Claude correctly classified it as **Sustaining** — faster quoting is an improvement along existing competitive dimensions, not a disruption. The SKILL.md defines sustaining innovation as serving "existing customers better along performance dimensions they already value." Quoting speed is precisely that.

---

## 5. Structural Completeness vs. SKILL.md Requirements

| SKILL.md Requirement | GPT-4o | Claude | Gap |
|---------------------|--------|--------|-----|
| Input metadata/stats | ❌ Missing | ✅ Present | Minor |
| Supporting comment indices per signal | ❌ Missing | ✅ Every signal | **Major** — no evidence traceability |
| Sustaining signal treatment (`sustaining_rationale`, `competitive_implication`) | ❌ Incomplete | ✅ Full block for all 5 sustaining signals | **Major** |
| Litmus test before filters | ❌ Not applied | ✅ Applied to every disruptive signal | **Major** — prerequisite step skipped |
| Value network insight | ❌ Not present | ✅ Present for every disruptive signal | **Major** — core analytical output missing |
| Alternative explanation per signal | ❌ Not present | ✅ Present for every signal | **Major** — SKILL rule #4 violated |
| Key evidence gap per signal | ❌ Not present | ✅ Present for every signal | **Major** — SKILL rule #8 violated |
| Reinforcement map between signals | ❌ Not present | ✅ Causal chain identified | **Major** — highest-value strategic insight missing |
| RPV assessment in Phase 4 | ❌ Not present | ✅ Full R/P/V breakdown per recommendation | Moderate |
| Next steps with owner/timeframe | ❌ Not present | ✅ 3 per signal, with owner and timeframe | Moderate |
| Experiment success/failure criteria | ❌ Not present | ✅ Present for every Investigate/Act signal | Moderate |
| Watching briefs for Monitor signals | ❌ Not present | ✅ 3 briefs with indicator and escalation trigger | Moderate |

---

## 6. Analytical Insight Quality

The most significant qualitative difference is the **reinforcement map**. Claude identified that signals form a causal chain:

```
Firmware paywall (1) + iLO monetization (2)
    → Self-service blocked (9)
        → AI bypass (5)
            → Support contract devaluation
```

The strategic insight — that fixing upstream signals (1, 2, 9) is more efficient than competing with the downstream disruptor (5) — is the kind of synthesis the SKILL.md framework is designed to produce. GPT-4o treated each signal as independent, missing this interrelationship entirely.

Additionally, Claude identified that the 5 sustaining signals (3, 4, 6, 8, 10) act as **accelerants** — they weaken HPE's ability to retain customers long enough to respond to the disruptive signals. This systems-level insight is absent from the GPT-4o output.

---

## 7. Recommendations to Improve GPT-4o Output Quality

### R1: Increase Signal Extraction Minimum

**Problem:** GPT-4o extracted only 4 signals from 20 comments, leaving 11 comments uncited.

**Fix:** Add to the system prompt:
> *"Extract at least 7-10 distinct signals from the input material. Do not collapse related phenomena into a single signal — a pricing issue and a portal access issue may share root causes but represent separate signals with different disruption trajectories. Every comment in the input should be cited as evidence by at least one signal."*

### R2: Enforce Sustaining/Disruptive Classification Gate

**Problem:** GPT-4o applied disruption filter names to a signal it classified as Sustaining, and misclassified a sustaining signal as disruptive.

**Fix:** Add an explicit classification gate:
> *"Before applying disruption filters, output a sustaining/disruptive classification for EVERY signal. Sustaining signals must NOT receive disruption filter analysis — they receive a `sustaining_rationale` and `competitive_implication` instead. Only signals classified as Disruptive proceed to litmus test and filter analysis."*

### R3: Require Per-Filter Assessment Tables

**Problem:** GPT-4o listed filter names without individual assessments, confidence ratings, or rationale.

**Fix:** Strengthen the structured output requirement:
> *"For each disruptive signal, you MUST output a 6-row assessment table evaluating ALL six disruption filters (Asymmetric Motivation, Asymmetric Skills/RPV, Trajectory, Performance Overshoot, Barrier Removal, Business Model Conflict). Each row must include: result (Yes/No/Unclear), confidence (Low/Medium/High), and a 1-2 sentence rationale specific to this signal. Do not list filter names without assessments."*

### R4: Mandate Comment-Level Evidence Linking

**Problem:** GPT-4o cited comments by quoting fragments but did not link signals to specific comment indices, making evidence traceability impossible.

**Fix:** Add to the system prompt:
> *"For each signal, cite the specific comment numbers (e.g., Comment 3, Comment 12) that provide supporting evidence. Each input comment should be cited by at least one signal."*

### R5: Add Reinforcement/Interrelation Step to Phase 3

**Problem:** GPT-4o treated all signals as independent, missing the causal chain that represents the highest-value strategic insight.

**Fix:** Add to Phase 3 instructions:
> *"After scoring all signals, identify any causal chains or reinforcement patterns between signals. If Signal A creates conditions that make Signal B more likely or more impactful, document the relationship. Output a reinforcement map showing how signals connect."*

### R6: Expand Pydantic Schema to Enforce Completeness

**Problem:** The current `SignalScanResult` Pydantic schema in `step1_signal_llm.py` lacks fields for several SKILL.md requirements.

**Fix:** Add these fields to the structured output models:

| Model | Missing Fields |
|-------|---------------|
| `DetectedSignal` | `supporting_comments: list[int]` |
| `InterpretedSignal` | `litmus_test: str`, `litmus_rationale: str`, `value_network_insight: str`, `alternative_explanation: str`, `key_evidence_gap: str`, `disruptive_potential: str` |
| `InterpretedSignal` (sustaining) | `sustaining_rationale: str`, `competitive_implication: str` |
| `SignalScanResult` | `reinforcement_map: dict` |
| `SignalRecommendation` | `rpv_assessment: dict`, `next_steps: list[dict]`, `experiment_type: str`, `experiment_success: str`, `experiment_failure: str` |

### R7: Consider Multi-Pass Prompting

**Problem:** GPT-4o may allocate insufficient attention to later phases when all 4 phases are requested in a single prompt.

**Fix:** Split the single-pass approach in `step1_signal_llm.py` into 2-4 sequential LLM calls:
1. **Pass 1 (Scan + Interpret):** Extract signals and classify sustaining/disruptive
2. **Pass 2 (Prioritize + Recommend):** Given the signals from Pass 1, score and recommend

This ensures each phase receives full context window attention and the model cannot shortcut later phases. Claude handled all 4 phases in one pass successfully; GPT-4o may need this decomposition to match quality.

---

## Summary

| Quality Dimension | GPT-4o | Claude Opus 4.6 | Primary Gap Driver |
|-------------------|--------|------------------|--------------------|
| Signal coverage | 4 signals, 9/20 comments | 10 signals, 20/20 comments | Signal compression / insufficient extraction |
| Classification accuracy | 1 misclassification, no new-market | Correct sustaining/disruptive split | Missing classification gate |
| Filter rigor | Names only, no assessment | Full 6-filter tables with confidence | Schema doesn't enforce filter detail |
| Priority calibration | Under-scored by 2-6 points | Evidence-grounded scoring | Missing per-signal rationale requirement |
| Structural completeness | ~40% of SKILL requirements met | ~95% of SKILL requirements met | Schema gaps + prompt compression |
| Strategic insight | Independent signal treatment | Causal chain + reinforcement map | No interrelation step in prompt |

The gap is addressable through prompt engineering (R1-R5), schema enforcement (R6), and architecture changes (R7). The most impactful single change would be **R6 — expanding the Pydantic schema** — because it forces the LLM to fill required fields regardless of its tendency to compress.
