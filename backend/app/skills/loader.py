from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PromptAsset:
    name: str
    kind: str
    path: Path
    metadata: dict[str, Any]
    body: str


class PromptAssetLoader:
    def __init__(self, base_dir: Path | None = None) -> None:
        app_dir = base_dir or Path(__file__).resolve().parents[1]
        self._app_dir = app_dir
        self._skills_dir = app_dir / "skills"
        self._prompts_dir = app_dir / "prompts"

    def list_skill_assets(self) -> list[str]:
        skill_names: list[str] = []
        for child in sorted(self._skills_dir.iterdir()):
            if not child.is_dir():
                continue
            if (child / "SKILL.md").exists() or (child / "agent.md").exists():
                skill_names.append(child.name)
        return skill_names

    def load_skill_asset(self, name: str) -> PromptAsset:
        skill_dir = self._skills_dir / name
        if not skill_dir.exists():
            raise FileNotFoundError(f"Unknown skill asset: {name}")

        for file_name, kind in (("SKILL.md", "skill"), ("agent.md", "agent")):
            path = skill_dir / file_name
            if path.exists():
                return self._load_markdown_asset(path, default_name=name, kind=kind)

        raise FileNotFoundError(f"No SKILL.md or agent.md found for skill asset: {name}")

    def load_step_prompt(self, name: str) -> PromptAsset:
        file_name = name if name.endswith(".md") else f"{name}.md"
        path = self._prompts_dir / file_name
        if not path.exists():
            raise FileNotFoundError(f"Unknown step prompt: {name}")
        prompt_name = Path(file_name).stem
        return self._load_markdown_asset(path, default_name=prompt_name, kind="prompt")

    def load_prompt_asset(self, path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8")

    def _load_markdown_asset(self, path: Path, default_name: str, kind: str) -> PromptAsset:
        text = path.read_text(encoding="utf-8")
        metadata, body = _split_frontmatter(text)
        name = str(metadata.get("name") or default_name)
        return PromptAsset(name=name, kind=kind, path=path, metadata=metadata, body=body)


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text

    end_marker = text.find("\n---\n", 4)
    if end_marker == -1:
        return {}, text

    raw_frontmatter = text[4:end_marker]
    body = text[end_marker + 5 :].lstrip("\n")
    metadata: dict[str, Any] = {}
    for line in raw_frontmatter.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = _parse_frontmatter_value(value.strip())
    return metadata, body


def _parse_frontmatter_value(value: str) -> Any:
    if not value:
        return ""
    if value in {"[]", "{}"}:
        return [] if value == "[]" else {}
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


def load_prompt_asset(path: str | Path) -> str:
    return PromptAssetLoader().load_prompt_asset(path)

