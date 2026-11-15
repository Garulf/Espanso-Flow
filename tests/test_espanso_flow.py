import subprocess
import sys
from pathlib import Path

import espanso_flow


def test_query_lists_snippets(program, write):
    write("match/base.yml", 'matches:\n  - trigger: ":hi"\n    replace: "Hello"\n')

    (result,) = espanso_flow.query("")

    assert result.title == ":hi"
    assert result.subtitle == "Hello"
    assert result.json_rpc_action["Method"] == "activate"
    assert result.json_rpc_action["Parameters"] == [":hi"]


def test_query_reports_missing_espanso(appdata):
    (result,) = espanso_flow.query("")

    assert result.title == "Espanso not found!"
    assert result.json_rpc_action is None


def test_path_setting_overrides_the_default(appdata, settings, tmp_path):
    custom = tmp_path / "portable" / "espanso.cmd"
    settings["path"] = f'"{custom}"'

    assert espanso_flow.program(settings, {}) == custom


def test_activate_runs_the_trigger_script(program, monkeypatch):
    calls = []
    monkeypatch.setattr(subprocess, "Popen", lambda args, **kwargs: calls.append(args))

    espanso_flow.activate(":hi")

    assert calls == [[str(espanso_flow.pythonw()), str(espanso_flow.TRIGGER_SCRIPT), str(program), ":hi"]]


def test_pythonw_falls_back_to_the_running_python(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "executable", str(tmp_path / "python.exe"))
    assert espanso_flow.pythonw() == tmp_path / "python.exe"

    (tmp_path / "pythonw.exe").write_text("")
    assert espanso_flow.pythonw() == tmp_path / "pythonw.exe"


def test_trigger_script_is_shipped_next_to_the_plugin():
    assert espanso_flow.TRIGGER_SCRIPT == Path(espanso_flow.__file__).with_name("trigger.py")
    assert espanso_flow.TRIGGER_SCRIPT.exists()


def test_snippets_with_several_triggers_expand_the_first(program, write):
    write("match/base.yml", 'matches:\n  - triggers: [":hello", ":hey"]\n    replace: "Hello!"\n')

    (result,) = espanso_flow.query("")

    assert result.title == ":hello, :hey"
    assert result.json_rpc_action["Parameters"] == [":hello"]


def test_query_reports_a_missing_config_folder(program):
    (result,) = espanso_flow.query("")

    assert result.title == "Espanso config folder not found"


def test_query_reads_the_portable_config_next_to_the_program(appdata, settings):
    portable = appdata / "Espanso"
    (portable / "espanso.cmd").parent.mkdir()
    (portable / "espanso.cmd").write_text("")
    (portable / ".espanso" / "match").mkdir(parents=True)
    (portable / ".espanso" / "match" / "base.yml").write_text('matches:\n  - trigger: ":p"\n    replace: "portable"\n')
    settings["path"] = str(portable / "espanso.cmd")

    assert [result.title for result in espanso_flow.query("")] == [":p"]
