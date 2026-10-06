---
title: Semantic LaTeX Template Demo
subtitle: A book of university notes
author:
  - Giulio Salvi
date: 20 March 2026
lang: en
copyright-year: 2026
license: CC BY 4.0
colophon-text: 'These notes were typeset using \LaTeX{} software.'
preface-title: Preface
preface: |
  This short preface demonstrates how the template places optional front-matter
  sections before the main table of contents.

  It is a good place for context, scope, acknowledgements, or reading advice.
dedication: |
  To everyone who keeps refining their notes until they become a real book.
epigraph: |
  Everything should be made as simple as possible, but not simpler.
epigraph-author: Albert Einstein
---

\part{Fundamentals}

# AVL trees {#ch:avl}

\begin{propertybox}{Binary search tree property}
\label{prop:bst}
An AVL tree satisfies the binary search tree property.
\end{propertybox}

## Balance and height

\begin{definitionbox}{Balance factor}
\label{def:balance}
For each internal node $x$, the balance factor is
\[
\bal{x} = h(\text{left}(x)) - h(\text{right}(x)).
\]
\end{definitionbox}

\begin{axiombox}{Extensionality}
Two sets are equal if and only if they have the same elements.
\end{axiombox}

\begin{theorembox}
\label{thm:height}
An AVL tree with $n$ nodes has height $O(\log n)$.
\end{theorembox}

\begin{proofsection}
The key idea is that the minimum number of nodes in an AVL tree of height $h$
satisfies a Fibonacci-style recurrence, so the height grows logarithmically in
the number of nodes.
\end{proofsection}

\part{Tools and applications}

# Algorithms and diagrams {#ch:algorithms}

## Search

\begin{algorithm}[H]
\caption{Search in an AVL tree}
\KwIn{Root node $r$, key $k$}
\KwOut{The node containing $k$, if it exists}
\While{$r \neq \texttt{nil}$}{
  \uIf{$k = r.key$}{
    \Return{$r$}
  }
  \uElseIf{$k < r.key$}{
    $r \gets r.left$
  }
  \Else{
    $r \gets r.right$
  }
}
\Return{\texttt{nil}}
\end{algorithm}

## A diagram

\begin{figure}[H]
\centering
\begin{tikzpicture}[
  every node/.style={circle,draw,minimum size=8mm,inner sep=0pt},
  level distance=10mm,
  sibling distance=20mm
]
\node {10}
  child {node {5}}
  child {node {15}};
\end{tikzpicture}
\caption{Simple AVL diagram drawn directly with TikZ.}
\end{figure}


# Mathematical notation and references {#ch:notation}

\begin{lemmabox}
\label{lem:norm}
For real $x$, the expression $\abs{x}$ is non-negative.
\end{lemmabox}

## Numbers and delimiters

The commands keep their previous syntax: $\set{1,2,3}$, $\abs{-2}$ and
$\norm{\begin{pmatrix}1\\2\end{pmatrix}}$. Unicode maths also supports
$\mathbb{R}$, $\mathcal{F}$, $\symbf{v}$ and $\int_0^1 x^2\,dx=\frac13$.

\begin{observationbox}
The statement counter continues across sections of the same chapter.
\end{observationbox}

The earlier \cref{def:balance,thm:height} belong to \cref{ch:avl}.
This chapter's \cref{lem:norm} has its own counter sequence.

| Notation | Meaning |
|:---------|:--------|
| $\abs{x}$ | Absolute value |
| $\norm{v}$ | Vector norm |
| $\set{1,2}$ | A finite set |

: Notation used in the examples.

## Code and figures

```python
def square(x):
    return x * x
```

![The quadratic function on a symmetric interval.](usage_example/assets/quadratic.png){#fig:quadratic width=65%}

\begin{tipbox}
PDF and PNG figures compile without enabling shell escape.
\end{tipbox}

## Lists and derivations

\begin{numberedlist}
\item Choose the input.
\item Compute the square.
\end{numberedlist}

\begin{unorderedlist}
\item The badge style matches the original template.
\item This list remains a standard LaTeX list.
\end{unorderedlist}

\begin{derivation}
\derivstep{(x+1)^2=x^2+2x+1}{expansion}
\derivstep{(x+1)^2-x^2=2x+1}{subtraction}
\end{derivation}

\begin{timeanalysissection}
Evaluating the square takes constant time.
\end{timeanalysissection}

\appendix

# Supplementary material

\begin{definitionbox}{A finite sequence}
\label{def:appendix}
A finite sequence has a fixed number of terms.
\end{definitionbox}

Appendix boxes use letters, as in \cref{def:appendix}.
