"""Phase 3 validation tests — prompt scoping, empathy gate diversity, VoC passthrough."""
from backend.app.nodes.step3_profile_llm import (
    check_empathy_gate, CustomerEmpathyProfile, CustomerJob, CustomerPain, CustomerGain,
)
from backend.app.skills.loader import PromptAssetLoader


def test_all_phase_specific_prompts_load():
    loader = PromptAssetLoader()
    for name in ["step3_empathize", "step4_measure_define", "step5_value_proposition",
                  "step6_business_model", "step7_risk_map"]:
        asset = loader.load_step_prompt(name)
        assert asset.kind == "prompt"
        assert len(asset.body) > 100, f"{name} prompt body too short"


def test_step3_prompt_contains_trigger_questions():
    loader = PromptAssetLoader()
    asset = loader.load_step_prompt("step3_empathize")
    assert "What important issue is the customer trying to resolve" in asset.body
    assert "How does the customer want to be perceived" in asset.body
    assert "What makes the customer feel bad" in asset.body
    assert "How does the customer measure success" in asset.body


def test_step5_prompt_contains_supplier_perspective():
    loader = PromptAssetLoader()
    asset = loader.load_step_prompt("step5_value_proposition")
    assert "SUPPLIER" in asset.body
    assert "supplier's perspective" in asset.body.lower() or "SUPPLIER'S" in asset.body


def test_step7_prompt_contains_suggested_quadrant_framing():
    loader = PromptAssetLoader()
    asset = loader.load_step_prompt("step7_risk_map")
    assert "SUGGESTIONS" in asset.body
    assert "Test first" in asset.body


def test_empathy_gate_passes_diverse_profile():
    profile = CustomerEmpathyProfile(
        customer_segment="Test",
        jobs=[
            CustomerJob(type="Functional", job="Do X", importance="High"),
            CustomerJob(type="Social", job="Look good", importance="Medium"),
        ],
        pains=[
            CustomerPain(type="Functional", pain="Hard", severity="Severe"),
            CustomerPain(type="Emotional", pain="Stressful", severity="Moderate"),
        ],
        gains=[
            CustomerGain(type="Functional", gain="Faster", relevance="Essential"),
            CustomerGain(type="Financial", gain="Save money", relevance="Desired"),
        ],
    )
    gaps = check_empathy_gate(profile)
    assert gaps == {}


def test_empathy_gate_fires_for_single_type_jobs():
    profile = CustomerEmpathyProfile(
        customer_segment="Test",
        jobs=[
            CustomerJob(type="Functional", job="Do X", importance="High"),
            CustomerJob(type="Functional", job="Do Y", importance="Medium"),
            CustomerJob(type="Functional", job="Do Z", importance="Low"),
        ],
        pains=[
            CustomerPain(type="Functional", pain="Hard", severity="Severe"),
            CustomerPain(type="Emotional", pain="Stressful", severity="Moderate"),
        ],
        gains=[
            CustomerGain(type="Functional", gain="Faster", relevance="Essential"),
            CustomerGain(type="Financial", gain="Save money", relevance="Desired"),
        ],
    )
    gaps = check_empathy_gate(profile)
    assert "jobs" in gaps
    assert "pains" not in gaps
    assert "gains" not in gaps
    # Should only return trigger questions for types NOT already present
    for type_name, _ in gaps["jobs"]:
        assert type_name != "Functional"


def test_empathy_gate_fires_for_empty_section():
    profile = CustomerEmpathyProfile(
        customer_segment="Test",
        jobs=[],
        pains=[
            CustomerPain(type="Functional", pain="Hard", severity="Severe"),
        ],
        gains=[
            CustomerGain(type="Functional", gain="Faster", relevance="Essential"),
            CustomerGain(type="Financial", gain="Save money", relevance="Desired"),
        ],
    )
    gaps = check_empathy_gate(profile)
    assert "jobs" in gaps
    assert len(gaps["jobs"]) == 4  # All 4 type trigger questions for empty section
    assert "pains" in gaps  # Single-type pains should fire


def test_step5_build_messages_includes_voc_data():
    from backend.app.nodes.step5_define_llm import _build_messages
    state = {
        "customer_profile": "## Customer Empathy Profile\nTest profile content",
        "actionable_insights": "## Context Analysis\nTest insights",
        "value_driver_tree": "## Value Driver Tree\nTest tree",
        "selected_patterns": ["Cost Differentiators"],
        "pattern_direction": "shift",
        "voc_data": "Customer complaint: onboarding is too complex and takes too long",
    }
    messages = _build_messages(state)
    user_msg = messages[1].content
    assert "Original Voice of Customer evidence" in user_msg
    assert "onboarding is too complex" in user_msg


def test_step6_build_messages_includes_voc_data():
    from backend.app.nodes.step6_design_llm import _build_messages
    state = {
        "value_proposition_canvas": "## Value Proposition Canvas\nTest VPC content",
        "customer_profile": "## Customer Empathy Profile\nTest profile",
        "actionable_insights": "## Context Analysis\nTest insights",
        "selected_patterns": ["Cost Differentiators"],
        "pattern_direction": "shift",
        "voc_data": "Customer feedback: we need faster activation with less manual steps",
    }
    messages = _build_messages(state)
    user_msg = messages[1].content
    assert "Original Voice of Customer evidence" in user_msg
    assert "faster activation" in user_msg
