from typing import TypedDict


class BMIWorkflowState(TypedDict, total=False):
    session_id: str
    session_name: str
    current_step: str
    run_status: str
    pending_checkpoint: str
    input_type: str
    llm_backend: str
    voc_data: str
    signals: list[dict[str, object]]
    signal_recommendations: list[dict[str, object]]
    interpreted_signals: list[dict[str, object]]
    priority_matrix: list[dict[str, object]]
    coverage_gaps: list[dict[str, str]]
    agent_recommendation: str
    pattern_direction: str
    selected_patterns: list[str]
    pattern_rationale: str
    customer_profile: str
    empathy_gap_questions: str
    supplemental_voc: str
    value_driver_tree: str
    actionable_insights: str
    value_proposition_canvas: str
    fit_assessment: str
    business_model_canvas: str
    assumptions: str
    step7_structured: dict[str, object]
    experiment_selections: str
    experiment_plans: str
    experiment_worksheets: str
    experiment_cards: list[dict[str, object]]
    # Orchestration fields (Phase 1)
    next_step: str
    completed_steps: list[str]
