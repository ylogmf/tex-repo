# tex-repo

A structural manager for LaTeX repositories supporting book-scale and paper-scale projects. Built for long-lived research repositories, not ad-hoc papers.

## Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Repository structure](#repository-structure)
- [Commands](#commands)
- [Documentation](#documentation)
- [Development](#development)

## Overview

tex-repo provides:
- Repository initialization with deterministic structure
- Book-class documents with Part/Chapter hierarchy
- Article-class papers with auto-numbering
- Structure validation and repair
- Reproducible PDF builds
- Immutable release bundles

## Requirements

- Python 3.8+
- LaTeX toolchain with `latexmk` (required) and `pdflatex` (optional)

Verify your environment:

```sh
tex-repo env check
```

## Installation

From the repository root:

```sh
pip install .
```

This installs the `tex-repo` CLI. You can also run directly from source:

```sh
python -m texrepo ...
```

## Quick start

```sh
# Initialize repository
tex-repo init demo-repo
cd demo-repo

# Create a book
tex-repo book "Introduction"
cd 00_introduction

# Add structure
tex-repo part "Foundations"
cd parts/parts/01_foundations
tex-repo chapter "Overview"

# Build
cd ../../..
tex-repo build 00_introduction
```

## Repository structure

A tex-repo repository is identified by `.paperrepo` at its root. No global configuration is used.

### Typical layout

```
.
├── .paperrepo
├── shared/              # Common macros, notation, identity
├── 00_introduction/     # Book-class document
├── 01_process_regime/   # Stage directory
├── 02_function_application/
├── 03_hypophysis/
├── releases/            # Immutable release bundles (tracked)
└── .gitignore
```

### Book structure

Books use LaTeX `book` class with explicit frontmatter/mainmatter/backmatter separation:

```
00_introduction/
├── 00_introduction.tex           # Entry file
├── parts/
│   ├── frontmatter/              # Title, preface, TOC
│   ├── parts/
│   │   └── NN_<part_name>/
│   │       ├── part.tex
│   │       └── chapters/
│   │           └── NN_<chapter_name>.tex
│   └── backmatter/
└── build/                        # Generated indices
    ├── sections_index.tex        # Frontmatter spine
    └── chapters_index.tex        # Mainmatter spine
```

**Important:** `sections_index.tex` contains frontmatter navigation only (no sectioning commands). `chapters_index.tex` contains all mainmatter content. This separation prevents duplicate TOC entries.

### Paper structure

Papers use LaTeX `article` class:

```
NN_<paper_name>/
├── paper.tex                     # Entry file
├── sections/
├── refs.bib
└── build/
```

## Commands

### Repository setup

```sh
tex-repo init <name>
```

Initialize a new repository with `.paperrepo`, `.gitignore`, `shared/` directory, and stage directories.

### Authoring

**`tex-repo book "<title>"`**

Create a book-class document at repository root. Auto-numbered (00_, 01_, ...).

```sh
tex-repo book "Introduction to Category Theory"
# Creates: 00_introduction_to_category_theory/
```

**`tex-repo paper "<title>"`**

Create an article-class paper at repository root. Auto-numbered.

```sh
tex-repo paper "Quantum Mechanics Primer"
# Creates: 01_quantum_mechanics_primer/
```

**`tex-repo part "<title>"`**

Create a part inside a book. Must run inside a book directory. Auto-numbered (01_, 02_, ...).

```sh
cd 00_introduction
tex-repo part "Foundations"
# Creates: parts/parts/01_foundations/
```

**`tex-repo chapter "<title>"`**

Create a chapter inside a part. Must run inside a part directory. Auto-numbered.

```sh
cd parts/parts/01_foundations
tex-repo chapter "Basic Concepts"
# Creates: chapters/01_basic_concepts.tex
```

### Build and release

**`tex-repo build [target|all]`**

Build LaTeX documents. Default target is current directory; `all` builds everything.

```sh
tex-repo build                    # Build current document
tex-repo build 00_introduction    # Build specific document
tex-repo build all                # Build all documents
```

**`tex-repo release <target>`**

Create immutable release bundle for a built document. Bundles are written to `releases/` and should be committed.

```sh
tex-repo build 00_introduction
tex-repo release 00_introduction
```

### Validation

**`tex-repo status`**

Validate repository structure. Reports violations, does not modify files.

**`tex-repo fix`**

Create missing required files and directories. Never overwrites or deletes user content.

**`tex-repo guard`**

Enforce repository invariants for CI. Exits non-zero on any violation.

```sh
tex-repo guard    # For CI pipelines
```

## Documentation

- **[NAMING.md](docs/NAMING.md)** - Directory naming rules and title formatting
- **[INVARIANTS.md](docs/INVARIANTS.md)** - Structural invariants checklist
- **[GUARD_CODES.md](docs/GUARD_CODES.md)** - Guard violation codes and formal detection rules

## Git policy

- All `build/` directories are ignored
- Editor and OS artifacts are ignored
- `releases/` is tracked

## Development

Run tests:

```sh
python -m pytest
```

Run specific test:

```sh
python -m pytest tests/test_new_commands.py -v
```

## Design principles

- **Explicit structure**: No implicit global state or background mutation
- **Deterministic ordering**: Enforced by directory prefixes (NN_)
- **Strict separation**: Generated files (`build/`) separated from authored content
- **Fail fast**: If structure is ambiguous, tex-repo rejects it
- **Enumerable**: All structure is discoverable from the filesystem

---

**Philosophy:** A document is not a directory with LaTeX files. A document is a directory that satisfies invariants.
