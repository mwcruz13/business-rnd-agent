"""Run workflow Step 1 (SOC Radar signal scan) on a VoC input file and save results as JSON.

Uses the two-pass architecture: Step 1a (Scan+Interpret) then Step 1b (Prioritize+Recommend).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.app.nodes.step1a_signal_scan import run_step as run_step1a
from backend.app.nodes.step1b_signal_recommend import run_step as run_step1b
from backend.app.state import BMIWorkflowState


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python -m backend.evaluation.run_step1_eval <input.txt> <output.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    voc_data = input_path.read_text(encoding="utf-8").strip()
    if not voc_data:
        print("Error: input file is empty")
        sys.exit(1)

    state: BMIWorkflowState = {
        "session_id": "eval-step1",
        "current_step": "ingest",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": voc_data,
    }

    print(f"Running Step 1a (Scan + Interpret) on: {input_path}")
    state_after_1a = run_step1a(state)
    print(f"  Step 1a complete — signals: {len(state_after_1a.get('signals', []))}, "
          f"interpreted: {len(state_after_1a.get('interpreted_signals', []))}")

    print("Running Step 1b (Prioritize + Recommend)...")
    result = run_step1b(state_after_1a)

    # Extract all step 1 output fields (1a + 1b)
    step1_fields = [
        "signals",
        "interpreted_signals",
        "coverage_gaps",
        "priority_matrix",
        "reinforcement_map",
        "signal_recommendations",
        "watching_briefs",
        "agent_recommendation",
    ]
    report = {k: result[k] for k in step1_fields if k in result}
    report["_meta"] = {
        "input_file": str(input_path),
        "step": "step1_signal_scan (1a+1b)",
        "llm_backend": "azure",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Step 1 report saved to: {output_path}")
    print(f"  Signals detected: {len(report.get('signals', []))}")
    print(f"  Interpreted signals: {len(report.get('interpreted_signals', []))}")
    print(f"  Coverage gaps: {len(report.get('coverage_gaps', []))}")
    print(f"  Priority matrix entries: {len(report.get('priority_matrix', []))}")
    print(f"  Recommendations (Act/Investigate): {len(report.get('signal_recommendations', []))}")
    print(f"  Watching briefs (Monitor): {len(report.get('watching_briefs', []))}")


if __name__ == "__main__":
    main()
