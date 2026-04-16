# BMI Consultant App — Usage Guide

This guide walks through how to use the BMI Consultant App from start to finish, including how to prepare input data, start a workflow run, interact with checkpoints, and interpret outputs.

---

## Prerequisites

Before using the application, ensure:

1. The Docker Compose stack is running (`make up` from the project root)
2. Database migrations have been applied (`make migrate`)
3. The `backend/.env` file is configured with valid LLM credentials (Azure OpenAI or Ollama)

Access points:
- **Web UI:** `http://localhost:8501`
- **Backend API:** `http://localhost:8000`
- **CLI:** `make cli -- <command>`

---

## Preparing Your Input Data

The workflow starts with **Voice of Customer (VoC) data** — raw customer research that the system will analyze for signals, patterns, and insights.

### Accepted Input Formats

| Format | How to Provide | Best For |
|--------|---------------|----------|
| **Plain text** | Paste directly into the text input field | Interview transcripts, meeting notes, qualitative observations |
| **Text file (.txt)** | Upload via file upload | Longer documents, compiled research notes |
| **CSV file (.csv)** | Upload via file upload | Structured survey results, feedback datasets, NPS data |

### Tips for Good Input Data

- **Include diverse sources.** The richer the input, the better the signal detection. Combine interview quotes, survey results, support ticket patterns, and competitive observations.
- **Use the customer's language.** Verbatim quotes produce better empathy profiles than summarized observations.
- **Include context.** Mention the customer segment, industry, and business context. The LLM uses this context to ground its analysis.
- **Volume matters less than relevance.** A focused set of 10 customer interview excerpts is more valuable than 1000 undifferentiated survey responses.

---

## Starting a New Run

### Using the Web UI

1. Open `http://localhost:8501` in your browser.
2. On the **Home Page**, choose your input method:
   - **Text Input** — Paste VoC data directly into the text area
   - **File Upload** — Upload a `.txt` or `.csv` file
   - **CSV Input** — Enter structured data as a table
3. Click **Start Run**.
4. The workflow will begin processing at Step 1 (Signal Scanning).

### Starting at a Specific Step

If you already have outputs from earlier steps (e.g., you have a customer profile and want to start at Step 5):

1. Select the target step from the **Start at Step** dropdown.
2. Fill in the **Upstream Fields** that appear — these are the outputs from prior steps that the selected step depends on:
   - Starting at Step 3 requires: signals and pattern direction
   - Starting at Step 5 requires: customer profile, value driver tree
   - Starting at Step 7 requires: value proposition canvas, business model canvas
3. Provide the upstream data in the expected format (JSON for structured data, markdown for text outputs).
4. Click **Start Run**.

### Using the CLI

```bash
# Start from raw text input
make cli -- run --input path/to/voc_data.txt

# Start from CSV input  
make cli -- run --input path/to/survey_results.csv
```

### Using the API

```bash
# Start a new run with text input
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"input_text": "Customer interview excerpts...", "input_format": "text"}'

# Start a new run with a file path (file must be accessible inside the container)
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"input_path": "/data/voc_data.csv", "input_format": "csv"}'
```

---

## The Workflow Experience

Once a run starts, the application processes each step sequentially. The UI displays the current step and its output as it completes.

### Step Progression

```
Step 1: Signal Scanning ──► [Checkpoint 1] ──► Step 2: Pattern Mapping ──► [Checkpoint 2]
  ──► Step 3: Customer Profile ──► Step 4: Success Measures
  ──► Step 5: Actionable Insights ──► Step 6: Design & Fit
  ──► Step 7: Risk Map ──► [Checkpoint 3] ──► Step 8: Experiment Plans
```

Steps between checkpoints run automatically. The workflow pauses at each checkpoint and waits for your decision.

### Reading Step Outputs

Each step produces a structured markdown output displayed in the UI. Outputs include:

- **Tables** with categorized data (signals, jobs, pains, gains, assumptions)
- **Rankings** showing priority or severity (High/Medium/Low, Severe/Moderate/Light)
- **Narrative sections** with analysis and interpretation
- **Structured frameworks** (Value Driver Tree, Business Model Canvas, PDSA plans)

Take time to read each output carefully. The quality of downstream analysis depends on the accuracy of upstream outputs.

---

## Working with Checkpoints

Checkpoints are the most important interaction points in the workflow. They are where your expertise and judgment matter most.

### Checkpoint 1 — After Step 1 (Signal Scanning)

**What you are reviewing:** The signals of change detected from your VoC data.

**What to check:**
- Are the signal zone assignments and Sustaining / Disruptive classifications accurate?
- Are the confidence levels and priority tiers (Act / Investigate / Monitor) appropriate? A high-priority signal should have multiple supporting data points.
- Are there signals the system missed that you know from domain expertise?
- Are any detected signals based on misinterpretation of the input data?

**Your options:**
| Action | When to Use |
|--------|------------|
| **Approve** | The signals are accurate and complete enough to proceed |
| **Edit** | You want to modify signal classifications, add missing signals, or remove false positives |
| **Retry** | The output quality is poor; re-run the step with the same input |

### Checkpoint 2 — After Step 2 (Pattern Mapping)

**What you are reviewing:** The recommended innovation direction (Invent vs. Shift) and the selected business model patterns.

**What to check:**
- Does the Invent/Shift recommendation align with your strategic context?
- Are the selected business model patterns relevant to the signals detected?
- Is the priority matrix sensible — are high-priority patterns the ones with the strongest signal alignment?

**Your options:**
| Action | When to Use |
|--------|------------|
| **Approve** | The direction and patterns match your strategic assessment |
| **Edit** | You want to change the direction (e.g., from Invent to Shift) or select different patterns |
| **Retry** | The pattern mapping does not align with the signals |

### Checkpoint 3 — After Step 7 (Risk Map)

**What you are reviewing:** The extracted DVF assumptions and their importance-evidence placement.

**What to check:**
- Are the assumptions correctly categorized (Desirability vs. Viability vs. Feasibility)?
- Are importance and evidence scores realistic? High-importance assumptions should be ones where being wrong would fundamentally break the business model.
- Is the "Test First" quadrant (high importance, low evidence) populated with the right assumptions?
- Does the DVF tension analysis identify a real conflict between categories?

**Your options:**
| Action | When to Use |
|--------|------------|
| **Approve** | The risk map accurately represents the model's critical uncertainties |
| **Edit** | You want to adjust importance/evidence scores, recategorize assumptions, or add missing ones |
| **Retry** | The assumptions do not reflect the business model from Step 6 |

---

## Resuming a Paused Run

If you leave the application while a run is paused at a checkpoint, you can resume later.

### Using the Web UI

1. On the Home Page, enter the **Session ID** from your previous run.
2. The UI will load the current state and display the pending checkpoint.
3. Make your checkpoint decision (Approve / Edit / Retry).

### Using the CLI

```bash
# Resume with approval
make cli -- resume --session-id <your-session-id> --decision approve

# Resume with edits (provide modified state as JSON)
make cli -- resume --session-id <your-session-id> --decision edit --edit-state '{"signals": [...]}'
```

### Using the API

```bash
# Resume with approval
curl -X POST http://localhost:8000/runs/<session-id>/resume \
  -H "Content-Type: application/json" \
  -d '{"decision": "approve"}'

# Resume with edits
curl -X POST http://localhost:8000/runs/<session-id>/resume \
  -H "Content-Type: application/json" \
  -d '{"decision": "edit", "edit_state": {"signals": [...]}}'
```

---

## Restarting from a Specific Step

If you want to re-run a step with different upstream data (e.g., after new customer interviews), you can restart from any step.

### Using the API

```bash
# Restart from Step 5 with updated customer profile
curl -X POST http://localhost:8000/runs/<session-id>/restart \
  -H "Content-Type: application/json" \
  -d '{"step_number": 5, "edit_state": {"customer_profile": "...updated profile..."}}'
```

This preserves outputs from steps before the restart point and re-runs everything from the specified step forward.

---

## Interpreting the Final Outputs

After completing all 8 steps, you will have a complete set of deliverables. Here is how to use them:

### For Stakeholder Presentations

| Deliverable | Use It To |
|-------------|-----------|
| **Signal Scan** (Step 1) | Show the market evidence driving the innovation initiative |
| **Customer Profile** (Step 3) | Demonstrate deep understanding of customer needs |
| **Value Driver Tree** (Step 4) | Quantify the business impact with measurable success criteria |
| **Business Model Canvas** (Step 6) | Present the proposed business model structure |
| **Fit Assessment** (Step 6) | Show what is validated vs. what is still assumed |

### For Experiment Execution

| Deliverable | Use It To |
|-------------|-----------|
| **Risk Map** (Step 7) | Explain why specific assumptions were prioritized for testing |
| **Experiment Plans** (Step 8) | Execute structured PDSA experiments with clear success criteria |
| **Experiment Worksheets** (Step 8) | Track observations, results, and decisions during each experiment |

### For Decision Making

| Deliverable | Use It To |
|-------------|-----------|
| **Importance-Evidence Matrix** (Step 7) | Determine which unknowns are most dangerous |
| **DVF Tension Analysis** (Step 7) | Understand where the business model has internal conflicts |
| **Experiment Decision Framework** (Step 8) | Decide whether to continue, pivot, or stop after each experiment |

---

## Updating Experiment Cards

After running experiments, you can update individual experiment cards with your results:

### Using the API

```bash
# Update an experiment card with results
curl -X PATCH http://localhost:8000/runs/<session-id>/experiment-cards/<card-id> \
  -H "Content-Type: application/json" \
  -d '{"updates": {"observations": "...", "outcome": "confirmed", "confidence": "medium"}}'
```

This supports the full PDSA cycle — the Do, Study, and Act phases happen outside the application, and you record results back for tracking.

---

## Best Practices

### Before Starting

- [ ] Gather VoC data from multiple sources (interviews, surveys, support data, competitive intel)
- [ ] Identify the customer segment you are analyzing
- [ ] Know your strategic context — is this about defending existing revenue or exploring new markets?

### During the Workflow

- [ ] Read every step output before approving checkpoints
- [ ] Use the Edit action when you have domain knowledge the AI lacks
- [ ] Do not rush through checkpoints — each one shapes all downstream analysis
- [ ] If an output seems generic or off-target, use Retry rather than Edit

### After Completing the Workflow

- [ ] Review the full set of deliverables as a cohesive story, not isolated documents
- [ ] Check that the experiment plans in Step 8 actually test the "Test First" assumptions from Step 7
- [ ] Present the Fit Assessment honestly — "Assumed" status is expected at this stage; it shows intellectual rigor, not weakness
- [ ] Sequence experiments from cheap/fast to expensive/slow as confidence grows

### Common Pitfalls to Avoid

| Pitfall | Why It Matters | What to Do Instead |
|---------|---------------|-------------------|
| Skipping checkpoint review | Downstream steps build on upstream outputs; errors compound | Review every checkpoint with domain expertise |
| Editing feature files to match outputs | The workflow methodology is the behavioral contract | Fix the input data or retry the step; do not alter the methodology |
| Treating all assumptions equally | Not all unknowns matter equally; testing low-importance assumptions wastes resources | Focus experiments on the high-importance / low-evidence quadrant |
| Running expensive experiments first | Early experiments should be cheap and fast to reduce uncertainty | Start with interviews and smoke tests; scale up as confidence grows |
| Accepting "Validated" status without evidence | Calling something "Validated" without test data creates false confidence | Be honest about what is tested and what is assumed |

---

## Quick Reference

### Key Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Health check | GET | `/health` |
| Start new run | POST | `/runs` |
| Load run state | GET | `/runs/{session_id}` |
| Resume at checkpoint | POST | `/runs/{session_id}/resume` |
| Restart from step | POST | `/runs/{session_id}/restart` |
| Update experiment card | PATCH | `/runs/{session_id}/experiment-cards/{card_id}` |

### Key CLI Commands

| Action | Command |
|--------|---------|
| Start run | `make cli -- run --input <path>` |
| Resume run | `make cli -- resume --session-id <id> --decision <approve\|edit\|retry>` |
| View logs | `make logs` |

### Checkpoint Summary

| Checkpoint | After Step | Key Question |
|------------|-----------|-------------|
| 1 | Signal Scanning | Are these the right signals? |
| 2 | Pattern Mapping | Is this the right innovation direction? |
| 3 | Risk Map | Are we testing the right assumptions? |

---

*For questions about the underlying methodology, refer to the [Workflow Concepts](02-workflow-concepts.md) document. For information about the application's purpose and architecture, refer to the [Application Objective](01-application-objective.md) document.*
