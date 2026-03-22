from backend.app.graph import WORKFLOW_STEP_ORDER, build_graph


def test_graph_runs_all_eight_steps_end_to_end():
    graph = build_graph()

    result = graph.invoke(
        {
            "session_id": "graph-test-session",
            "input_type": "text",
            "llm_backend": "azure",
            "voc_data": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        }
    )

    assert len(WORKFLOW_STEP_ORDER) == 8
    assert result["current_step"] == "pdsa_plan"
    assert result["signals"]
    assert result["experiment_selections"]
    assert result["experiment_plans"]
    assert result["experiment_worksheets"]
