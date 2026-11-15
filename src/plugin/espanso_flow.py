from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Mapping, Optional

from pyflowlauncher import FlowLauncherV2, Plugin, Result

import espanso

PLUGIN_DIR = Path(__file__).resolve().parent
ICON = str(PLUGIN_DIR.parent / "icon.png")
TRIGGER_SCRIPT = PLUGIN_DIR / "trigger.py"

plugin = Plugin(launcher=FlowLauncherV2())


def program(settings: Mapping, env: Mapping[str, str]) -> Optional[Path]:
    configured = os.path.expandvars((settings.get("path") or "").strip().strip('"'))
    return Path(configured) if configured else espanso.default_program(env)


def pythonw() -> Path:
    windowless = Path(sys.executable).with_name("pythonw.exe")
    return windowless if windowless.exists() else Path(sys.executable)


def snippet_result(snippet: espanso.Snippet) -> Result:
    return Result(
        title=", ".join(snippet.triggers),
        subtitle=snippet.preview,
        icon=ICON,
    ).add_action(activate, parameters=[snippet.trigger])


@plugin.on_method
def query(query: str) -> List[Result]:
    exe = program(plugin.settings, os.environ)
    if exe is None or not exe.exists():
        return [
            Result(
                title="Espanso not found!",
                subtitle="Please make sure you are using the latest version and set its path in the settings.",
                icon=ICON,
            )
        ]
    config = espanso.config_dir(os.environ, Path.home(), exe)
    if config is None:
        return [
            Result(
                title="Espanso config folder not found",
                subtitle="Run 'espanso path' to see where Espanso keeps its config.",
                icon=ICON,
            )
        ]
    return [snippet_result(snippet) for snippet in espanso.snippets(config, env=os.environ)]


@plugin.on_method
def activate(trigger: str) -> None:
    exe = program(plugin.settings, os.environ)
    subprocess.Popen(
        [str(pythonw()), str(TRIGGER_SCRIPT), str(exe), trigger],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
