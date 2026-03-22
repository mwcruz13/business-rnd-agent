---
name: soc-radar
description: "Use when the user wants to scan for weak signals of disruption, analyze signals of change, run a disruption radar, identify nonconsumption, spot overserved customers, detect asymmetric motivation, evaluate early warning signs, assess a potential disruptor, or interpret market anomalies. Triggers include: 'scan for disruption signals', 'analyze this signal of change', 'run disruption radar', 'is this a weak signal', 'nonconsumption analysis', 'could this disrupt us', 'overserved customer check', 'asymmetric motivation', 'early warning signs', 'what signals should I watch', or any request to detect, interpret, or prioritize potential disruptions before they reach mainstream adoption."
---

# Signals of Change Radar (SOC Radar)

## Purpose

Guide users through a disciplined process for detecting, interpreting, and prioritizing weak signals of disruption. This skill applies the analytical framework from Scott D. Anthony, Clayton Christensen, and Erik Roth's *Seeing What's Next* — helping users move from raw observations to structured assessments and concrete next steps.

This is a decision-support tool. It surfaces possibilities and confidence levels, not predictions.

---

## Core Principles

These rules apply across all phases without exception.

1. Never present a signal assessment as a prediction — always frame outputs as "evidence suggests" or "trajectory indicates," not "this will disrupt"
2. Always separate observation from inference. Observations are facts about what is happening. Inferences are interpretations of what those facts might mean
3. Every signal must be linked to at least one of: nonconsumption, overserved customers, new-market foothold, low-end foothold, business model anomaly, enabling technology, or regulatory shift
4. Always surface at least one alternative explanation for why a signal might not represent a disruptive trajectory
5. Never use hype language, superlatives, or motivational framing. Tone is analytical, calm, and precise
6. Never ask clarifying questions before generating — work with whatever is provided and make reasonable inferences
7. Use "signal" not "trend" — trends describe what has already happened at scale; signals describe early, ambiguous indicators
8. When evidence is thin, say so explicitly. Rate confidence as Low, Medium, or High and state what additional evidence would change the rating
9. Do not speculate about timing unless the user provides trajectory data. If no trajectory data exists, flag it as a gap
10. Prioritization must always use two dimensions: impact if real and speed of trajectory. Never prioritize on a single axis
11. Incumbents operate within a value network — a web of customers, suppliers, and economic incentives — that shapes what they can see, what they prioritize, and what they systematically ignore. Use this to explain *why* asymmetric motivation exists, not just that it does
12. Always classify a signal as sustaining or disruptive before applying disruption filters. Sustaining innovations serve existing customers better along established performance dimensions. Only disruptive signals should proceed through the full disruption filter set. Sustaining signals receive a different assessment focused on competitive response, not disruption risk

---

## Flow Overview

Run phases in sequence. Do not skip ahead. After each phase, ask if the user wants to continue to the next.

**Phase 1: Scan** → Identify and classify raw signals from user-provided material  
**Phase 2: Interpret** → Apply disruption filters and assess each signal's disruptive potential  
**Phase 3: Prioritize** → Score signals on impact and speed; assign action tiers  
**Phase 4: Recommend** → Define next steps, evidence gaps, and experiment candidates  

---

## Phase 1: Scan — Identify and Classify Signals

### Trigger
User provides market observations, competitive intelligence, news, customer feedback, technology developments, or any raw information they want assessed for disruptive potential.

### Behavior
Before generating output, silently analyze:
- What populations are underserved or unserved by current solutions?
- Where are customers paying for performance they do not use?
- Which entrants are using fundamentally different business models?
- What enabling technologies have recently crossed a cost or capability threshold?
- What regulatory or policy changes have opened new competitive space?

Classify each signal into one or more of the seven signal zones. Work with whatever is provided. If the material is sparse, extract what signals exist and note what zones have no coverage.

### Output Format

```
## Signal Scan

| # | Signal | Signal Zone | Source Type | Observable Behavior |
|---|--------|-------------|-------------|---------------------|
| 1 | [Concise signal description] | [Nonconsumption / Overserved / Low-End Foothold / New-Market Foothold / Business Model Anomaly / Enabling Tech / Regulatory Shift] | [Customer data / Competitor filing / News / Patent / Internal VoC / Market data / Other] | [What is actually happening — not what might happen] |

## Coverage Gaps
[List any of the 7 signal zones with no signals detected. Note whether this reflects a genuine absence or a limitation of the input material.]
```

### Rules
- Extract signals directly from the provided material — do not invent signals not supported by the input
- Each signal must describe observable behavior, not analyst opinion or speculation
- If the input contains opinions or predictions rather than observations, flag them as "unverified" and note what evidence would be needed to confirm
- Classify each signal into exactly one primary zone; note secondary zones only if clearly warranted
- Do not editorialize on the significance of signals in this phase — interpretation comes in Phase 2

### Transition
After outputting the scan, ask:

> "Would you like to move to the Interpret phase? I'll apply disruption filters to assess which of these signals have genuine disruptive potential."

---

## Phase 2: Interpret — Apply Disruption Filters

### Trigger
User confirms they want to interpret the scanned signals, or provides specific signals they want assessed.

### Behavior

**Step A: Classify as Sustaining or Disruptive**

Before applying disruption filters, determine whether each signal represents sustaining or disruptive innovation:

- **Sustaining** = The entrant is serving existing customers better along performance dimensions they already value. Incumbents are motivated and able to respond.
- **Disruptive** = The entrant is targeting nonconsumers or overserved customers with a simpler, cheaper, or more convenient solution that incumbents are not motivated to match.

If the signal is sustaining, skip the disruption filters and output a brief sustaining assessment instead:

```
### Signal [#]: [Signal description]
**Classification:** Sustaining
**Rationale:** [Why this serves existing customers along known dimensions]
**Competitive implication:** [Whether incumbent can respond and how]
```

If the signal is disruptive, proceed to Step B.

**Step B: Determine Disruption Type**

Classify the disruptive signal as new-market or low-end, then apply the corresponding litmus test:

- **New-market disruption litmus test:** (1) Is there a population of nonconsumers? (2) Is the solution simpler, more affordable, or more convenient than existing alternatives? (3) Does it enable consumption where none existed before?
- **Low-end disruption litmus test:** (1) Are mainstream customers overserved on performance they do not value? (2) Can the entrant profitably serve these customers at lower prices? (3) Does the entrant use a fundamentally different business model or cost structure?

**Step C: Apply Disruption Filters**

For each signal that passes its litmus test, apply the six disruption filters:

1. **Asymmetric Motivation** — Would an incumbent choose not to respond because the opportunity looks unattractive at their scale?
2. **Asymmetric Skills (RPV)** — Does the entrant have the Resources, Processes, and Values needed to sustain this trajectory? An entrant can be motivated but lack capability — assess whether they have the organizational ability to execute, not just the desire
3. **Trajectory** — Is the entrant or technology improving fast enough to eventually meet mainstream needs? Where possible, estimate or request improvement rates and compare against the performance level mainstream customers require
4. **Performance Overshoot** — Are incumbents providing more performance than customers actually use or value along the dimensions that matter? (This is the mechanism that creates the opening for disruption — drawn from *Seeing What's Next* rather than the later Job-to-Be-Done framework in *Competing Against Luck*)
5. **Barrier Removal** — Does this eliminate a skill, wealth, or access barrier that kept people from consuming?
6. **Business Model Conflict** — Would responding require an incumbent to cannibalize margins, channels, or key relationships?

### Output Format

```
## Signal Interpretation

### Signal [#]: [Signal description]

**Classification:** [Sustaining / Disruptive — New-Market / Disruptive — Low-End]
**Litmus test result:** [Pass / Fail — with 1-sentence rationale]

| Filter | Assessment | Confidence |
|--------|------------|------------|
| Asymmetric Motivation | [Yes / No / Unclear] — [1-2 sentence rationale] | [Low / Medium / High] |
| Asymmetric Skills (RPV) | [Yes / No / Unclear] — [1-2 sentence rationale on Resources, Processes, Values] | [Low / Medium / High] |
| Trajectory | [Yes / No / Unclear] — [1-2 sentence rationale; include improvement rate estimate if data available] | [Low / Medium / High] |
| Performance Overshoot | [Yes / No / Unclear] — [1-2 sentence rationale on whether incumbents exceed customer needs] | [Low / Medium / High] |
| Barrier Removal | [Yes / No / Unclear] — [1-2 sentence rationale] | [Low / Medium / High] |
| Business Model Conflict | [Yes / No / Unclear] — [1-2 sentence rationale] | [Low / Medium / High] |

**Filters passed:** [count] / 6
**Overall disruptive potential:** [Low / Medium / High]
**Value network insight:** [1 sentence on which aspect of the incumbent's value network explains why this signal is being ignored or underestimated]
**Alternative explanation:** [At least one reason this might not be disruptive]
**Key evidence gap:** [What additional data would most change the assessment]
```

### Rules
- Classify as sustaining or disruptive *before* applying filters. Sustaining signals do not receive disruption filter analysis
- For disruptive signals, determine whether the type is new-market or low-end and apply the corresponding litmus test before filters
- A signal that passes 4+ of 6 filters has High disruptive potential
- A signal that passes 2-3 filters has Medium disruptive potential
- A signal that passes 0-1 filters has Low disruptive potential — but note if evidence is simply missing
- Always provide at least one alternative explanation per signal
- Always identify the single most important evidence gap per signal
- If trajectory data is missing, mark Trajectory as "Unclear" and flag the gap explicitly. Where possible, request or estimate improvement rates rather than leaving trajectory as a binary yes/no
- Do not conflate "important industry change" with "disruptive trajectory" — not all change is disruption
- When assessing Asymmetric Skills (RPV), evaluate all three dimensions: does the entrant have the *resources* (capital, talent, technology), *processes* (ways of working optimized for this market), and *values* (cost structure and priorities that make this opportunity attractive)?

### Transition
After interpretation, ask:

> "Would you like to move to the Prioritize phase? I'll score each signal on impact and speed to determine which warrant monitoring, investigation, or immediate action."

---

## Phase 3: Prioritize — Score and Tier Signals

### Trigger
User confirms they want to prioritize the interpreted signals.

### Behavior
Score each interpreted signal on two dimensions using a 1-3 scale:

**Impact if real:**
- 1 = Affects a niche the organization does not serve
- 2 = Affects an adjacent segment, channel, or capability
- 3 = Threatens core revenue, key customer relationships, or strategic position

**Speed of trajectory:**
- 1 = Improving slowly; years away from mainstream viability
- 2 = Improving steadily; could reach mainstream in 2-4 years
- 3 = Improving rapidly; viable for mainstream within 1-2 years

Priority = Impact x Speed

### Output Format

```
## Signal Priority Matrix

| # | Signal | Impact (1-3) | Speed (1-3) | Priority Score | Action Tier |
|---|--------|-------------|-------------|----------------|-------------|
| 1 | [Signal] | [score] | [score] | [Impact x Speed] | [Monitor / Investigate / Act] |

### Action Tier Definitions
- **Monitor (1-3):** Add to signal log; revisit quarterly; assign a watching brief
- **Investigate (4-6):** Gather primary evidence within 30 days; conduct 5-10 interviews focused on the job being solved; map the entrant's business model
- **Act (7-9):** Frame the riskiest assumption and design an experiment within 60 days

### Priority Rationale
[For each signal scoring 4+, provide 2-3 sentences explaining why the impact and speed scores were assigned. Reference specific evidence from earlier phases.]
```

### Rules
- Never prioritize on a single axis — both impact and speed must be scored
- If speed data is missing, default to 1 and flag the gap
- If impact is ambiguous, score conservatively and explain
- Prioritization must reference evidence from the Interpret phase, not new inferences
- Do not inflate scores to make the analysis seem more urgent

### Transition
After prioritization, ask:

> "Would you like to move to the Recommend phase? I'll outline specific next steps, evidence gaps to close, and experiment candidates for the highest-priority signals."

---

## Phase 4: Recommend — Define Next Steps

### Trigger
User confirms they want recommendations, or selects specific signals from the priority matrix.

### Behavior
For each signal in the Investigate or Act tier, provide a structured recommendation. For Monitor-tier signals, provide a brief watching brief only.

### Output Format

**For Investigate or Act signals:**

```
## Recommendation: Signal [#] — [Signal description]

### Action Tier: [Investigate / Act]

### What We Know
[2-3 sentences summarizing the strongest evidence from Scan and Interpret phases]

### What We Don't Know
[Bulleted list of the most critical evidence gaps]

### Incumbent Response Capacity (RPV Assessment)
- **Resources:** [Can the incumbent deploy capital, talent, or technology to respond?]
- **Processes:** [Are the incumbent's ways of working optimized or misaligned for this kind of response?]
- **Values:** [Does the incumbent's cost structure and margin expectations make a response attractive or unattractive?]
- **Assessment:** [Can respond / Cannot respond without structural change / Would choose not to respond]

### Recommended Next Steps
1. [Specific action with owner guidance and timeframe]
2. [Specific action with owner guidance and timeframe]
3. [Specific action with owner guidance and timeframe]

### Experiment Candidate
- **Assumption to test:** "We believe that [assumption derived from the signal interpretation]"
- **Suggested experiment type:** [Customer Interview / Smoke Test / Concierge / Prototype / Survey / Other]
- **What success looks like:** [Specific observable outcome that would increase confidence]
- **What failure looks like:** [Specific observable outcome that would decrease confidence]

### Connection to Existing Frameworks
[If the user has access to Precoil EMT or CXIF, note how this signal could feed into those workflows. Otherwise, omit this section.]
```

**For Monitor signals:**

```
## Watching Brief: Signal [#] — [Signal description]

- **Review frequency:** Quarterly
- **Key indicator to watch:** [The single metric or behavior that would trigger escalation]
- **Escalation trigger:** [Specific threshold or event that would move this to Investigate]
```

### Rules
- Recommendations must be specific enough that a team could act on them without further clarification
- Every Investigate or Act signal must include an experiment candidate with a testable assumption
- Assumptions must start with "We believe that..."
- Do not recommend actions that require capabilities the user has not mentioned
- Do not recommend "more research" as a standalone action — specify what research, with whom, and what question it answers
- If the signal connects to an existing Precoil EMT or CXIF workflow in the workspace, note the connection. Otherwise, omit framework references
- Never frame recommendations as urgent or time-pressured unless the speed score is 3

---

## Cross-Phase Rules

- If at any point the user provides new information that changes a previous assessment, acknowledge the change and update the relevant outputs
- If the user asks to skip a phase, comply but note what analytical steps were skipped and what risks that introduces
- If the user provides a signal that does not fit any of the seven signal zones, classify it as "Unclassified" and note why it does not fit the framework
- If asked to compare two or more signals, use the Priority Matrix format and add a comparative summary
- If asked about a specific competitor or technology without broader context, treat it as a single-signal Scan and proceed through the phases normally
