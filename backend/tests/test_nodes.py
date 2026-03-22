from backend.app.nodes.step1_signal import run_step


def test_step_updates_current_step():
    assert run_step({})["current_step"] == "signal_scan"
