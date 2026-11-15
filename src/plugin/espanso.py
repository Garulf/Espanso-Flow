from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
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


def config_dir(env: Mapping[str, str], home: Path, program: Optional[Path]) -> Optional[Path]:
    candidates = [home / ".espanso", home / ".config" / "espanso"]
    if program is not None:
        candidates.insert(0, program.parent / ".espanso")
    if env.get("APPDATA"):
        candidates.append(Path(env["APPDATA"], "espanso"))
    return next((candidate for candidate in candidates if candidate.is_dir()), None)


def is_legacy(config: Path) -> bool:
    return (config / "user").is_dir() and (config / "default.yml").is_file()


def match_files(config: Path, env: Mapping[str, str]) -> List[Path]:
    if is_legacy(config):
        return legacy_match_files(config, env)
    return sorted(path for path in (config / "match").rglob("*.yml") if not path.name.startswith("_"))


def legacy_match_files(config: Path, env: Mapping[str, str]) -> List[Path]:
    package_dirs = [config / "packages"]
    if env.get("LOCALAPPDATA"):
        package_dirs.append(Path(env["LOCALAPPDATA"], "espanso", "packages"))
    files = [config / "default.yml", *sorted((config / "user").rglob("*.yml"))]
    for packages in package_dirs:
        files.extend(sorted(packages.rglob("package.yml")))
    return files


def snippets(
    config: Optional[Path], now: Optional[datetime] = None, env: Optional[Mapping[str, str]] = None
) -> List[Snippet]:
    if config is None:
        return []
    now = now or datetime.now()
    return [snippet for path in match_files(config, env or {}) for snippet in load_file(path, now)]


def load_file(path: Path, now: datetime) -> List[Snippet]:
    try:
        stat = path.stat()
    except OSError:
        return []
    entries = read_entries(path, stat.st_mtime_ns, stat.st_size)
    return [snippet for snippet in (to_snippet(entry, path, now) for entry in entries) if snippet]


@lru_cache(maxsize=512)
def read_entries(path: Path, mtime_ns: int, size: int) -> Tuple[Any, ...]:
    try:
        data = _yaml.load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, YAMLError):
        log.warning("Skipping unreadable match file %s", path, exc_info=True)
        return ()
    entries = data.get("matches") if isinstance(data, dict) else None
    return tuple(entries) if isinstance(entries, list) else ()


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
