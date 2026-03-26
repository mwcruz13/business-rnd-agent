# Signals of Change → Business Model Pattern Routing

## Purpose

This document records the rationale for mapping SOC Radar signal classifications to Strategyzer business model pattern directions (INVENT vs SHIFT). It was created after verifying the routing logic in `step2_pattern.py` against the original framework by Scott D. Anthony, Clayton Christensen, and Erik Roth.

---

## Source Framework

**Primary source:** Scott D. Anthony, Clayton M. Christensen, and Erik A. Roth — *Seeing What's Next: Using the Theories of Innovation to Predict Industry Change* (Harvard Business School Press, 2004).

**Supporting sources:**
- Clayton Christensen Institute — [Disruptive Innovation Theory](https://www.christenseninstitute.org/theory/disruptive-innovation/)
- Clayton M. Christensen, Michael E. Raynor, Rory McDonald — "What Is Disruptive Innovation?" (*Harvard Business Review*, December 2015)
- Clayton M. Christensen and Michael E. Raynor — *The Innovator's Solution* (Harvard Business Press, 2003), pp. 23–45

---

## Two Types of Disruption

The framework distinguishes two fundamental disruption mechanisms:

### Low-End Disruption

Targets **overserved customers** — those paying for performance they do not use or value. The disruptor enters at the bottom of the existing market with a simpler, cheaper alternative, then moves upmarket.

Key characteristics:
- The incumbent's existing business model *can* be adapted (simplify, reprice, strip excess features)
- The disruptor uses a lower cost structure to profitably serve the least demanding customers
- The incumbent is not initially motivated to defend this low-margin segment

**Low-end disruption litmus test** (from SKILL.md / *Seeing What's Next*):
1. Are mainstream customers overserved on performance they do not value?
2. Can the entrant profitably serve these customers at lower prices?
3. Does the entrant use a fundamentally different business model or cost structure?

### New-Market Disruption

Targets **nonconsumers** — a population that was previously unserved. The disruptor creates demand where none existed before.

Key characteristics:
- The incumbent needs a *fundamentally different* business model because the existing one was never designed to serve this population
- The disruptor competes against nonconsumption, not against the incumbent directly
- Success requires a new value network

---

## Routing Decision Table

| Signal Zone | Classification | Pattern Direction | Rationale |
|---|---|---|---|
| Nonconsumption | Disruptive — New-Market | **INVENT** | No existing model serves this population |
| New-Market Foothold | Disruptive — New-Market | **INVENT** | New demand requires a new business model |
| Overserved Customers | Disruptive — Low-End | **SHIFT** | Existing model can be simplified and repriced |
| Low-End Foothold | Disruptive — Low-End | **SHIFT** | Incumbent adapts by moving down-market |
| Enabling Technology | Either | **INVENT or SHIFT** | Depends on whether the current model can absorb the technology |
| Business Model Anomaly | Disruptive (either) | **INVENT** | Entrant's model is fundamentally different |
| Regulatory / Policy Shift | Disruptive (either) | **INVENT** | New rules create new markets |
| Any zone | Sustaining | **SHIFT** | Sustaining innovations improve within the existing model |

---

## Edge Case: Low-End + Business Model Anomaly

If a low-end disruptor *also* has a fundamentally different business model (not just a cheaper version of the same model), this surfaces as a separate **Business Model Anomaly** signal. The framework self-corrects:

- `Overserved Customers` + `Disruptive — Low-End` alone → **SHIFT**
- If a `Business Model Anomaly` signal also exists at higher priority → **INVENT**

The `_find_best_disruptive_signal()` function in `step2_pattern.py` handles this by scanning *all* interpreted signals for the highest-priority disruptive signal, rather than relying on position `[0]`. If a Business Model Anomaly signal scores higher than the Overserved Customers signal, it takes routing precedence and triggers INVENT.

---

## Implementation in Code

### Production routing (`backend/app/nodes/step2_pattern.py`)

The INVENT path triggers when:
- Classification is `Disruptive — New-Market` (or `Disruptive - New-Market`), **OR**
- Normalized zone is in `{New-Market Foothold, Nonconsumption, Regulatory / Policy Shift, Business Model Anomaly}`

Everything else falls to SHIFT.

### Zone normalization

The LLM (via SKILL.md) may produce abbreviated zone names. A normalization map converts them to canonical pattern-library names before routing:

| LLM Output | Canonical Name |
|---|---|
| Enabling Tech | Enabling Technology |
| Overserved | Overserved Customers |
| Regulatory Shift | Regulatory / Policy Shift |

---

## Internal Codebase Consistency

Three independent sources within the project agree on the routing logic:

1. **Strategic analysis** (`assistant/docs/strategic-analysis-standalone-bmi-app.md`) — decision table mapping signal zones to pattern directions
2. **Step 2 prompt** (`backend/app/prompts/step2_pattern_matcher.md`) — "Overserved customers or low-end disruption usually favors SHIFT"
3. **SOC Radar SKILL** (`backend/app/skills/soc-radar/SKILL.md`) — low-end litmus test implies incumbent adaptation (SHIFT)

All three are consistent with Anthony/Christensen/Roth's original framework.
