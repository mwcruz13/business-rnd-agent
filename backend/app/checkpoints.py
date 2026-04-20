from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from typing import cast

from backend.app.state import BMIWorkflowState


CheckpointDecision = Literal["approve", "edit", "retry"]


@dataclass(frozen=True)
class CheckpointDefinition:
    name: str
    after_step_name: str
    step_number: int
    required_state_fields: tuple[str, ...] = ()


CHECKPOINTS_BY_STEP = {
    "step1_signal": CheckpointDefinition(
        name="checkpoint_1",
        after_step_name="step1_signal",
        step_number=1,
    ),
    "step2_pattern": CheckpointDefinition(
        name="checkpoint_2",
        after_step_name="step2_pattern",
        step_number=2,
        required_state_fields=("pattern_direction",),
    ),
    "step3_profile": CheckpointDefinition(
        name="checkpoint_3",
        after_step_name="step3_profile",
        step_number=3,
    ),
    "step4_vpm": CheckpointDefinition(
        name="checkpoint_4",
        after_step_name="step4_vpm",
        step_number=4,
    ),
    "step5_define": CheckpointDefinition(
        name="checkpoint_5",
        after_step_name="step5_define",
        step_number=5,
    ),
    "step6_design": CheckpointDefinition(
        name="checkpoint_6",
        after_step_name="step6_design",
        step_number=6,
    ),
    "step7_risk": CheckpointDefinition(
        name="checkpoint_7",
        after_step_name="step7_risk",
        step_number=7,
    ),
    "step8_pdsa": CheckpointDefinition(
        name="checkpoint_8",
        after_step_name="step8_pdsa",
        step_number=8,
    ),
}

CHECKPOINTS_BY_NAME = {definition.name: definition for definition in CHECKPOINTS_BY_STEP.values()}


# Fields that must be present in initial_state to start execution at a given step.
# Step 1 only needs voc_data (the universal input).
REQUIRED_UPSTREAM_STATE: dict[str, tuple[str, ...]] = {
    "step1_signal": ("voc_data",),
    "step2_pattern": ("voc_data", "signals"),
    "step3_profile": ("voc_data", "signals", "pattern_direction", "selected_patterns"),
    "step4_vpm": ("voc_data", "signals", "pattern_direction", "selected_patterns", "customer_profile"),
    "step5_define": ("voc_data", "signals", "pattern_direction", "selected_patterns", "customer_profile", "value_driver_tree", "actionable_insights"),
    "step6_design": ("voc_data", "signals", "pattern_direction", "selected_patterns", "customer_profile", "value_driver_tree", "actionable_insights", "value_proposition_canvas", "fit_assessment"),
    "step7_risk": ("voc_data", "signals", "pattern_direction", "selected_patterns", "customer_profile", "value_driver_tree", "actionable_insights", "value_proposition_canvas", "fit_assessment", "business_model_canvas"),
    "step8_pdsa": ("voc_data", "signals", "pattern_direction", "selected_patterns", "customer_profile", "value_driver_tree", "actionable_insights", "value_proposition_canvas", "fit_assessment", "business_model_canvas", "assumptions"),
}


def validate_initial_state_for_step(step_name: str, state: BMIWorkflowState) -> None:
    """Raise *ValueError* if *state* is missing fields required to start at *step_name*."""
    required = REQUIRED_UPSTREAM_STATE.get(step_name)
    if required is None:
        raise ValueError(f"Unknown step: {step_name}")
    missing = [f for f in required if not state.get(f)]
    if missing:
        raise ValueError(
            f"Cannot start at {step_name}: missing required upstream state — {', '.join(missing)}"
        )


def validate_decision(decision: str) -> CheckpointDecision:
    if decision not in {"approve", "edit", "retry"}:
        raise ValueError(f"Unsupported decision: {decision}")
    return cast(CheckpointDecision, decision)


def get_checkpoint_for_step(step_name: str) -> CheckpointDefinition | None:
    return CHECKPOINTS_BY_STEP.get(step_name)


def validate_checkpoint_state(checkpoint_name: str, state: BMIWorkflowState) -> None:
    checkpoint = CHECKPOINTS_BY_NAME.get(checkpoint_name)
    if checkpoint is None:
        raise ValueError(f"Unsupported checkpoint: {checkpoint_name}")

    for field_name in checkpoint.required_state_fields:
        value = state.get(field_name)
        if not value:
            raise ValueError(f"Checkpoint {checkpoint.name} requires {field_name} before proceeding")
