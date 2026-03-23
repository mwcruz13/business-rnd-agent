from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.app.patterns.loader import PatternLibraryLoader
from backend.app.skills.loader import PromptAssetLoader
from backend.app.state import BMIWorkflowState


@dataclass(frozen=True)
class SignalSpec:
    signal_id: str
    signal: str
    zone: str
    classification: str
    filter_names: tuple[str, ...]
    impact: int
    speed: int
    source_type: str
    observable_behavior: str
    confidence: str
    rationale: str
    alternative_explanation: str
    key_evidence_gap: str
    trigger_groups: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class SectionLine:
    section: str
    excerpt: str
    is_heading: bool = False


@dataclass(frozen=True)
class EvidenceCandidate:
    section_line: SectionLine
    matched_group_indexes: tuple[int, ...]
    keyword_weight: int


SIGNAL_SPECS: tuple[SignalSpec, ...] = (
    SignalSpec(
        signal_id="competitor_self_serve",
        signal="Competitors are shifting firmware assessment toward automated self-serve delivery",
        zone="Business Model Anomaly",
        classification="Disruptive — New-Market",
        filter_names=("Asymmetric Motivation", "Barrier Removal", "Business Model Conflict"),
        impact=3,
        speed=3,
        source_type="Internal VoC",
        observable_behavior="Competitors are reportedly gaining market advantage with automated self-serve firmware assessment offers.",
        confidence="High",
        rationale="The source describes a delivery-model shift that changes speed, price, and service access, not just feature performance.",
        alternative_explanation="This may still be aggressive digitization inside the existing market rather than a durable disruptive foothold.",
        key_evidence_gap="External proof of adoption, pricing, and customer switching behavior is still needed.",
        trigger_groups=(("competitor", "competitors"), ("self-serve", "self serve"), ("automated",)),
    ),
    SignalSpec(
        signal_id="interoperability_shift",
        signal="Customers are shifting value from isolated recommendations to environment-wide interoperability assessment",
        zone="Overserved Customers",
        classification="Sustaining",
        filter_names=(),
        impact=3,
        speed=2,
        source_type="Internal VoC",
        observable_behavior="Customers want firmware guidance that reflects environment-wide interoperability rather than isolated product recommendations.",
        confidence="Medium",
        rationale="The text points to existing customers redefining the performance they care about in the current job, which is a sustaining shift in the basis of competition.",
        alternative_explanation="This may be a normal product-scope enhancement rather than a strategic discontinuity.",
        key_evidence_gap="Need direct customer evidence on how often deals are won or lost on interoperability coverage.",
        trigger_groups=(("environment wide interoperability", "interoperability"), ("isolated product", "isolated product based")),
    ),
    SignalSpec(
        signal_id="turnaround_expectation",
        signal="Time-to-assessment is becoming a core part of the firmware assessment value proposition",
        zone="Overserved Customers",
        classification="Sustaining",
        filter_names=(),
        impact=3,
        speed=3,
        source_type="Internal VoC",
        observable_behavior="Customers expect on-time delivery and fresher assessments, while the current turnaround creates stale outputs and delayed time to value.",
        confidence="High",
        rationale="The source ties delivery delay directly to lost credibility and production disruption, making timeliness part of the product value rather than an operational detail.",
        alternative_explanation="The issue may be execution quality within the current service model rather than a strategic market shift.",
        key_evidence_gap="Need baseline customer churn, escalation, or satisfaction data tied to turnaround time.",
        trigger_groups=(("on time delivery", "delivery delays", "stale data", "high tat", "time to value", "4-25 days"),),
    ),
    SignalSpec(
        signal_id="delivery_economics",
        signal="The current firmware assessment operating model is not economically scalable",
        zone="Business Model Anomaly",
        classification="Sustaining",
        filter_names=(),
        impact=3,
        speed=3,
        source_type="Internal VoC",
        observable_behavior="The current delivery process is described as unscalable, margin-dilutive, and unable to cover more than a small fraction of the install base.",
        confidence="High",
        rationale="The source repeatedly links delivery economics to coverage, profitability, and the ability to embed the service in broader offers.",
        alternative_explanation="This may be an internal cost-accounting problem rather than evidence of an external market shift.",
        key_evidence_gap="Need quantified unit economics for the current model versus an automated alternative.",
        trigger_groups=(("not scalable", "scalability", "profitability", "current costs", "margin", "5% of install base", "cost of delivering"),),
    ),
    SignalSpec(
        signal_id="access_friction",
        signal="Firmware code access friction is degrading the customer experience",
        zone="Nonconsumption",
        classification="Sustaining",
        filter_names=(),
        impact=2,
        speed=2,
        source_type="Internal VoC",
        observable_behavior="Customers struggle to access the correct firmware code through channels such as HPESC and SPP.",
        confidence="High",
        rationale="Access friction is acting as a barrier to successful consumption of the service outcome, even for current customers.",
        alternative_explanation="This may reflect a fixable channel and entitlement issue rather than a strategic threat.",
        key_evidence_gap="Need evidence on where access failure occurs most often and how often it blocks completion.",
        trigger_groups=(("access issues", "cannot access", "difficulty in accessing", "hpesc", "spp"),),
    ),
    SignalSpec(
        signal_id="data_fragmentation",
        signal="Fragmented data structures and governance are becoming binding constraints on automation",
        zone="Enabling Technology",
        classification="Sustaining",
        filter_names=(),
        impact=3,
        speed=2,
        source_type="Internal VoC",
        observable_behavior="Changing data structures, siloed sources, and weak governance are reducing accuracy and slowing automation.",
        confidence="High",
        rationale="The source indicates that automation quality is constrained by the underlying information architecture and governance model.",
        alternative_explanation="This may be a temporary integration debt issue rather than a durable structural blocker.",
        key_evidence_gap="Need defect, rework, and integration-failure data by source system to size the constraint.",
        trigger_groups=(("data structure", "data inconsistency", "data governance", "multiple data sources", "siloed organizations", "shadow it"),),
    ),
    SignalSpec(
        signal_id="nonconsumer_self_serve",
        signal="A lower-cost self-serve offer can unlock SMB and edge nonconsumers",
        zone="New-Market Foothold",
        classification="Disruptive — New-Market",
        filter_names=("Barrier Removal", "Asymmetric Motivation", "Trajectory"),
        impact=3,
        speed=2,
        source_type="Internal VoC",
        observable_behavior="The source explicitly names SMB and edge nonconsumers and proposes a lower-cost self-serve model to reach them.",
        confidence="Medium",
        rationale="This is a classic non-consumption signal: a simpler, cheaper offer is being positioned to create demand where the current model does not reach.",
        alternative_explanation="The opportunity may be aspirational if demand and willingness to adopt self-serve remain unvalidated.",
        key_evidence_gap="Need direct evidence from SMB and edge buyers on willingness to adopt a self-serve firmware assessment offer.",
        trigger_groups=(("non-consumers", "nonconsumers"), ("self-serve", "self serve", "lower cost self-serve")),
    ),
    SignalSpec(
        signal_id="onboarding_complexity",
        signal="Customers are signaling that the workflow is more complex than the value they receive",
        zone="Overserved Customers",
        classification="Disruptive — Low-End",
        filter_names=("Performance Overshoot", "Business Model Conflict"),
        impact=2,
        speed=2,
        source_type="Internal VoC",
        observable_behavior="Some buyers delay progress because the process feels too complex relative to the value delivered.",
        confidence="Medium",
        rationale="When lower-complexity alternatives can satisfy the core job, process friction can signal an overserved segment and a low-end opening.",
        alternative_explanation="This may reflect a fixable onboarding and workflow issue rather than a real low-end foothold.",
        key_evidence_gap="Need evidence that customers choose a simpler, lower-performance alternative rather than waiting for the current process to improve.",
        trigger_groups=(("onboarding",), ("too complex", "more complex", "friction")),
    ),
)


def _load_soc_context() -> tuple[set[str], set[str], dict[range, str]]:
    library = PatternLibraryLoader().load_library("soc-radar-pattern-library.json").data
    PromptAssetLoader().load_skill_asset("soc-radar")

    zones = {zone["name"] for zone in library["signal_zones"]["zones"]}
    filters = {item["name"] for item in library["disruption_filters"]["filters"]}
    action_tiers = {
        range(_range_start(item["score_range"]), _range_end(item["score_range"]) + 1): item["tier"]
        for item in library["scoring"]["action_tiers"]
    }
    return zones, filters, action_tiers


def _range_start(score_range: str) -> int:
    start, _ = score_range.split("-", 1)
    return int(start)


def _range_end(score_range: str) -> int:
    _, end = score_range.split("-", 1)
    return int(end)


def _iter_section_lines(voc_data: str) -> list[SectionLine]:
    section_name = "Document"
    section_lines: list[SectionLine] = []
    for raw_line in voc_data.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("### "):
            section_name = line[4:].strip()
            section_lines.append(SectionLine(section=section_name, excerpt=section_name, is_heading=True))
            continue
        if line.startswith("## "):
            section_name = line[3:].strip()
            section_lines.append(SectionLine(section=section_name, excerpt=section_name, is_heading=True))
            continue
        section_lines.append(SectionLine(section=section_name, excerpt=line))
    return section_lines


def _matches_spec(normalized_voc_data: str, spec: SignalSpec) -> bool:
    return all(any(keyword in normalized_voc_data for keyword in group) for group in spec.trigger_groups)


def _build_evidence_candidates(
    section_lines: Iterable[SectionLine], spec: SignalSpec
) -> list[EvidenceCandidate]:
    candidates: list[EvidenceCandidate] = []
    for section_line in section_lines:
        normalized_line = section_line.excerpt.lower()
        matched_group_indexes: list[int] = []
        keyword_weight = 0
        for index, group in enumerate(spec.trigger_groups):
            matched_keywords = [keyword for keyword in group if keyword in normalized_line]
            if matched_keywords:
                matched_group_indexes.append(index)
                keyword_weight += max(len(keyword) for keyword in matched_keywords)
        if matched_group_indexes:
            candidates.append(
                EvidenceCandidate(
                    section_line=section_line,
                    matched_group_indexes=tuple(matched_group_indexes),
                    keyword_weight=keyword_weight,
                )
            )
    return sorted(
        candidates,
        key=lambda candidate: (
            -len(candidate.matched_group_indexes),
            -candidate.keyword_weight,
            candidate.section_line.is_heading,
            candidate.section_line.section,
            candidate.section_line.excerpt,
        ),
    )


def _collect_evidence(section_lines: Iterable[SectionLine], spec: SignalSpec) -> list[dict[str, str]]:
    candidates = _build_evidence_candidates(section_lines, spec)
    if not candidates:
        return []

    total_groups = len(spec.trigger_groups)
    covered_groups: set[int] = set()
    selected: list[EvidenceCandidate] = []
    selected_excerpts: set[str] = set()
    strong_match_threshold = 2 if total_groups >= 3 else 1

    for candidate in candidates:
        if len(candidate.matched_group_indexes) < strong_match_threshold:
            continue
        if candidate.section_line.excerpt in selected_excerpts:
            continue
        selected.append(candidate)
        selected_excerpts.add(candidate.section_line.excerpt)
        covered_groups.update(candidate.matched_group_indexes)
        if covered_groups == set(range(total_groups)):
            break

    if covered_groups != set(range(total_groups)):
        for candidate in candidates:
            if candidate.section_line.excerpt in selected_excerpts:
                continue
            if not set(candidate.matched_group_indexes) - covered_groups:
                continue
            selected.append(candidate)
            selected_excerpts.add(candidate.section_line.excerpt)
            covered_groups.update(candidate.matched_group_indexes)
            if covered_groups == set(range(total_groups)):
                break

    if not selected:
        selected.append(candidates[0])

    return [
        {"section": candidate.section_line.section, "excerpt": candidate.section_line.excerpt}
        for candidate in selected[:3]
    ]


def _build_detected_signal(spec: SignalSpec, evidence: list[dict[str, str]]) -> dict[str, object]:
    return {
        "signal_id": spec.signal_id,
        "signal": spec.signal,
        "zone": spec.zone,
        "source_type": spec.source_type,
        "observable_behavior": spec.observable_behavior,
        "source_sections": sorted({item["section"] for item in evidence}),
        "evidence": [item["excerpt"] for item in evidence],
    }


def _build_interpreted_signal(spec: SignalSpec, detected_signal: dict[str, object]) -> dict[str, object]:
    return {
        **detected_signal,
        "classification": spec.classification,
        "filters": list(spec.filter_names),
        "confidence": spec.confidence,
        "rationale": spec.rationale,
        "alternative_explanation": spec.alternative_explanation,
        "key_evidence_gap": spec.key_evidence_gap,
    }


def _build_priority_signal(spec: SignalSpec, action_tiers: dict[range, str]) -> dict[str, object]:
    score = spec.impact * spec.speed
    return {
        "signal_id": spec.signal_id,
        "signal": spec.signal,
        "impact": spec.impact,
        "speed": spec.speed,
        "score": score,
        "tier": _resolve_tier(score, action_tiers),
        "rationale": spec.rationale,
    }


def _fallback_signal(action_tiers: dict[range, str]) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    spec = SignalSpec(
        signal_id="generic_delivery_shift",
        signal="An alternative delivery model appears to be changing how customers access firmware assessment value",
        zone="Business Model Anomaly",
        classification="Sustaining",
        filter_names=(),
        impact=1,
        speed=2,
        source_type="Internal VoC",
        observable_behavior="The source suggests pressure on the current delivery model but does not provide enough structure to isolate more specific signals.",
        confidence="Low",
        rationale="The input implies a delivery-model issue, but evidence is too thin for more specific extraction.",
        alternative_explanation="The document may simply lack enough detail for structured signal extraction.",
        key_evidence_gap="Need clearer evidence of customer behavior, competitive action, or access barriers.",
        trigger_groups=(("delivery",),),
    )
    detected_signal = {
        "signal_id": spec.signal_id,
        "signal": spec.signal,
        "zone": spec.zone,
        "source_type": spec.source_type,
        "observable_behavior": spec.observable_behavior,
        "source_sections": ["Document"],
        "evidence": [],
    }
    return detected_signal, _build_interpreted_signal(spec, detected_signal), _build_priority_signal(spec, action_tiers)


def _rank_signal_triplets(
    triplets: list[tuple[dict[str, object], dict[str, object], dict[str, object]]]
) -> list[tuple[dict[str, object], dict[str, object], dict[str, object]]]:
    return sorted(
        triplets,
        key=lambda triplet: (
            -int(triplet[2]["score"]),
            0 if str(triplet[1]["classification"]).startswith("Disruptive") else 1,
            str(triplet[0]["signal"]),
        ),
    )


def _scan_signals(
    voc_data: str,
    valid_zones: set[str],
    valid_filters: set[str],
    action_tiers: dict[range, str],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    normalized_voc_data = voc_data.lower()
    section_lines = _iter_section_lines(voc_data)
    triplets: list[tuple[dict[str, object], dict[str, object], dict[str, object]]] = []

    for spec in SIGNAL_SPECS:
        if not _matches_spec(normalized_voc_data, spec):
            continue
        if spec.zone not in valid_zones:
            raise ValueError(f"Unsupported SOC zone: {spec.zone}")
        if any(filter_name not in valid_filters for filter_name in spec.filter_names):
            raise ValueError("Unsupported SOC disruption filter detected")

        evidence = _collect_evidence(section_lines, spec)
        detected_signal = _build_detected_signal(spec, evidence)
        interpreted_signal = _build_interpreted_signal(spec, detected_signal)
        priority_signal = _build_priority_signal(spec, action_tiers)
        triplets.append((detected_signal, interpreted_signal, priority_signal))

    if not triplets:
        detected_signal, interpreted_signal, priority_signal = _fallback_signal(action_tiers)
        return [detected_signal], [interpreted_signal], [priority_signal]

    ranked_triplets = _rank_signal_triplets(triplets)
    signals = [detected_signal for detected_signal, _, _ in ranked_triplets]
    interpreted_signals = [interpreted_signal for _, interpreted_signal, _ in ranked_triplets]
    priority_matrix = [priority_signal for _, _, priority_signal in ranked_triplets]
    return signals, interpreted_signals, priority_matrix


def _resolve_tier(score: int, action_tiers: dict[range, str]) -> str:
    for score_range, tier in action_tiers.items():
        if score in score_range:
            return tier
    raise ValueError(f"No SOC action tier configured for score {score}")


def _build_coverage_gaps(valid_zones: set[str], signals: list[dict[str, object]]) -> list[dict[str, str]]:
    detected_zones = {str(signal["zone"]) for signal in signals}
    missing_zones = sorted(valid_zones - detected_zones)
    return [
        {
            "zone": zone,
            "note": "No direct evidence found in this input; treat as an intelligence blind spot rather than proof of absence.",
        }
        for zone in missing_zones
    ]


def _build_agent_recommendation(
    interpreted_signals: list[dict[str, object]],
    priority_matrix: list[dict[str, object]],
    coverage_gaps: list[dict[str, str]],
) -> str:
    disruptive_signals = [
        str(signal["signal"])
        for signal in interpreted_signals
        if str(signal.get("classification", "")).startswith("Disruptive")
    ]
    top_signals = [
        f"{entry['signal']} [{entry['tier']}]"
        for entry in priority_matrix[:3]
    ]
    blind_spots = ", ".join(gap["zone"] for gap in coverage_gaps[:3]) or "none"

    if disruptive_signals:
        disruptive_summary = "; ".join(disruptive_signals[:2])
    else:
        disruptive_summary = "no disruptive signals clearly surfaced in the current input"

    return (
        "Step 1 detected multiple signals rather than a single workflow-friction issue. "
        f"Highest-priority items: {', '.join(top_signals)}. "
        f"Disruptive pressure is concentrated in {disruptive_summary}. "
        f"Blind spots from this input: {blind_spots}."
    )


def run_step(state: BMIWorkflowState) -> BMIWorkflowState:
    voc_data = state.get("voc_data", "")
    valid_zones, valid_filters, action_tiers = _load_soc_context()
    signals, interpreted_signals, priority_matrix = _scan_signals(
        voc_data,
        valid_zones,
        valid_filters,
        action_tiers,
    )
    coverage_gaps = _build_coverage_gaps(valid_zones, signals)
    agent_recommendation = _build_agent_recommendation(
        interpreted_signals,
        priority_matrix,
        coverage_gaps,
    )

    return {
        **state,
        "current_step": "signal_scan",
        "signals": signals,
        "interpreted_signals": interpreted_signals,
        "priority_matrix": priority_matrix,
        "coverage_gaps": coverage_gaps,
        "agent_recommendation": agent_recommendation,
    }
