from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PatternLibrary:
    name: str
    path: Path
    data: dict[str, Any]


class PatternLibraryLoader:
    def __init__(self, base_dir: Path | None = None) -> None:
        app_dir = base_dir or Path(__file__).resolve().parents[1]
        self._patterns_dir = app_dir / "patterns"

    def list_libraries(self) -> list[str]:
        return sorted(
            path.name for path in self._patterns_dir.glob("*.json") if path.is_file()
        )

    def load_library(self, file_name: str) -> PatternLibrary:
        path = self._patterns_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Unknown pattern library: {file_name}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return PatternLibrary(name=path.stem, path=path, data=data)

    def load_pattern_details(self, pattern_names: list[str]) -> list[dict[str, Any]]:
        """Load full pattern + flavor details for given pattern names.

        Searches both INVENT and SHIFT sections of the Strategyzer library.
        Returns a list of dicts with name, category, strategic_imperative,
        description, trigger_question, assessment_question, flavors, and
        direction (invent/shift).
        """
        library = self.load_library("strategyzer-pattern-library.json")
        results: list[dict[str, Any]] = []
        name_set = {n.lower() for n in pattern_names}

        # Search INVENT patterns
        for pattern in library.data.get("invent", {}).get("patterns", []):
            if pattern["name"].lower() in name_set:
                results.append({
                    "name": pattern["name"],
                    "direction": "invent",
                    "category": pattern.get("category", ""),
                    "strategic_imperative": pattern.get("strategic_imperative", ""),
                    "description": pattern.get("description", ""),
                    "trigger_question": pattern.get("trigger_question", ""),
                    "assessment_question": pattern.get("assessment_question", ""),
                    "flavors": pattern.get("flavors", []),
                })

        # Search SHIFT patterns
        for pattern in library.data.get("shift", {}).get("patterns", []):
            if pattern["name"].lower() in name_set:
                results.append({
                    "name": pattern["name"],
                    "direction": "shift",
                    "category": pattern.get("category", ""),
                    "strategic_imperative": pattern.get("strategic_reflection", ""),
                    "description": pattern.get("description", ""),
                    "trigger_question": pattern.get("strategic_reflection", ""),
                    "assessment_question": pattern.get("reverse_reflection", ""),
                    "flavors": [],
                })

        return results
