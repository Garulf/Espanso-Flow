from pathlib import Path
from textwrap import dedent

import pytest

import espanso_flow


@pytest.fixture
def appdata(tmp_path, monkeypatch):
    roaming = tmp_path / "Roaming"
    local = tmp_path / "Local"
    roaming.mkdir()
    local.mkdir()
    monkeypatch.setenv("APPDATA", str(roaming))
    monkeypatch.setenv("LOCALAPPDATA", str(local))
    return tmp_path


@pytest.fixture
def program(appdata):
    exe = appdata / "Local" / "Programs" / "Espanso" / "espanso.cmd"
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    return exe


@pytest.fixture
def config(appdata):
    return appdata / "Roaming" / "espanso"


@pytest.fixture
def write(config):
    def write(relative: str, text: str) -> Path:
        path = config / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(text), encoding="utf-8")
        return path

    return write


@pytest.fixture(autouse=True)
def settings():
    launcher = espanso_flow.plugin.launcher
    launcher._settings = {"path": ""}
    yield launcher._settings
    launcher._settings = {}
