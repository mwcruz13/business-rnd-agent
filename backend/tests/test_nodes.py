import pytest

from backend.app.nodes.step1_signal import run_step


def test_step_rejects_empty_input():
    """Step 1 now runs through the LLM path and requires non-empty VoC data."""
    with pytest.raises(ValueError, match="cannot be empty"):
        run_step({})
