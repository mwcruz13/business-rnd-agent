from __future__ import annotations

from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


def _load_precoil_context() -> tuple[set[str], set[str]]:
    library = PatternLibraryLoader().load_library("precoil-emt-pattern-library.json").data
    PromptAssetLoader().load_skill_asset("precoil-emt")
    category_names = {category["name"] for category in library["dvf_categories"]["categories"]}
    quadrant_labels = {quadrant["label"] for quadrant in library["mapping_matrix"]["quadrants"]}
    return category_names, quadrant_labels


def _build_assumptions(state: BMIWorkflowState, categories: set[str], quadrants: set[str]) -> str:
    selected_patterns = ", ".join(state.get("selected_patterns", [])) or "approved patterns"
    desirability = [
        (
            "Desirable",
            "I believe operational buyers will choose a simpler onboarding path when it clearly reduces setup effort.",
            "If buyers do not value lower-friction activation, the value proposition loses its core appeal.",
        ),
        (
            "Desirable",
            "I believe customers care more about faster time-to-value than about preserving the current high-touch onboarding model.",
            "If time-to-value is not a priority, the proposed direction solves the wrong problem.",
        ),
        (
            "Desirable",
            "I believe visible onboarding progress increases customer confidence during activation.",
            "If progress visibility does not matter, part of the proposed experience is unnecessary.",
        ),
    ]
    viability = [
        (
            "Viable",
            "I believe the business can protect expansion revenue by accelerating activation through Cost Differentiators.",
            "If faster activation does not improve revenue retention or expansion, the model may not justify the investment.",
        ),
        (
            "Viable",
            "I believe reduced onboarding effort will lower support costs enough to improve business model sustainability.",
            "If support costs remain unchanged, the economics of the new model weaken.",
        ),
        (
            "Viable",
            "I believe customers will continue to adopt the offer without requiring a more expensive service layer.",
            "If adoption requires costly human intervention, margins may erode.",
        ),
    ]
    feasibility = [
        (
            "Feasible",
            "I believe the team can operationalize a guided onboarding flow without breaking existing delivery commitments.",
            "If the team cannot deliver the new flow reliably, the design will stall in execution.",
        ),
        (
            "Feasible",
            "I believe product telemetry and onboarding playbooks are sufficient to support the new activation path.",
            "If these resources are inadequate, the model will be difficult to run consistently.",
        ),
        (
            "Feasible",
            "I believe support teams can handle exceptions while most customers self-serve successfully.",
            "If exception volume stays high, the operating model will not scale.",
        ),
    ]

    if categories != {"Desirability", "Viability", "Feasibility"}:
        raise ValueError("Unexpected Precoil DVF categories")
    required_quadrants = {"Test first", "Monitor", "Deprioritize", "Safe zone"}
    if not required_quadrants.issubset(quadrants):
        raise ValueError("Unexpected Precoil matrix quadrants")

    matrix_rows = [
        (desirability[0][1], "Desirability", "Test first"),
        (desirability[1][1], "Desirability", "Monitor"),
        (desirability[2][1], "Desirability", "Safe zone"),
        (viability[0][1], "Viability", "Test first"),
        (viability[1][1], "Viability", "Monitor"),
        (viability[2][1], "Viability", "Deprioritize"),
        (feasibility[0][1], "Feasibility", "Test first"),
        (feasibility[1][1], "Feasibility", "Monitor"),
        (feasibility[2][1], "Feasibility", "Safe zone"),
    ]

    def render_section(title: str, rows: list[tuple[str, str, str]]) -> list[str]:
        section = [f"## {title}", "| Category | Assumption | Rationale |", "|----------|------------|-----------|"]
        section.extend(f"| {category} | {assumption} | {rationale} |" for category, assumption, rationale in rows)
        return section

    lines = []
    lines.extend(render_section("Desirability", desirability))
    lines.append("")
    lines.extend(render_section("Viability", viability))
    lines.append("")
    lines.extend(render_section("Feasibility", feasibility))
    lines.append("")
    lines.append("## DVF Tensions")
    lines.append(
        f"The strongest tension is between the Desirability assumption that customers want a simpler onboarding path and the Viability assumption that {selected_patterns} will protect revenue without adding a costly service layer. If simplification requires more human support than expected, the model may be desirable but not viable."
    )
    lines.append("")
    lines.append("## Importance × Evidence Map")
    lines.append("| Assumption | Category | Quadrant |")
    lines.append("|------------|----------|----------|")
    lines.extend(f"| {assumption} | {category} | {quadrant} |" for assumption, category, quadrant in matrix_rows)
    return "\n".join(lines)


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    categories, quadrants = _load_precoil_context()
    return {
        **state,
        "current_step": "risk_map",
        "assumptions": _build_assumptions(state, categories, quadrants),
    }
