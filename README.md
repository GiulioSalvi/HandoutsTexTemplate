# Handouts LaTeX Template

A Pandoc LaTeX template for university handouts, lecture notes, and course
volumes. It uses LuaLaTeX and the standard `book` class, with an A4 layout,
semantic boxes, mathematical notation, algorithms, and linked references.

Write the main text in Pandoc Markdown and use the supplied LaTeX environments
for definitions, theorems, proofs, and other structured material.

## Features

- Parts, chapters, sections, and subsections, with chapter openings on right-hand
  pages by default.
- A cover, title page, and colophon, plus optional preface, dedication, and
  epigraph.
- Roman page numbers for preliminary material and Arabic page numbers for the
  main text.
- At least one completely blank page between the preliminary contents and the
  main text when the table of contents is enabled.
- Coloured semantic boxes with icons, shared chapter-based numbering, and
  automatic references.
- Unicode mathematics and Latin Modern OpenType fonts.
- English and Italian captions, hyphenation, and reference names.
- Algorithms, lists with badges, TikZ diagrams, plots, tables, images, and
  Pandoc code highlighting.
- Bibliographies processed with Pandoc Citeproc.

## Requirements

- Pandoc.
- A TeX distribution with LuaLaTeX and a LaTeX kernel dated June 2022 or later.
  TeX Live or MacTeX with the packages used by this repository is suitable.
- `latexmk` if you use the two-stage build described below.

The template uses packages including `fontspec`, `unicode-math`, `babel`,
`microtype`, `tcolorbox`, `fontawesome5`, `algorithm2e`, `tikz`, `pgfplots`,
`hyperref`, and `cleveref`. The complete package list is in [`requirements.txt`](requirements.txt).
The default fonts are provided by TeX Live.

## Build the example

Run the following commands from the root of this repository:

```sh
mkdir -p build
TEXINPUTS="$PWD:" pandoc \
  --defaults=defaults.yaml \
  --defaults=usage_example/defaults.yaml \
  --template=template.tex \
  --pdf-engine=lualatex \
  -o build/example.pdf
```

The output is `build/example.pdf`. The explicit `--template` option selects
the template in the repository root. The example's image paths also assume
this working directory.

To inspect the generated LaTeX or use `latexmk` for subsequent builds:

```sh
mkdir -p build
pandoc \
  --defaults=defaults.yaml \
  --defaults=usage_example/defaults.yaml \
  --template=template.tex \
  -o build/example.tex

TEXINPUTS="$PWD:" latexmk \
  -lualatex \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir=build \
  build/example.tex
```

`template.tex` contains Pandoc placeholders such as `$body$` and `$title$`.
Pandoc must expand these before LaTeX compilation.

## Usage

Keep each course's Markdown, assets, and build configuration in its own
project. Start from [`usage_example/defaults.yaml`](usage_example/defaults.yaml)
and customise the source, output, and document options. For example:

```yaml
from: markdown+raw_tex
to: latex
standalone: true
input-file: '${.}/handout.md'
output-file: '${.}/handout.pdf'
template: '${TEX_TEMPLATE_PATH}'
pdf-engine: lualatex
top-level-division: chapter
number-sections: true
table-of-contents: true
toc-depth: 3
variables:
  fontsize: 11pt
```

`${.}` refers to the directory containing the defaults file. Define
`TEX_TEMPLATE_PATH` as the path to this repository's `template.tex`, and put
the repository root in `TEXINPUTS` for the build process. From the course
project, for a template installed at `~/.tex_templates/templates/handouts`:

```sh
TEX_TEMPLATE_PATH="$HOME/.tex_templates/templates/handouts/template.tex" \
TEXINPUTS="$HOME/.tex_templates/templates/handouts:" \
pandoc --defaults=pandoc.yaml
```

The trailing `:` in `TEXINPUTS` retains the standard TeX search paths. The
template root is searched without the recursive `//` suffix, so the example
directory is not added as a source of template modules.

## Document structure

With `top-level-division: chapter`, use the following hierarchy:

| Source | Document level |
| --- | --- |
| `\part{Foundations}` | Part |
| `# Real numbers` | Chapter |
| `## Ordering` | Section |
| `### Properties` | Subsection |
| `#### Further details` | Subsubsection |

Parts and chapters have their own opening pages. Chapter numbering continues
across parts. Insert `\appendix` before appendix chapters to obtain lettered
chapter numbers and corresponding box numbers.

With this hierarchy, `toc-depth: 3` includes subsections in the table of
contents. Use `toc-depth: 4` to include subsubsections as well.

The main text starts on a right-hand page. When the contents end on a
right-hand page, one blank page separates them from the main text; when they
end on a left-hand page, two blank pages are inserted. Blank pages have no
visible headers or page numbers. If lists of figures or tables are enabled,
the separation follows those lists.

## Metadata and customisation

Put editorial metadata in a YAML block at the beginning of the Markdown file,
or in a separate file loaded with `--metadata-file=metadata.yaml`:

```yaml
---
title: Mathematical Analysis
subtitle: Volume II
author:
  - Giulio Salvi
date: October 2026
lang: en
copyright-year: 2026
preface: |
  Scope, prerequisites, and suggestions for using these notes.
---
```

- `lang: en` or `lang: it` selects English or Italian. Italian is the default.
- `dedication`, `epigraph`, `epigraph-author`, `preface-title`, and
  `colophon-text` customise optional preliminary material.
- `license` prints the document's declared licence in its colophon. The
  repository's software licence is specified separately in `LICENSE`.
- `openany: true` allows subsequent chapter openings on either side; the
  default is `openright`. The transition to the main text still opens on the
  right-hand page.
- `table-of-contents: true` enables the contents. Set it to `false` to omit
  them. `toc-depth` controls which heading levels are included.
- `fontsize` accepts the standard `book` sizes: `10pt`, `11pt`, and `12pt`.
  The default is `11pt`; `linestretch` defaults to `1.08`.
- `mainfont`, `monofont`, and `mathfont`, with their respective
  `mainfontoptions`, `monofontoptions`, and `mathfontoptions`, customise fonts.
- `header-includes` adds document-specific LaTeX to the preamble.

Set `secnumdepth` under `variables` to control LaTeX heading numbering. Its
default is `3` when section numbering is enabled, which numbers through
subsubsections.

## Semantic environments and references

Use LaTeX blocks in the Markdown source:

```latex
\begin{definitionbox}{Continuity}
\label{def:continuity}
Write the definition here using LaTeX syntax.
\end{definitionbox}

As stated in \cref{def:continuity}, ...
```

Numbered environments are `propertybox`, `definitionbox`, `theorembox`,
`axiombox`, `lemmabox`, `observationbox`, and `tipbox`. Their numbers share one sequence
per chapter: `1.1`, `1.2`, and so on, restarting at `2.1` in the next chapter.
Sections do not restart that sequence. Place numbered boxes inside numbered
chapters. `\cref` preserves the type of the referenced box.

Additional environments include `proofsection`,
`timeanalysissection`, and `sidebarsection`. Examples of boxes, algorithms,
custom lists, diagrams, images, and appendices are provided in
[`usage_example/example-pandoc.md`](usage_example/example-pandoc.md).

Raw LaTeX environments use LaTeX syntax internally; Markdown formatting
inside them is not automatically converted. The `\set{...}`, `\abs{...}`,
`\norm{...}`, and `\bal{...}` mathematical shorthand commands are available.

## Citations and additional resources

Use Pandoc Citeproc for bibliographies, for example by adding `--citeproc`
and supplying a bibliography in the document configuration. The template
includes the LaTeX support needed for Citeproc output.

PDF and PNG images require no shell escape. SVG conversion through
`\includesvg` additionally requires Inkscape and the conversion setup used by
the `svg` package.

A Markdown directive such as `!include chapter.md` requires an additional
Pandoc filter. No inclusion filter is bundled with this template. Pandoc's
Lua filters use its embedded Lua interpreter.

## Repository layout

```text
handouts/
├── README.md
├── LICENSE
├── defaults.yaml
├── environment.sh
├── requirements.txt
├── .gitattributes
├── .github/workflows/
│   ├── ci.yml
│   └── release.yml
├── scripts/
│   ├── package-release.py
│   ├── publish-release.sh
│   └── smoke-test.sh
├── template.tex
├── style/
│   ├── packages.tex
│   ├── colors.tex
│   ├── commands.tex
│   ├── boxes.tex
│   ├── pandoc-support.tex
│   └── citations.tex
└── usage_example/
    ├── defaults.yaml
    ├── example-pandoc.md
    ├── example-pandoc.pdf
    └── assets/
```

The repository can be used on its own or registered as a Git submodule in a
larger template library. Its files are resolved relative to the selected
template root.

## License

Copyright (C) 2026 Giulio Salvi.

This project is licensed under the **GNU General Public License, version 3
or, at your option, any later version** (`GPL-3.0-or-later`), as stated in the
source-file notices. See [`LICENSE`](LICENSE) for the full licence text.

## References

- [Pandoc user guide](https://pandoc.org/MANUAL.html)
- [Pandoc Lua filters](https://pandoc.org/lua-filters.html)
- [Standard LaTeX classes](https://www.latex-project.org/help/documentation/classes.pdf)
- [fontspec](https://ctan.org/pkg/fontspec)
- [GNU GPL version 3](https://www.gnu.org/licenses/gpl-3.0.html)


## Release automation

The CI packages the selected Git tree and compiles the example against the
extracted package. The development example remains in the Git repository;
release archives exclude it, `.gitignore`, `.gitattributes`, `.github`, and
maintenance scripts according to `.gitattributes`.

Push a stable three-part version tag to publish a release:

```sh
git tag v0.1.0
git push origin v0.1.0
```

The release workflow creates these assets:

- `handouts-X.Y.Z.tar.gz`, whose top-level directory is `handouts/`;
- `handouts-X.Y.Z.json`, describing the repository, tag, full commit, archive
  filename, and SHA256;
- `SHA256SUMS` for both assets.

Archives are generated from the exact tagged commit. The workflow attaches
assets to a draft before publishing, so it works with optional GitHub release
immutability. Rerunning the workflow verifies an existing published release
and can resend its library notification without replacing published assets.

To notify a parent library after publication, configure these values under
**Settings → Secrets and variables → Actions** in this repository:

- Repository variable `LIBRARY_REPOSITORY`: the full name of the parent
  repository, for example `GiulioSalvi/TexTemplates`.
- Repository secret `LIBRARY_DISPATCH_TOKEN`: a fine-grained PAT with access to
  that parent repository and **Contents: Read and write**. This credential is
  used only to send the cross-repository notification.

The receiving parent workflow must exist on its default branch and accept the
`template-released` repository-dispatch event. The payload identifies the
released template ID, tag, and full commit. If `LIBRARY_REPOSITORY` is unset,
the template still publishes independently and skips notification. If it is
set, a missing dispatch secret is reported as a configuration error.

Install and push the workflow changes before creating the first version tag.
To retry an existing tag, use **Actions → Publish template release → Run
workflow** and supply that tag.

For local packaging from a committed version tag:

```sh
python3 scripts/package-release.py --tag v0.1.0 --output dist
sh scripts/smoke-test.sh dist/handouts-0.1.0.tar.gz
```

The smoke test needs Pandoc and LuaLaTeX. It creates a temporary installation,
compiles with the extracted runtime template, and removes its temporary files.

The example source is available in the [GitHub development checkout](https://github.com/GiulioSalvi/HandoutsTexTemplate/tree/main/usage_example).
