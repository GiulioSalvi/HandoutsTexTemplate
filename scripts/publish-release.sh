#!/usr/bin/env bash
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

# A published release is read-only. Retry uploads only while it remains a draft.
set -euo pipefail
if [[ $# -ne 2 ]]; then
    printf 'Usage: %s TAG ASSET_DIRECTORY\n' "$0" >&2
    exit 2
fi
tag=$1
assets=$2
: "${GITHUB_REPOSITORY:?Set GITHUB_REPOSITORY to the child owner/repository.}"
: "${GH_TOKEN:?Set GH_TOKEN to the child release token.}"
if [[ ! $tag =~ ^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]; then
    printf 'Release tag must be stable SemVer: vX.Y.Z.\n' >&2
    exit 2
fi
version=${tag#v}
archive=handouts-$version.tar.gz
metadata=handouts-$version.json
for filename in "$archive" "$metadata" SHA256SUMS; do
    [[ -f $assets/$filename ]] || { printf 'Missing release asset: %s\n' "$filename" >&2; exit 1; }
done
commit=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["commit"])' "$assets/$metadata")
workspace=$(mktemp -d "${TMPDIR:-/tmp}/handouts-publish.XXXXXXXX")
trap 'rm -rf -- "$workspace"' EXIT
state=missing
if gh api "repos/$GITHUB_REPOSITORY/releases/tags/$tag" > "$workspace/release.json" 2> "$workspace/lookup.err"; then
    state=$(python3 -c 'import json,sys; print("draft" if json.load(open(sys.argv[1]))["draft"] else "published")' "$workspace/release.json")
elif ! grep -q 'HTTP 404' "$workspace/lookup.err"; then
    cat "$workspace/lookup.err" >&2
    exit 1
fi

if [[ $state == published ]]; then
    gh release download "$tag" --repo "$GITHUB_REPOSITORY" --dir "$workspace" \
        --pattern "$archive" --pattern "$metadata" --pattern SHA256SUMS
    python3 - "$assets" "$workspace" "$archive" "$metadata" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
expected, downloaded = map(Path, sys.argv[1:3])
names = sys.argv[3:]
if json.loads((expected / names[1]).read_text()) != json.loads((downloaded / names[1]).read_text()):
    raise SystemExit("Published release metadata differs from this tag; refusing to modify it.")
if (expected / "SHA256SUMS").read_bytes() != (downloaded / "SHA256SUMS").read_bytes():
    raise SystemExit("Published release checksums differ; refusing to modify it.")
for name in names:
    actual = hashlib.sha256((downloaded / name).read_bytes()).hexdigest()
    wanted = hashlib.sha256((expected / name).read_bytes()).hexdigest()
    if actual != wanted:
        raise SystemExit(f"Published release asset {name} differs; refusing to modify it.")
print("Published release already matches the exact tag; no release assets were changed.")
PY
    exit 0
fi

if [[ $state == missing ]]; then
    gh release create "$tag" --repo "$GITHUB_REPOSITORY" --verify-tag --target "$commit" \
        --draft --title "$tag" --notes "Versioned handouts runtime package, metadata, and SHA-256 checksums."
fi
# Uploads may be replaced only before publication, including interrupted drafts.
gh release upload "$tag" "$assets/$archive" "$assets/$metadata" "$assets/SHA256SUMS" \
    --repo "$GITHUB_REPOSITORY" --clobber
gh release edit "$tag" --repo "$GITHUB_REPOSITORY" --draft=false
printf 'Published handouts release %s.\n' "$tag"
