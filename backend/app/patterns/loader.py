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
