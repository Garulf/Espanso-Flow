from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Mapping, Optional

from ruamel.yaml import YAML

PROGRAM = "espanso.cmd"

_yaml = YAML(typ="safe", pure=True)


@dataclass(frozen=True)
class Snippet:
    trigger: str
    preview: str
    source: Path


def default_program(env: Mapping[str, str]) -> Optional[Path]:
    local = env.get("LOCALAPPDATA")
    return Path(local, "Programs", "Espanso", PROGRAM) if local else None


def config_dir(env: Mapping[str, str]) -> Optional[Path]:
    appdata = env.get("APPDATA")
    return Path(appdata, "espanso") if appdata else None


def match_files(config: Path) -> List[Path]:
    return sorted((config / "match").glob("*.yml"))


def snippets(config: Optional[Path], now: Optional[datetime] = None) -> List[Snippet]:
    if config is None:
        return []
    now = now or datetime.now()
    return [snippet for path in match_files(config) for snippet in load_file(path, now)]


def load_file(path: Path, now: datetime) -> List[Snippet]:
    data = _yaml.load(path.read_text(encoding="utf-8"))
    return [Snippet(entry["trigger"], preview(entry, now), path) for entry in data["matches"]]


def preview(entry: Mapping[str, Any], now: datetime) -> str:
    first_var = (entry.get("vars") or [{}])[0]
    if first_var.get("type") == "date":
        return now.strftime(first_var["params"]["format"])
    return entry.get("replace")
