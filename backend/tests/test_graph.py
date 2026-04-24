from backend.app.graph import WORKFLOW_STEP_ORDER, build_graph


def test_graph_runs_all_workflow_steps_end_to_end():
    graph = build_graph()

    result = graph.invoke(
        {
            "session_id": "graph-test-session",
            "input_type": "text",
            "llm_backend": "azure",
            "voc_data": "Customers report onboarding friction, too many manual steps, and delays before they reach value.",
        },
        {"recursion_limit": 64},
    )

    assert "step8a_evidence_audit" in WORKFLOW_STEP_ORDER
    assert "step8c_path_sequencing" in WORKFLOW_STEP_ORDER
    assert "step8_pdsa" in WORKFLOW_STEP_ORDER
    assert "step9_artifact_designer" in WORKFLOW_STEP_ORDER
    assert result["current_step"] == "pdsa_plan"
    assert result["signals"]
    assert result["assumption_evidence_audit"]
    assert result["experiment_paths"]
    assert result["experiment_selections"]
    assert result["experiment_plans"]
    assert result["experiment_worksheets"]
    assert result["artifact_designs"]
