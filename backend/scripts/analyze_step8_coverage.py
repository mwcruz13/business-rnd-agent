"""Analyze Step 8 experiment card coverage and identify gaps.

Run from inside the container:
    docker compose exec bmi-backend python backend/scripts/analyze_step8_coverage.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

LIBRARY_PATH = Path("backend/app/patterns/experiment-library.json")

# Current hardcoded paths in step8_pdsa.py
PATH_BY_CATEGORY = {
    "Desirability": ["Problem Interviews", "Landing Page", "Fake Door"],
    "Feasibility": ["Expert Interviews", "Throwaway Prototype", "Wizard of Oz"],
    "Viability": ["Competitor Analysis", "Mock Sale", "Pre-Order Test"],
}

EXPERIMENT_MATRIX = {
    "Desirability": {
        "Weak": ["Problem Interviews", "Solution Interviews", "Surveys / Questionnaires"],
        "Medium": ["Landing Page", "Fake Door", "A/B Testing"],
        "Strong": [],
    },
    "Feasibility": {
        "Weak": ["Expert Interviews", "Paper Prototype", "Wireframe Prototype"],
        "Medium": ["Throwaway Prototype", "Usability Testing", "3D Prototype"],
        "Strong": ["Concierge Test", "Wizard of Oz", "Single-Feature MVP"],
    },
    "Viability": {
        "Weak": ["Competitor Analysis", "Analogous Markets"],
        "Medium": ["Mock Sale", "Letter of Intent", "Price Testing"],
        "Strong": ["Pre-Order Test", "Crowdfunding", "Paid Pilot"],
    },
}


def load_library() -> dict:
    with open(LIBRARY_PATH) as f:
        return json.load(f)


def analyze():
    lib = load_library()
    experiments = lib["experiments"]
    total = len(experiments)

    print("=" * 70)
    print("STEP 8 EXPERIMENT CARD COVERAGE ANALYSIS")
    print("=" * 70)

    # --- 1. Card distribution ---
    print(f"\n1. CARD DISTRIBUTION ({total} total cards)")
    print("-" * 50)
    dist = Counter((e["category"], e["evidence_strength"]) for e in experiments)
    for cat in ["Desirability", "Feasibility", "Viability"]:
        for strength in ["Weak", "Medium", "Strong"]:
            count = dist.get((cat, strength), 0)
            print(f"  {cat:15} {strength:8} = {count:2}")
        print()

    # --- 2. PATH_BY_CATEGORY usage ---
    used_names = set()
    for names in PATH_BY_CATEGORY.values():
        used_names.update(names)
    print(f"2. PATH_BY_CATEGORY USAGE (hardcoded in step8_pdsa.py)")
    print("-" * 50)
    print(f"  Cards used:   {len(used_names)} / {total}")
    print(f"  Cards unused: {total - len(used_names)} / {total}")
    print(f"  Coverage:     {len(used_names)/total*100:.1f}%")
    print()

    # --- 3. EXPERIMENT_MATRIX usage ---
    matrix_names = set()
    for cat_dict in EXPERIMENT_MATRIX.values():
        for names in cat_dict.values():
            matrix_names.update(names)
    print(f"3. EXPERIMENT_MATRIX COVERAGE (defined but unused)")
    print("-" * 50)
    print(f"  Cards referenced: {len(matrix_names)} / {total}")
    print(f"  Cards still out:  {total - len(matrix_names)} / {total}")
    print(f"  Coverage:         {len(matrix_names)/total*100:.1f}%")
    print()

    # --- 4. Evidence strength of PATH_BY_CATEGORY ---
    print("4. EVIDENCE STRENGTH OF HARDCODED PATHS")
    print("-" * 50)
    card_lookup = {e["name"]: e for e in experiments}
    for cat, names in PATH_BY_CATEGORY.items():
        strengths = [card_lookup[n]["evidence_strength"] for n in names]
        print(f"  {cat}:")
        for name, strength in zip(names, strengths):
            print(f"    {name:25} → {strength}")
    print()

    # --- 5. Unused cards detail ---
    print("5. CARDS NEVER REACHABLE BY CURRENT STEP 8")
    print("-" * 50)
    unused = [e for e in experiments if e["name"] not in used_names]
    for e in unused:
        print(f"  {e['name']:35} {e['category']:15} {e['evidence_strength']}")
    print()

    # --- 6. Desirability path problem ---
    print("6. DESIRABILITY PATH EVIDENCE PROBLEM")
    print("-" * 50)
    des_cards = [e for e in experiments if e["category"] == "Desirability"]
    des_strong = [e for e in des_cards if e["evidence_strength"] == "Strong"]
    print(f"  Total Desirability cards:  {len(des_cards)}")
    print(f"  Strong Desirability cards: {len(des_strong)}")
    if not des_strong:
        print("  ** No Strong-evidence Desirability cards exist in the library.")
        print("     The hardcoded path stops at Medium (Fake Door) — there is")
        print("     no strong-evidence escalation for Desirability assumptions.")
    print()

    # --- 7. Monotonicity analysis ---
    print("7. MONOTONICITY: SAME-CATEGORY ASSUMPTIONS GET IDENTICAL EXPERIMENTS")
    print("-" * 50)
    print("  If Step 7 produces 2 Desirability 'Test first' assumptions,")
    print("  both get EXACTLY: Problem Interviews → Landing Page → Fake Door")
    print()
    print("  If Step 7 produces 2 Feasibility 'Test first' assumptions,")
    print("  both get EXACTLY: Expert Interviews → Throwaway Prototype → Wizard of Oz")
    print()
    print("  The assumption content is irrelevant to card selection.")
    print()

    # --- 8. Summary of structural issues ---
    print("=" * 70)
    print("SUMMARY OF STRUCTURAL ISSUES")
    print("=" * 70)
    print("""
  A. Step 8 has NO LLM call — it is purely template-based.
     The 44-card library is loaded but only 9 cards are ever selected.

  B. PATH_BY_CATEGORY is hardcoded per DVF category.
     Two assumptions in the same category always get the same experiments.

  C. EXPERIMENT_MATRIX exists with 25 cards but is never invoked.
     It was left as a "future releases" placeholder.

  D. Evidence level is always hardcoded to "None" — no audit of what
     evidence the VoC or prior steps already provide.

  E. Success/failure criteria are generic boilerplate (70%/40% thresholds)
     rather than assumption-specific.

  F. The precoil-emt agent CTA points to precoil.com/library, but
     the workflow uses the @testing-business-ideas 44-card library.
     This is a library identity contradiction.
""")


if __name__ == "__main__":
    analyze()
