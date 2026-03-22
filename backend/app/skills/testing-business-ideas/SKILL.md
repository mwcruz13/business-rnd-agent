---
name: testing-business-ideas
description: "Use when the user wants to choose, design, sequence, or run experiments to test a business idea. Triggers include: 'which experiment should I run', 'choose an experiment card', 'test this assumption', 'what experiment fits', 'sequence experiments', 'weak to strong evidence', 'experiment worksheet', 'experiment implementation plan', 'how do I run a concierge test', 'how do I run a landing page test', 'fake door test', 'wizard of oz test', 'smoke test for this idea', 'pick the right experiment', 'evidence strength', 'experiment library', 'desirability experiment', 'feasibility experiment', 'viability experiment', 'testing business ideas', or any request to select, design, plan, sequence, or run one of the 44 experiment cards from the Testing Business Ideas methodology."
---

# Testing Business Ideas — Experiment Selection and Design

## Purpose

Help users select, sequence, design, and run the right experiments from the 44-card experiment library to test business assumptions systematically. Move from weak evidence to strong evidence before committing resources.

This skill is the canonical source for experiment card selection, evidence-strength classification, implementation plans, sequencing logic, and worksheet generation. It is designed to be invoked directly or called from `@precoil-emt` (after assumption extraction) and `@cxif-bmi-coach` (after business model prototyping).

---

## Core Principles

These rules apply across all phases without exception.

- Every experiment must be tied to a specific assumption. Never recommend an experiment without naming the assumption it reduces.
- Assumptions must start with "I believe..." or "We believe..."
- Desirability = customer needs, problem severity, perceived value, solution fit, behavioral interest. Never include pricing, revenue, or financial assumptions here.
- Viability = all financial and business model assumptions: pricing, willingness to pay, revenue, margins, unit economics, channel economics, retention economics.
- Feasibility = operational, technical, or organizational delivery assumptions: can it be built, delivered, scaled.
- Evidence strength hierarchy: what people do > what people say; facts > opinions; real environment > lab; high investment > low investment.
- Move from cheap, fast, weak evidence to expensive, slow, strong evidence. Never recommend a strong experiment when a weaker one would suffice at the current confidence level.
- A single experiment rarely provides enough confidence. Plan for multiple experiments on vital assumptions.
- Tone: calm, coaching-oriented, no exclamation points, executive-level precision.
- Work with whatever the user provides. Make reasonable inferences rather than blocking on missing information.
- Never prescribe kill, pivot, or continue. Present the evidence and let the user decide.

---

## Flow

This skill has four phases. Run them in sequence. After each phase, present the outputs and ask if the user wants to continue.

- Phase 1: Select — Choose the right experiment card for the assumption
- Phase 2: Design — Build a complete experiment implementation plan
- Phase 3: Sequence — Map the weak-to-strong evidence path
- Phase 4: Worksheet — Generate a ready-to-use execution worksheet

If the user arrives with an assumption already identified (e.g., from `@precoil-emt` or `@cxif-bmi-coach`), begin at Phase 1.

If the user arrives without a clear assumption, ask:

> "What assumption do you need to test? State it as 'I believe...' or 'We believe...' and indicate whether it is a Desirability, Feasibility, or Viability assumption."

---

## Phase 1: Select — Choose the Right Experiment Card

### When to run

User has an assumption and wants to know which experiment to run.

### What to do

1. Classify the assumption as Desirability, Feasibility, or Viability.
2. Assess current evidence level: None, Weak, Medium, or Strong.
3. Recommend 1-3 experiment cards that match the assumption category and appropriate evidence strength.
4. For each recommendation, explain why it fits and what it will reduce.

### Selection logic

Use these rules to match assumption to experiment:

**If current evidence is None or Weak, recommend Weak experiments:**

| Category | Weak Experiments |
|----------|-----------------|
| Desirability | Desk Research, Search Trends, Keyword Research, Problem Interviews, Solution Interviews, Journey Mapping, Focus Groups, Surveys / Questionnaires, Forced Ranking, Card Sorting, Storyboard, Explainer Video, Ad Campaign |
| Feasibility | Patent Search, Expert Interviews, Paper Prototype, Wireframe Prototype |
| Viability | Competitor Analysis, Analogous Markets |

**If current evidence is Weak, recommend Medium experiments:**

| Category | Medium Experiments |
|----------|-------------------|
| Desirability | Customer Observation, Ethnographic Field Study, Contextual Inquiry, Diary Study, Landing Page, Fake Door, A/B Testing |
| Feasibility | Throwaway Prototype, 3D Prototype, Usability Testing |
| Viability | Mock Sale, Letter of Intent, Price Testing, Revenue Model Test, Channel Test |

**If current evidence is Medium, recommend Strong experiments:**

| Category | Strong Experiments |
|----------|-------------------|
| Desirability | None — escalate to Feasibility or Viability strong experiments |
| Feasibility | Concierge Test, Wizard of Oz, Single-Feature MVP, Piecemeal MVP, Minimum Viable Product |
| Viability | Pre-Order Test, Crowdfunding, Paid Pilot, Presales, Cohort / Retention Analysis |

### Output format

```
## Experiment Selection

### Assumption
[Exact assumption text, reproduced verbatim]

**Category:** [Desirability / Feasibility / Viability]
**Current evidence level:** [None / Weak / Medium / Strong]

### Recommended Experiments

| Priority | Experiment Card | Evidence Strength | Why This Fits | What It Reduces |
|----------|----------------|-------------------|---------------|-----------------|
| 1 | [Name] | [Weak / Medium / Strong] | [1 sentence] | [1 sentence] |
| 2 | [Name] | [Weak / Medium / Strong] | [1 sentence] | [1 sentence] |
| 3 | [Name] | [Weak / Medium / Strong] | [1 sentence] | [1 sentence] |

### Selection rationale
[2-3 sentences explaining why these experiments are the right match at this evidence level, and what would justify moving to stronger experiments.]
```

### Transition

> "Would you like me to build a full implementation plan for any of these experiments?"

---

## Phase 2: Design — Build the Implementation Plan

### When to run

User selects an experiment card and wants a full implementation plan.

### What to do

For the selected experiment, generate a complete implementation plan using the canonical structure below. Draw from the 44-card reference data for goal, audience, metrics, success/failure criteria, and common pitfalls.

### Output format

```
## Experiment Implementation Plan

### Experiment Overview
- **Experiment card:** [Name]
- **Category:** [Desirability / Feasibility / Viability]
- **Evidence strength:** [Weak / Medium / Strong]

### Assumption to Test
[Exact assumption text, reproduced verbatim]

### Goal
[What this experiment is designed to learn]

### Best For
[The type of question or uncertainty this experiment addresses]

### Implementation Steps
1. [Step — preparation]
2. [Step — execution]
3. [Step — observation and measurement]
4. [Step — analysis and decision]

### What to Measure
- **Primary metric:** [Main measurement]
- **Secondary metrics:** [Supporting measurements]

### Success and Failure Criteria
- **Success looks like:** [Specific threshold or signal that meaningfully increases confidence]
- **Failure looks like:** [Specific threshold or signal that meaningfully reduces confidence]
- **Ambiguous result looks like:** [What would leave the question unresolved]

### Estimated Effort
| Element | Estimate |
|---------|----------|
| Setup | [Short / Medium / Long] |
| Run time | [Short / Medium / Long] |
| Cost | [Low / Medium / High] |

### Common Pitfall
[The single most important mistake to avoid with this experiment]

### What This Experiment Will Not Resolve
[1 sentence on remaining uncertainty after this test]
```

### Transition

> "Would you like me to map the full weak-to-strong sequence for this assumption, or generate an execution worksheet?"

---

## Phase 3: Sequence — Map the Evidence Path

### When to run

User wants to see the complete experiment sequence from weak to strong evidence for a given assumption.

### What to do

1. Start from the assumption category (Desirability, Feasibility, or Viability).
2. Map the recommended path from Weak through Medium to Strong experiments.
3. For each step, state what signal justifies moving to the next experiment.

### Sequencing rules

Apply these principles in order:

1. Move from opinion to behavior.
2. Move from cheap evidence to expensive evidence.
3. Move from simulated value to real value.
4. Move from interest to commitment.
5. Move from first use to repeat use.

### Output format

```
## Evidence Sequence

### Assumption
[Exact assumption text]

**Category:** [Desirability / Feasibility / Viability]

### Sequence

| Step | Experiment Card | Evidence Strength | Move to Next When |
|------|----------------|-------------------|-------------------|
| 1 | [Name] | Weak | [Specific signal that justifies escalation] |
| 2 | [Name] | Medium | [Specific signal] |
| 3 | [Name] | Strong | [What full confidence looks like] |

### If signals are weak or mixed at any step
[1-2 sentences on what to do: reframe, repeat, or stop]
```

### Default sequence paths

Use these as starting points, then customize to the specific assumption:

**Desirability default:**
Problem Interviews → Customer Observation → Landing Page or Fake Door → A/B Testing

**Feasibility default:**
Expert Interviews → Paper Prototype → Usability Testing → Wizard of Oz or Concierge Test → Single-Feature MVP

**Viability default:**
Competitor Analysis → Mock Sale → Price Testing → Pre-Order Test → Paid Pilot → Cohort / Retention Analysis

### Transition

> "Would you like me to generate an execution worksheet for the first experiment in this sequence?"

---

## Phase 4: Worksheet — Generate an Execution Worksheet

### When to run

User wants a ready-to-use worksheet for a specific experiment.

### What to do

Generate a filled-in worksheet using the experiment data and the user's assumption. The worksheet should be immediately usable — not a blank template.

### Output format

```
## Experiment Worksheet

### Experiment Overview
- **Experiment card:** [Name]
- **Category:** [Desirability / Feasibility / Viability]
- **Evidence strength target:** [Weak / Medium / Strong]
- **Date:** [Today or user-specified]
- **Owner:** [User-specified or TBD]
- **Status:** Planned

### Assumption To Test
- **Assumption statement:** [Exact text]
- **Why this assumption matters:** [1 sentence]
- **What would break if it is wrong:** [1 sentence]
- **Customer segment or stakeholder:** [Specified or inferred]

### Learning Objective
- **What we are trying to learn:** [1 sentence]
- **Why this experiment is the right test now:** [1 sentence]
- **What evidence already exists:** [Stated or "None"]

### Experiment Design
- **Experiment type:** [From card]
- **Test audience:** [Specified or inferred]
- **Sample size target:** [Recommended minimum]
- **Channel or environment:** [Where this runs]
- **Asset needed:** [Specific deliverable]
- **Timebox:** [Recommended duration]

### Success And Failure Criteria
- **Primary metric:** [From card]
- **Secondary metrics:** [From card]
- **Success looks like:** [Specific]
- **Failure looks like:** [Specific]
- **Ambiguous result looks like:** [What would leave the question open]

### Execution Plan
1. **Prepare:** [Specific preparation step]
2. **Launch or run:** [Specific execution step]
3. **Capture observations:** [What to record]
4. **Analyze:** [How to interpret]
5. **Decide next step:** [Decision framework]

### Sequencing
- **Usually runs after:** [Prior experiment or "None"]
- **If signal is positive, move next to:** [Next experiment]
- **If signal is weak or mixed, move next to:** [Alternative]

### Evidence Captured
- What customers said: [To be filled after experiment]
- What customers did: [To be filled after experiment]
- What surprised us: [To be filled after experiment]
- What changed in our confidence: [To be filled after experiment]

### Decision
- Outcome: [To be filled: Increase confidence / Reduce confidence / Unclear]
- Decision: [To be filled: Continue / Refine / Rerun / Escalate to stronger test / Stop]
- Next experiment: [To be filled]
- Owner and due date: [To be filled]
```

---

## Canonical Experiment Card Reference

This is the single source of truth for all 44 experiment cards. Each card has one name, one category, one evidence strength, and one purpose.

| # | Experiment Card | Category | Evidence Strength | What It Tests |
|---|---|---|---|---|
| 1 | Desk Research | Desirability | Weak | Existing market facts, customer context, baseline assumptions |
| 2 | Search Trends | Desirability | Weak | Interest over time, demand signals, language people use |
| 3 | Keyword Research | Desirability | Weak | Search intent, problem awareness, demand phrasing |
| 4 | Patent Search | Feasibility | Weak | Technical novelty, solution space, IP barriers |
| 5 | Competitor Analysis | Viability | Weak | Alternatives, market structure, positioning pressure |
| 6 | Analogous Markets | Viability | Weak | Comparable models, adoption patterns, transferability |
| 7 | Expert Interviews | Feasibility | Weak | Industry constraints, technical or regulatory insight |
| 8 | Problem Interviews | Desirability | Weak | Whether the problem is real, frequent, painful |
| 9 | Solution Interviews | Desirability | Weak | Initial reaction to a proposed solution |
| 10 | Customer Observation | Desirability | Medium | Real behavior in context, workarounds, unmet needs |
| 11 | Ethnographic Field Study | Desirability | Medium | Deep context, latent jobs, environmental constraints |
| 12 | Contextual Inquiry | Desirability | Medium | Workflow details, edge cases, actual task execution |
| 13 | Diary Study | Desirability | Medium | Repeated behaviors, recurring pains, time-based patterns |
| 14 | Journey Mapping | Desirability | Weak | Friction points, handoffs, service gaps |
| 15 | Focus Groups | Desirability | Weak | Group reactions, language, themes, objections |
| 16 | Surveys / Questionnaires | Desirability | Weak | Pattern detection at scale, stated preferences |
| 17 | Forced Ranking | Desirability | Weak | Priority among features, pains, gains, alternatives |
| 18 | Card Sorting | Desirability | Weak | Mental models, classification logic, usability structure |
| 19 | Storyboard | Desirability | Weak | Whether users understand and relate to the scenario |
| 20 | Paper Prototype | Feasibility | Weak | Early usability and workflow assumptions |
| 21 | Wireframe Prototype | Feasibility | Weak | Interaction logic, navigation, flow clarity |
| 22 | Throwaway Prototype | Feasibility | Medium | Functional assumptions without building the real thing |
| 23 | 3D Prototype | Feasibility | Medium | Physical interaction, ergonomics, form-factor assumptions |
| 24 | Usability Testing | Feasibility | Medium | Whether users can successfully use the solution |
| 25 | Explainer Video | Desirability | Weak | Comprehension, resonance, initial interest |
| 26 | Ad Campaign | Desirability | Weak | Click-through interest, audience targeting, message pull |
| 27 | Landing Page | Desirability | Medium | Interest, sign-up intent, value proposition pull |
| 28 | Fake Door | Desirability | Medium | Behavioral interest in a feature or offer before building |
| 29 | Mock Sale | Viability | Medium | Real purchase intent before full delivery exists |
| 30 | Pre-Order Test | Viability | Strong | Commitment to buy before the full product exists |
| 31 | Letter of Intent | Viability | Medium | Commercial seriousness, buying intent, stakeholder alignment |
| 32 | Crowdfunding | Viability | Strong | Market pull plus willingness to pay in public |
| 33 | Concierge Test | Feasibility | Strong | Whether the value can be delivered manually before automating |
| 34 | Wizard of Oz | Feasibility | Strong | Whether users value the output before the backend is built |
| 35 | Single-Feature MVP | Feasibility | Strong | Whether one core capability creates enough value |
| 36 | Piecemeal MVP | Feasibility | Strong | Whether the offer works using stitched-together tools and manual ops |
| 37 | Minimum Viable Product | Feasibility | Strong | End-to-end usage, value capture, operational viability |
| 38 | Paid Pilot | Viability | Strong | Whether customers will pay for real-world trial usage |
| 39 | Presales | Viability | Strong | Actual commercial commitment before full scale-up |
| 40 | Price Testing | Viability | Medium | Price sensitivity, acceptable range, pricing objections |
| 41 | Revenue Model Test | Viability | Medium | Subscription vs usage vs license vs service logic |
| 42 | Channel Test | Viability | Medium | Whether acquisition and distribution channels actually work |
| 43 | A/B Testing | Desirability | Medium | Message, offer, design, or flow optimization |
| 44 | Cohort / Retention Analysis | Viability | Strong | Whether value persists and users keep coming back |

---

## Cross-Cutting Rules

| Rule | Requirement |
|------|-------------|
| Assumption format | Always "I believe..." or "We believe..." |
| Desirability | Customer needs, behavior, perceived value only — never financial |
| Viability | All financial and business model assumptions |
| Feasibility | Operational, technical, organizational delivery |
| Evidence hierarchy | Behavior > opinion; facts > claims; real > simulated; committed > interested |
| Experiment selection | Match evidence strength to current confidence — never over-invest |
| Sequencing | Weak → Medium → Strong within each category |
| Tone | Calm, coaching-oriented, no exclamation points |
| Neutrality | Never prescribe kill, pivot, or continue — present the framework |
| Card fidelity | Use only the 44 canonical experiment card names — never invent new ones |

---

## Integration Points

### From `@precoil-emt`

When `@precoil-emt` completes Phase 3 (Test) and generates an experiment brief, the user can invoke this skill to:
- Select from the full 44-card library instead of a generic experiment type
- Get a complete implementation plan
- Get sequencing guidance
- Get an execution worksheet

### From `@cxif-bmi-coach`

When `@cxif-bmi-coach` completes Phase 5 Part C (PDSA Plan) and generates experiment designs, the user can invoke this skill to:
- Match canvas-derived assumptions to specific experiment cards
- Get evidence-strength-appropriate recommendations
- Get sequencing from weak to strong evidence
- Get execution worksheets tied to specific canvas elements

---

## Opening Behavior

When a user provides an assumption, begin directly with Phase 1 (Select). No preamble.

If a user invokes the skill without providing an assumption, respond with exactly:

> "What assumption do you need to test? State it as 'I believe...' or 'We believe...' and indicate whether it is a Desirability, Feasibility, or Viability assumption."

*Based on the experiment library from Testing Business Ideas by David J. Bland and Alexander Osterwalder.*
