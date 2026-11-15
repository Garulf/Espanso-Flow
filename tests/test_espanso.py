from datetime import datetime
from pathlib import Path

import espanso

NOW = datetime(2026, 11, 15, 9, 30)


def test_default_program_is_under_local_appdata():
    env = {"LOCALAPPDATA": "C:/Users/me/AppData/Local"}
    assert espanso.default_program(env) == Path("C:/Users/me/AppData/Local/Programs/Espanso/espanso.cmd")


def test_default_program_needs_local_appdata():
    assert espanso.default_program({}) is None


def test_snippets_read_every_match_file(config, write):
    write(
        "match/base.yml",
        """
        matches:
          - trigger: ":espanso"
            replace: "Hi there!"
          - trigger: ":sig"
            replace: "Best regards,\\nAlex"
        """,
    )
    write(
        "match/emails.yml",
        """
        matches:
          - trigger: ":addr"
            replace: "221B Baker Street"
        """,
    )

    snippets = espanso.snippets(config, NOW)

    assert [(s.trigger, s.preview, s.source.name) for s in snippets] == [
        (":espanso", "Hi there!", "base.yml"),
        (":sig", "Best regards,\nAlex", "base.yml"),
        (":addr", "221B Baker Street", "emails.yml"),
    ]


def test_date_snippets_preview_the_current_date(config, write):
    write(
        "match/base.yml",
        """
        matches:
          - trigger: ":date"
            replace: "{{mydate}}"
            vars:
              - name: mydate
                type: date
                params:
                  format: "%d/%m/%Y"
        """,
    )

    (snippet,) = espanso.snippets(config, NOW)

    assert snippet.preview == "15/11/2026"


def test_no_config_dir_means_no_snippets():
    assert espanso.snippets(None, NOW) == []


def test_files_without_matches_are_skipped(config, write):
    write("match/vars.yml", "global_vars:\n  - name: me\n    type: echo\n    params:\n      echo: Alex\n")
    write("match/empty.yml", "")
    write("match/broken.yml", "matches: [\n")
    write("match/base.yml", 'matches:\n  - trigger: ":hi"\n    replace: "Hello"\n')

    assert [s.trigger for s in espanso.snippets(config, NOW)] == [":hi"]


def test_multiple_triggers_and_regex_matches(config, write):
    write(
        "match/base.yml",
        """
        matches:
          - triggers: [":hello", ":hey"]
            replace: "Hello!"
          - regex: ":greet\\\\((?P<person>.*)\\\\)"
            replace: "Hi {{person}}!"
        """,
    )

    (snippet,) = espanso.snippets(config, NOW)

    assert snippet.triggers == (":hello", ":hey")
    assert snippet.trigger == ":hello"


def test_preview_falls_back_to_other_replacement_kinds(config, write):
    write(
        "match/base.yml",
        """
        matches:
          - trigger: ":md"
            markdown: "**bold**"
          - trigger: ":form"
            form: "Hey [[name]]"
          - trigger: ":cat"
            image_path: "C:/Pictures/cat.png"
          - trigger: ":nothing"
            label: "Only a label"
        """,
    )

    assert [s.preview for s in espanso.snippets(config, NOW)] == [
        "**bold**",
        "Hey [[name]]",
        "C:/Pictures/cat.png",
        "Only a label",
    ]


def test_date_vars_are_filled_into_the_replacement(config, write):
    write(
        "match/base.yml",
        """
        matches:
          - trigger: ":today"
            replace: "Today is {{day}}, {{ who }}"
            vars:
              - name: who
                type: echo
                params:
                  echo: Alex
              - name: day
                type: date
                params:
                  format: "%Y-%m-%d"
          - trigger: ":noformat"
            replace: "{{day}}"
            vars:
              - name: day
                type: date
        """,
    )

    assert [s.preview for s in espanso.snippets(config, NOW)] == ["Today is 2026-11-15, {{ who }}", "{{day}}"]
