# Step 1 Signal Scan Contract

This document defines the target output contract for the `signal_scan` workflow state emitted by Step 1.

## Purpose

Step 1 must transform raw VoC material into a multi-signal SOC Radar scan that can be used by Step 2, the consultant checkpoint, and the Streamlit UI.

Step 1 must not collapse a full document into a single keyword-driven signal. It must emit a portfolio of detected signals, an interpretation for each signal, a priority matrix sorted by urgency, signal-zone blind spots, and a short recommendation summary for the consultant.

## Required State Fields

### `signals`

List of detected signals. Each item must be a JSON object with at least these fields:

- `signal_id`: stable identifier for downstream correlation
- `signal`: concise signal title
- `zone`: one of the seven SOC Radar zones from `soc-radar-pattern-library.json`
- `source_type`: where the signal came from, for example `Internal VoC`
- `observable_behavior`: observation separated from inference
- `source_sections`: list of source headings or sections where evidence was found
- `evidence`: list of supporting excerpts from the source document

### `interpreted_signals`

List aligned to `signals` by `signal_id`. Each item must include:

- `signal_id`
- `signal`
- `zone`
- `classification`: `Sustaining`, `Disruptive — Low-End`, or `Disruptive — New-Market`
- `filters`: list of SOC Radar filter names actually used
- `confidence`: `Low`, `Medium`, or `High`
- `rationale`
- `alternative_explanation`
- `key_evidence_gap`

### `priority_matrix`

List of prioritized signals sorted by:

1. descending `score`
2. disruptive classifications ahead of sustaining classifications when scores are tied
3. alphabetical `signal` as a final stable tie-break

Each entry must include:

- `signal_id`
- `signal`
- `impact`
- `speed`
- `score`
- `tier`
- `rationale`

### `coverage_gaps`

List of signal zones not observed in the source material. Each item must include:

- `zone`
- `note`

### `agent_recommendation`

Short consultant-facing summary that:

- names the highest-priority signals
- distinguishes disruptive pressure from sustaining pressure
- notes the major blind spots from `coverage_gaps`

## Compatibility Requirements

Step 2 currently depends on the first item in `interpreted_signals` and `priority_matrix`.

To preserve compatibility:

- the highest-priority signal must appear first in both lists
- each interpreted signal must keep `zone` and `classification`
- each priority item must keep `signal`, `impact`, `speed`, `score`, and `tier`

## Minimum Quality Bar

For realistic VoC documents, Step 1 should usually emit multiple signals when the source discusses:

- customer needs or jobs
- competitive shifts
- business model changes
- access barriers
- enabling infrastructure constraints
- non-consumer opportunities

The signal scan should only emit one signal when the input genuinely contains only one discrete signal.