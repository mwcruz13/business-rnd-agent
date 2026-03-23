from __future__ import annotations

import json
from typing import Any

import streamlit as st


CHECKPOINT_LABELS = {
    "checkpoint_1": "Checkpoint 1: Signal Scan Review",
    "checkpoint_1_5": "Checkpoint 1.5: Pattern Direction Review",
    "checkpoint_2": "Checkpoint 2: Risk Map Review",
}

STEP_ARTIFACTS = {
    "signal_scan": ["signals", "interpreted_signals", "priority_matrix", "coverage_gaps", "agent_recommendation"],
    "pattern_select": ["pattern_direction", "selected_patterns", "pattern_rationale", "agent_recommendation"],
    "risk_map": [
        "customer_profile",
        "value_driver_tree",
        "actionable_insights",
        "value_proposition_canvas",
        "business_model_canvas",
        "fit_assessment",
        "assumptions",
    ],
    "pdsa_plan": ["experiment_selections", "experiment_plans", "experiment_worksheets"],
}


def render_run_summary(run_state: dict[str, Any]) -> None:
    status = run_state.get("run_status", "unknown")
    pending_checkpoint = run_state.get("pending_checkpoint") or "none"
    cols = st.columns(4)
    cols[0].metric("Session", str(run_state.get("session_id", "-"))[:8])
    cols[1].metric("Step", str(run_state.get("current_step", "-")))
    cols[2].metric("Status", status)
    cols[3].metric("Checkpoint", pending_checkpoint)


def render_checkpoint_editor(run_state: dict[str, Any], *, editor_key: str) -> None:
    checkpoint_name = str(run_state.get("pending_checkpoint") or "")
    if not checkpoint_name:
        return

    st.subheader(CHECKPOINT_LABELS.get(checkpoint_name, checkpoint_name))
    st.caption("Review the generated output. Approve to continue, edit the JSON payload to override fields, or retry the same step.")

    edit_payload = json.dumps(build_editable_payload(run_state, checkpoint_name), indent=2, ensure_ascii=True)
    st.text_area(
        "Editable checkpoint payload",
        value=edit_payload,
        height=260,
        key=editor_key,
        help="Only the fields in this JSON are sent back to the backend for an edit decision.",
    )


def render_artifacts(run_state: dict[str, Any]) -> None:
    for section_title, field_names in _build_sections(run_state).items():
        with st.expander(section_title, expanded=section_title.startswith("Current")):
            for field_name in field_names:
                if field_name in run_state and run_state[field_name]:
                    st.markdown(f"**{field_name}**")
                    _render_value(run_state[field_name])


def build_editable_payload(run_state: dict[str, Any], checkpoint_name: str) -> dict[str, Any]:
    if checkpoint_name == "checkpoint_1":
        return _subset(
            run_state,
            ["signals", "interpreted_signals", "priority_matrix", "agent_recommendation"],
        )
    if checkpoint_name == "checkpoint_1_5":
        return _subset(
            run_state,
            ["pattern_direction", "selected_patterns", "pattern_rationale", "agent_recommendation"],
        )
    if checkpoint_name == "checkpoint_2":
        return _subset(
            run_state,
            [
                "customer_profile",
                "value_driver_tree",
                "actionable_insights",
                "value_proposition_canvas",
                "business_model_canvas",
                "fit_assessment",
                "assumptions",
            ],
        )
    return {}


def parse_edit_payload(raw_text: str) -> dict[str, Any]:
    parsed = json.loads(raw_text)
    if not isinstance(parsed, dict):
        raise ValueError("Checkpoint edit payload must be a JSON object")
    return parsed


def _build_sections(run_state: dict[str, Any]) -> dict[str, list[str]]:
    current_step = str(run_state.get("current_step", ""))
    sections: dict[str, list[str]] = {}

    current_fields = STEP_ARTIFACTS.get(current_step, [])
    if current_fields:
        sections[f"Current Step Outputs: {current_step}"] = current_fields

    final_fields = STEP_ARTIFACTS.get("pdsa_plan", [])
    if any(run_state.get(field_name) for field_name in final_fields):
        sections["Final Experiment Plan"] = final_fields

    sections["Run Context"] = ["voc_data", "input_type", "llm_backend"]
    return sections


def _subset(run_state: dict[str, Any], field_names: list[str]) -> dict[str, Any]:
    return {field_name: run_state[field_name] for field_name in field_names if field_name in run_state}


def _render_value(value: Any) -> None:
    if isinstance(value, (dict, list)):
        st.json(value, expanded=False)
        return
    if isinstance(value, str) and len(value) > 200:
        st.code(value, language="markdown")
        return
    st.write(value)