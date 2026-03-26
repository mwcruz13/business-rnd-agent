"""Deterministic affinity shortlister for Step 2 pattern selection.

Given a signal's zone, classification, and disruption filters, this module
produces a ranked shortlist of INVENT and/or SHIFT patterns from the
Strategyzer library.

The affinity matrix encodes theoretical alignment between Christensen's
disruption signal zones and Osterwalder's business model patterns.  Scores
are qualitative: HIGH = 3, MED = 2, LOW = 1.  Disruption filters provide
additive bonuses that adjust the base zone affinity.

Design reference: docs/step2-signal-to-pattern-mapping-research.md §4-§6.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

# ---------------------------------------------------------------------------
# Score constants
# ---------------------------------------------------------------------------

class Affinity(IntEnum):
    LOW = 1
    MED = 2
    HIGH = 3


L, M, H = Affinity.LOW, Affinity.MED, Affinity.HIGH

# ---------------------------------------------------------------------------
# Canonical names — must match strategyzer-pattern-library.json exactly
# ---------------------------------------------------------------------------

INVENT_PATTERNS: list[str] = [
    "Market Explorers",
    "Channel Kings",
    "Gravity Creators",
    "Resource Castles",
    "Activity Differentiators",
    "Scalers",
    "Revenue Differentiators",
    "Cost Differentiators",
    "Margin Masters",
]

SHIFT_PATTERNS: list[str] = [
    "Product to Recurring Service",
    "Low Tech to High Tech",
    "Sales to Platform",
    "Niche Market to Mass Market",
    "B2B to B2(B2)C",
    "Low Touch to High Touch",
    "Dedicated Resources to Multi-Usage",
    "Asset Heavy to Asset Light",
    "Closed to Open Innovation",
    "High Cost to Low Cost",
    "Transactional to Recurring Revenue",
    "Conventional to Contrarian",
]

# ---------------------------------------------------------------------------
# Zone → INVENT affinity matrix
# Rows: signal zones (7).  Columns: INVENT pattern names (9).
# Each cell: qualitative affinity score.
# ---------------------------------------------------------------------------

_ZONE_INVENT_AFFINITY: dict[str, dict[str, Affinity]] = {
    "Nonconsumption": {
        "Market Explorers": H, "Channel Kings": M, "Gravity Creators": L,
        "Resource Castles": L, "Activity Differentiators": M, "Scalers": M,
        "Revenue Differentiators": M, "Cost Differentiators": H, "Margin Masters": L,
    },
    "Overserved Customers": {
        "Market Explorers": L, "Channel Kings": L, "Gravity Creators": L,
        "Resource Castles": L, "Activity Differentiators": M, "Scalers": M,
        "Revenue Differentiators": L, "Cost Differentiators": H, "Margin Masters": H,
    },
    "Low-End Foothold": {
        "Market Explorers": M, "Channel Kings": M, "Gravity Creators": L,
        "Resource Castles": L, "Activity Differentiators": H, "Scalers": M,
        "Revenue Differentiators": M, "Cost Differentiators": H, "Margin Masters": M,
    },
    "New-Market Foothold": {
        "Market Explorers": H, "Channel Kings": M, "Gravity Creators": L,
        "Resource Castles": M, "Activity Differentiators": L, "Scalers": M,
        "Revenue Differentiators": M, "Cost Differentiators": L, "Margin Masters": L,
    },
    "Business Model Anomaly": {
        "Market Explorers": M, "Channel Kings": L, "Gravity Creators": M,
        "Resource Castles": M, "Activity Differentiators": M, "Scalers": L,
        "Revenue Differentiators": H, "Cost Differentiators": M, "Margin Masters": M,
    },
    "Enabling Technology": {
        "Market Explorers": M, "Channel Kings": M, "Gravity Creators": L,
        "Resource Castles": H, "Activity Differentiators": H, "Scalers": H,
        "Revenue Differentiators": M, "Cost Differentiators": M, "Margin Masters": L,
    },
    "Regulatory / Policy Shift": {
        "Market Explorers": M, "Channel Kings": M, "Gravity Creators": M,
        "Resource Castles": H, "Activity Differentiators": M, "Scalers": L,
        "Revenue Differentiators": M, "Cost Differentiators": L, "Margin Masters": L,
    },
}

# ---------------------------------------------------------------------------
# Zone → SHIFT affinity matrix
# Rows: signal zones that typically imply SHIFT (5 relevant).
# Columns: SHIFT pattern names (12).
# Zones that primarily imply INVENT (Nonconsumption, New-Market Foothold)
# still get LOW baseline entries for completeness.
# ---------------------------------------------------------------------------

_ZONE_SHIFT_AFFINITY: dict[str, dict[str, Affinity]] = {
    "Nonconsumption": {
        "Product to Recurring Service": L, "Low Tech to High Tech": L,
        "Sales to Platform": L, "Niche Market to Mass Market": M,
        "B2B to B2(B2)C": L, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": L, "Asset Heavy to Asset Light": L,
        "Closed to Open Innovation": L, "High Cost to Low Cost": M,
        "Transactional to Recurring Revenue": L, "Conventional to Contrarian": L,
    },
    "Overserved Customers": {
        "Product to Recurring Service": M, "Low Tech to High Tech": L,
        "Sales to Platform": L, "Niche Market to Mass Market": M,
        "B2B to B2(B2)C": L, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": L, "Asset Heavy to Asset Light": M,
        "Closed to Open Innovation": L, "High Cost to Low Cost": H,
        "Transactional to Recurring Revenue": M, "Conventional to Contrarian": H,
    },
    "Low-End Foothold": {
        "Product to Recurring Service": L, "Low Tech to High Tech": L,
        "Sales to Platform": L, "Niche Market to Mass Market": H,
        "B2B to B2(B2)C": L, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": L, "Asset Heavy to Asset Light": H,
        "Closed to Open Innovation": L, "High Cost to Low Cost": H,
        "Transactional to Recurring Revenue": M, "Conventional to Contrarian": H,
    },
    "New-Market Foothold": {
        "Product to Recurring Service": L, "Low Tech to High Tech": M,
        "Sales to Platform": L, "Niche Market to Mass Market": L,
        "B2B to B2(B2)C": L, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": L, "Asset Heavy to Asset Light": L,
        "Closed to Open Innovation": L, "High Cost to Low Cost": L,
        "Transactional to Recurring Revenue": L, "Conventional to Contrarian": L,
    },
    "Business Model Anomaly": {
        "Product to Recurring Service": H, "Low Tech to High Tech": M,
        "Sales to Platform": H, "Niche Market to Mass Market": M,
        "B2B to B2(B2)C": M, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": M, "Asset Heavy to Asset Light": M,
        "Closed to Open Innovation": M, "High Cost to Low Cost": M,
        "Transactional to Recurring Revenue": H, "Conventional to Contrarian": M,
    },
    "Enabling Technology": {
        "Product to Recurring Service": M, "Low Tech to High Tech": H,
        "Sales to Platform": M, "Niche Market to Mass Market": M,
        "B2B to B2(B2)C": L, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": M, "Asset Heavy to Asset Light": M,
        "Closed to Open Innovation": H, "High Cost to Low Cost": M,
        "Transactional to Recurring Revenue": M, "Conventional to Contrarian": L,
    },
    "Regulatory / Policy Shift": {
        "Product to Recurring Service": M, "Low Tech to High Tech": M,
        "Sales to Platform": L, "Niche Market to Mass Market": M,
        "B2B to B2(B2)C": L, "Low Touch to High Touch": L,
        "Dedicated Resources to Multi-Usage": L, "Asset Heavy to Asset Light": L,
        "Closed to Open Innovation": M, "High Cost to Low Cost": L,
        "Transactional to Recurring Revenue": L, "Conventional to Contrarian": L,
    },
}

# ---------------------------------------------------------------------------
# Disruption filter → pattern bonus map
# Each filter adds +1 to the listed patterns when present on the signal.
# ---------------------------------------------------------------------------

_FILTER_INVENT_BONUS: dict[str, list[str]] = {
    "Asymmetric Motivation": ["Revenue Differentiators", "Cost Differentiators"],
    "Asymmetric Skills": ["Resource Castles", "Activity Differentiators"],
    "Trajectory": ["Scalers", "Channel Kings"],
    "Performance Overshoot": ["Cost Differentiators", "Margin Masters"],
    "Barrier Removal": ["Market Explorers", "Channel Kings"],
    "Business Model Conflict": ["Revenue Differentiators"],
}

_FILTER_SHIFT_BONUS: dict[str, list[str]] = {
    "Asymmetric Motivation": ["High Cost to Low Cost", "Conventional to Contrarian"],
    "Asymmetric Skills": ["Low Tech to High Tech", "Closed to Open Innovation"],
    "Trajectory": ["Niche Market to Mass Market", "Sales to Platform"],
    "Performance Overshoot": ["High Cost to Low Cost", "Conventional to Contrarian"],
    "Barrier Removal": ["Niche Market to Mass Market", "Asset Heavy to Asset Light"],
    "Business Model Conflict": [
        "Product to Recurring Service",
        "Sales to Platform",
        "Transactional to Recurring Revenue",
    ],
}

# ---------------------------------------------------------------------------
# Direction decision logic
# ---------------------------------------------------------------------------

_NEW_MARKET_CLASSIFICATIONS = {
    "Disruptive — New-Market",
    "Disruptive - New-Market",
}
_LOW_END_CLASSIFICATIONS = {
    "Disruptive — Low-End",
    "Disruptive - Low-End",
}
_INVENT_ZONES = {
    "New-Market Foothold",
    "Nonconsumption",
}
_SHIFT_ZONES = {
    "Overserved Customers",
    "Low-End Foothold",
}
_AMBIGUOUS_ZONES = {
    "Business Model Anomaly",
    "Enabling Technology",
    "Regulatory / Policy Shift",
}


def determine_direction(zone: str, classification: str) -> str:
    """Return 'invent', 'shift', or 'both' based on zone and classification.

    Deterministic logic:
    - New-market disruption or INVENT-favoring zones → 'invent'
    - Low-end disruption or SHIFT-favoring zones → 'shift'
    - Ambiguous zones with sustaining classification → 'shift'
    - Ambiguous zones with mixed/unclear signals → 'both'
    """
    if classification in _NEW_MARKET_CLASSIFICATIONS or zone in _INVENT_ZONES:
        return "invent"
    if classification in _LOW_END_CLASSIFICATIONS or zone in _SHIFT_ZONES:
        return "shift"
    if zone in _AMBIGUOUS_ZONES:
        if classification == "Sustaining":
            return "shift"
        return "both"
    # Unknown zone — default to both so the consultant gets full visibility
    return "both"


# ---------------------------------------------------------------------------
# Shortlist computation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PatternScore:
    """A scored pattern recommendation."""
    name: str
    library: str  # "invent" or "shift"
    score: float
    affinity: str  # "HIGH", "MED", or "LOW" (base zone affinity before bonuses)


def _compute_scores(
    zone: str,
    filters: list[str],
    zone_matrix: dict[str, dict[str, Affinity]],
    filter_bonus: dict[str, list[str]],
    library_label: str,
) -> list[PatternScore]:
    """Score all patterns in one library and return sorted descending."""
    base_affinities = zone_matrix.get(zone, {})
    scores: dict[str, float] = {}
    original_affinity: dict[str, Affinity] = {}

    for pattern_name, affinity in base_affinities.items():
        scores[pattern_name] = float(affinity)
        original_affinity[pattern_name] = affinity

    for f in filters:
        for pattern_name in filter_bonus.get(f, []):
            if pattern_name in scores:
                scores[pattern_name] += 1.0

    results = []
    for pattern_name, total in scores.items():
        aff = original_affinity.get(pattern_name, Affinity.LOW)
        results.append(PatternScore(
            name=pattern_name,
            library=library_label,
            score=total,
            affinity=aff.name,
        ))
    results.sort(key=lambda ps: ps.score, reverse=True)
    return results


def shortlist_patterns(
    zone: str,
    classification: str,
    filters: list[str] | None = None,
    max_results: int = 4,
) -> tuple[str, list[PatternScore]]:
    """Produce a ranked pattern shortlist from zone, classification, and filters.

    Returns (direction, shortlist) where direction is 'invent', 'shift', or
    'both', and shortlist contains the top patterns from the relevant
    library/libraries, up to *max_results*.
    """
    filters = filters or []
    direction = determine_direction(zone, classification)

    invent_scores: list[PatternScore] = []
    shift_scores: list[PatternScore] = []

    if direction in ("invent", "both"):
        invent_scores = _compute_scores(
            zone, filters, _ZONE_INVENT_AFFINITY, _FILTER_INVENT_BONUS, "invent",
        )
    if direction in ("shift", "both"):
        shift_scores = _compute_scores(
            zone, filters, _ZONE_SHIFT_AFFINITY, _FILTER_SHIFT_BONUS, "shift",
        )

    # Merge and take the top N
    combined = invent_scores + shift_scores
    combined.sort(key=lambda ps: ps.score, reverse=True)
    shortlist = combined[:max_results]

    return direction, shortlist
