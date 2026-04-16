# BMI Consultant Workflow — Concepts & Methodology

This document explains the frameworks, concepts, and analytical methods used at each step of the BMI Consultant workflow. Understanding these concepts is essential for interpreting the outputs and making informed decisions at each checkpoint.

---

## The CXIF Framework

The entire BMI Consultant workflow is an implementation of the **Customer Experience Innovation Framework (CXIF)** — a structured, agile methodology that combines Business Model Innovation, Customer Experience, and Design approaches. CXIF guides teams from market signal detection through to validated, de-risked business models.

CXIF is organized into **three overarching phases**:

| Phase | Name | Purpose | Steps | Engine |
|-------|------|---------|-------|--------|
| Phase 1 | **DETECT** | Scan for signals of change and determine innovation direction | Steps 1–2 | Signal of Change (SoC) Radar |
| Phase 2 | **ARCHITECT** | Build deep customer empathy and design the business model | Steps 3–6 | Empathize → Measure → Define → Design |
| Phase 3 | **DE-RISK** | Surface assumptions and validate through experimentation | Steps 7–8 | Extract-Map-Test (EMT) |

**Core principle:** Always maintain a customer-centric perspective. Frame everything from the customer's point of view, using their language, tied to their business outcomes.

```
DETECT ──→ ARCHITECT ──→ DE-RISK
Signal Scanning    Empathize         Extract
Pattern Mapping    Measure           Map
                   Define            Test
                   Design
```

Each phase builds on the outputs of the previous one. Checkpoints between phases allow the consultant to validate, adjust, and approve before proceeding.

---

## Phase 1: DETECT (Steps 1–2)

**Purpose:** Scan Voice of Customer data for weak signals of market change, classify and prioritize those signals, and determine the strategic innovation direction.

**Engine:** Signal of Change (SoC) Radar — a framework based on disruption theory and competitive analysis.

**Core concept:** Markets do not change overnight. Change begins as weak signals — emerging patterns in customer behavior, technology capability, regulation, or competitor activity — that are easy to dismiss individually but collectively indicate shifts in the competitive landscape. Incumbents operate within a value network that shapes what they can see and what they systematically ignore.

### SoC Radar Methodology

**Signal zones:** Every signal is classified into one of seven canonical zones:

| Signal Zone | Definition | Example |
|-------------|-----------|---------|
| **Nonconsumption** | A population that is underserved or unserved by current solutions — no existing product meets their need | SMB and Edge workload customers manage firmware manually because no affordable assessment option exists |
| **Overserved Customers** | Customers paying for performance they do not use — an opening for simpler, cheaper alternatives | Enterprise customers receiving specialist-driven firmware assessments when they only need basic compatibility checks |
| **Low-End Foothold** | An entrant profitably serving customers at lower prices with a different cost structure | A competitor offers automated firmware assessment as a self-serve tool at a fraction of the specialist-delivery cost |
| **New-Market Foothold** | A simpler, more affordable, or more convenient solution enabling consumption where none existed | AI-powered assessment makes firmware analysis accessible to teams without infrastructure specialists |
| **Business Model Anomaly** | An entrant using a fundamentally different business model that incumbents are not motivated to match | A competitor bundles firmware assessment into a platform subscription, bypassing per-engagement pricing |
| **Enabling Technology** | A technology that has crossed a cost or capability threshold, enabling new solutions | AI-powered analysis can now assess firmware compatibility at scale without human specialists |
| **Regulatory / Policy Shift** | A regulatory or policy change that opens new competitive space or forces operational changes | New compliance requirements mandate proactive firmware assessment for critical infrastructure |

**Signal classification:** Each signal is first classified as **Sustaining** (serving existing customers better along known performance dimensions) or **Disruptive** (targeting nonconsumers or overserved customers with a simpler solution incumbents are not motivated to match). Disruptive signals are further typed as **New-Market** or **Low-End**.

**Signal prioritization:** Signals are scored on two dimensions — **impact** (1–3) and **speed of trajectory** (1–3) — producing a composite score (impact × speed) that assigns each signal to a tier: **Act** (7–9), **Investigate** (4–6), or **Monitor** (1–3). Each interpreted signal also carries a **confidence** rating (Low / Medium / High).

### Step 1: Signal Scanning

**What happens:** The LLM analyzes Voice of Customer (VoC) data — interview transcripts, survey results, feedback, or market observations — and extracts signals of change.

**Key concepts:**

- **Voice of Customer (VoC) data** — Raw customer input in any form: interview transcripts, survey responses, support tickets, NPS comments, competitive intelligence notes. This is the primary input to the entire workflow.
- **Signal extraction** — The process of identifying meaningful patterns in unstructured customer data. Not every customer comment is a signal; signals represent recurring themes or emerging trends that indicate market movement.
- **Source attribution** — Every signal is traced back to the specific VoC data that supports it. This grounds the analysis in evidence rather than speculation.
- **Coverage gaps** — After scanning, any of the 7 signal zones with no detected signals are flagged. A gap reflects a limitation of the input material, not proof of absence — it is an intelligence blind spot.
- **Disruption filters** — Disruptive signals are assessed through six filters: Asymmetric Motivation, Asymmetric Skills (RPV), Trajectory, Performance Overshoot, Barrier Removal, and Business Model Conflict. These determine the signal's disruptive potential and the incumbent's ability to respond.

**Output:** Classified signals with zone assignment, Sustaining/Disruptive classification, confidence (Low/Medium/High), a priority matrix (impact × speed → Act/Investigate/Monitor tiers), coverage gaps, and an agent recommendation summarizing the highest-priority signals.

**Checkpoint 1:** The consultant reviews detected signals. This is critical because signal interpretation is subjective — the consultant's domain knowledge validates whether the AI's signal classification aligns with market reality.

### Step 2: Pattern Mapping & Direction

**What happens:** The detected signals are cross-referenced against a library of established business model patterns to determine the innovation direction.

**Key concepts:**

- **Invent vs. Shift** — The fundamental strategic decision:
  - **Invent** — Create a fundamentally new business model to serve unaddressed needs or new markets. Appropriate when signals indicate nonconsumption, new-market disruption, or business model anomalies from new entrants.
  - **Shift** — Adapt and improve an existing business model to respond to changing conditions. Appropriate when signals indicate overserved customers, core revenue under threat, or opportunities to simplify and reprice.

- **Business model patterns** — Established archetypes for how companies create, deliver, and capture value. The pattern library includes categories such as:
  - **Market Explorers** — Models that discover and serve new markets
  - **Cost Differentiators** — Models that compete on cost structure innovation
  - **Resource Castles** — Models that build defensible resource advantages
  - **Channel Kings** — Models that innovate on delivery and distribution
  - **Gravity Creators** — Models that create ecosystem pull
  - **Revenue Differentiators** — Models that innovate on how revenue is generated
  - **Margin Masters** — Models that optimize the profit formula
  - **Activity Scalers** — Models that scale through operational efficiency

- **Pattern-to-signal alignment** — Not all patterns fit all signals. The mapping considers which pattern archetypes are most relevant given the specific signals detected.

**Checkpoint 2:** The consultant confirms the innovation direction and selects which patterns to explore. This shapes all downstream analysis.

---

## Phase 2: ARCHITECT (Steps 3–6)

**Purpose:** Build deep customer empathy, define measurable outcomes, frame the problem, and design the business model — progressing from understanding to prototype.

**Engine:** Four sequential sub-phases — **Empathize → Measure → Define → Design** — that move from raw customer insight to a fully articulated Value Proposition Canvas, Business Model Canvas, and Fit Assessment.

| Sub-phase | Name | Purpose | Step |
|-----------|------|---------|------|
| A1 | **Empathize** | Surface customer jobs, pains, and gains | Step 3 |
| A2 | **Measure** | Define customer business outcomes and success measures | Step 4 |
| A3 | **Define** | Build actionable insights and frame the problem | Step 5 |
| A4 | **Design** | Prototype value propositions and business models | Step 6 |

The ARCHITECT phase produces two stages of output:

- **Build Insights** (Steps 3–4) — Understand the customer deeply, define measurable outcomes
- **De-risk Ideas** (Steps 5–6) — Frame the problem and design solutions

### Step 3: Customer Profile (Empathize)

**What happens:** A deep Customer Empathy Profile is built from the VoC data, structured around jobs, pains, and gains.

**Key concepts:**

- **Customer Jobs** — What the customer is trying to accomplish. Jobs are categorized by type:
  - **Functional** — Practical tasks or problems the customer needs to solve (e.g., "keep infrastructure stable by managing firmware")
  - **Social** — How the customer wants to be perceived by others (e.g., "be seen as a proactive IT leader")
  - **Emotional** — Feelings the customer seeks (e.g., "confidence that systems are secure")
  - **Supporting** — Ancillary tasks in buyer, co-creator, or transferrer roles (e.g., "evaluate vendor proposals without specialist help")
  Each job is ranked by **Importance** (High / Medium / Low).

- **Customer Pains** — What frustrates, blocks, or annoys the customer:
  - **Functional** — Difficulties or obstacles encountered (e.g., "firmware issues discovered reactively after downtime")
  - **Social** — Negative social consequences (e.g., "blamed for preventable outages")
  - **Emotional** — Frustration, anxiety, or annoyance (e.g., "stress from unpredictable system failures")
  - **Ancillary** — Annoyances before, during, or after getting a job done (e.g., "re-explaining history to each support engineer")
  Each pain is ranked by **Severity** (Severe / Moderate / Light).

- **Customer Gains** — What outcomes or benefits the customer seeks:
  - **Functional** — Required, expected, or desired outcomes (e.g., "higher system availability")
  - **Social** — Positive social consequences (e.g., "team recognized for operational excellence")
  - **Emotional** — Positive feelings sought (e.g., "peace of mind from proactive monitoring")
  - **Financial** — Savings or financial benefits (e.g., "reduced cost of unplanned downtime")
  Each gain is ranked by **Relevance** (Essential / Expected / Desired / Unexpected).

**Critical rule:** Jobs describe what the *customer* is trying to accomplish, not what the supplier wants to deliver. Pains describe what annoys the *customer*, not what the supplier finds difficult. Gains describe what the *customer* values, not what the supplier assumes they value.

### Step 4: Success Measures (Measure)

**What happens:** Customer jobs, pains, and gains are translated into measurable business outcomes using a Value Driver Tree.

**Key concepts:**

- **Value Driver Tree** — A structured breakdown of how customer value translates into measurable outcomes. For each customer need:
  - **Customer Business Outcome** — A measurable result that would satisfy the customer's job (e.g., "firmware assessment turnaround reduced from days to hours")
  - **Key Deliverable** — A specific output or capability that supports the outcome
  - **Success Measure** — A SMART metric stated in the customer's terms
  - **Baseline** — Current state measurement
  - **Target** — Goal state measurement
  - **Driver Type** — How the measure impacts value: Cost, Revenue, Time, Effort, Volume, or Satisfaction

- **SMART metrics** — Success measures must be Specific, Measurable, Achievable, Relevant, and Time-bound. "Improve customer experience" is not SMART. "Reduce firmware assessment turnaround from 4-25 days to under 1 day within 6 months" is SMART.

- **FTE Impact Estimate** — When workload or labor cost evaluation is relevant, the step calculates the Full-Time Equivalent impact of changing operations (e.g., automating a manual process).

### Step 5: Actionable Insights (Define)

**What happens:** The customer and supplier context is analyzed to identify value chain weak links, friction points, and root causes. The findings are synthesized into actionable insight statements and problem framings.

**Key concepts:**

- **Value Chain Assessment** — An analysis of every activity in the value chain to identify where value is created, where it leaks, and where weak links exist. A weak link is any activity that creates friction, delays, errors, or cost without proportionate customer value.

- **Customer Journey Friction Points** — A map of touchpoints in the customer journey where friction occurs. Friction types include:
  - **Pain** — The customer experiences difficulty or frustration
  - **Gap** — An expected capability or service is missing
  - **Delay** — The customer waits longer than expected or acceptable
  - **Error** — Inaccurate information or unreliable outputs

- **Actionable Insight Format** — Every insight follows a precise structure:
  > **[Customer segment]** DOES **[activity or behavior]** BECAUSE **[needs, drivers, motivations]** BUT **[barriers, constraints]**
  
  This format forces specificity. It names who is affected, what they do, why they do it, and what blocks them. Insights focus on *why* a situation is happening (root causes), not *what* is happening (symptoms).

- **"How Might We" Statements** — Problem statements converted from insights into opportunity framings. A good HMW statement enables innovative solutions to emerge without prescribing a specific answer.

### Step 6: Design & Fit (Design)

**What happens:** The analysis is translated into concrete prototypes — a Value Proposition Canvas, a Business Model Canvas, and a Fit Assessment.

**Key concepts:**

- **Value Proposition Canvas (VPC)** — A framework that maps the connection between what the customer needs and what the solution offers:
  - **Products & Services** — The specific offerings (physical, digital, intangible, financial)
  - **Pain Relievers** — How each product or service addresses specific customer pains
  - **Gain Creators** — How each product or service enables specific customer gains
  
  Pain relievers must map to specific pains from Step 3. Gain creators must map to specific gains from Step 3. This traceability ensures the value proposition is grounded in actual customer needs.

- **Ad-Lib Prototype** — A quick, structured statement that captures the essence of a value proposition:
  > **OUR** [products & services] **HELP** [customer segment] **WHO WANT TO** [jobs] **BY** [reducing/avoiding] [pain] **AND** [improving/enabling] [gain]
  
  The step generates 2-3 alternative ad-libs to encourage exploration of multiple directions rather than premature convergence.

- **Business Model Canvas (BMC)** — The 9-block framework that describes how an organization creates, delivers, and captures value:

  | Dimension | Building Blocks |
  |-----------|----------------|
  | **Desirability** | Customer Segments, Value Proposition, Channels, Customer Relationships |
  | **Feasibility** | Key Partnerships, Key Activities, Key Resources |
  | **Viability** | Revenue Streams, Cost Structure |

- **Fit Assessment** — A structured evaluation of three progressive levels of validation:
  - **Problem-Solution Fit** — Evidence that customers care about these jobs, pains, and gains, and that the value proposition addresses the most important ones
  - **Product-Market Fit** — Measurable evidence that the value proposition creates real value and catches market interest
  - **Business Model Fit** — Evidence that the full model is desirable, feasible, and viable

  Each criterion is rated as **Validated** (tested with evidence), **Assumed** (believed but untested), or **Unknown** (no basis for assessment). At this stage in the workflow, most criteria will be "Assumed" — that is expected and honest.

---

## Phase 3: DE-RISK (Steps 7–8)

**Purpose:** Pressure-test the business model by surfacing its riskiest assumptions and validating them through structured experimentation before committing resources.

**Engine:** Extract-Map-Test (EMT) — developed by David J. Bland — combined with the Testing Business Ideas experiment library.

**DVF Categories — the organizing principle:**

Every assumption, risk, and experiment in the DE-RISK phase is categorized into one of three dimensions:

| Category | Scope | Canvas Elements | Question It Answers |
|----------|-------|----------------|---------------------|
| **Desirability** | Customer needs, problem severity, perceived value, solution fit | Customer Segments, Value Proposition, Channels, Customer Relationships | Do customers want this? |
| **Viability** | All financial assumptions: pricing, willingness to pay, revenue, margins, unit economics | Revenue Streams, Cost Structure | Can we make money from this? |
| **Feasibility** | Operational, technical, or organizational delivery capability | Key Partnerships, Key Activities, Key Resources | Can we build and deliver this? |

**Critical rule:** Financial assumptions (pricing, revenue, margins) always belong in Viability, never in Desirability. User-need assumptions always belong in Desirability, never in Viability.

### Step 7: Risk Map (Extract & Map)

**What happens:** The business model is pressure-tested by extracting its implicit assumptions, categorizing them by DVF, and prioritizing them on an importance-evidence matrix.

**Key concepts:**

- **Assumption extraction** — Every business model rests on beliefs that have not yet been proven. This step makes those beliefs explicit. Each assumption:
  - Starts with "I believe..." or "We believe..."
  - Belongs to exactly one DVF category (Desirability, Viability, or Feasibility)
  - Describes something that could prove the idea wrong if tested
  - Represents observable behavior rather than opinions

- **Importance × Evidence Matrix** — A 2×2 prioritization framework:

  | Quadrant | Meaning | Action |
  |----------|---------|--------|
  | **High Importance / Low Evidence** | The riskiest assumptions — vital for survival, minimal supporting data | **Test first** — design experiments immediately |
  | **High Importance / Some Evidence** | Important with partial validation | Continue testing with more robust experiments |
  | **Low Importance / Low Evidence** | Low priority unknowns | Backlog — revisit if context changes |
  | **Low Importance / High Evidence** | Well-understood, low consequence | Monitor — no action needed |

  The assumptions in the **"Test First"** quadrant (high importance, low evidence) are the ones that flow into Step 8.

- **DVF Tension Check** — After extracting assumptions, the step identifies the single most important tension between DVF categories. A tension is a conflict where one assumption depends on another assumption being true in a different category. For example: a Desirability assumption about customer willingness to self-serve may conflict with a Feasibility assumption about the complexity of the onboarding process.

**Checkpoint 3:** The consultant reviews the risk map before experiment design. This is the most consequential checkpoint — it determines which assumptions will be tested and which will be deferred.

### Step 8: Experiment Design (Test)

**What happens:** For each "Test First" assumption from Step 7, a structured PDSA experiment is designed with clear success and failure criteria.

**Key concepts:**

- **PDSA Cycle** — Plan-Do-Study-Act, an iterative experiment framework:
  - **Plan** — Define the hypothesis, experiment method, and success criteria ("We believe that... To verify, we will... We are right if...")
  - **Do** — Execute the experiment according to the plan
  - **Study** — Analyze results against the success criteria
  - **Act** — Make a decision: continue, pivot, or stop

- **Experiment types** — The step draws from a library of 44 experiment cards (from *Testing Business Ideas* by Strategyzer and David J. Bland). Common types include:

  | Experiment Type | Evidence Strength | Cost | Speed | Best For |
  |----------------|------------------|------|-------|----------|
  | **Customer Interview** | Weak-Medium | Low | Fast | Early desirability validation |
  | **Landing Page / Smoke Test** | Medium | Low | Fast | Demand signals (click-through, sign-up rates) |
  | **Concierge Test** | Medium-Strong | Medium | Medium | Service experience validation with real customers |
  | **Pricing Variant Test** | Medium | Low | Medium | Willingness-to-pay exploration |
  | **Prototype Test** | Medium | Medium | Medium | Usability and feasibility validation |
  | **A/B Test** | Strong | Medium | Slow | Comparing alternatives with statistical rigor |
  | **Pilot** | Strong | High | Slow | Full operational validation |

- **Evidence hierarchy** — Not all evidence is equal:
  - What people **do** > what people **say**
  - **Facts** > opinions
  - **Real environment** > lab setting
  - **High investment** (time/money) by the participant > low investment
  
  The workflow sequences experiments from cheap/fast/weak-evidence (early, when uncertainty is high) to expensive/slow/strong-evidence (later, when confidence is growing).

- **Experiment worksheets** — Structured templates for executing and documenting each experiment, including:
  - Assumption being tested
  - Experiment design (method, participants, duration, cost)
  - Success and failure thresholds
  - Observation recording
  - Decision framework (what to do with the results)

- **Decision framework after testing:**

  | Result | Possible Actions |
  |--------|-----------------|
  | Evidence refutes assumption | Kill the idea or pivot the business model |
  | Evidence confirms assumption | Test the next riskiest assumption or increase evidence strength |
  | New learnings emerge | Adjust the model and run additional experiments |
  | Results are unclear | Continue testing with different methods |

**Critical rule:** The workflow never recommends killing or pivoting an idea. It presents the decision framework and evidence, and the consultant decides.

---

## Cross-Cutting Concepts

These concepts apply throughout the entire workflow:

### Fit Progression

The workflow tracks three progressive levels of business model validation:

```
Problem-Solution Fit → Product-Market Fit → Business Model Fit
```

| Fit Level | Validated When |
|-----------|---------------|
| **Problem-Solution Fit** | Evidence that customers care about the jobs, pains, and gains; the value proposition addresses the most important ones |
| **Product-Market Fit** | Measurable evidence that the value proposition creates real value and catches market interest |
| **Business Model Fit** | Evidence that the model is desirable, feasible, and viable |

Each test cycle should update the fit status. Canvases change rapidly early in the process and stabilize as learnings accumulate.

### Innovation Zone vs. Production Zone

The BMI workflow operates in the **Innovation Zone** — a space for exploring, prototyping, and testing ideas quickly and cheaply. This is complementary to (not competing with) the **Production Zone** where validated ideas are built, scaled, and optimized.

The key difference: In the Innovation Zone, the goal is to **learn fast** and **fail cheap**. In the Production Zone, the goal is to **execute reliably** and **scale efficiently**.

### Checkpoint Discipline

Checkpoints are not optional review points — they are quality gates. The AI generates structured analysis, but the consultant's domain expertise, contextual knowledge, and judgment are essential for validating whether the analysis aligns with reality. Skipping checkpoint review means downstream steps may be built on flawed foundations.

---

*This document covers the Customer Experience Innovation Framework (CXIF) as implemented in the BMI Consultant App — encompassing the DETECT phase (SoC Radar), the ARCHITECT phase (Empathize, Measure, Define, Design), and the DE-RISK phase (EMT). For the original framework definitions, refer to "Value Proposition Design" and "The Invincible Company" (Strategyzer), "Testing Business Ideas" (David J. Bland), and the CXIF methodology documentation.*
