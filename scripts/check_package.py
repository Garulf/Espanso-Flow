"""Start a packaged plugin zip and check that it answers a query.

Usage: python scripts/check_package.py dist/Espanso-Flow-<version>.zip

Run it with the oldest supported Python and no packages installed, so a missing
vendored dependency fails here instead of in Flow Launcher.
"""
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

MATCHES = 'matches:\n  - trigger: ":hi"\n    replace: "Hello from the package check"\n'
REQUESTS = [
    {"jsonrpc": "2.0", "id": 1, "method": "query", "params": [{"search": "", "actionKeyword": "es"}, {"path": ""}]},
    {"jsonrpc": "2.0", "id": 2, "method": "close", "params": []},
]


def main(zip_path: str) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        plugin_dir = root / "plugin"
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(plugin_dir)

        roaming, local = root / "Roaming", root / "Local"
        (roaming / "espanso" / "match").mkdir(parents=True)
        (roaming / "espanso" / "match" / "base.yml").write_text(MATCHES, encoding="utf-8")
        program = local / "Programs" / "Espanso" / "espanso.cmd"
        program.parent.mkdir(parents=True)
        program.write_text("", encoding="utf-8")

        env = dict(os.environ, APPDATA=str(roaming), LOCALAPPDATA=str(local), PYTHONNOUSERSITE="1")
        manifest = json.loads((plugin_dir / "plugin.json").read_text(encoding="utf-8"))
        completed = subprocess.run(
            [sys.executable, "-S", manifest["ExecuteFileName"]],
            cwd=str(plugin_dir),
            env=env,
            input="".join(json.dumps(request) + "\n" for request in REQUESTS),
            capture_output=True,
            text=True,
            timeout=60,
        )

    replies = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    query_reply = next((reply for reply in replies if reply.get("id") == 1), None)
    titles = [result["Title"] for result in (query_reply or {}).get("result", {}).get("result", [])]
    if completed.returncode != 0 or titles != [":hi"]:
        print(completed.stdout, completed.stderr, sep="\n", file=sys.stderr)
        print(f"Unexpected reply (exit {completed.returncode}): {titles}", file=sys.stderr)
        return 1
    print(f"{Path(zip_path).name} answered the query on Python {sys.version.split()[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
