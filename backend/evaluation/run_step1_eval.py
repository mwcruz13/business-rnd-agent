"""Run workflow Step 1 (SOC Radar signal scan) on a VoC input file and save results as JSON."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from backend.app.nodes.step1_signal import run_step
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

    print(f"Running Step 1 signal scan on: {input_path}")
    result = run_step(state)

    # Extract only the step 1 output fields
    step1_fields = [
        "signals",
        "interpreted_signals",
        "priority_matrix",
        "coverage_gaps",
        "signal_recommendations",
        "agent_recommendation",
    ]
    report = {k: result[k] for k in step1_fields if k in result}
    report["_meta"] = {
        "input_file": str(input_path),
        "step": "step1_signal_scan",
        "llm_backend": "azure",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Step 1 report saved to: {output_path}")
    print(f"  Signals detected: {len(report.get('signals', []))}")
    print(f"  Priority matrix entries: {len(report.get('priority_matrix', []))}")
    print(f"  Recommendations: {len(report.get('signal_recommendations', []))}")


if __name__ == "__main__":
    main()
