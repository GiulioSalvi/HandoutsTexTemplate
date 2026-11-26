#!/usr/bin/env python3
# HandoutsTexTemplate - Copyright (C) 2026 Giulio Salvi
# GNU GPL version 3 or later; without warranty. See LICENSE.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile the full template and verify blank-facing part openings.

Usage: TEX_TEMPLATES_HOME=/path/to/library python check-part-openings.py TEMPLATE_HOME
Requires Pandoc, LuaLaTeX, and pypdf. All compilation artifacts are temporary.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import tempfile

from pypdf import PdfReader


PARTS = (
    'PART-FIRST',
    'PART-STARRED',
    'PART-CONSECUTIVE',
    'PART-AFTER-ODD',
    'PART-AFTER-EVEN',
    'PART-UNNUMBERED',
)
# Four title/colophon pages, then a single ToC + blank (ToC cases), or two
# inserted blanks after the colophon (no-ToC cases). Subsequent offsets also
# assert that existing blank reverse pages are reused rather than duplicated.
EXPECTED_PAGES = (7, 9, 11, 15, 21, 23)
BODY = r'''```{=latex}
\part[SHORT-FIRST]{PART-FIRST}
\part*{PART-STARRED}
\part[SHORT-CONSECUTIVE]{PART-CONSECUTIVE}
\cleardoublepage
\noindent ODD-END-MARKER\par
\part{PART-AFTER-ODD}
\cleardoublepage
\noindent TWO-PAGE-START\par
\newpage
\noindent EVEN-END-MARKER\par
\part{PART-AFTER-EVEN}
\setcounter{secnumdepth}{-2}
\part{PART-UNNUMBERED}
```
'''
# A blank facing page must contain no painted paths, glyphs, images, forms,
# shading, or inline images; checking text alone would miss a border/logo.
PAINT_OPERATORS = {
    b'S', b's', b'f', b'F', b'f*', b'B', b'B*', b'b', b'b*',
    b'Tj', b'TJ', b"'", b'"', b'Do', b'sh', b'INLINE IMAGE', b'BI',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_pdf(pdf: Path, *, toc: bool, name: str) -> None:
    reader = PdfReader(pdf)
    texts = [page.extract_text() or '' for page in reader.pages]
    # PDF kerning may produce spurious spaces in large Latin Modern titles.
    compact = lambda value: ''.join(value.split())
    actual = []
    for marker in PARTS:
        # The ToC can contain several marker strings. Title pages contain only
        # their own marker, and their exact line has no page number/leader.
        matches = [
            index for index, text in enumerate(texts)
            if compact(marker) in {compact(line) for line in text.splitlines()}
            and sum(compact(other) in compact(text) for other in PARTS) == 1
        ]
        require(len(matches) == 1, f'{name}: expected one title page for {marker}, got {matches}; extracted pages: {[(i + 1, text[:150]) for i, text in enumerate(texts)]!r}')
        index = matches[0]
        physical = index + 1
        require(physical % 2 == 1, f'{name}: {marker} is on left page {physical}')
        require(index > 0, f'{name}: {marker} has no facing page')
        previous = reader.pages[index - 1]
        require(not texts[index - 1].strip(), f'{name}: text precedes {marker}: {texts[index - 1]!r}')
        require(not list(previous.images), f'{name}: an image precedes {marker}')
        stream = previous.get_contents()
        painted = [] if stream is None else [op for _, op in stream.operations if op in PAINT_OPERATORS]
        require(not painted, f'{name}: nonblank graphics precede {marker}: {painted}')
        actual.append(physical)
    require(tuple(actual) == EXPECTED_PAGES,
            f'{name}: redundant or missing blank pages: expected {EXPECTED_PAGES}, got {tuple(actual)}')
    for marker, parity in [('ODD-END-MARKER', 1), ('EVEN-END-MARKER', 0)]:
        pages = [i + 1 for i, text in enumerate(texts) if compact(marker) in compact(text)]
        require(len(pages) == 1 and pages[0] % 2 == parity,
                f'{name}: fixture failed to end text on requested parity: {marker}: {pages}')
    joined = '\n'.join(texts)
    require(('SHORT-FIRST' in compact(joined)) == toc, f'{name}: optional first ToC title not preserved')
    require(('SHORT-CONSECUTIVE' in compact(joined)) == toc, f'{name}: optional consecutive ToC title not preserved')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template_home', type=Path)
    args = parser.parse_args()
    template = args.template_home.resolve()
    require((template / 'template.tex').is_file(), f'Missing template: {template}')
    defaults = next((template / n for n in ('defaults.yaml', 'defaults.yml') if (template / n).is_file()), None)
    require(defaults is not None, f'Missing template defaults: {template}')
    with tempfile.TemporaryDirectory(prefix='handouts-part-openings-') as temporary:
        root = Path(temporary)
        environment = dict(os.environ)
        roots = [str(template)]
        library = environment.get('TEX_TEMPLATES_HOME')
        if library:
            roots.extend(str(p) for p in sorted((Path(library) / 'components').glob('*')) if p.is_dir())
        existing = environment.get('TEXINPUTS', '')
        environment['TEXINPUTS'] = ':'.join(roots) + ':' + existing
        if not environment['TEXINPUTS'].endswith(':'):
            environment['TEXINPUTS'] += ':'
        for key, directory in [('TEXMFVAR', 'texmf-var'), ('TEXMFCACHE', 'texmf-var'), ('TEXMFCONFIG', 'texmf-config')]:
            environment[key] = str(root / directory)
            (root / directory).mkdir(exist_ok=True)
        for openany in (False, True):
            for toc in (False, True):
                name = f'{"openany" if openany else "openright"}-{"toc" if toc else "no-toc"}'
                project = root / name
                project.mkdir()
                source = project / 'parts.md'
                source.write_text(BODY, encoding='utf-8')
                metadata = project / 'metadata.yml'
                metadata.write_text('title: Part openings regression\nauthor: Regression fixture\nlang: en\n', encoding='utf-8')
                pdf = project / 'parts.pdf'
                command = [
                    'pandoc', '--defaults', str(defaults), '--template', str(template / 'template.tex'),
                    '--from', 'markdown+raw_tex', '--number-sections',
                    '--metadata-file', str(metadata), '--output', str(pdf), str(source),
                ]
                if toc:
                    command.append('--toc')
                if openany:
                    command.extend(['--variable', 'openany'])
                result = subprocess.run(command, cwd=project, env=environment, capture_output=True, text=True, timeout=180)
                require(result.returncode == 0, f'{name}: compilation failed\n{result.stdout[-3000:]}\n{result.stderr[-10000:]}')
                check_pdf(pdf, toc=toc, name=name)
                print(f'Passed {name}: first/starred/consecutive/odd/even/unnumbered parts', flush=True)


if __name__ == '__main__':
    main()
