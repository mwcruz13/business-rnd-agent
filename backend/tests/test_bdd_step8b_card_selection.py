from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step8b_card_selection_llm import run_step8b_llm
from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.state import BMIWorkflowState


scenarios("features/step8b-card-selection.feature")


DESIRABILITY_A = "I believe operational buyers need proof that onboarding complexity drops before they will engage implementation."
DESIRABILITY_B = "I believe customers will only react if they see feature-level value messaging in-market before booking a meeting."
FEASIBILITY_C = "I believe the team can operationalize guided onboarding without manual recovery in most deployments."


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


@given("a workflow state with audited assumptions ready for card selection", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-8b",
        "current_step": "evidence_audit",
        "input_type": "text",
        "llm_backend": "azure",
        "assumption_evidence_audit": [
            {
                "assumption": DESIRABILITY_A,
                "category": "Desirability",
                "existing_evidence_level": "None",
                "evidence_summary": "Current VoC mentions onboarding friction but no validated preference for a specific intervention.",
            },
            {
                "assumption": DESIRABILITY_B,
                "category": "Desirability",
                "existing_evidence_level": "None",
                "evidence_summary": "Signals suggest messaging confusion, but no direct behavior tests are present.",
            },
            {
                "assumption": FEASIBILITY_C,
                "category": "Feasibility",
                "existing_evidence_level": "Weak",
                "evidence_summary": "Multiple comments mention delivery friction and exception handling burden.",
            },
        ],
    }


@when("the Step 8b card selection node runs", target_fixture="step8b_result")
def step8b_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    payload = {
        "selections": [
            {
                "assumption": DESIRABILITY_A,
                "category": "Desirability",
                "existing_evidence_level": "None",
                "candidates": [
                    {
                        "card_name": "Problem Interviews",
                        "evidence_strength": "Weak",
                        "rationale": "Need direct language about onboarding pain before testing solution behavior.",
                    },
                    {
                        "card_name": "Journey Mapping",
                        "evidence_strength": "Weak",
                        "rationale": "Clarifies where complexity blocks progress in the current process.",
                    },
                    {
                        "card_name": "Landing Page",
                        "evidence_strength": "Medium",
                        "rationale": "After pain clarity, test willingness to engage with the proposed onboarding simplification.",
                    },
                ],
                "primary_card_name": "Problem Interviews",
                "alternatives_considered": "Kept solution-facing cards as follow-ons after pain validation.",
            },
            {
                "assumption": DESIRABILITY_B,
                "category": "Desirability",
                "existing_evidence_level": "None",
                "candidates": [
                    {
                        "card_name": "Landing Page",
                        "evidence_strength": "Medium",
                        "rationale": "Assumption is messaging-reactivity oriented, so market-facing conversion signal is the fastest fit.",
                    },
                    {
                        "card_name": "Fake Door",
                        "evidence_strength": "Medium",
                        "rationale": "Measures concrete feature-level intent before delivery investment.",
                    },
                    {
                        "card_name": "A/B Testing",
                        "evidence_strength": "Medium",
                        "rationale": "Compares framing choices directly against engagement outcomes.",
                    },
                ],
                "primary_card_name": "Landing Page",
                "alternatives_considered": "Skipped interview-first path because assumption is explicitly about in-market message response.",
            },
            {
                "assumption": FEASIBILITY_C,
                "category": "Feasibility",
                "existing_evidence_level": "Weak",
                "candidates": [
                    {
                        "card_name": "Throwaway Prototype",
                        "evidence_strength": "Medium",
                        "rationale": "Weak evidence already exists, so begin with a delivery simulation to test implementation viability.",
                    },
                    {
                        "card_name": "Usability Testing",
                        "evidence_strength": "Medium",
                        "rationale": "Validates handoff friction and failure points under realistic guided flow conditions.",
                    },
                    {
                        "card_name": "Wizard of Oz",
                        "evidence_strength": "Strong",
                        "rationale": "Escalates to a near-real workflow while minimizing build investment.",
                    },
                ],
                "primary_card_name": "Throwaway Prototype",
                "alternatives_considered": "Skipped weak-tier expert interview because prior evidence already indicates operational friction.",
            },
        ]
    }
    return run_step8b_llm(workflow_state, _FakeLLM(payload))


@when("the Step 8b card selection node runs without an LLM", target_fixture="step8b_result")
def step8b_result_without_llm(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step8b_llm(workflow_state, None)


@then('the workflow current step is "card_selection"')
def assert_current_step(step8b_result: BMIWorkflowState) -> None:
    assert step8b_result["current_step"] == "card_selection"


@then("the workflow state contains experiment card selections")
def assert_selections_present(step8b_result: BMIWorkflowState) -> None:
    selections = step8b_result.get("experiment_card_selections")
    assert isinstance(selections, list)
    assert selections


@then("the two desirability assumptions have different primary cards")
def assert_desirability_differentiation(step8b_result: BMIWorkflowState) -> None:
    desirability = [
        s
        for s in step8b_result["experiment_card_selections"]
        if s["category"] == "Desirability"
    ]
    assert len(desirability) == 2
    primaries = {d["primary_card_name"] for d in desirability}
    assert len(primaries) == 2, f"Expected differentiated primary cards, got {primaries}"


@then("the feasibility assumption with weak prior evidence starts at medium or strong")
def assert_weak_skips_weak(step8b_result: BMIWorkflowState) -> None:
    feasibility = next(
        s
        for s in step8b_result["experiment_card_selections"]
        if s["assumption"] == FEASIBILITY_C
    )
    strengths = {c["evidence_strength"] for c in feasibility["candidates"]}
    assert "Weak" not in strengths, f"Weak-tier cards should be excluded, got {strengths}"


@then("every selected card name exists in the experiment library")
def assert_canonical_names(step8b_result: BMIWorkflowState) -> None:
    library = PatternLibraryLoader().load_library("experiment-library.json").data
    canonical = {e["name"] for e in library["experiments"]}
    for selection in step8b_result["experiment_card_selections"]:
        for candidate in selection["candidates"]:
            assert candidate["card_name"] in canonical, (
                f"Non-canonical card: {candidate['card_name']}"
            )


@then("each assumption has between 3 and 5 candidates")
def assert_candidate_count(step8b_result: BMIWorkflowState) -> None:
    for selection in step8b_result["experiment_card_selections"]:
        count = len(selection["candidates"])
        assert 3 <= count <= 5, f"Expected 3-5 candidates, got {count}"


@then("each candidate includes rationale text")
def assert_candidate_rationale(step8b_result: BMIWorkflowState) -> None:
    for selection in step8b_result["experiment_card_selections"]:
        for candidate in selection["candidates"]:
            assert isinstance(candidate["rationale"], str)
            assert candidate["rationale"].strip()
