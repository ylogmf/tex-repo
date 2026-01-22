# tex-repo

LaTeX repository manager for book-scale and paper-scale projects.  
Provides repository scaffolding, structure validation, PDF builds, and immutable release bundles.

---

## Requirements

- **Python 3.8+**
- **LaTeX toolchain**
  - `latexmk` (required)
  - `pdflatex` (optional)

Check environment:

```bash
tex-repo env check
```

---

## Installation

From the repository root:

```bash
pip install .
```

This installs the `tex-repo` CLI (entry point: `texrepo.__main__:main`).

You may also run from a checkout:

```bash
./tex-repo ...
# or
python -m texrepo ...
```

---

## Quick Start

```bash
pip install .
tex-repo init demo-repo
cd demo-repo
tex-repo ns overview
tex-repo b
```

This initializes a repository and builds the introduction book.

---

## Repository Layout

A repository is identified by the presence of `.paperrepo`.

**Top-level structure:**

```
.
├── .paperrepo
├── shared/
├── 00_introduction/
├── 01_process_regime/
├── 02_function_application/
├── 03_hypnosis/
└── releases/
```

---

## Introduction (Book)

The introduction is a book-class LaTeX document.

**Structure:**

```
00_introduction/
├── 00_introduction.tex
├── parts/
│   ├── frontmatter/
│   │   ├── title.tex
│   │   ├── preface.tex
│   │   └── how_to_read.tex
│   ├── sections/
│   │   └── NN_<name>/
│   │       ├── chapter.tex
│   │       ├── 1-1.tex
│   │       ├── 1-2.tex
│   │       ├── ...
│   │       └── 1-10.tex
│   ├── backmatter/
│   │   ├── closing_notes.tex
│   │   └── scope_limits.tex
│   └── appendix/                # optional
│       ├── A_<name>.tex
│       ├── B_<name>.tex
│       └── ...
└── build/                       # generated files only
    ├── chapters_index.tex
    ├── sections_index.tex
    └── latexmk.log
```

- `parts/` contains source files
- `build/` contains generated files only

**Entry file:** `00_introduction/00_introduction.tex`

- Uses `\documentclass{book}`
- Defines `\frontmatter`, `\mainmatter`, `\backmatter`
- Inputs generated files from `build/`

---

## Commands Overview

### `tex-repo init <path>`
Create a new repository with the standard layout.

### `tex-repo ns <name>`
Add a new chapter to the introduction book.

**Creates:**
```
parts/sections/NN_<name>/
├── chapter.tex
├── 1-1.tex
└── ...
```

### `tex-repo np <path> [title]`
Create a new paper under an allowed `papers/` directory.

Each paper has its own entry `.tex`, `sections/`, `refs.bib`, and `build/`.

**Structure:**
```
papers/NN_<paper_name>/
├── NN_<paper_name>.tex        # paper entry file
├── sections/
│   ├── 1.tex
│   ├── 2.tex
│   ├── 3.tex
│   ├── ...
│   └── N.tex
├── refs.bib                  # bibliography
├── build/                    # generated files only
│   ├── NN_<paper_name>.pdf
│   ├── latexmk.log
│   └── aux/                  # engine-specific temp files
└── README.md                 # paper notes / scope / status
```

### `tex-repo b [target|all]`
Build a paper or the introduction book.

- Outputs go to `build/`
- Uses `latexmk` by default

### `tex-repo release <paper_path>`
Create an immutable release bundle under `releases/`.

### `tex-repo status`
Validate repository structure.

### `tex-repo fix`
Create missing required files and directories.  
Does not delete or overwrite user content.

---

## Git Policy

- `build/` directories are ignored
- Editor and OS files are ignored
- `releases/` is tracked

---

## Development

Run tests from the repository root:

```bash
python -m pytest
```

---

## CLI Commands Reference

tex-repo is invoked as:

```bash
tex-repo COMMAND [options]
```

---

### `tex-repo init`

**Purpose**  
Create a new tex-repo with staged layout, shared assets, and metadata.

**Required arguments**
- `target` — New repository path or name

**Optional arguments**
- `--layout {new,old}` — Repository layout (default: `new`)
- `--legacy-seed-text PATH` — Old layout only. Must be a `.txt` file used to seed `00_world/01_spec/sections/section_1.tex`

**Behavior**
- Writes `.paperrepo` with metadata collected via prompts
- Adds the gitignore policy block
- Creates shared preamble/macros/notation/identity files
- Scaffolds stage folders according to the selected layout
- Seeds foundation/spec papers for the old layout

**Example**

```bash
tex-repo init my-repo
```

**Common failures**
- Target directory already exists (including an existing tex-repo)
- Invalid layout name
- Missing or non-.txt seed file
- Seed text provided when layout is new (ignored)

---

### tex-repo nd

Purp`tex-repo nd`

**Purpose**  
Create the next numbered domain folder under a valid `papers/` root.

**Required arguments**
- `parent_path` — Example: `01_process_regime/process`
- `domain_name` — Slug without numbering

**Behavior**
- Resolves the canonical parent based on layout rules
- Picks the next `NN_` prefix
- Creates the folder
- Writes a simple `README.md` if absent

**Example**

```bash
tex-repo nd 01_process_regime/process my-topic
```

**Common failures**
- Not inside a tex-repo
- Parent outside allowed stages or branches
- Target folder already exists

### tex-repo np

Purp`tex-repo np`

**Purpose**  
Create a new paper skeleton outside the introduction book.

**Required arguments**
- `path_or_domain`

**Optional arguments**
- `maybe_slug`
- `title` (default: `Untitled Paper`)

**Behavior**
- Resolves the path according to layout rules
- Rejects placement under `00_introduction`
- Ensures no entry `.tex` file exists
- Writes:
  - Entry `.tex` file
  - `sections/`
  - `refs.bib`
  - `build/`
  - `README.md`
- Uses `.texrepo-config` defaults:
  - `section_count = 10`
  - `document_class = article`
  - `document_options = 11pt`
  - `include_abstract = true`
- Injects author metadata from `.paperrepo`
- Foundation/spec papers use specialized skeletons
- If only two arguments are supplied, the second is treated as the title when the slug is embedded in the first path

**Example**

```bash
tex-repo np 01_process_regime/process/papers/00_topic "Process Paper"
```

**Common failures**
- Invalid stage or branch
- Attempting to place papers under `00_introduction`
- Existing entry `.tex` file in the target directory

### tex-repo ns
`tex-repo ns`

**Purpose**  
Add a numbered chapter to the introduction book.

**Required arguments**
- `section_name`

**Behavior**
- Creates: `00_introduction/parts/sections/NN_<section_name>/`
- Skips `NN = 00`
- Generates:
  - `chapter.tex`
  - `1-1.tex` through `1-10.tex` placeholders
- Errors if the section already exists

**Example**

```bash
tex-repo ns overview
```

**Common failures**
- Introduction stage missing
- Duplicate section name
---

### `tex-repo b`

**Purpose**  
Compile a paper (or all papers) to PDF with caching and log hints.

**Required arguments**
- None

**Optional positional arguments**
- `target` — Path to a paper or directory (default: `.`)
- `all` — Build every discovered paper

**Optional flags**
- `--engine {latexmk,pdflatex}` — LaTeX engine (default: `latexmk`)

---

## Title Formatting Contract (Introduction Sections)

Section titles in the Introduction book are **display-only** and are derived from section folder names under:

```
00_introduction/parts/sections/NN_<raw-name>/
```

This formatting affects **only** the generated `\section{...}` text in:

```
00_introduction/build/sections_index.tex
```

It never changes folder names, file paths, ordering, or any user-authored `.tex` content.

---

### Normalization

- The section title source is the folder suffix `<raw-name>` after the `NN_` prefix
- Hyphens (`-`) and underscores (`_`) are treated as word separators and rendered as spaces

---

### Book-Style Capitalization

The formatter applies book-style capitalization to the normalized words:

- The **first word** is always capitalized
- The following connector words are lowercase unless first:
  ```
  vs, and, or, of, in, on, for, to, the, a, an
  ```
- Acronyms are preserved:
  - Words that are all-uppercase remain all-uppercase
  - Short lowercase tokens of length 1–2 are treated as acronyms and uppercased, unless they are connector words
- Numeric tokens are preserved as-is

---

### Examples

| Folder Name              | Generated Title              |
|--------------------------|------------------------------|
| `01_section-1`           | `\section{Section 1}`        |
| `02_np_vs_p`             | `\section{NP vs P}`          |
| `03_law_of_motion`       | `\section{Law of Motion}`    |
| `04_in_the_beginning`    | `\section{In the Beginning}` |

---

### Title Overrides (Mathematical Notation)

**Policy**  
Directory names are structural identifiers and **MUST NOT** encode mathematical notation.

When mathematical notation or complex LaTeX is required in a section title (e.g. `$\alpha$ vs NP`), use an explicit override file instead of embedding symbols in folder names.

---

### Override Mechanism

For any section directory:

```
00_introduction/parts/sections/NN_<raw-name>/
```

If a file named `title.tex` exists inside that directory, its content is used **verbatim** as the section title, replacing the formatted folder name.

---

### Rules

- `title.tex` contains **only** the LaTeX content for the title
- Do **NOT** include `\section{}` or any other structural commands
- The generator emits:
  ```latex
  \section{<content of title.tex>}
  ```
- `title.tex` may contain math mode, formatting commands, or any valid LaTeX
- If `title.tex` is missing or empty (whitespace-only), the system falls back to the book-style formatted folder name

---

### Override Example

**Directory:**

```
00_introduction/parts/sections/01_np_vs_p/
├── title.tex        # contains: $\alpha$ vs NP
├── 1-1.tex
├── 1-2.tex
└── ...
```

**Generated output in `sections_index.tex`:**

```latex
\section{$\alpha$ vs NP}
```

**Without `title.tex`**, the folder name `01_np_vs_p` generates:

```latex
\section{NP vs P}
```
