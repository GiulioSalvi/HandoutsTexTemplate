#!/usr/bin/env python3
# HandoutsTexTemplate - Copyright (C) 2026 Giulio Salvi
# GNU GPL version 3 or later; without warranty. See LICENSE.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compile the full template and verify blank-facing part/chapter openings.

Usage: TEX_TEMPLATES_HOME=/path/to/library python check-page-openings.py TEMPLATE_HOME
Requires Pandoc, LuaLaTeX, and pypdf. Compilation artifacts are temporary.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import tempfile

from pypdf import PdfReader


PARTS = (
    'PART-FIRST', 'PART-STARRED', 'PART-CONSECUTIVE',
    'PART-AFTER-ODD', 'PART-AFTER-EVEN', 'PART-UNNUMBERED',
)
PART_BODY = r'''
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
'''
CHAPTERS = (
    'CHAPTER-FIRST', 'CHAPTER-STARRED', 'CHAPTER-CONSECUTIVE',
    'CHAPTER-AFTER-ODD', 'CHAPTER-AFTER-EVEN', 'CHAPTER-AFTER-FLOAT',
    'CHAPTER-UNNUMBERED', 'APPENDIX-CHAPTER', 'BACKMATTER-CHAPTER',
)
CHAPTER_BODY = r'''
\chapter[SHORT-FIRST]{CHAPTER-FIRST}
% TOC-FILLERS
\chapter*{CHAPTER-STARRED}
\chapter[SHORT-CONSECUTIVE]{CHAPTER-CONSECUTIVE}
\noindent ODD-END-MARKER\par
\chapter{CHAPTER-AFTER-ODD}
\noindent TWO-PAGE-START\par
\newpage
\noindent EVEN-END-MARKER\par
\chapter{CHAPTER-AFTER-EVEN}
\begin{figure}[p]
\centering
\rule{25mm}{25mm}
\caption{PENDING-FLOAT}
\end{figure}
\chapter{CHAPTER-AFTER-FLOAT}
\setcounter{secnumdepth}{-2}
\chapter{CHAPTER-UNNUMBERED}
\appendix
\setcounter{secnumdepth}{3}
\chapter{APPENDIX-CHAPTER}
\backmatter
\chapter{BACKMATTER-CHAPTER}
'''
MIXED = ('FIRST-CHAPTER', 'MIXED-PART', 'AFTER-PART', 'MIXED-STARRED-PART', 'LAST-CHAPTER')
MIXED_BODY = r'''
\chapter{FIRST-CHAPTER}
\blankpage
\part{MIXED-PART}
\chapter{AFTER-PART}
\newpage
\noindent MANUAL-END-MARKER\par
\blankpage
\part*{MIXED-STARRED-PART}
\chapter*{LAST-CHAPTER}
'''
PAINT_OPERATORS = {
    b'S', b's', b'f', b'F', b'f*', b'B', b'B*', b'b', b'b*',
    b'Tj', b'TJ', b"'", b'"', b'Do', b'sh', b'INLINE IMAGE', b'BI',
}


@dataclass(frozen=True)
class Case:
    name: str
    kind: str
    openany: bool = False
    toc_pages: int = 0
    fillers: int = 0
    title: bool = True
    preliminaries: bool = False


CASES = (
    Case('parts-openright-no-toc', 'parts'),
    Case('parts-openany-no-toc', 'parts', openany=True),
    Case('parts-openright-toc', 'parts', toc_pages=1),
    Case('parts-openany-toc', 'parts', openany=True, toc_pages=1),
    Case('parts-no-title', 'parts', title=False),
    Case('chapters-no-toc', 'chapters'),
    Case('chapters-one-page-toc', 'chapters', toc_pages=1),
    Case('chapters-two-page-toc', 'chapters', toc_pages=2, fillers=42),
    Case('chapters-three-page-toc-preliminaries', 'chapters', toc_pages=3, fillers=90, preliminaries=True),
    Case('mixed-no-title', 'mixed', title=False),
    Case('mixed-openany-no-title', 'mixed', openany=True, title=False),
    Case('mixed-with-title', 'mixed'),
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def compact(value: str) -> str:
    # PDF kerning can introduce spaces in large Latin Modern titles.
    return ''.join(value.split())


def check_pdf(pdf: Path, case: Case) -> None:
    reader = PdfReader(pdf)
    texts = [page.extract_text() or '' for page in reader.pages]
    blank = []
    for page, text in zip(reader.pages, texts):
        stream = page.get_contents()
        painted = stream is not None and any(op in PAINT_OPERATORS for _, op in stream.operations)
        blank.append(not text.strip() and not painted and not list(page.images))

    def find(marker: str, *, first_only: bool = False) -> int:
        matches = [i for i, text in enumerate(texts)
                   if compact(marker) in {compact(line) for line in text.splitlines()}]
        if first_only:
            require(bool(matches), f'{case.name}: missing {marker}')
            return matches[0]
        require(len(matches) == 1, f'{case.name}: expected one title for {marker}, got {matches}')
        return matches[0]

    def check_opening(marker: str, *, part: bool = False, first_only: bool = False) -> int:
        index = find(marker, first_only=first_only)
        physical = index + 1
        previous_used = next((j + 1 for j in range(index - 1, -1, -1) if not blank[j]), 0)
        if case.openany and not part:
            # Explicit opt-out retains native page-by-page chapter openings.
            require(physical == previous_used + 1,
                    f'{case.name}: openany inserted blanks before {marker}: {physical}, previous {previous_used}')
        else:
            require(physical % 2 == 1, f'{case.name}: {marker} is on left page {physical}')
            if index:
                require(blank[index - 1], f'{case.name}: facing page {index} of {marker} is not blank: {texts[index - 1]!r}')
            # Minimum recto following a blank verso: one blank after used recto,
            # two after used verso. Reuse blanks from parts, ToC and manual calls.
            expected = 1 if previous_used == 0 else previous_used + (2 if previous_used % 2 else 3)
            require(physical == expected,
                    f'{case.name}: missing/redundant blanks before {marker}: expected {expected}, got {physical}')
        return index

    markers = PARTS if case.kind == 'parts' else CHAPTERS if case.kind == 'chapters' else MIXED
    for marker in markers:
        check_opening(marker, part=marker in PARTS or marker in ('MIXED-PART', 'MIXED-STARRED-PART'))
    if case.kind in ('parts', 'chapters'):
        for marker, parity in [('ODD-END-MARKER', 1), ('EVEN-END-MARKER', 0)]:
            pages = [i + 1 for i, text in enumerate(texts) if compact(marker) in compact(text)]
            require(len(pages) == 1 and pages[0] % 2 == parity,
                    f'{case.name}: fixture did not end on requested parity: {marker}: {pages}')
        joined = compact('\n'.join(texts))
        for short in ('SHORT-FIRST', 'SHORT-CONSECUTIVE'):
            require((short in joined) == bool(case.toc_pages), f'{case.name}: optional ToC title not preserved: {short}')
    if case.kind == 'chapters':
        float_pages = [i for i, text in enumerate(texts) if compact('PENDING-FLOAT') in compact(text)
                       and i > find('CHAPTER-AFTER-EVEN')]
        require(len(float_pages) == 1 and float_pages[0] < find('CHAPTER-AFTER-FLOAT'),
                f'{case.name}: pending figure did not ship before the next chapter')
        appendix = compact(texts[find('APPENDIX-CHAPTER')])
        require('AppendixA' in appendix, f'{case.name}: appendix chapter numbering changed')
    if case.preliminaries:
        preface = check_opening('PRELIM-PREFACE')
        require(reader.page_labels[preface] == 'i', f'{case.name}: first preliminary page is not i')
        for marker in ('PRELIM-DEDICATION', 'PRELIM-EPIGRAPH', 'List of Figures', 'List of Tables'):
            check_opening(marker)
    if case.toc_pages:
        toc_start = find('Contents', first_only=True)
        if not case.openany:
            check_opening('Contents', first_only=True)
        toc_pages = {toc_start} | {i for i, text in enumerate(texts) if 'TOC-FILLER-' in text}
        require(len(toc_pages) == case.toc_pages,
                f'{case.name}: expected {case.toc_pages} ToC pages, got {sorted(i + 1 for i in toc_pages)}')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('template_home', type=Path)
    parser.add_argument('--case', choices=[case.name for case in CASES])
    args = parser.parse_args()
    template = args.template_home.resolve()
    require((template / 'template.tex').is_file(), f'Missing template: {template}')
    defaults = next((template / n for n in ('defaults.yaml', 'defaults.yml') if (template / n).is_file()), None)
    require(defaults is not None, f'Missing template defaults: {template}')
    with tempfile.TemporaryDirectory(prefix='handouts-page-openings-') as temporary:
        root = Path(temporary)
        environment = dict(os.environ)
        roots = [str(template)]
        library = environment.get('TEX_TEMPLATES_HOME')
        if library:
            roots.extend(str(p) for p in sorted((Path(library) / 'components').glob('*')) if p.is_dir())
        environment['TEXINPUTS'] = ':'.join(roots) + ':' + environment.get('TEXINPUTS', '')
        if not environment['TEXINPUTS'].endswith(':'):
            environment['TEXINPUTS'] += ':'
        for key, directory in [('TEXMFVAR', 'texmf-var'), ('TEXMFCACHE', 'texmf-var'), ('TEXMFCONFIG', 'texmf-config')]:
            environment[key] = str(root / directory)
            (root / directory).mkdir(exist_ok=True)
        for case in CASES:
            if args.case and case.name != args.case:
                continue
            project = root / case.name
            project.mkdir()
            body = PART_BODY if case.kind == 'parts' else CHAPTER_BODY if case.kind == 'chapters' else MIXED_BODY
            fillers = '\n'.join(r'\addcontentsline{toc}{section}{TOC-FILLER-%03d}' % i for i in range(case.fillers))
            source = project / 'openings.md'
            source.write_text('```{=latex}\n' + body.replace('% TOC-FILLERS', fillers) + '\n```\n', encoding='utf-8')
            metadata = project / 'metadata.yml'
            data = 'lang: en\n'
            if case.title:
                data += 'title: Page openings regression\nauthor: Regression fixture\n'
            if case.preliminaries:
                data += ('preface-title: PRELIM-PREFACE\npreface: PRELIM-PREFACE-BODY\n'
                         'dedication: PRELIM-DEDICATION\nepigraph: PRELIM-EPIGRAPH\n')
            metadata.write_text(data, encoding='utf-8')
            pdf = project / 'openings.pdf'
            command = [
                'pandoc', '--defaults', str(defaults), '--template', str(template / 'template.tex'),
                '--from', 'markdown+raw_tex', '--number-sections',
                '--metadata-file', str(metadata), '--output', str(pdf), str(source),
            ]
            if case.toc_pages:
                command.append('--toc')
            if case.openany:
                command.extend(['--variable', 'openany'])
            if case.preliminaries:
                command.extend(['--variable', 'lof', '--variable', 'lot'])
            result = subprocess.run(command, cwd=project, env=environment, capture_output=True, text=True, timeout=180)
            require(result.returncode == 0, f'{case.name}: compilation failed\n{result.stdout[-3000:]}\n{result.stderr[-10000:]}')
            check_pdf(pdf, case)
            print(f'Passed {case.name}', flush=True)


if __name__ == '__main__':
    main()
