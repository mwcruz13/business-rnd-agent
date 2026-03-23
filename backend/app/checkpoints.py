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
        name="checkpoint_1_5",
        after_step_name="step2_pattern",
        step_number=2,
        required_state_fields=("pattern_direction", "selected_patterns"),
    ),
    "step7_risk": CheckpointDefinition(
        name="checkpoint_2",
        after_step_name="step7_risk",
        step_number=7,
    ),
}

CHECKPOINTS_BY_NAME = {definition.name: definition for definition in CHECKPOINTS_BY_STEP.values()}


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
        if field_name == "selected_patterns":
            if not isinstance(value, list) or not value:
                raise ValueError("Checkpoint 1.5 requires consultant-selected pattern(s) before proceeding")
        elif not value:
            raise ValueError(f"Checkpoint {checkpoint.name} requires {field_name} before proceeding")
