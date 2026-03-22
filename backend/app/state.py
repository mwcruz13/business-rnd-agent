from typing import TypedDict


class BMIWorkflowState(TypedDict, total=False):
    session_id: str
    current_step: str
    input_type: str
    llm_backend: str
    voc_data: str
    signals: list[dict[str, object]]
    interpreted_signals: list[dict[str, object]]
    priority_matrix: list[dict[str, object]]
    agent_recommendation: str
    pattern_direction: str
    selected_patterns: list[str]
    pattern_rationale: str
    customer_profile: str
    value_driver_tree: str
    actionable_insights: str
    value_proposition_canvas: str
    fit_assessment: str
    business_model_canvas: str
    assumptions: str
    experiment_selections: str
    experiment_plans: str
    experiment_worksheets: str
