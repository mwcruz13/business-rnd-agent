from typing import Literal
from typing import cast


CheckpointDecision = Literal["approve", "edit", "retry"]


def validate_decision(decision: str) -> CheckpointDecision:
    if decision not in {"approve", "edit", "retry"}:
        raise ValueError(f"Unsupported decision: {decision}")
    return cast(CheckpointDecision, decision)
