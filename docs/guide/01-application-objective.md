# BMI Consultant App — Application Objective

## What Is the BMI Consultant App?

The BMI Consultant App is a containerized, AI-assisted application that automates and guides consultants through an **8-step Business Model Innovation (BMI) workflow**. It takes raw customer research data as input and produces a fully structured set of deliverables — from market signal analysis through validated experiment plans — following established innovation methodologies.

The application codifies the **Customer Experience Innovation Framework (CXIF)** into a repeatable, step-by-step digital workflow organized into three phases — **DETECT** (Signal of Change Radar), **ARCHITECT** (Empathize, Measure, Define, Design), and **DE-RISK** (Extract-Map-Test). Each step is powered by a Large Language Model (LLM) guided by structured skill prompts, ensuring consistency, depth, and methodological rigor across every engagement.

---

## Why Does This Application Exist?

Business Model Innovation consulting typically requires deep expertise across multiple frameworks, weeks of manual analysis, and iterative document creation. The BMI Consultant App addresses three core problems:

1. **Methodology consistency** — The CXIF framework and its phase engines (SoC Radar, EMT) each have precise rules, output formats, and sequencing requirements. Manual execution risks skipping steps, mixing up DVF categories, or producing outputs that do not adhere to the framework contracts. The app enforces the correct sequence and output structure at every step.

2. **Speed to insight** — A workflow that traditionally takes weeks of consultant effort can be completed in hours. The LLM generates structured analysis from Voice of Customer (VoC) data, producing customer profiles, value propositions, business model canvases, risk maps, and experiment plans in a single session.

3. **Portability** — The app runs as a self-contained Docker Compose stack, independent of any enterprise infrastructure. It can operate against Azure OpenAI for production-grade reasoning or a local Ollama instance for air-gapped or cost-sensitive environments.

---

## What Problem Does It Solve?

The application addresses the full lifecycle of **business model de-risking**:

| Challenge | How the App Addresses It |
|-----------|--------------------------|
| Raw customer data is unstructured and hard to interpret | **DETECT** — Step 1 scans VoC data for weak signals of market change using the SoC Radar engine |
| Innovation direction is unclear (new model vs. adapt existing) | **DETECT** — Step 2 maps signals to business model patterns and recommends Invent vs. Shift direction |
| Customer needs are assumed rather than structured | **ARCHITECT** — Step 3 builds a rigorous Customer Empathy Profile (jobs, pains, gains) |
| Success is undefined or unmeasurable | **ARCHITECT** — Step 4 translates customer needs into a Value Driver Tree with SMART metrics |
| Problems are described as symptoms, not root causes | **ARCHITECT** — Step 5 produces actionable insights using the WHO-DOES-BECAUSE-BUT format |
| Value propositions are vague or untestable | **ARCHITECT** — Step 6 designs a Value Proposition Canvas and Business Model Canvas with fit assessment |
| Assumptions are implicit and never surfaced | **DE-RISK** — Step 7 extracts DVF assumptions, scores them by importance and evidence, and maps tensions |
| Ideas are funded without validation | **DE-RISK** — Step 8 designs PDSA experiment cycles to test the riskiest assumptions before committing resources |

---

## Who Is It For?

The primary users are **CX and Business Process Innovation consultants** who apply the CXIF methodology to evaluate and de-risk business ideas. Secondary users include:

- **Product managers** exploring new value propositions or service models
- **Strategy teams** evaluating market signals and competitive threats
- **Innovation leads** who need structured experiment plans to present to stakeholders
- **Any team** that needs to move from raw customer feedback to a validated business model prototype

---

## What Does It Produce?

A complete run through the 8-step workflow generates the following deliverables:

| Phase | Step | Deliverable | Format |
|-------|------|-------------|--------|
| **DETECT** | 1 — Signal Scan | Classified and scored signals of change | Signal list with zone assignment, Sustaining/Disruptive classification, confidence, and priority tiers (Act/Investigate/Monitor) |
| **DETECT** | 2 — Pattern Mapping | Innovation direction and applicable business model patterns | Direction (Invent/Shift) + pattern recommendations |
| **ARCHITECT** | 3 — Customer Profile | Customer Empathy Profile | Jobs, pains, and gains tables with importance/severity/relevance rankings |
| **ARCHITECT** | 4 — Success Measures | Value Driver Tree | Key deliverables, success measures, baselines, targets, and FTE impact estimates |
| **ARCHITECT** | 5 — Actionable Insights | Problem framing and insights | Value chain assessment, friction points, WHO-DOES-BECAUSE-BUT insights, HMW problem statements |
| **ARCHITECT** | 6 — Design & Fit | Value Proposition Canvas + Business Model Canvas + Fit Assessment | VPC (products, pain relievers, gain creators), BMC (9 blocks), and Problem-Solution / Product-Market / Business Model Fit status |
| **DE-RISK** | 7 — Risk Map | DVF assumption tables with importance-evidence scoring | Desirability, Viability, Feasibility assumptions with tension analysis |
| **DE-RISK** | 8 — Experiment Plans | PDSA experiment designs and worksheets | Plan-Do-Study-Act cycles for each prioritized assumption with success/failure criteria |

---

## Architecture Overview

The application is composed of three services running in Docker Compose:

| Service | Technology | Role |
|---------|-----------|------|
| **bmi-postgres** | PostgreSQL + pgvector | Persists workflow state, step outputs, and checkpoint snapshots |
| **bmi-backend** | FastAPI + LangGraph + Typer CLI | Orchestrates the 8-step workflow, manages checkpoints, exposes REST API and CLI |
| **bmi-frontend-react** | React + Grommet (HPE Design System) | Interactive UI for starting runs, reviewing outputs, and making checkpoint decisions |

### Workflow Engine

The backend uses **LangGraph** to implement the workflow as a directed graph with an orchestrator-worker topology:

```
START → Orchestrator → Step 1 → Orchestrator → Step 2 → ... → Step 8 → END
```

The orchestrator reads the current state, determines the next uncompleted step, routes to the appropriate worker node, and detects when all steps are done. Each worker encapsulates the logic for one step, including loading the relevant skill prompt and invoking the LLM.

### Checkpoints

The workflow includes mandatory pause points (checkpoints) where the consultant reviews and approves the analysis before proceeding:

- **Checkpoint 1** (after Step 1): Review detected signals before pattern mapping
- **Checkpoint 2** (after Step 2): Confirm innovation direction and selected patterns
- **Checkpoint 3** (after Step 7): Review and adjust the risk map before experiment design

At each checkpoint, the consultant can **approve** (continue), **edit** (modify state and re-run), or **retry** (re-run the step from scratch).

### LLM Backend

The application supports two LLM backends, configurable via environment variable:

- **Azure OpenAI** — Production-grade, uses GPT-4o for reasoning and analysis
- **Ollama** — Local inference for air-gapped or cost-sensitive environments

---

## Design Principles

The application follows these design principles throughout:

1. **Customer-centric perspective** — Every output is framed from the customer's point of view, using their language and tied to their business outcomes
2. **Methodology fidelity** — Each step strictly follows the rules and output formats defined in the CXIF framework across its DETECT, ARCHITECT, and DE-RISK phases
3. **Sequential progression** — No step can be skipped; each builds on the outputs of the previous step
4. **Human-in-the-loop** — Checkpoints ensure the consultant reviews and validates AI-generated analysis before it feeds into downstream steps
5. **Multiple alternatives over premature refinement** — The Design phase prototypes 2-3 value proposition alternatives rather than converging on a single direction too early
6. **Test before committing** — The workflow ends with experiment plans, not implementation plans; the goal is to de-risk before building

---

*The BMI Consultant App is not a replacement for consultant expertise. It is an accelerator that ensures methodological rigor, speeds up structured analysis, and produces consistent, high-quality deliverables from raw customer data.*
