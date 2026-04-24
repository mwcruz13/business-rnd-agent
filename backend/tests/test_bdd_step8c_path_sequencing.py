from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step8c_path_sequencing_llm import run_step8c_llm
from backend.app.state import BMIWorkflowState


scenarios("features/step8c-path-sequencing.feature")


class _FakeStructuredInvoker:
    def __init__(self, payload):
        self._payload = payload

    def invoke(self, messages):  # noqa: D401 - langchain-compatible signature
        return self._payload


class _FakeLLM:
    def __init__(self, payload):
        self._payload = payload

    def with_structured_output(self, schema):
        return _FakeStructuredInvoker(schema(**self._payload))


@given(
    "a workflow state with experiment card selections ready for path sequencing",
    target_fixture="workflow_state",
)
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-8c",
        "current_step": "card_selection",
        "input_type": "text",
        "llm_backend": "azure",
        "experiment_card_selections": [
            {
                "assumption": "I believe operational buyers need proof onboarding complexity drops before they engage implementation.",
                "category": "Desirability",
                "existing_evidence_level": "None",
                "candidates": [
                    {
                        "card_name": "Problem Interviews",
                        "evidence_strength": "Weak",
                        "rationale": "Validate pain language before testing demand mechanics.",
                    },
                    {
                        "card_name": "Landing Page",
                        "evidence_strength": "Medium",
                        "rationale": "Check message-to-action behavior once pain is clear.",
                    },
                    {
                        "card_name": "Fake Door",
                        "evidence_strength": "Medium",
                        "rationale": "Test commitment for the onboarding simplification proposition.",
                    },
                ],
                "primary_card_name": "Problem Interviews",
                "alternatives_considered": "Held A/B testing for later once baseline conversion exists.",
            },
            {
                "assumption": "I believe the team can deliver guided onboarding flow without manual recovery in most deployments.",
                "category": "Feasibility",
                "existing_evidence_level": "Weak",
                "candidates": [
                    {
                        "card_name": "Throwaway Prototype",
                        "evidence_strength": "Medium",
                        "rationale": "Simulates operational workflow quickly with minimal build investment.",
                    },
                    {
                        "card_name": "Usability Testing",
                        "evidence_strength": "Medium",
                        "rationale": "Reveals process failure points and intervention load.",
                    },
                    {
                        "card_name": "Wizard of Oz",
                        "evidence_strength": "Strong",
                        "rationale": "Escalates to realistic execution before full automation commitment.",
                    },
                ],
                "primary_card_name": "Throwaway Prototype",
                "alternatives_considered": "Skipped weak-tier cards because weak evidence already exists.",
            },
        ],
    }


@when("the Step 8c path sequencing node runs", target_fixture="step8c_result")
def step8c_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    payload = {
        "paths": [
            {
                "assumption": "I believe operational buyers need proof onboarding complexity drops before they engage implementation.",
                "category": "Desirability",
                "existing_evidence_level": "None",
                "path_cards": [
                    {
                        "card_name": "Problem Interviews",
                        "evidence_strength": "Weak",
                        "sequence_reason": "Start by confirming pain framing directly.",
                    },
                    {
                        "card_name": "Landing Page",
                        "evidence_strength": "Medium",
                        "sequence_reason": "Move to behavior-level signal once pain is validated.",
                    },
                    {
                        "card_name": "Fake Door",
                        "evidence_strength": "Medium",
                        "sequence_reason": "Deepen commitment signal with concrete intent interaction.",
                    },
                ],
                "sequencing_rationale": "Progresses from language validation to behavior signal to commitment check.",
            },
            {
                "assumption": "I believe the team can deliver guided onboarding flow without manual recovery in most deployments.",
                "category": "Feasibility",
                "existing_evidence_level": "Weak",
                "path_cards": [
                    {
                        "card_name": "Throwaway Prototype",
                        "evidence_strength": "Medium",
                        "sequence_reason": "Begin with medium evidence due to existing weak signals.",
                    },
                    {
                        "card_name": "Usability Testing",
                        "evidence_strength": "Medium",
                        "sequence_reason": "Evaluate intervention load and process breakdowns.",
                    },
                    {
                        "card_name": "Wizard of Oz",
                        "evidence_strength": "Strong",
                        "sequence_reason": "Escalate to strong evidence before full build decision.",
                    },
                ],
                "sequencing_rationale": "Escalates evidence strength while preserving feasibility learning continuity.",
            },
        ]
    }
    return run_step8c_llm(workflow_state, _FakeLLM(payload))


@when("the Step 8c path sequencing node runs without an LLM", target_fixture="step8c_result")
def step8c_result_without_llm(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step8c_llm(workflow_state, None)


@then('the workflow current step is "path_sequencing"')
def assert_current_step(step8c_result: BMIWorkflowState) -> None:
    assert step8c_result["current_step"] == "path_sequencing"


@then("the workflow state contains experiment paths")
def assert_paths_present(step8c_result: BMIWorkflowState) -> None:
    paths = step8c_result.get("experiment_paths")
    assert isinstance(paths, list)
    assert paths


@then("each assumption path has exactly 3 cards")
def assert_three_cards(step8c_result: BMIWorkflowState) -> None:
    for path in step8c_result["experiment_paths"]:
        assert len(path["path_cards"]) == 3


@then("each path is non-decreasing by evidence strength")
def assert_non_decreasing_evidence(step8c_result: BMIWorkflowState) -> None:
    order = {"Weak": 1, "Medium": 2, "Strong": 3}
    for path in step8c_result["experiment_paths"]:
        strengths = [order[card["evidence_strength"]] for card in path["path_cards"]]
        assert strengths == sorted(strengths), f"Expected non-decreasing strengths, got {strengths}"


@then("each path card is selected from that assumption candidate list")
def assert_path_cards_are_allowed(step8c_result: BMIWorkflowState, workflow_state: BMIWorkflowState) -> None:
    by_assumption = {
        selection["assumption"]: {
            candidate["card_name"] for candidate in selection["candidates"]
        }
        for selection in workflow_state["experiment_card_selections"]
    }
    for path in step8c_result["experiment_paths"]:
        allowed = by_assumption[path["assumption"]]
        for card in path["path_cards"]:
            assert card["card_name"] in allowed
