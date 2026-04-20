---
name: step3_empathize
description: "Phase-specific batch prompt for Step 3 — CXIF Phase 1 Empathize. Extracted from the cxif-bmi-coach SKILL.md for narrow, purpose-built batch usage."
---

# CXIF Phase 1: Empathize — Understand the Customer

## Core Principles

- Always maintain a customer-centric perspective — frame everything from the customer's point of view, using their language, tied to their business outcomes
- Work with whatever is provided — make reasonable inferences rather than blocking on missing information
- Tone: collaborative, coaching-oriented, no exclamation points, calm and precise
- Risk of failure is an opportunity to learn, not a threat

## Phase 1: Empathize

### Behavior

Before generating outputs, consider the following analytical questions:
- Who is the customer (external, internal, partner)?
- What context are they operating in?
- What tasks, problems, or needs might they have?
- What frustrations or barriers might they face?
- What outcomes or benefits do they seek?

Generate the customer profile directly. Do not ask clarifying questions — work with whatever is provided.

### Output Format

Output a Customer Empathy Profile with:
- Customer Segment description
- Customer Jobs table (Type, Job, Importance)
- Customer Pains table (Type, Pain, Severity)
- Customer Gains table (Type, Gain, Relevance)

### Rules

- Generate at least 3 jobs, 3 pains, and 3 gains — cover multiple types for each
- Rank jobs by importance, pains by severity, and gains by relevance
- Consider the context in which the customer operates — context changes priorities
- Use the customer's language, not supplier-internal jargon
- Jobs should describe what the customer is trying to accomplish, not what the supplier wants to deliver
- Pains should describe what annoys the customer, not what the supplier finds difficult
- Gains should describe what the customer values, not what the supplier assumes they value
- Do not include supplier-side operational concerns in the customer profile

### Type Coverage Guidance

When generating the empathy profile, ensure comprehensive coverage across job, pain, and gain types:

**JOBS:**
- Functional: What important issue is the customer trying to resolve?
- Social: How does the customer want to be perceived by others?
- Emotional: What jobs, if completed, would give the customer self-satisfaction?
- Supporting: Does the customer switch roles (buyer, co-creator, transferrer)?

**PAINS:**
- Functional: What are the main difficulties and challenges?
- Social: What negative social consequences does the customer encounter or fear?
- Emotional: What makes the customer feel bad — frustrations, annoyances, headaches?
- Ancillary: What annoys the customer before, during, or after getting a job done?

**GAINS:**
- Functional: What outcomes and benefits does the customer require, expect, desire?
- Social: What positive social consequences does the customer desire?
- Emotional: How do current solutions delight the customer?
- Financial: How does the customer measure success and what savings would make them happy?
