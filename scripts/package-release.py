#!/usr/bin/env python3
# HandoutsTexTemplate
# Copyright (C) 2026 Giulio Salvi
#
# This is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version. This software is distributed WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received
# a copy of the licence with this software; otherwise see
# <https://www.gnu.org/licenses/>.
# SPDX-FileCopyrightText: 2026 Giulio Salvi
# SPDX-License-Identifier: GPL-3.0-or-later

"""Package the exact tree of a stable release tag using Git export attributes."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile


TEMPLATE_ID = "handouts"
REPOSITORY = "GiulioSalvi/HandoutsTexTemplate"
TAG_PATTERN = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
REQUIRED_FILES = {
    "README.md", "LICENSE", "environment.sh", "defaults.yaml",
    "requirements.txt", "template.tex", "style/packages.tex",
    "style/colors.tex", "style/commands.tex", "style/boxes.tex",
    "style/pandoc-support.tex", "style/citations.tex",
}
ROOT_FILES = {name for name in REQUIRED_FILES if "/" not in name}
EXCLUDED_ROOTS = {".git", ".gitignore", ".gitattributes", ".github", "scripts", "usage_example"}


class PackageError(Exception):
    """A tag or exported tree cannot be used as a runtime release."""


def git(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), *args], stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise PackageError("Git is required to package a release.") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise PackageError(f"Git could not package the release: {detail}") from exc


def inspect_archive(data: bytes) -> None:
    """Check the runtime contract and reject unsafe or development-only members."""
    found: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
        for member in archive.getmembers():
            name = member.name.rstrip("/")
            parts = name.split("/")
            if (
                not parts or parts[0] != TEMPLATE_ID
                or any(part in {"", ".", "..", ".git"} for part in parts)
                or "\\" in name or PurePosixPath(name).is_absolute()
            ):
                raise PackageError(f"Unsafe archive path: {member.name}")
            if not member.isdir() and not member.isfile():
                raise PackageError(f"Unsupported archive member (links are forbidden): {name}")
            if len(parts) == 1:
                if not member.isdir():
                    raise PackageError("The handouts archive prefix must be a directory.")
                continue
            relative = "/".join(parts[1:])
            if parts[1] in EXCLUDED_ROOTS:
                raise PackageError(f"Development files were exported: {relative}")
            if parts[1] != "style" and relative not in ROOT_FILES:
                raise PackageError(f"Unexpected runtime file: {relative}")
            if member.isfile():
                found.add(relative)
                if relative == "environment.sh" and not (member.mode & 0o111):
                    raise PackageError("environment.sh must be executable in the tagged Git tree.")
    missing = sorted(REQUIRED_FILES - found)
    if missing:
        raise PackageError("Missing required runtime files: " + ", ".join(missing))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package(tag: str, output: Path, repo: Path) -> list[Path]:
    if not TAG_PATTERN.fullmatch(tag):
        raise PackageError("Release tags must be stable SemVer: vX.Y.Z, without leading zeroes or suffixes.")
    commit = git(repo, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}").decode().strip()
    if not COMMIT_PATTERN.fullmatch(commit):
        raise PackageError("Expected the full, lowercase 40-character Git commit SHA.")

    # The committed .gitattributes is read from this tree. No working-tree files
    # are copied into a release, and the commit controls tar entry timestamps.
    data = git(repo, "archive", "--format=tar", f"--prefix={TEMPLATE_ID}/", commit)
    inspect_archive(data)

    output.mkdir(parents=True, exist_ok=True)
    version = tag[1:]
    archive_name = f"{TEMPLATE_ID}-{version}.tar.gz"
    metadata_name = f"{TEMPLATE_ID}-{version}.json"
    names = [archive_name, metadata_name, "SHA256SUMS"]
    with tempfile.TemporaryDirectory(prefix=".package-", dir=output) as temporary:
        staging = Path(temporary)
        archive_path = staging / archive_name
        with archive_path.open("wb") as destination:
            # Empty filename and fixed gzip mtime make repeat packaging identical.
            with gzip.GzipFile(filename="", mode="wb", fileobj=destination, mtime=0) as compressed:
                compressed.write(data)
        metadata = {
            "schema": 1,
            "id": TEMPLATE_ID,
            "repository": REPOSITORY,
            "tag": tag,
            "commit": commit,
            "archive": archive_name,
            "sha256": sha256(archive_path),
        }
        (staging / metadata_name).write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8",
        )
        (staging / "SHA256SUMS").write_text(
            "".join(f"{sha256(staging / name)}  {name}\n" for name in names[:2]),
            encoding="ascii",
        )
        for name in names:
            os.replace(staging / name, output / name)
    return [output / name for name in names]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Existing stable Git tag, for example v1.2.3")
    parser.add_argument("--output", required=True, type=Path, help="Directory for the three release assets")
    args = parser.parse_args()
    try:
        paths = package(args.tag, args.output, Path(__file__).resolve().parents[1])
    except (PackageError, OSError, tarfile.TarError) as exc:
        print(f"package-release: {exc}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
