"""Render the README screenshots and hero image with flow-render.

Usage (from the repo root):

    uvx --from flow-render==0.15.0 python docs/screenshots/render.py

Each ``<shot>.json`` is a flow-render config with paths relative to this folder.
Every shot is rendered in the light and dark Windows 11 themes; ``hero.json`` is
rendered once as the README banner.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHOTS_DIR = ROOT / "docs" / "screenshots"
ASSETS_DIR = ROOT / ".github" / "assets"
THEMES = ("dark", "light")
HERO = {"shot": "hero", "css": ["win11-dark.css", "docs/screenshots/hero.css"]}


def flow_render(args, out_path: Path) -> None:
    with tempfile.TemporaryDirectory() as out_dir:
        subprocess.run(["flow-render", *args, "-o", out_dir], check=True, cwd=ROOT)
        (rendered,) = Path(out_dir).glob("*.png")
        shutil.move(str(rendered), out_path)
    print(f"Wrote {out_path}")


def render_config(shot: str, css, out_path: Path, work: Path) -> None:
    config = json.loads((SHOTS_DIR / f"{shot}.json").read_text(encoding="utf-8"))
    config["icon"] = str((SHOTS_DIR / config["icon"]).resolve())
    for result in config["results"]:
        result["icon"] = str((SHOTS_DIR / result["icon"]).resolve())
    config["css"] = css
    config_path = work / f"{shot}-{out_path.stem}.json"
    config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
    flow_render(["-c", str(config_path)], out_path)


def main() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    shots = sorted(path.stem for path in SHOTS_DIR.glob("*.json") if path.stem != HERO["shot"])
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for shot in shots:
            for theme in THEMES:
                render_config(shot, f"win11-{theme}.css", ASSETS_DIR / f"{shot}-{theme}.png", work)
        render_config(HERO["shot"], HERO["css"], ASSETS_DIR / "hero.png", work)


if __name__ == "__main__":
    sys.exit(main())
