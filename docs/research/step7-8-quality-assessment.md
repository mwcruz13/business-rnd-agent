# Step 7–8 Quality Assessment: Research Findings

**Date:** 2026-04-18
**Scope:** Evaluate Steps 7 (Assumptions & Risk Map) and 8 (Experiment Selection & PDSA Plans) against the Precoil EMT methodology and the 44-card Testing Business Ideas library.
**Evidence:** End-to-end workflow runs across multiple VoC inputs (HBM-SSD supply chain disruption, firmware assessment self-serve, others).

---

## 1. Observed Symptoms

Across every workflow run tested, Steps 7–8 produce output with the same structural characteristics:

- 3–5 experiments recommended, all starting from Weak evidence
- Identical experiment paths for every assumption within the same DVF category
- Generic success/failure criteria (70%/40% thresholds) regardless of assumption content
- Boilerplate rationale that reads the same across very different business contexts
- Consultants receive limited options — no cards to choose from, no alternative paths

---

## 2. Root Cause Analysis

### 2.1 Step 7: Fixed 3×3 Grid

The Step 7 prompt (`backend/app/prompts/step7_risk_map.md`) enforces:

- **Exactly 3 assumptions per DVF category** (9 total, always)
- "At least 1 assumption per category should be Test first"
- "Err toward Test first for high-impact assumptions where evidence strength is ambiguous"

**Effect:** A firmware assessment with narrow scope and a multi-signal HBM supply chain disruption both produce the same 3×3 grid. The prompt cannot scale the assumption count to match VoC richness.

### 2.2 Step 8: Zero LLM Reasoning, Hardcoded Paths

`backend/app/nodes/step8_pdsa.py` is **entirely deterministic** — no LLM call. It performs three mechanical operations:

1. Parses Step 7's markdown for "Test first" rows
2. Looks up a hardcoded 3-card path per DVF category (`PATH_BY_CATEGORY`)
3. Templates the same boilerplate brief, plan, and worksheet for each

**Hardcoded paths:**

| Category | Card 1 (Weak) | Card 2 (Medium) | Card 3 |
|----------|---------------|-----------------|--------|
| Desirability | Problem Interviews | Landing Page | Fake Door (Medium) |
| Feasibility | Expert Interviews | Throwaway Prototype | Wizard of Oz (Strong) |
| Viability | Competitor Analysis | Mock Sale | Pre-Order Test (Strong) |

### 2.3 Card Library Utilization

```
44-Card Library Distribution:
  Desirability    Weak     = 13    Medium =  7    Strong =  0
  Feasibility     Weak     =  4    Medium =  3    Strong =  5
  Viability       Weak     =  2    Medium =  5    Strong =  5

Cards used by PATH_BY_CATEGORY:  9 / 44  (20.5%)
Cards in EXPERIMENT_MATRIX:     23 / 44  (52.3%) — defined but never invoked
Cards never reachable:          35 / 44  (79.5%)
```

The `EXPERIMENT_MATRIX` with richer options per evidence level exists in the code but is explicitly commented as "supports evidence-aware selection in future releases" — it is never called.

### 2.4 No Evidence Audit

Every assumption enters Step 8 with `"Current evidence level: None"` hardcoded. The VoC data from Step 1 and the customer profile from Step 3 may already contain weak evidence for some assumptions, but this is never assessed.

### 2.5 No Desirability Strong-Evidence Escalation

The 44-card library has **zero** Strong-evidence Desirability cards. The Desirability path peaks at Medium (Fake Door). This is a library design characteristic, not a bug — but the current output does not explain this ceiling to the consultant.

---

## 3. Contradiction: Library Identity

The `precoil-emt.agent.md` Phase 3 output template includes:

> If you want access to the full library: [precoil.com/library](https://www.precoil.com/library)

But the workflow does **not** use the Precoil library. It uses the `@testing-business-ideas` 44-card experiment library (`backend/app/patterns/experiment-library.json`), sourced from David J. Bland and Alexander Osterwalder's *Testing Business Ideas* methodology.

This creates two problems:

1. **Attribution confusion:** The CTA directs the consultant to an external commercial library they are not using, while the actual library powering their recommendations is already embedded in the system.
2. **Trust erosion:** If a consultant follows the link and sees different card names, sequencing, or evidence levels than what the workflow produced, it undermines confidence in the tool.

The agent CTA should reference the embedded 44-card library and the `@testing-business-ideas` agent, not `precoil.com/library`. The Precoil EMT methodology (Extract → Map → Test) is correctly attributed — it is the experiment card library that is misreferenced.

---

## 4. Comparison Against Precoil EMT Agent Standard

The `precoil-emt.agent.md` Phase 3 (Test) specifies that experiment briefs should:

| Requirement | Agent Spec | Current Step 8 |
|-------------|-----------|-----------------|
| Context-specific learning objectives | "What would this experiment confirm or contradict?" — 1-2 sentences tied to the assumption | Generic: "tests whether the team should increase confidence in the assumption that..." |
| Specific success/failure thresholds | "Specific enough that a reasonable observer would agree they change confidence" | Boilerplate: 70% success / 40% failure for everything |
| Assumption-aware card selection | "1-3 specific experiment card names that match the assumption category and appropriate evidence strength" | Same 3 cards per category regardless of assumption content |
| Evidence strength matching | "Match evidence strength to current confidence level" | Always starts at "None" / Weak |
| Remaining uncertainty | Specific to what won't be resolved | Generic template text |

---

## 5. Structural Recommendations

### Short-term (Quick Win)
Replace `PATH_BY_CATEGORY` with `EXPERIMENT_MATRIX` and add a single LLM call to select from the matrix based on assumption content. This expands coverage from 9 to 23 cards and differentiates recommendations within the same DVF category.

### Medium-term (Full Decomposition)
Break Step 8 into sub-steps:
- **8a — Evidence Audit:** Assess existing evidence from VoC and prior steps
- **8b — Card Selection:** LLM-powered selection from full 44-card library
- **8c — Path Sequencing:** Build assumption-specific escalation paths
- **8d — Brief & Worksheet Generation:** Context-specific success/failure criteria

### Step 7 Adjustments
- Allow 2–5 assumptions per category based on VoC complexity
- Add a "strength of VoC evidence" field per assumption
- Let the LLM assess whether some categories genuinely have fewer testable assumptions

---

## 6. Analysis Script

The coverage analysis was performed by `backend/scripts/analyze_step8_coverage.py`. Run:

```bash
docker compose exec bmi-backend python backend/scripts/analyze_step8_coverage.py
```
