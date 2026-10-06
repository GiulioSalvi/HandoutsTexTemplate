#!/bin/sh
# HandoutsTexTemplate
# Copyright (C) 2026 Giulio Salvi
#
# This is free software: you can redistribute it and/or modify it under the
# GNU General Public License, version 3 or (at your option) any later version.
# It is distributed WITHOUT ANY WARRANTY, including the implied warranties
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the licence
# included with this software, or <https://www.gnu.org/licenses/>.
# SPDX-FileCopyrightText: 2026 Giulio Salvi
# SPDX-License-Identifier: GPL-3.0-or-later

# Compile with an extracted runtime package. Fixtures stay outside that package.
set -eu

if [ "$#" -ne 1 ]; then
    printf 'Usage: %s ARCHIVE.tar.gz\n' "$0" >&2
    exit 2
fi
repository=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
archive=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).resolve())' "$1")
workspace=$(mktemp -d "${TMPDIR:-/tmp}/handouts-smoke.XXXXXXXX")
trap 'rm -rf -- "$workspace"' EXIT HUP INT TERM
mkdir -p "$workspace/installed"
tar -xzf "$archive" -C "$workspace/installed"
cp -R "$repository/usage_example" "$workspace/usage_example"
# Keep LuaLaTeX's generated font/config caches inside this disposable test.
TEXMFVAR=$workspace/texmf-var
TEXMFCONFIG=$workspace/texmf-config
TEXMFCACHE=$TEXMFVAR
mkdir -p "$TEXMFVAR" "$TEXMFCONFIG"
export TEXMFVAR TEXMFCONFIG TEXMFCACHE
TEX_TEMPLATE_HOME=$workspace/installed/handouts
export TEX_TEMPLATE_HOME
. "$TEX_TEMPLATE_HOME/environment.sh"

# The fixture's resource-path is its parent: the original usage_example/assets
# image URLs resolve here, without installing examples inside the template.
cd "$workspace"
if ! pandoc \
    --defaults="$TEX_TEMPLATE_HOME/defaults.yaml" \
    --defaults="$workspace/usage_example/defaults.yaml" \
    --template="$TEX_TEMPLATE_PATH" \
    --verbose \
    --output="$workspace/smoke.pdf" > "$workspace/compile.log" 2>&1; then
    tail -n 120 "$workspace/compile.log" >&2
    exit 1
fi
python3 - "$workspace/smoke.pdf" <<'PY'
from pathlib import Path
import sys
pdf = Path(sys.argv[1])
if pdf.stat().st_size < 1000 or not pdf.read_bytes().startswith(b"%PDF-"):
    raise SystemExit("Smoke compilation did not produce a valid PDF.")
print(f"Extracted-package smoke test passed ({pdf.stat().st_size} bytes).")
PY
