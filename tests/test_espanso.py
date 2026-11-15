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
