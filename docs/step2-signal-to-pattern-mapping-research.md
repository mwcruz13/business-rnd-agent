# Step 2 Signal-to-Pattern Mapping — Research Analysis & Strategy

**Date:** 2026-03-25  
**Status:** Research / Pre-implementation  
**Author:** BMI Consultant App Development Team

---

## 1. Problem Statement

The current `step2_pattern.py` uses a hardcoded `pattern_name = "Market Explorers"` for every INVENT-direction signal, regardless of the signal's zone, classification, disruption filter results, or contextual details. This produces a single recommendation every time, which undermines the purpose of pattern matching.

The real question is: **given a disruption signal classified by the SOC Radar (Christensen framework), which Strategyzer business model patterns (INVENT and/or SHIFT) are most likely to produce an effective response?**

This document analyzes the three source taxonomies, identifies theoretical alignment bridges, evaluates algorithmic approaches, and recommends a strategy.

---

## 2. Taxonomy Inventory

### 2.1 SOC Radar — Signal Zones (Christensen, "Seeing What's Next")

The diagnostic framework. Answers: *"What type of disruption is happening?"*

| # | Zone | Core Idea |
|---|------|-----------|
| 1 | **Nonconsumption** | People who need the outcome but can't access, afford, or use today's solutions |
| 2 | **Overserved Customers** | Customers paying for performance they don't use or value |
| 3 | **Low-End Foothold** | Simpler, cheaper alternatives gaining traction from below |
| 4 | **New-Market Foothold** | Solutions creating demand where none existed before |
| 5 | **Business Model Anomaly** | Entrants using fundamentally different cost/channel/revenue models |
| 6 | **Enabling Technology** | Technologies that reduce barriers to entry or change the cost curve |
| 7 | **Regulatory / Policy Shift** | Rule changes that open or close market access |

**Classification types:** Sustaining, Disruptive — Low-End, Disruptive — New-Market

**Disruption Filters (6):** Asymmetric Motivation, Asymmetric Skills, Trajectory, Performance Overshoot, Barrier Removal, Business Model Conflict

### 2.2 Strategyzer INVENT Patterns (Osterwalder, "The Invincible Company")

The generative framework for **new growth**. Answers: *"What new business model architecture could exploit this disruption?"*

Organized into three disruption categories, 9 patterns, 27 flavors:

**Frontstage Disruption (customer-facing)**

| Pattern | Strategic Imperative | Key Flavors |
|---------|---------------------|-------------|
| **Market Explorers** | Unlock untapped/underserved markets | Visionaries, Repurposers, Democratizers |
| **Channel Kings** | Radically change how to reach customers | Disintermediators, Opportunity Builders |
| **Gravity Creators** | Lock in customers / create switching costs | Stickiness Scalers, Superglue Makers |

**Backstage Disruption (operations/resources)**

| Pattern | Strategic Imperative | Key Flavors |
|---------|---------------------|-------------|
| **Resource Castles** | Build hard-to-copy competitive moats | User Base Castles, Platform Castles, IP Castles, Brand Castles |
| **Activity Differentiators** | Radically reconfigure activities | Efficiency Disruptors, Speed Masters, Sustainability Masters, Build-to-Order |
| **Scalers** | Grow faster than conventional models | Delegators, Licensors, Franchisors |

**Profit Formula Disruption**

| Pattern | Strategic Imperative | Key Flavors |
|---------|---------------------|-------------|
| **Revenue Differentiators** | Innovative value capture / pricing | Recurring Revenue, Bait & Hook, Freemium, Subsidizers |
| **Cost Differentiators** | Game-changing cost structure | Resource Dodgers, Technologists, Low Cost |
| **Margin Masters** | Optimize margin through focus | Contrarians, High Enders |

> **Data quality note:** The `strategyzer-pattern-library.json` currently stores only pattern names (8 verified + 1 partial). It does not contain descriptions, trigger questions, or flavors. The full text resides in `assistant/docs/The Invent Pattern Library.txt`. This gap must be closed for any LLM-based approach.

### 2.3 Strategyzer SHIFT Patterns (Osterwalder, "The Invincible Company")

The generative framework for **incumbent transformation**. Answers: *"How should an incumbent transform its existing business model?"*

12 shift patterns across three categories:

**Value Proposition Shifts**

| # | Shift | Core Transformation |
|---|-------|---------------------|
| 1 | **Product → Recurring Service** | Transactional sales → predictable recurring revenue |
| 2 | **Low Tech → High Tech** | Labor-intensive → technology-based scaling |
| 3 | **Sales → Platform** | Value chain → platform ecosystem with network effects |

**Frontstage Driven Shifts**

| # | Shift | Core Transformation |
|---|-------|---------------------|
| 4 | **Niche Market → Mass Market** | Simplify VP for larger market |
| 5 | **B2B → B2(B2)C** | Hidden supplier → consumer-relevant brand |
| 6 | **Low Touch → High Touch** | Standardized → customized premium experience |

**Backstage Driven Shifts**

| # | Shift | Core Transformation |
|---|-------|---------------------|
| 7 | **Dedicated Resources → Multi-Usage** | One-purpose resource → multiple value propositions |
| 8 | **Asset Heavy → Asset Light** | High fixed costs → variable costs + service focus |
| 9 | **Closed → Open Innovation** | Internal R&D → external R&D and IP sharing |

**Profit Formula Driven Shifts**

| # | Shift | Core Transformation |
|---|-------|---------------------|
| 10 | **High Cost → Low Cost** | Reconfigure activities/resources for disruptive pricing |
| 11 | **Transactional → Recurring Revenue** | One-time sales → subscription/recurring model |
| 12 | **Conventional → Contrarian** | Eliminate costly elements, focus on what customers love |

> **Data quality note:** The `strategyzer-pattern-library.json` has `shift.patterns: []` (empty). The full text resides in `assistant/docs/The Business Model Shifts Library.txt`. This must be populated before any automated SHIFT recommendation.

---

## 3. Why a Deterministic 1:1 Mapping Fails

### 3.1 The Frameworks Operate at Different Levels of Abstraction

| Framework | Question Answered | Level |
|-----------|-------------------|-------|
| Christensen (SOC Radar) | "What type of disruption is this?" | **Diagnostic** — classifies the signal |
| Osterwalder INVENT | "What new business model could exploit it?" | **Generative** — creates new growth |
| Osterwalder SHIFT | "How should the incumbent transform?" | **Generative** — transforms existing model |

A diagnostic classification doesn't determine a single generative response. **The same signal zone can warrant different patterns depending on the signal's specific mechanism, the incumbent's current model, and whether the response is offensive or defensive.**

### 3.2 Worked Example: Why "Nonconsumption" ≠ "Market Explorers"

Consider three nonconsumption signals:

1. **"Rural farmers can't access crop insurance because no agent visits them"**
   - Barrier: physical access → **Channel Kings** (Opportunity Builders) or **Scalers** (Delegators)
   - NOT Market Explorers — the market exists, the channel doesn't

2. **"Small businesses don't use ERP because current solutions cost $500K+"**
   - Barrier: price/complexity → **Cost Differentiators** (Resource Dodgers) or **Market Explorers** (Democratizers)
   - Multiple patterns apply, depending on approach

3. **"Nobody has ever offered real-time translation for sign language in video calls"**
   - Barrier: the solution doesn't exist yet → **Market Explorers** (Visionaries) + **Resource Castles** (IP Castles)
   - Competition is about technology moats, not just market creation

All three are "Nonconsumption" signals, but they point to completely different patterns. **The signal zone is necessary but not sufficient to select a pattern.**

### 3.3 The Role of Disruption Filters

The 6 disruption filters from the SOC Radar provide critical context that affects pattern selection:

| Filter | What It Reveals | Pattern Affinity |
|--------|----------------|------------------|
| **Asymmetric Motivation** | Incumbent *chooses* not to respond (unattractive margins) | Revenue Differentiators, Cost Differentiators — target spaces incumbents deliberately ignore |
| **Asymmetric Skills** | Entrant has capabilities incumbent can't replicate | Resource Castles, Activity Differentiators — build on unique capabilities |
| **Trajectory** | Entrant is improving fast enough to go mainstream | Scalers, Channel Kings — speed and reach matter |
| **Performance Overshoot** | Incumbent exceeds what mainstream customers need | Cost Differentiators, Margin Masters (Contrarians) — strip to essentials |
| **Barrier Removal** | Entrant removes skill/wealth/access barriers | Market Explorers (Democratizers), Channel Kings, SHIFT: Niche→Mass |
| **Business Model Conflict** | Responding would cannibalize incumbent's existing model | Revenue Differentiators, SHIFT: Product→Service, Sales→Platform |

**Insight: The mapping is at minimum 2-dimensional** — (signal zone × disruption filter) → pattern shortlist. It's not (signal zone) → single pattern.

---

## 4. Theoretical Alignment Bridges

### 4.1 INVENT vs SHIFT Direction Decision

This part IS reasonably deterministic based on zone + classification:

| Signal Profile | Direction | Reasoning |
|---|---|---|
| Disruptive — New-Market + (New-Market Foothold, Nonconsumption) | **INVENT** | Creating demand where none exists → build a new growth engine |
| Disruptive — Low-End + (Overserved Customers, Low-End Foothold) | **SHIFT** | Existing market being attacked from below → transform existing model |
| Business Model Anomaly | **INVENT or SHIFT** | Depends on whether the anomaly represents an offensive opportunity (INVENT) or a threat requiring defensive transformation (SHIFT) |
| Enabling Technology | **INVENT or SHIFT** | Depends on whether the incumbent's model can absorb the tech (SHIFT) or a new model is needed (INVENT) |
| Regulatory / Policy Shift | **INVENT or SHIFT** | Opens new market → INVENT. Forces compliance transformation → SHIFT |
| Sustaining | **SHIFT** | Improvements within existing model → transform, don't reinvent |

**Takeaway:** Direction selection can remain semi-deterministic, but the ambiguous zones (Enabling Technology, Business Model Anomaly, Regulatory Shift) require reasoning about the signal's specifics.

### 4.2 Signal Zone → INVENT Pattern Affinity Matrix (Draft)

Each cell represents a qualitative affinity: HIGH (strong theoretical alignment), MED (plausible depending on context), LOW (unlikely to be the right response).

| Zone | Market Explorers | Channel Kings | Gravity Creators | Resource Castles | Activity Diff. | Scalers | Revenue Diff. | Cost Diff. | Margin Masters |
|---|---|---|---|---|---|---|---|---|---|
| **Nonconsumption** | HIGH | MED | LOW | LOW | MED | MED | MED | HIGH | LOW |
| **Overserved Customers** | LOW | LOW | LOW | LOW | MED | MED | LOW | HIGH | HIGH |
| **Low-End Foothold** | MED | MED | LOW | LOW | HIGH | MED | MED | HIGH | MED |
| **New-Market Foothold** | HIGH | MED | LOW | MED | LOW | MED | MED | LOW | LOW |
| **Business Model Anomaly** | MED | LOW | MED | MED | MED | LOW | HIGH | MED | MED |
| **Enabling Technology** | MED | MED | LOW | HIGH | HIGH | HIGH | MED | MED | LOW |
| **Regulatory / Policy Shift** | MED | MED | MED | HIGH | MED | LOW | MED | LOW | LOW |

**Reading this matrix:** For a "Nonconsumption" signal, the system should recommend exploring Market Explorers and Cost Differentiators (both HIGH), with Activity Differentiators, Scalers, Revenue Differentiators, and Channel Kings as secondary options (MED).

### 4.3 Signal Zone → SHIFT Pattern Affinity Matrix (Draft)

| Zone | Prod→Svc | LowTech→HighTech | Sales→Platform | Niche→Mass | B2B→B2C | LowTouch→HighTouch | Dedicated→MultiUse | Heavy→Light | Closed→Open | HighCost→Low | Trans→Recurring | Conv→Contrarian |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Overserved** | MED | LOW | LOW | MED | LOW | LOW | LOW | MED | LOW | HIGH | MED | HIGH |
| **Low-End** | LOW | LOW | LOW | HIGH | LOW | LOW | LOW | HIGH | LOW | HIGH | MED | HIGH |
| **Enabling Tech** | MED | HIGH | MED | MED | LOW | LOW | MED | MED | HIGH | MED | MED | LOW |
| **Biz Model Anomaly** | HIGH | MED | HIGH | MED | MED | LOW | MED | MED | MED | MED | HIGH | MED |
| **Regulatory Shift** | MED | MED | LOW | MED | LOW | LOW | LOW | LOW | MED | LOW | LOW | LOW |

### 4.4 Key Insight: The Affinity Is Graduated, Not Binary

For any signal zone, typically **2–4 INVENT patterns** and **2–4 SHIFT patterns** have HIGH affinity. The right selection among those finalists depends on:

1. **Signal-specific details**: the "observable behavior", "watch_for" evidence, and signal description generated in Step 1
2. **Disruption filter results**: which of the 6 filters the signal passes (especially Asymmetric Motivation, Performance Overshoot, Barrier Removal)
3. **Incumbent context**: what the current business model looks like (not available at Step 2 today, but could be captured as upstream state)
4. **Pattern trigger questions**: each pattern has a strategic trigger question — alignment between the signal evidence and these questions drives selection

---

## 5. Approach Evaluation

### 5.1 Option A: Weighted Affinity Matrix (Deterministic)

**Mechanism:** Encode the affinity matrices from §4.2 and §4.3 as static data. For each signal, combine (zone affinity) + (disruption filter bonus) to produce a scored shortlist. Return the top 2–3 patterns.

**Pros:**
- Fast, deterministic, testable with unit tests
- No LLM cost per invocation
- Transparent — consultant can audit why a pattern was recommended

**Cons:**
- Cannot reason about signal-specific details (the description text, the observable behavior)
- Misses nuanced cases where two zones overlap or filter combinations create unexpected affinities
- Requires manual maintenance when new patterns are added
- Would still recommend wrong patterns in edge cases — the matrix is an approximation

**Verdict:** Viable as a **shortlisting layer** but not sufficient as a final selection mechanism.

### 5.2 Option B: LLM Agent Skill (Fully Non-Deterministic)

**Mechanism:** Convert Step 2 into an LLM-backed node. Give it the full signal output from Step 1, the pattern library text (with descriptions and trigger questions), and ask it to reason about alignment.

**Pros:**
- Can reason about signal descriptions, trigger questions, and contextual nuance
- Handles ambiguous zones (Enabling Technology, Business Model Anomaly) well
- Can explain its rationale in consultant-friendly language
- Naturally handles the "mixed signal" case where both INVENT and SHIFT apply

**Cons:**
- Non-deterministic — same input may produce different output
- Harder to test with BDD (assertions on LLM output are fragile)
- Full pattern library context is large (~4K tokens for INVENT + ~3K for SHIFT) — adds cost
- Risk of hallucinating pattern names or flavors not in the library

**Verdict:** Good reasoning quality but testing and reliability concerns for production use.

### 5.3 Option C: Hybrid — Affinity Shortlist + LLM Final Selection (Recommended)

**Mechanism:** Two-phase approach:

1. **Phase 1 (Deterministic):** The affinity matrix produces a ranked shortlist of 2–4 HIGH/MED patterns based on zone + disruption filters. This is fast, testable, and transparent.

2. **Phase 2 (LLM Reasoning):** The LLM receives ONLY the shortlisted patterns' descriptions and trigger questions (small context, ~800 tokens) plus the signal details. It selects the best 1–2 patterns from the shortlist and generates a rationale.

**Pros:**
- Deterministic filtering narrows the LLM's search space → fewer hallucinations
- The shortlisting step is unit-testable (given zone X and filter Y, the shortlist contains patterns A, B, C)
- The LLM step handles contextual nuance with a focused prompt
- Modular — if the LLM call fails or times out, the shortlist alone is a reasonable fallback
- Supports the checkpoint model — consultant still reviews at checkpoint_1_5

**Cons:**
- More complex to implement (two phases, two pieces of logic)
- Adds an LLM call where there currently isn't one (cost for Step 2)
- Requires the pattern library to store descriptions/trigger questions (data enrichment needed)

**Verdict:** **Recommended approach.** Best balance of quality, testability, and maintainability.

---

## 6. Recommended Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 1 Output (interpreted_signals, priority_matrix)           │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Phase 1: Deterministic Shortlister                              │
│                                                                  │
│  Input:  best_signal.zone, best_signal.classification,           │
│          disruption_filter_results (from Step 1)                 │
│                                                                  │
│  Logic:  affinity_matrix[zone] → base scores per pattern         │
│          + filter_bonuses[filter] → adjusted scores              │
│          → direction = INVENT | SHIFT | BOTH                    │
│          → shortlist = top 3-4 patterns by score                 │
│                                                                  │
│  Output: direction, pattern_shortlist (ranked)                   │
│  Testability: 100% deterministic, full BDD coverage              │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  Phase 2: LLM Pattern Reasoner (Agent Skill)                    │
│                                                                  │
│  Input:  signal details (zone, classification, description,      │
│          observable_behavior, evidence_fields),                   │
│          shortlisted pattern descriptions + trigger questions,   │
│          disruption filter rationale                             │
│                                                                  │
│  Prompt: "Given this disruption signal, which of these           │
│           shortlisted patterns best addresses the opportunity?   │
│           Select 1-2. Explain using signal evidence and the      │
│           pattern's trigger question."                           │
│                                                                  │
│  Output: selected_patterns, rationale, confidence, evidence_used │
│  Testability: Structural assertions (output schema), not content │
│  Fallback: If LLM fails → return full shortlist as suggestion    │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│  checkpoint_1_5: Consultant reviews pattern recommendation       │
│  Can override selected_patterns, add/remove patterns,            │
│  change direction                                                │
└──────────────────────────────────────────────────────────────────┘
```

### 6.1 Why This Works for BDD Testing

- **Phase 1 tests** are pure unit tests: "Given signal zone=X and filter=Y, the shortlist MUST contain pattern Z." Deterministic. No flakiness.
- **Phase 2 tests** validate the structure: "The output MUST have `selected_patterns` as a list, `rationale` as non-empty string, each pattern MUST be from the shortlist." We don't assert *which* pattern the LLM picks — that's the consultant's checkpoint job.
- **Existing BDD contract** (`step2-pattern-matcher.feature`) defines the behavioral expectation. The contract doesn't need to change — the *production code* improves to meet it better.

---

## 7. Prerequisites & Open Items

### 7.1 Data Enrichment Required

Before implementing Phase 2, the pattern library JSON must be enriched:

| Item | Current State | Required State |
|------|--------------|----------------|
| INVENT pattern descriptions | `assistant/docs/The Invent Pattern Library.txt` (unstructured) | Structured in JSON with name, description, trigger_question, flavors[] |
| INVENT pattern count | 8 verified + 1 partial in JSON | 9 verified with correct names |
| SHIFT patterns | Empty in JSON (`shift.patterns: []`) | 12 patterns with name, description, strategic_reflection |
| Pattern library naming | `Activity Scalers` vs `Scalers` vs `Activity Differentiators` discrepancy | Reconciled against book |
| Disruption filter results | Not currently passed from Step 1 to Step 2 | Added to state schema or computed in Step 2 |

### 7.2 Name Reconciliation Issue

The JSON has `"Activity Scalers"` but the book reference has two separate patterns:
- **Activity Differentiators** (section 2.2) — Efficiency Disruptors, Speed Masters, Sustainability Masters, Build-to-Order
- **Scalers** (section 2.3) — Delegators, Licensors, Franchisors

This needs to be resolved against the primary source (The Invincible Company book) before the affinity matrix can be finalized.

### 7.3 State Schema Consideration

Currently Step 1 produces `interpreted_signals` and `priority_matrix`. For the affinity matrix to use disruption filter results, one of:
- (a) Step 1 must emit `disruption_filter_results` per signal (preferred — the SOC Radar already runs these filters)
- (b) Step 2 must re-derive filter results from the signal evidence fields

Option (a) is cleaner and avoids redundant computation.

### 7.4 Confidence Calibration

The current code always outputs `"Confidence: medium"`. The hybrid approach should calibrate confidence based on:
- How many HIGH-affinity patterns matched (1 = high confidence, 3+ = low — too many options)
- How strongly the disruption filters converge on a single pattern
- Whether the LLM's explanation shows strong alignment with trigger questions

---

## 8. Implementation Sequence (Proposed)

If this analysis is approved, the implementation would proceed in these stages:

| Stage | Description | Scope |
|-------|-------------|-------|
| **S1** | Enrich `strategyzer-pattern-library.json` with INVENT descriptions + trigger questions + flavors | Data only, no code |
| **S2** | Populate SHIFT patterns in the JSON | Data only, no code |
| **S3** | Reconcile pattern naming (Activity Scalers vs Activity Differentiators vs Scalers) | Data audit |
| **S4** | Build the deterministic affinity matrix as a Python module (`pattern_affinity.py`) | New module, unit tests |
| **S5** | Verify disruption filter data flows from Step 1 → Step 2 (or add it) | State schema review |
| **S6** | Create LLM-backed pattern reasoning as an Agent Skill prompt | Prompt engineering |
| **S7** | Integrate Phase 1 + Phase 2 into `step2_pattern.py` with fallback | Production code change |
| **S8** | Write BDD scenarios for shortlisting + structural output validation | Feature file + step defs |

Stages S1–S3 are data work with no code risk. S4–S5 are deterministic code with full test coverage. S6–S8 add the LLM reasoning layer.

---

## 9. Alternative Considered: Pure Skill Approach (No Affinity Matrix)

If we determine that even the affinity matrix is too rigid, the entire Step 2 could become a pure LLM Agent Skill:

- Input: full Step 1 output + full pattern library (INVENT + SHIFT descriptions)
- Skill prompt: detailed reasoning instructions similar to `step2_pattern_matcher.md` but with all pattern trigger questions embedded
- Output: direction, selected_patterns, rationale

**Risk:** Token cost is higher (~7K tokens of pattern context per call), and the LLM could hallucinate pattern names. This is mitigable with post-processing validation (assert `selected_patterns ⊆ known_patterns`).

**When to choose this:** If the affinity matrix produces consistently incorrect shortlists during S4 testing — meaning the theoretical alignment bridges in §4.2/§4.3 are too unreliable.

The hybrid approach keeps the pure-skill path as a fallback: if Phase 1 adds no value, we remove it and Phase 2 sees all patterns.

---

## 10. Summary & Decision Request

| Question | Recommendation |
|----------|---------------|
| Can we build a deterministic 1:1 zone→pattern mapping? | **No.** The theoretical relationship is many-to-many and context-dependent. |
| Can we build a deterministic shortlisting layer? | **Yes.** A zone×filter affinity matrix reliably narrows 21 patterns to 3-4 candidates. |
| Do we need an LLM for final selection? | **Yes.** Signal-specific reasoning (descriptions, trigger questions) requires language understanding. |
| Should we implement this as an Agent Skill? | **Phase 2 yes, Phase 1 no.** The shortlisting remains deterministic code. |
| What data work is required first? | Enrich JSON with pattern descriptions, populate SHIFT patterns, reconcile naming. |
| Does this change the behavioral contract? | **No.** The BDD feature file expectations remain the same — Step 2 recommends patterns. The *quality* of recommendations improves. |

**Recommended next step:** Approve or refine this strategy, then begin with S1–S3 (data enrichment) which is risk-free and unblocks everything else.
