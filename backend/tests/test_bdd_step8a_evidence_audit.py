from __future__ import annotations

from pytest_bdd import given, scenarios, then, when

from backend.app.nodes.step8a_evidence_audit_llm import run_step8a_llm
from backend.app.state import BMIWorkflowState


scenarios("features/step8a-evidence-audit.feature")


DELIVERY_ASSUMPTION = "I believe customers will reject the current offer if delivery delays continue past quarter-end planning windows."
CXL_ASSUMPTION = "I believe CXL adoption risk is already low enough that the team can skip explicit customer validation."


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


@given("a workflow state with test-first assumptions and delivery-delay VoC evidence", target_fixture="workflow_state")
def workflow_state() -> BMIWorkflowState:
    return {
        "session_id": "session-8a",
        "current_step": "risk_map",
        "input_type": "text",
        "llm_backend": "azure",
        "voc_data": (
            "Customers repeatedly report delivery delays stretching from 6 to 14 months, "
            "causing planning disruptions and forcing them to postpone deployments. "
            "Several comments state they will reconsider future orders if delays continue."
        ),
        "customer_profile": "Operational buyers need dependable delivery timelines for quarter-end planning and deployment sequencing.",
        "signals": [
            {"summary": "Delivery reliability is becoming a recurring buying concern in enterprise accounts."},
        ],
        "interpreted_signals": [
            {"summary": "Sustained complaints suggest timeline reliability is a weak but real evidence signal."},
        ],
        "step7_structured": {
            "categories": [
                {
                    "category": "Desirability",
                    "assumptions": [
                        {
                            "assumption": DELIVERY_ASSUMPTION,
                            "rationale": "If customers tolerate delays, the delivery concern may not be a priority decision driver.",
                            "suggested_quadrant": "Test first",
                            "voc_evidence_strength": "Weak",
                        },
                        {
                            "assumption": "I believe buyers mainly care about premium implementation services rather than timeline certainty.",
                            "rationale": "If this is wrong, the sales motion is mispositioned.",
                            "suggested_quadrant": "Monitor",
                            "voc_evidence_strength": "None",
                        },
                    ],
                },
                {
                    "category": "Feasibility",
                    "assumptions": [
                        {
                            "assumption": CXL_ASSUMPTION,
                            "rationale": "If CXL adoption risk is not actually low, the team may scale the wrong roadmap.",
                            "suggested_quadrant": "Test first",
                            "voc_evidence_strength": "None",
                        },
                        {
                            "assumption": "I believe operations can absorb exception handling without adding delivery friction.",
                            "rationale": "If not, the operating model will not scale.",
                            "suggested_quadrant": "Safe zone",
                            "voc_evidence_strength": "None",
                        },
                    ],
                },
                {
                    "category": "Viability",
                    "assumptions": [
                        {
                            "assumption": "I believe customers will pay a premium for guaranteed delivery windows.",
                            "rationale": "If not, the revenue upside is overstated.",
                            "suggested_quadrant": "Monitor",
                            "voc_evidence_strength": "None",
                        },
                        {
                            "assumption": "I believe improved delivery confidence will protect renewal revenue.",
                            "rationale": "If not, the economics of the fix weaken.",
                            "suggested_quadrant": "Safe zone",
                            "voc_evidence_strength": "Weak",
                        },
                    ],
                },
            ],
            "dvf_tensions": [],
        },
    }


@when("the Step 8a evidence audit node runs", target_fixture="step8a_result")
def step8a_result(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    llm = _FakeLLM(
        {
            "audits": [
                {
                    "assumption": DELIVERY_ASSUMPTION,
                    "category": "Desirability",
                    "existing_evidence_level": "Weak",
                    "evidence_summary": "Customers repeatedly describe 6-14 month delivery delays that disrupt planning, which is direct but still anecdotal complaint evidence.",
                },
                {
                    "assumption": CXL_ASSUMPTION,
                    "category": "Feasibility",
                    "existing_evidence_level": "None",
                    "evidence_summary": "The provided VoC and interpreted signals do not mention CXL adoption at all.",
                },
            ]
        }
    )
    return run_step8a_llm(workflow_state, llm)


@when("the Step 8a evidence audit node runs without an LLM", target_fixture="step8a_result")
def step8a_result_without_llm(workflow_state: BMIWorkflowState) -> BMIWorkflowState:
    return run_step8a_llm(workflow_state, None)


@then('the workflow current step is "evidence_audit"')
def assert_current_step(step8a_result: BMIWorkflowState) -> None:
    assert step8a_result["current_step"] == "evidence_audit"


@then("the workflow state contains assumption evidence audits")
def assert_audits_present(step8a_result: BMIWorkflowState) -> None:
    audits = step8a_result.get("assumption_evidence_audit")
    assert isinstance(audits, list)
    assert audits


def _find_audit(step8a_result: BMIWorkflowState, assumption: str) -> dict[str, object]:
    for audit in step8a_result["assumption_evidence_audit"]:
        if audit["assumption"] == assumption:
            return audit
    raise AssertionError(f"Audit not found for assumption: {assumption}")


@then('the delivery-delay assumption is classified as "Weak"')
def assert_delivery_assumption_weak(step8a_result: BMIWorkflowState) -> None:
    audit = _find_audit(step8a_result, DELIVERY_ASSUMPTION)
    assert audit["existing_evidence_level"] == "Weak"


@then("the delivery-delay audit includes a non-empty evidence summary")
def assert_delivery_summary(step8a_result: BMIWorkflowState) -> None:
    audit = _find_audit(step8a_result, DELIVERY_ASSUMPTION)
    assert isinstance(audit["evidence_summary"], str)
    assert audit["evidence_summary"].strip()


@then('the CXL adoption assumption is classified as "None"')
def assert_cxl_none(step8a_result: BMIWorkflowState) -> None:
    audit = _find_audit(step8a_result, CXL_ASSUMPTION)
    assert audit["existing_evidence_level"] == "None"


@then("the audit count matches the number of test-first assumptions")
def assert_audit_count(step8a_result: BMIWorkflowState, workflow_state: BMIWorkflowState) -> None:
    expected = sum(
        1
        for cat in workflow_state["step7_structured"]["categories"]
        for assumption in cat["assumptions"]
        if assumption["suggested_quadrant"] == "Test first"
    )
    assert len(step8a_result["assumption_evidence_audit"]) == expected
