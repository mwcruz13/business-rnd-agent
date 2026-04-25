# Plan: Signal Repository Integration — Updated Strategy

## Changes Requested
1. Add Pathway B: In-app signal generation from uploaded CSV (users upload survey CSV → app calls step1a/step1b → signals generated automatically)
2. Remove Streamlit — React frontend-react only (Grommet HPE theme)

## Status: Full document drafted, needs to be written to `bmi-consultant-app/docs/research/Signals-pipeline-integration-plan.md`

## Key Additions
- "Two Signal Generation Pathways" section: Pathway A (batch ingestion from offline JSON — bootstrap) vs Pathway B (in-app from uploaded CSV — future primary)
- Steps 12-15 (Future Layer 5): Refactor bu_classify_pipeline.py into importable module, signal generation service calling existing run_step1a_llm/run_step1b_llm, POST /signals/generate endpoint, React upload UI
- All Streamlit references removed; Phase 4 is React + Grommet only (step 11)
- Pathway B explicitly reuses existing step1a/step1b functions without modification
