from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Mapping, Optional, Tuple

from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

PROGRAM = "espanso.cmd"
REPLACEMENT_KEYS = ("replace", "markdown", "html", "form", "image_path", "label")

log = logging.getLogger(__name__)
_yaml = YAML(typ="safe", pure=True)


@dataclass(frozen=True)
class Snippet:
    triggers: Tuple[str, ...]
    preview: str
    source: Path

    @property
    def trigger(self) -> str:
        return self.triggers[0]


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
    try:
        data = _yaml.load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, YAMLError):
        log.warning("Skipping unreadable match file %s", path, exc_info=True)
        return []
    entries = data.get("matches") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return []
    return [snippet for snippet in (to_snippet(entry, path, now) for entry in entries) if snippet]


def to_snippet(entry: Any, source: Path, now: datetime) -> Optional[Snippet]:
    if not isinstance(entry, dict):
        return None
    listed = entry.get("triggers") or [entry.get("trigger")]
    if isinstance(listed, str):
        listed = [listed]
    triggers = tuple(str(trigger) for trigger in listed if trigger)
    if not triggers:
        return None
    return Snippet(triggers, preview(entry, now), source)


def preview(entry: Mapping[str, Any], now: datetime) -> str:
    text = next((str(entry[key]) for key in REPLACEMENT_KEYS if entry.get(key)), "")
    for var in entry.get("vars") or []:
        if isinstance(var, dict) and var.get("type") == "date":
            text = fill_date(text, var, now)
    return text


def fill_date(text: str, var: Mapping[str, Any], now: datetime) -> str:
    date_format = (var.get("params") or {}).get("format")
    if not date_format or not var.get("name"):
        return text
    try:
        date = now.strftime(date_format)
    except ValueError:
        return text
    return re.sub(r"\{\{\s*" + re.escape(str(var["name"])) + r"\s*\}\}", lambda _: date, text)
