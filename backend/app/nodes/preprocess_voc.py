"""VoC input preprocessing — segmentation, cleaning, and metadata extraction.

Phase 1 (rule-based): segment detection, text cleaning, observation
re-indexing, near-duplicate detection and merging.

Phase 2 (LLM-backed): structured metadata extraction per observation
(source type, products, theater, BU, JTBD, dates, sentiment).
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import NamedTuple

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.app.llm.retry import invoke_with_retry
from backend.app.state import BMIWorkflowState


# ============================================================================
# Data structures
# ============================================================================

@dataclass
class Segment:
    """A detected source-type section of the input."""
    source_type: str
    start: int
    end: int
    body: str


@dataclass
class RawObservation:
    """A discrete observation extracted from a segment, before LLM enrichment."""
    observation_id: int
    source_type: str
    text: str
    original_excerpt: str


class DuplicatePair(NamedTuple):
    """Indices of two near-duplicate observations."""
    keep_index: int
    drop_index: int


# ============================================================================
# Product → BU mapping (deterministic)
# ============================================================================

PRODUCT_BU_MAP: dict[str, str] = {
    # HPE Compute
    "ProLiant": "HPE Compute",
    "DL380": "HPE Compute",
    "DL360": "HPE Compute",
    "DL320": "HPE Compute",
    "DL580": "HPE Compute",
    "Apollo": "HPE Compute",
    "Synergy": "HPE Compute",
    "Edgeline": "HPE Compute",
    "PCAI": "HPE Compute",
    # HPE Supercomputing
    "Cray": "HPE Supercomputing",
    "EX2500": "HPE Supercomputing",
    "XD 6500": "HPE Supercomputing",
    "XD6500": "HPE Supercomputing",
    "Grace Hopper": "HPE Supercomputing",
    "Direct Liquid Cooling": "HPE Supercomputing",
    "DLC": "HPE Supercomputing",
    # HPE Storage
    "Alletra": "HPE Storage",
    "StoreOnce": "HPE Storage",
    "Primera": "HPE Storage",
    # HPE GreenLake
    "GreenLake": "HPE GreenLake",
    # HPE Networking
    "Aruba": "HPE Networking",
    "FlexFabric": "HPE Networking",
    # GPU/Accelerator (default to Compute; context may override)
    "GPU": "HPE Compute",
    "H100": "HPE Compute",
    "H200": "HPE Compute",
    "MI300": "HPE Compute",
}

# Pre-compiled regex for product detection (longest match first)
_PRODUCT_PATTERN = re.compile(
    r"\b(" + "|".join(
        re.escape(k) for k in sorted(PRODUCT_BU_MAP, key=len, reverse=True)
    ) + r")\b",
    re.IGNORECASE,
)

_HPC_CONTEXT_TERMS = {"hpc", "supercomputer", "supercomputing", "cray", "exascale"}


def lookup_bu(text: str) -> str:
    """Return the best-match BU for a text snippet, or 'Unknown'."""
    matches = _PRODUCT_PATTERN.findall(text)
    if not matches:
        return "Unknown"
    lower_text = text.lower()
    is_hpc = any(term in lower_text for term in _HPC_CONTEXT_TERMS)
    for match in matches:
        bu = _resolve_bu(match, is_hpc)
        if bu != "Unknown":
            return bu
    return "Unknown"


def _resolve_bu(product_match: str, is_hpc: bool) -> str:
    """Resolve a product match to a BU, with HPC context override."""
    for key, bu in PRODUCT_BU_MAP.items():
        if key.lower() == product_match.lower():
            if key in ("GPU", "H100", "H200", "MI300") and is_hpc:
                return "HPE Supercomputing"
            return bu
    return "Unknown"


def detect_products(text: str) -> list[str]:
    """Return list of HPE product names found in text."""
    return list(dict.fromkeys(_PRODUCT_PATTERN.findall(text)))


# ============================================================================
# Phase 1 — Rule-based segmentation & cleaning
# ============================================================================

# Segment header patterns: (compiled_regex, source_type)
_SEGMENT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?i)from\s+.*?customer\s+comments?\s*:"), "Customer VoC"),
    (re.compile(r"(?i)from\s+.*?policy\s+guidance\s*.*?:"), "Corporate Policy"),
    (re.compile(r"(?i)from\s+the\s+technology\s+front\s*.*?:"), "Technology Intelligence"),
    (re.compile(r"(?i)from\s+the\s+industry\s*.*?:"), "Industry Analysis"),
    (re.compile(r"(?i)from\s+.*?competitive\s*.*?:"), "Competitive Intelligence"),
    (re.compile(r"(?i)from\s+.*?regulatory\s*.*?:"), "Regulatory Filing"),
]

# Cleaning patterns
_URL_BRACKET_RE = re.compile(r"\[(?:https?://)?[\w./\-…]+(?:\.(?:com|org|net|io|gov|edu)\b)[^\]]*\]")
_EMOJI_ARTIFACTS_RE = re.compile(r"[✅❌✓✗⚠️⬆⬇➡⬅🔴🟢🟡🔵]")
_HORIZONTAL_RULE_RE = re.compile(r"^-{3,}$|^={3,}$|^_{3,}$", re.MULTILINE)
_MULTI_BLANK_RE = re.compile(r"\n{3,}")

# Observation boundary patterns
_NUMBERED_HEADING_RE = re.compile(
    r"^(?:###?\s+)?(\d+(?:\.\d+)?)\s*[\.\):\-—]?\s+",
    re.MULTILINE,
)
_BRACKETED_NUM_RE = re.compile(r"^\[(\d+)\]\s*", re.MULTILINE)
_BLOCKQUOTE_RE = re.compile(r'^>\s*".*?"', re.MULTILINE | re.DOTALL)


def detect_segments(text: str) -> list[Segment]:
    """Identify source-type sections using header patterns.

    Returns segments in document order. If no headers match,
    returns a single segment with source_type='Unknown'.
    """
    boundaries: list[tuple[int, str]] = []
    for pattern, source_type in _SEGMENT_PATTERNS:
        for match in pattern.finditer(text):
            boundaries.append((match.start(), source_type))

    if not boundaries:
        return [Segment(source_type="Unknown", start=0, end=len(text), body=text)]

    boundaries.sort(key=lambda b: b[0])

    segments: list[Segment] = []
    for i, (pos, stype) in enumerate(boundaries):
        # Body starts after the header line
        header_end = text.index("\n", pos) + 1 if "\n" in text[pos:] else len(text)
        next_start = boundaries[i + 1][0] if i + 1 < len(boundaries) else len(text)
        body = text[header_end:next_start].strip()
        segments.append(Segment(source_type=stype, start=pos, end=next_start, body=body))

    return segments


def clean_text(text: str) -> str:
    """Strip URL references, formatting artifacts, and normalize whitespace."""
    result = _URL_BRACKET_RE.sub("", text)
    result = _EMOJI_ARTIFACTS_RE.sub("", result)
    result = _HORIZONTAL_RULE_RE.sub("", result)
    result = _MULTI_BLANK_RE.sub("\n\n", result)
    return result.strip()


def _split_segment_into_observations(body: str) -> list[str]:
    """Split a segment body into discrete observation texts.

    Tries numbered patterns first, then blockquote boundaries,
    then falls back to double-newline paragraph splitting.
    """
    # Try numbered headings (### 2.1, 5., etc.)
    splits = _NUMBERED_HEADING_RE.split(body)
    if len(splits) > 2:
        # splits alternates between text-before, number, text-after
        observations = []
        i = 1
        while i < len(splits):
            num = splits[i]
            text = splits[i + 1] if i + 1 < len(splits) else ""
            obs_text = f"{num}. {text.strip()}"
            if obs_text.strip() and obs_text.strip() != f"{num}.":
                observations.append(obs_text)
            i += 2
        if observations:
            return observations

    # Try bracketed numbers [1], [2], ...
    splits = _BRACKETED_NUM_RE.split(body)
    if len(splits) > 2:
        observations = []
        i = 1
        while i < len(splits):
            num = splits[i]
            text = splits[i + 1] if i + 1 < len(splits) else ""
            obs_text = text.strip()
            if obs_text:
                observations.append(obs_text)
            i += 2
        if observations:
            return observations

    # Fallback: double-newline paragraph breaks
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    return paragraphs if paragraphs else [body.strip()] if body.strip() else []


def reindex_observations(segments: list[Segment]) -> list[RawObservation]:
    """Split each segment into observations and assign sequential IDs."""
    observations: list[RawObservation] = []
    obs_id = 1
    for segment in segments:
        raw_texts = _split_segment_into_observations(segment.body)
        for text in raw_texts:
            cleaned = clean_text(text)
            if cleaned:
                observations.append(RawObservation(
                    observation_id=obs_id,
                    source_type=segment.source_type,
                    text=cleaned,
                    original_excerpt=text.strip(),
                ))
                obs_id += 1
    return observations


# ============================================================================
# Near-duplicate detection
# ============================================================================

def _trigrams(text: str) -> set[str]:
    """Generate character trigrams from normalized text."""
    normalized = re.sub(r"\s+", " ", text.lower().strip())
    if len(normalized) < 3:
        return {normalized}
    return {normalized[i:i + 3] for i in range(len(normalized) - 2)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def find_near_duplicates(
    observations: list[RawObservation],
    threshold: float = 0.7,
) -> list[DuplicatePair]:
    """Find pairs of observations with trigram Jaccard similarity >= threshold."""
    trigram_cache = [_trigrams(o.text) for o in observations]
    pairs: list[DuplicatePair] = []
    seen_dropped: set[int] = set()

    for i in range(len(observations)):
        if i in seen_dropped:
            continue
        for j in range(i + 1, len(observations)):
            if j in seen_dropped:
                continue
            sim = _jaccard(trigram_cache[i], trigram_cache[j])
            if sim >= threshold:
                # Keep the longer (richer) observation
                keep, drop = (i, j) if len(observations[i].text) >= len(observations[j].text) else (j, i)
                pairs.append(DuplicatePair(keep_index=keep, drop_index=drop))
                seen_dropped.add(drop)

    return pairs


def merge_duplicates(
    observations: list[RawObservation],
    duplicates: list[DuplicatePair],
) -> list[RawObservation]:
    """Remove duplicate observations and re-index sequentially."""
    drop_indices = {d.drop_index for d in duplicates}
    kept = [obs for i, obs in enumerate(observations) if i not in drop_indices]
    # Re-index sequentially
    for new_id, obs in enumerate(kept, start=1):
        obs.observation_id = new_id
    return kept


# ============================================================================
# Phase 2 — LLM metadata extraction
# ============================================================================

class ObservationMetadata(BaseModel):
    """Enriched observation with metadata tags."""
    observation_id: int = Field(description="Sequential 1-based index")
    source_type: str = Field(
        description="Customer VoC | Corporate Policy | Technology Intelligence | "
        "Industry Analysis | Competitive Intelligence | Regulatory Filing"
    )
    text: str = Field(description="Cleaned observation text (1-3 sentences)")
    original_excerpt: str = Field(description="Verbatim excerpt for traceability")
    products: list[str] = Field(default_factory=list, description="HPE products mentioned")
    theater: str = Field(default="Unknown", description="AMS | EMEA | APJ | Global | Unknown")
    business_unit: str = Field(
        default="Unknown",
        description="HPE Compute | HPE Storage | HPE Supercomputing | "
        "HPE Networking | HPE GreenLake | HPE Intelligent Edge | Cross-BU | Unknown"
    )
    jtbd: str = Field(
        default="",
        description="Customer Job-to-Be-Done in format: [Verb] [object] [context]"
    )
    date_references: list[str] = Field(default_factory=list, description="Dates or periods mentioned")
    sentiment: str = Field(default="Neutral", description="Positive | Negative | Neutral | Mixed")


class PreprocessingResult(BaseModel):
    """LLM-produced metadata for all observations."""
    observations: list[ObservationMetadata]


_METADATA_SYSTEM_PROMPT = """\
You are a preprocessing assistant for a disruption signal radar.
Your job is to extract structured metadata from raw observations.

For each observation, determine:
1. source_type: One of [Customer VoC, Corporate Policy, Technology Intelligence, \
Industry Analysis, Competitive Intelligence, Regulatory Filing]
2. products: HPE products explicitly mentioned (use official names)
3. theater: AMS, EMEA, APJ, Global, or Unknown
4. business_unit: HPE Compute, HPE Storage, HPE Supercomputing, HPE Networking, \
HPE GreenLake, HPE Intelligent Edge, Cross-BU, or Unknown
5. jtbd: The functional Job-to-Be-Done the customer/stakeholder is trying to accomplish. \
Frame as: "[Verb] [object] [context]" — e.g., "Deploy AI training cluster on schedule", \
"Maintain budget predictability during hardware refresh cycle". \
For non-customer observations (policy, industry), infer the impacted customer JTBD.
6. date_references: Any dates, quarters, or time periods mentioned
7. sentiment: Positive, Negative, Neutral, or Mixed

Rules:
- JTBD must describe the customer's job, not HPE's action. \
Wrong: "HPE should fix delivery". Right: "Receive ordered hardware within committed delivery window".
- BU assignment: Use product mentions first. If no product, infer from context \
(e.g., "HPC environment" → HPE Supercomputing). If ambiguous, use Cross-BU.
- Do not invent products or theaters not supported by the text.
- Keep text field to 1-3 sentences — concise but preserving the signal-relevant content.
- Preserve the observation_id and original_excerpt exactly as provided.
"""

_MAX_OBSERVATIONS_PER_BATCH = 50


def extract_observation_metadata(
    observations: list[RawObservation],
    llm: BaseChatModel,
) -> list[ObservationMetadata]:
    """Run LLM metadata extraction over observations (with batching)."""
    if not observations:
        return []

    # Batch by segment source type if over threshold
    if len(observations) > _MAX_OBSERVATIONS_PER_BATCH:
        return _extract_batched(observations, llm)

    return _extract_single_batch(observations, llm)


def _format_observations_for_llm(observations: list[RawObservation]) -> str:
    """Render observations into a numbered text block for the LLM."""
    lines: list[str] = []
    for obs in observations:
        lines.append(
            f"[{obs.observation_id}] (source_hint: {obs.source_type})\n"
            f"{obs.text}\n"
        )
    return "\n".join(lines)


def _extract_single_batch(
    observations: list[RawObservation],
    llm: BaseChatModel,
) -> list[ObservationMetadata]:
    """Extract metadata for a single batch of observations."""
    user_prompt = (
        f"Extract metadata for the following {len(observations)} observations.\n"
        f"Return exactly {len(observations)} ObservationMetadata records, "
        f"one per observation, preserving observation_id and original_excerpt.\n\n"
        f"{_format_observations_for_llm(observations)}"
    )

    messages = [
        SystemMessage(content=_METADATA_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    structured_llm = llm.with_structured_output(PreprocessingResult)
    result: PreprocessingResult = invoke_with_retry(
        structured_llm, messages, step_name="preprocess_voc"
    )

    # Patch original_excerpt from our source data (LLM may truncate)
    obs_by_id = {o.observation_id: o for o in observations}
    for meta in result.observations:
        if meta.observation_id in obs_by_id:
            meta.original_excerpt = obs_by_id[meta.observation_id].original_excerpt
        # Apply deterministic BU override when product map has a clear answer
        rule_bu = lookup_bu(meta.text + " " + meta.original_excerpt)
        if rule_bu != "Unknown":
            meta.business_unit = rule_bu
        # Detect products deterministically
        if not meta.products:
            meta.products = detect_products(meta.text + " " + meta.original_excerpt)

    return result.observations


def _extract_batched(
    observations: list[RawObservation],
    llm: BaseChatModel,
) -> list[ObservationMetadata]:
    """Split observations by source type and extract metadata per batch."""
    by_source: dict[str, list[RawObservation]] = {}
    for obs in observations:
        by_source.setdefault(obs.source_type, []).append(obs)

    all_metadata: list[ObservationMetadata] = []
    for _source_type, batch in by_source.items():
        all_metadata.extend(_extract_single_batch(batch, llm))

    # Re-sort by observation_id
    all_metadata.sort(key=lambda m: m.observation_id)
    return all_metadata


# ============================================================================
# Output rendering
# ============================================================================

_SOURCE_ORDER = [
    "Customer VoC",
    "Corporate Policy",
    "Technology Intelligence",
    "Industry Analysis",
    "Competitive Intelligence",
    "Regulatory Filing",
    "Unknown",
]


def render_preprocessed_voc(metadata: list[ObservationMetadata]) -> str:
    """Render enriched observations into structured text for step1a consumption."""
    if not metadata:
        return ""

    # Group by source type
    by_source: dict[str, list[ObservationMetadata]] = {}
    for obs in metadata:
        by_source.setdefault(obs.source_type, []).append(obs)

    source_count = len(by_source)
    total = len(metadata)
    lines: list[str] = [
        f"=== PREPROCESSED INPUT ({total} observations from {source_count} source types) ===",
        "",
    ]

    for source_type in _SOURCE_ORDER:
        group = by_source.get(source_type)
        if not group:
            continue
        lines.append(f"--- Source: {source_type} ({len(group)} observations) ---")
        lines.append("")
        for obs in group:
            products_str = ", ".join(obs.products) if obs.products else "N/A"
            lines.append(
                f"[{obs.observation_id}] "
                f"[Product: {products_str} | Theater: {obs.theater} | BU: {obs.business_unit}]"
            )
            if obs.jtbd:
                lines.append(f"[JTBD: {obs.jtbd}]")
            lines.append(f'"{obs.text}"')
            lines.append("")

    # Metadata summary
    lines.append("=== METADATA SUMMARY ===")

    source_counts = ", ".join(
        f"{st} ({len(by_source[st])})"
        for st in _SOURCE_ORDER
        if st in by_source
    )
    lines.append(f"Source types: {source_counts}")

    product_counter: Counter[str] = Counter()
    for obs in metadata:
        for p in obs.products:
            product_counter[p] += 1
    if product_counter:
        top_products = ", ".join(
            f"{p} ({c})" for p, c in product_counter.most_common(10)
        )
        lines.append(f"Products: {top_products}")

    theater_counter = Counter(obs.theater for obs in metadata)
    theater_str = ", ".join(f"{t} ({c})" for t, c in theater_counter.most_common())
    lines.append(f"Theaters: {theater_str}")

    bu_counter = Counter(obs.business_unit for obs in metadata)
    bu_str = ", ".join(f"{b} ({c})" for b, c in bu_counter.most_common())
    lines.append(f"Business Units: {bu_str}")

    jtbd_counter: Counter[str] = Counter()
    for obs in metadata:
        if obs.jtbd:
            jtbd_counter[obs.jtbd] += 1
    if jtbd_counter:
        top_jtbds = ", ".join(
            f'"{j}" ({c})' for j, c in jtbd_counter.most_common(5)
        )
        lines.append(f"Top JTBDs: {top_jtbds}")

    dates = set()
    for obs in metadata:
        dates.update(obs.date_references)
    if dates:
        lines.append(f"Date references: {', '.join(sorted(dates))}")

    return "\n".join(lines)


# ============================================================================
# Full pipeline
# ============================================================================

def run_preprocessing(state: BMIWorkflowState, llm: BaseChatModel) -> BMIWorkflowState:
    """Run the full preprocessing pipeline and return updated state."""
    voc_data = str(state.get("voc_data", ""))
    if not voc_data.strip():
        return state

    # Phase 1: Rule-based
    segments = detect_segments(voc_data)
    observations = reindex_observations(segments)
    duplicates = find_near_duplicates(observations)
    observations = merge_duplicates(observations, duplicates)

    if not observations:
        return state

    # Phase 2: LLM metadata
    metadata = extract_observation_metadata(observations, llm)
    preprocessed = render_preprocessed_voc(metadata)

    source_counts: dict[str, int] = {}
    bu_counts: dict[str, int] = {}
    for obs in metadata:
        source_counts[obs.source_type] = source_counts.get(obs.source_type, 0) + 1
        bu_counts[obs.business_unit] = bu_counts.get(obs.business_unit, 0) + 1

    return {
        **state,
        "current_step": "preprocess_voc",
        "preprocessed_voc_data": preprocessed,
        "preprocessing_metadata": {
            "total_observations": len(metadata),
            "segments": len(segments),
            "duplicates_merged": len(duplicates),
            "source_types": source_counts,
            "business_units": bu_counts,
        },
        "observation_index": [m.model_dump() for m in metadata],
    }
