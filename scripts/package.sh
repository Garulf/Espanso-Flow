#!/usr/bin/env bash
# Build the Flow Launcher plugin archive and print its path.
# Usage: scripts/package.sh [out_dir]   (default: dist)
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
out_dir="${1:-$root/dist}"
version="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["Version"])' "$root/data/plugin.json")"
build_dir="$(mktemp -d)"
trap 'rm -rf "$build_dir"' EXIT

cp -r "$root/src/." "$build_dir/"
cp "$root/data/icon.png" "$root/data/plugin.json" "$root/data/SettingsTemplate.yaml" "$build_dir/"
find "$build_dir" -name __pycache__ -prune -exec rm -rf {} +

# Vendor pure-Python wheels for the oldest supported Python, so the archive
# works with whichever Python 3.8+ Flow Launcher is configured to use.
# requirements.txt pins every runtime package and --no-deps skips the
# environment markers pip would evaluate against the build Python: those pull in
# ruamel.yaml.clib, which has no pure-Python wheel and is optional.
python3 -m pip install -r "$root/requirements.txt" \
  --target "$build_dir/plugin/site-packages" \
  --only-binary=:all: --platform any --python-version 3.8 --implementation py \
  --no-deps --no-compile --quiet --disable-pip-version-check

mkdir -p "$out_dir"
zip_path="$(cd "$out_dir" && pwd)/Espanso-Flow-${version}.zip"
rm -f "$zip_path"
(cd "$build_dir" && zip -qr "$zip_path" .)
echo "$zip_path"
