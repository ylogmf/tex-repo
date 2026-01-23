# tex-repo

A structural manager for LaTeX repositories supporting book-scale and paper-scale projects. Built for long-lived research repositories, not ad-hoc papers.

## Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Repository identification](#repository-identification)
- [Repository layout (book + papers)](#repository-layout-book--papers)
- [Introduction book](#introduction-book)
- [Generated index files](#generated-index-files)
- [Commands](#commands)
- [Git policy](#git-policy)
- [Development](#development)
- [Design notes](#design-notes)

## Overview
tex-repo provides:
- repository initialization
- deterministic directory structure
- structure validation
- reproducible PDF builds
- immutable release bundles

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
tex-repo init demo-repo
cd demo-repo
tex-repo book "Introduction"
cd 00_introduction
tex-repo part "Foundations"
cd parts/parts/NN_foundations
tex-repo chapter "Overview"
cd ../../..
tex-repo build 00_introduction
```

Creates a repository, scaffolds the introduction book, and builds it.

## Repository identification
A directory is recognized as a tex-repo repository by the presence of:

```
.paperrepo
```

No global configuration is used; all structure is local and explicit.

## Repository layout (book + papers)
A typical repository contains:

```
.
├── .paperrepo
├── shared/
├── 00_introduction/
├── 01_process_regime/
├── 02_function_application/
├── 03_hypophysis/
├── releases/
└── .gitignore
```

- `shared/` holds common macros, notation, and identity files.
- Numbered stage directories define conceptual ordering.
- `releases/` contains immutable output bundles only.

## Introduction book
The introduction is a book-class LaTeX document with explicit structural separation.

**Entry file**
- `00_introduction/00_introduction.tex` uses `\documentclass{book}`, defines `\frontmatter`, `\mainmatter`, `\backmatter`, and includes generated index files from `build/`.

**Structure**
```
00_introduction/
├── 00_introduction.tex
├── parts/
│   ├── frontmatter/
│   ├── parts/
│   │   └── NN_<part_name>/
│   │       ├── part.tex
│   │       └── chapters/
│   │           └── NN_<chapter_name>/
│   │               ├── chapter.tex
│   │               ├── 1-1.tex
│   │               └── ...
│   ├── backmatter/
│   └── appendix/        # optional
└── build/               # generated only
```

## Generated index files
Inside `build/`:
- `sections_index.tex`: frontmatter navigation only; no sectioning commands.
- `chapters_index.tex`: all content (parts, chapters, sections, appendix, backmatter).

This separation avoids duplicate TOC entries and incorrect numbering.

## Commands

### Repository setup
- `tex-repo init <name>`: Initialize a new repository. Writes `.paperrepo`, installs `.gitignore` policy, creates `shared/`, and prepares ordered stage directories (`00_introduction/`, `01_process_regime/`, `02_function_application/`, `03_hypnosis/`, `releases/`). Fails if the target directory already exists.
  ```sh
  tex-repo init my-repo
  ```

### Authoring
- `tex-repo book "<title>"`: Create a book-class document at the repository root. Must be run from the root. Creates a numbered directory `NN_<slug>/` with an entry `.tex`, `parts/`, `frontmatter/`, `backmatter/`, and `build/`.
  ```sh
  tex-repo book "Introduction"
  ```
- `tex-repo paper "<title>"`: Create an article-class paper at the repository root. Must be run from the root. Creates a numbered directory `NN_<slug>/` with an entry `.tex` file, `sections/`, `refs.bib`, and `build/`.
  ```sh
  tex-repo paper "Process Notes"
  ```
- `tex-repo part "<title>"`: Create a new part inside a book. Must be run inside a book directory. Automatically numbers parts and creates `parts/parts/NN_<slug>/` with `part.tex` and `chapters/`.
  ```sh
  cd 00_introduction
  tex-repo part "Foundations"
  ```
- `tex-repo chapter "<title>"`: Create a new chapter inside a part. Must be run inside a part directory. Automatically numbers chapters and creates `chapters/NN_<slug>.tex`.
  ```sh
  cd parts/parts/01_foundations   # number assigned automatically
  tex-repo chapter "Overview"
  ```

Build and release

tex-repo build [target|all]
Build LaTeX documents.

If no target is given, builds the document in the current directory.

all builds all discovered documents in the repository.

A document is identified by the presence of a valid entry .tex file.

Output is written to the document’s build/ directory.

Default engine: latexmk.

tex-repo build
tex-repo build 00_introduction
tex-repo build all


tex-repo release <target>
Create an immutable release bundle for a successfully built document.

The target must refer to a document that has already been built.

Release artifacts are written under:

releases/


Release contents are immutable and intended to be committed.

tex-repo build 00_introduction
tex-repo release 00_introduction


### Validation and repair
- `tex-repo status`: Validate repository structure. Checks required files, placement, and ordering; does not modify the repository.
- `tex-repo fix`: Create missing required files and directories without deleting or overwriting user content; safe to run repeatedly.
- `tex-repo guard`: Enforce repository invariants for CI. Runs the same checks as `status`, exits non-zero on any violation, and produces a concise report.
  ```sh
  tex-repo guard
  ```

## Git policy
- All `build/` directories are ignored.
- Editor and OS artifacts are ignored.
- `releases/` is tracked.

## Development
Run tests:

```sh
python -m pytest
```

## Design notes
- Structure is explicit and enumerable.
- Ordering is enforced by directory prefixes.
- Generated files are strictly separated from authored content.
- No implicit global state or background mutation.
- If structure is ambiguous, tex-repo rejects it.

## Naming rules

tex-repo derives semantic structure from directory names. Naming rules are therefore part of the repository contract.

### General rules

- Directory names are lowercase.
- Words are separated by underscores (`_`) or hyphens (`-`).
- Numbering prefixes (`NN_`) are reserved for structural ordering and are managed by tex-repo.
- Users must not manually edit numbering prefixes.

### Stage directories

Top-level stage directories use fixed names and ordering:

```
00_introduction
01_process_regime
02_function_application
03_hypophysis
```

Stage directory names are fixed and must not be renamed.

### Book structure (Introduction)

Within `00_introduction/`, directory names carry semantic meaning.

#### Parts

```
parts/parts/NN_<part_name>/
```

- `<part_name>` is a semantic slug.
- Historically, parts correspond to sections of the overall work.
- The name is used to derive the displayed part title.
- Renaming a part directory renames the part.

**Examples:**

| Directory name | Displayed title |
|----------------|-----------------|
| `01_foundations` | Foundations |
| `02_type_consistency` | Type Consistency |
| `03_np_vs_p` | NP vs P |

#### Chapters

```
chapters/NN_<chapter_name>/
```

- `<chapter_name>` is a semantic slug.
- Chapters correspond to conceptual subdivisions within a part.
- The directory name determines the chapter title.

**Examples:**

| Directory name | Displayed title |
|----------------|-----------------|
| `01_overview` | Overview |
| `02_structural_limits` | Structural Limits |
| `03_in_the_beginning` | In the Beginning |

#### Papers

Standalone papers use the same naming rules.

```
NN_<paper_name>/
```

- `<paper_name>` is a semantic slug.
- The directory name determines:
  - the entry `.tex` filename
  - the displayed document title (unless overridden in the file)
- Paper directories must not be placed under `00_introduction`.

**Examples:**

| Directory name | Paper title |
|----------------|-------------|
| `01_process_notes` | Process Notes |
| `02_hypothesis_review` | Hypothesis Review |
| `03_np_vs_p` | NP vs P |

### Title formatting

Titles are derived from directory names using book-style capitalization:

- The first word is always capitalized.
- Connector words are lowercased unless first:
  ```
  vs, and, or, of, in, on, for, to, the, a, an
  ```
- All-uppercase tokens are preserved.
- Short lowercase tokens of length 1–2 are treated as acronyms unless they are connector words.
- Numeric tokens are preserved.
- Hyphens (`-`) and underscores (`_`) are treated as word separators.

**Examples:**

| Directory name | Generated title |
|----------------|-----------------|
| `np_vs_p` | NP vs P |
| `law_of_motion` | Law of Motion |
| `in_the_beginning` | In the Beginning |
| `section_1` | Section 1 |

### Enforcement

- `tex-repo status` reports naming violations.
- `tex-repo guard` fails on naming violations.
- `tex-repo fix` does not rename user directories.

## Naming invariant checklist

The following rules are invariants. Violations are reported by `tex-repo status` and fail under `tex-repo guard`.

### Global invariants

- [ ] All directory names are lowercase.
- [ ] Words are separated by underscores (`_`) or hyphens (`-`).
- [ ] Numbering prefixes (`NN_`) appear only where explicitly allowed.
- [ ] Numbering prefixes are assigned by tex-repo and must not be edited manually.
- [ ] Directory names are semantically meaningful; placeholder names are invalid.

### Stage directory invariants

- [ ] The following top-level directories exist:
  ```
  00_introduction
  01_process_regime
  02_function_application
  03_hypophysis
  ```
- [ ] Stage directory names are fixed and must not be renamed.
- [ ] No additional numbered stage directories are permitted.

### Introduction book invariants

#### Entry

- [ ] `00_introduction/00_introduction.tex` exists.
- [ ] The entry file uses `\documentclass{book}`.
- [ ] `\frontmatter`, `\mainmatter`, and `\backmatter` are defined.

#### Parts

- [ ] All parts live under: `00_introduction/parts/parts/`
- [ ] Each part directory is named: `NN_<part_name>`
- [ ] `<part_name>` is a semantic slug.
- [ ] Each part contains:
  - `part.tex`
  - `chapters/`
- [ ] Part numbering is contiguous and starts at 01.

#### Chapters

- [ ] All chapters live under: `chapters/`
- [ ] Each chapter directory is named: `NN_<chapter_name>`
- [ ] `<chapter_name>` is a semantic slug.
- [ ] Each chapter contains: `chapter.tex`
- [ ] Chapter numbering is contiguous within each part.

### Paper invariants

- [ ] Paper directories are named: `NN_<paper_name>`
- [ ] Papers are not placed under `00_introduction`.
- [ ] Each paper directory contains:
  - an entry `.tex` file named after the directory
  - `sections/`
  - `refs.bib`
  - `build/`
- [ ] Paper numbering is contiguous within its parent directory.

### Title derivation invariants

- [ ] Display titles are derived from directory names.
- [ ] Underscores and hyphens are treated as word separators.
- [ ] The first word is capitalized.
- [ ] Connector words are lowercased unless first: `vs, and, or, of, in, on, for, to, the, a, an`
- [ ] All-uppercase tokens are preserved.
- [ ] Numeric tokens are preserved.

### Generated content invariants

- [ ] All generated files are written under `build/`.
- [ ] No user-authored content is written to `build/`.
- [ ] `build/` directories are ignored by git.
- [ ] `releases/` is tracked by git.

### Enforcement invariants

- [ ] `tex-repo status` reports all invariant violations.
- [ ] `tex-repo guard` exits non-zero on any violation.
- [ ] `tex-repo fix` does not rename or delete user content.

### Why this checklist exists

This checklist is not documentation. It is the structural contract enforced by tex-repo.

If a repository violates these invariants, it is considered structurally invalid.

### Build → Release invariants

- [ ] tex-repo release <target> is permitted only if <target> is a valid document root and its build artifacts exist.

- [ ] A target is considered built only if its build/ directory contains the expected primary output:

book targets: a PDF matching the entry file basename

paper targets: a PDF matching the entry file basename

- [ ] tex-repo release never triggers a build. It only packages existing build outputs.

- [ ] Release bundles are written only under releases/ and do not modify authored source files.

- [ ] A release bundle is immutable once created: re-running release for the same (target, version) must fail rather than overwrite.

Book invariants (Introduction)
Book root and entry

- [ ] 00_introduction/ is the only book-class document in the repository.

- [ ] 00_introduction/00_introduction.tex exists and is the unique entry file for the book.

- [ ] 00_introduction/build/ exists and contains generated files only.

- [ ] 00_introduction/parts/ exists.

Required subtrees

- [ ] 00_introduction/parts/frontmatter/ exists.

- [ ] 00_introduction/parts/backmatter/ exists.

- [ ] 00_introduction/parts/parts/ exists.

- [ ] 00_introduction/parts/appendix/ is optional, and if present contains only .tex files.

Generated spine separation

- [ ] 00_introduction/build/sections_index.tex exists and is frontmatter navigation only.

- [ ] 00_introduction/build/chapters_index.tex exists and is the only spine for main content.

- [ ] sections_index.tex contains no \part, \chapter, or \section.

- [ ] chapters_index.tex is the only generated file allowed to include \part / \chapter / \section.

Entry-file inclusion rules

- [ ] The entry file inputs build/sections_index.tex only within \frontmatter.

- [ ] The entry file inputs build/chapters_index.tex only within \mainmatter.

- [ ] The entry file defines \frontmatter, \mainmatter, and \backmatter in this order.

Part structure

- [ ] Every part directory matches NN_<part_slug> and contains:

part.tex

chapters/

- [ ] Part numbering starts at 01 and is contiguous with no gaps.

Chapter structure

- [ ] Every chapter directory matches NN_<chapter_slug> and contains:

chapter.tex

1-1.tex through 1-10.tex (or a repo-wide configured count if supported)

- [ ] Chapter numbering is contiguous within each part.

- [ ] Section placeholder filenames follow the 1-K.tex pattern and are contiguous.

No build pollution

- [ ] No authored .tex content lives under 00_introduction/build/.

- [ ] No generated index file is written outside 00_introduction/build/.

Guard violation codes (book)

tex-repo guard emits violations as:

<CODE>\t<PATH>\t<MESSAGE>


Codes are stable. New codes may be added, but existing codes must not change meaning.

Book entry and root

BOOK_ROOT_MISSING
00_introduction/ missing.

BOOK_ENTRY_MISSING
00_introduction/00_introduction.tex missing.

BOOK_ENTRY_NOT_UNIQUE
Multiple candidate book entry files detected in 00_introduction/.

BOOK_BUILD_DIR_MISSING
00_introduction/build/ missing.

BOOK_PARTS_DIR_MISSING
00_introduction/parts/ missing.

Required subtrees

BOOK_FRONTMATTER_DIR_MISSING
00_introduction/parts/frontmatter/ missing.

BOOK_BACKMATTER_DIR_MISSING
00_introduction/parts/backmatter/ missing.

BOOK_PARTS_PARTS_DIR_MISSING
00_introduction/parts/parts/ missing.

BOOK_APPENDIX_INVALID
00_introduction/parts/appendix/ exists but contains invalid entries (non-.tex, wrong naming, etc.).

Spine (generated index) rules

BOOK_SECTIONS_INDEX_MISSING
00_introduction/build/sections_index.tex missing.

BOOK_CHAPTERS_INDEX_MISSING
00_introduction/build/chapters_index.tex missing.

BOOK_SECTIONS_INDEX_SECTIONING_LEAK
sections_index.tex contains forbidden sectioning commands (\part, \chapter, \section).

BOOK_CHAPTERS_INDEX_MISSING_SECTIONING
chapters_index.tex does not contain any recognized content spine entries when content exists.

BOOK_SPINE_WRITTEN_OUTSIDE_BUILD
A generated spine file (sections_index.tex or chapters_index.tex) is found outside 00_introduction/build/.

Entry inclusion rules

BOOK_ENTRY_MISSING_FRONTMATTER
Entry file does not define \frontmatter.

BOOK_ENTRY_MISSING_MAINMATTER
Entry file does not define \mainmatter.

BOOK_ENTRY_MISSING_BACKMATTER
Entry file does not define \backmatter.

BOOK_ENTRY_SPINE_INCLUDE_MISSING
Entry file does not include required spine files.

BOOK_ENTRY_SPINE_INCLUDE_WRONG_PHASE
Spine included in the wrong phase (e.g., chapters_index.tex included in \frontmatter).

Part structure

BOOK_PART_DIR_INVALID_NAME
A part directory under parts/parts/ does not match NN_<slug>.

BOOK_PART_NUMBER_GAP
Part numbering is not contiguous starting from 01.

BOOK_PART_DUPLICATE_SLUG
Duplicate part slugs detected (same <slug> across different NN_).

BOOK_PART_TEX_MISSING
part.tex missing inside a part directory.

BOOK_PART_CHAPTERS_DIR_MISSING
chapters/ missing inside a part directory.

Chapter structure

BOOK_CHAPTER_DIR_INVALID_NAME
A chapter directory under chapters/ does not match NN_<slug>.

BOOK_CHAPTER_NUMBER_GAP
Chapter numbering is not contiguous within a part.

BOOK_CHAPTER_DUPLICATE_SLUG
Duplicate chapter slugs detected within the same part.

BOOK_CHAPTER_TEX_MISSING
chapter.tex missing inside a chapter directory.

BOOK_SECTION_PLACEHOLDER_MISSING
One or more required 1-K.tex placeholders are missing.

BOOK_SECTION_PLACEHOLDER_GAP
1-K.tex placeholders are not contiguous (e.g., missing 1-4.tex).

BOOK_SECTION_PLACEHOLDER_INVALID_NAME
Invalid section placeholder filenames (not matching 1-<n>.tex).

Build pollution rules

BOOK_BUILD_CONTAINS_AUTHORED_CONTENT
Authored content detected under 00_introduction/build/ (anything beyond generated indices/logs).

BOOK_GENERATED_CONTENT_OUTSIDE_BUILD
Generated-only files detected outside 00_introduction/build/.

Recommended guard output examples

Example violations:

BOOK_ENTRY_MISSING\t00_introduction/00_introduction.tex\tMissing book entry file
BOOK_PART_NUMBER_GAP\t00_introduction/parts/parts/\tExpected parts 01..N contiguous
BOOK_SECTIONS_INDEX_SECTIONING_LEAK\t00_introduction/build/sections_index.tex\tFrontmatter index must not contain \\chapter/\\section

Formal detection rules (book)

Let:

R be the repository root.

B = R/00_introduction

E = B/00_introduction.tex

P = B/parts/parts

G = B/build

S = G/sections_index.tex

C = G/chapters_index.tex

Define helper predicates:

exists(x) : path x exists.

is_dir(x) : x exists and is a directory.

is_file(x) : x exists and is a regular file.

children(x) : immediate children of directory x.

match(name, regex) : filename matches regex.

read(x) : file contents as text.

contains(x, pattern) : pattern occurs in read(x).

glob(x, pattern) : matching paths under x (non-recursive unless stated).

parts(P) : sorted list of part directories under P matching ^(\d\d)_(.+)$.

chapters(part) : sorted list of chapter directories under part/chapters matching ^(\d\d)_(.+)$.

Parsing conventions (minimal, lexical):

SECTIONING = { "\\part", "\\chapter", "\\section" }

contains_any(file, SET) ⇔ ∃t∈SET : contains(file, t)

phase_split(E) is not required; inclusion rules are checked lexically by searching for required tokens and their relative order.

Book entry and root

BOOK_ROOT_MISSING
¬is_dir(B)

BOOK_ENTRY_MISSING
¬is_file(E)

BOOK_ENTRY_NOT_UNIQUE
count(glob(B, "*.tex")) ≠ 1 ∧ is_file(E)
(i.e., more than one .tex exists in 00_introduction/ besides the canonical entry)

BOOK_BUILD_DIR_MISSING
¬is_dir(G)

BOOK_PARTS_DIR_MISSING
¬is_dir(B/parts)

Required subtrees

BOOK_FRONTMATTER_DIR_MISSING
¬is_dir(B/parts/frontmatter)

BOOK_BACKMATTER_DIR_MISSING
¬is_dir(B/parts/backmatter)

BOOK_PARTS_PARTS_DIR_MISSING
¬is_dir(P)

BOOK_APPENDIX_INVALID
exists(B/parts/appendix) ∧ (¬is_dir(B/parts/appendix) ∨ ∃x∈children(B/parts/appendix): ¬match(x.name, r"^.+\.tex$"))

Spine (generated index) rules

BOOK_SECTIONS_INDEX_MISSING
¬is_file(S)

BOOK_CHAPTERS_INDEX_MISSING
¬is_file(C)

BOOK_SECTIONS_INDEX_SECTIONING_LEAK
is_file(S) ∧ contains_any(S, SECTIONING)

BOOK_CHAPTERS_INDEX_MISSING_SECTIONING
is_file(C) ∧ content_exists(B) ∧ ¬contains_any(C, { "\\part", "\\chapter" })

Where content_exists(B) may be defined purely structurally as:
content_exists(B) ⇔ ∃p∈parts(P): is_file(p/"part.tex") ∨ ∃ch∈chapters(p): is_file(ch/"chapter.tex")

BOOK_SPINE_WRITTEN_OUTSIDE_BUILD
∃x under B (recursive): x.name ∈ {"sections_index.tex","chapters_index.tex"} ∧ x.parent ≠ G

Entry inclusion rules (lexical)

Let T = read(E).

BOOK_ENTRY_MISSING_FRONTMATTER
is_file(E) ∧ ¬(" \\frontmatter" in T or "\\frontmatter" in T)

BOOK_ENTRY_MISSING_MAINMATTER
is_file(E) ∧ ¬contains(E, "\\mainmatter")

BOOK_ENTRY_MISSING_BACKMATTER
is_file(E) ∧ ¬contains(E, "\\backmatter")

BOOK_ENTRY_SPINE_INCLUDE_MISSING
is_file(E) ∧ (¬contains(E, "build/sections_index.tex") ∨ ¬contains(E, "build/chapters_index.tex"))

BOOK_ENTRY_SPINE_INCLUDE_WRONG_PHASE
is_file(E) ∧ order_violation(E)

where a minimal, implementable ordering rule is:

let i_f = index(T, "\\frontmatter")

let i_m = index(T, "\\mainmatter")

let i_b = index(T, "\\backmatter")

let i_S = index(T, "build/sections_index.tex")

let i_C = index(T, "build/chapters_index.tex")

Then:
order_violation(E) ⇔ ¬(i_f < i_S < i_m < i_C < i_b)
(Any missing index is handled by BOOK_ENTRY_SPINE_INCLUDE_MISSING first.)

Part structure

BOOK_PART_DIR_INVALID_NAME
is_dir(P) ∧ ∃x∈children(P): is_dir(x) ∧ ¬match(x.name, r"^\d\d_[a-z0-9][a-z0-9_-]*$")

BOOK_PART_NUMBER_GAP
parts = parts(P); nums = [int(NN) for (NN,slug) in parts]; nums ≠ [1..len(nums)]

BOOK_PART_DUPLICATE_SLUG
∃slug: count({p.slug | p∈parts(P)}) < len(parts(P))

BOOK_PART_TEX_MISSING
∃p∈parts(P): ¬is_file(p/"part.tex")

BOOK_PART_CHAPTERS_DIR_MISSING
∃p∈parts(P): ¬is_dir(p/"chapters")

Chapter structure

For each part p, let Q = p/chapters.

BOOK_CHAPTER_DIR_INVALID_NAME
∃p∈parts(P): is_dir(Q) ∧ ∃x∈children(Q): is_dir(x) ∧ ¬match(x.name, r"^\d\d_[a-z0-9][a-z0-9_-]*$")

BOOK_CHAPTER_NUMBER_GAP
For any part p:
chs = chapters(p); nums = [int(NN) ...]; nums ≠ [1..len(nums)]

BOOK_CHAPTER_DUPLICATE_SLUG
For any part p:
∃slug: count({ch.slug | ch∈chapters(p)}) < len(chapters(p))

BOOK_CHAPTER_TEX_MISSING
∃p∈parts(P), ch∈chapters(p): ¬is_file(ch/"chapter.tex")

Section placeholders (if enforced):

Let required count be K = 10 unless repo-wide configuration exists.

BOOK_SECTION_PLACEHOLDER_MISSING
∃p, ch: ∃n∈[1..K]: ¬is_file(ch/f"1-{n}.tex")

BOOK_SECTION_PLACEHOLDER_GAP
∃p, ch: files = {n | is_file(ch/f"1-{n}.tex")}; files ≠ [1..max(files)]

BOOK_SECTION_PLACEHOLDER_INVALID_NAME
∃p, ch: ∃x∈children(ch): match(x.name, r"^1-.*\.tex$") ∧ ¬match(x.name, r"^1-\d+\.tex$")

Build pollution rules

BOOK_BUILD_CONTAINS_AUTHORED_CONTENT
is_dir(G) ∧ ∃x under G (recursive): x.name matches authored_pattern

Minimal authored pattern:

any .tex file in G other than {sections_index.tex, chapters_index.tex}

any directory in G other than engine temp/log/aux conventions

Formally:
∃x under G: is_file(x) ∧ match(x.name, r"^.+\.tex$") ∧ x.name ∉ {"sections_index.tex","chapters_index.tex"}

BOOK_GENERATED_CONTENT_OUTSIDE_BUILD
∃x under B (recursive): x.name ∈ {"sections_index.tex","chapters_index.tex"} ∧ x.parent ≠ G

Notes on determinism

All rules above are lexical and filesystem-based.

No LaTeX compilation is required to validate structure.

guard must report all violations in a single run.

Guard violation codes (paper)

tex-repo guard emits violations as:

<CODE>\t<PATH>\t<MESSAGE>


Codes are stable. New codes may be added, but existing codes must not change meaning.

Formal detection rules (paper)
Definitions

Let:

R be the repository root.

I = R/00_introduction

D be a candidate paper directory.

E(D) be the paper entry file inside D.

S(D) = D/sections

B(D) = D/build

Helper predicates (same semantics as book):

exists(x), is_dir(x), is_file(x)

children(x)

match(name, regex)

glob(x, pattern)

read(x)

contains(x, pattern)

Paper-specific helpers:

paper_dir(D)
⇔ is_dir(D) ∧ match(D.name, r"^\d\d_[a-z0-9][a-z0-9_-]*$")

entry_tex(D)
⇔ the unique file f such that
is_file(f) ∧ f.parent = D ∧ match(f.name, r"^\d\d_[a-z0-9][a-z0-9_-]*\.tex$")

entry_basename(D)
⇔ D.name + ".tex"

Placement rules

PAPER_PLACEMENT_FORBIDDEN_UNDER_INTRO
paper_dir(D) ∧ D is descendant of I

PAPER_PLACEMENT_INVALID_STAGE
paper_dir(D) ∧ D.parent ∉ {01_process_regime, 02_function_application, 03_hypophysis} (recursive)

Entry file rules

PAPER_ENTRY_MISSING
paper_dir(D) ∧ ¬is_file(D/entry_basename(D))

PAPER_ENTRY_NOT_UNIQUE
paper_dir(D) ∧ count(glob(D, "*.tex")) ≠ 1

PAPER_ENTRY_NAME_MISMATCH
paper_dir(D) ∧ is_file(f) ∧ f.name ≠ entry_basename(D)

Required subtree rules

PAPER_SECTIONS_DIR_MISSING
paper_dir(D) ∧ ¬is_dir(S(D))

PAPER_BUILD_DIR_MISSING
paper_dir(D) ∧ ¬is_dir(B(D))

PAPER_REFS_MISSING
paper_dir(D) ∧ ¬is_file(D/"refs.bib")

Sections structure rules

Let K ≥ 1 be the number of section files detected.

PAPER_SECTIONS_EMPTY
is_dir(S(D)) ∧ count(children(S(D))) = 0

PAPER_SECTION_INVALID_NAME
∃x∈children(S(D)): is_file(x) ∧ ¬match(x.name, r"^\d+\.tex$")

PAPER_SECTION_NUMBER_GAP
Let nums = sorted({int(n) | "n.tex" exists in S(D)})
nums ≠ [1..len(nums)]

Build invariants

Let PDF(D) = B(D)/entry_basename(D).replace(".tex",".pdf").

PAPER_BUILD_PDF_MISSING
paper_dir(D) ∧ ¬is_file(PDF(D))

PAPER_BUILD_DIR_EMPTY
is_dir(B(D)) ∧ count(children(B(D))) = 0

Build pollution rules

PAPER_BUILD_CONTAINS_AUTHORED_CONTENT
∃x under B(D): is_file(x) ∧ match(x.name, r"\.tex$")

PAPER_GENERATED_CONTENT_OUTSIDE_BUILD
∃x under D: x.name endswith ".aux" or ".log" or ".pdf" ∧ x.parent ≠ B(D)

Numbering rules

For any directory P containing paper directories {D1, D2, …}:

PAPER_NUMBER_GAP
Let nums = sorted({int(D.name[0:2])})
nums ≠ [1..len(nums)]

PAPER_DUPLICATE_SLUG
∃slug: count({D.slug}) < count({D})

Release precondition rules

PAPER_RELEASE_BEFORE_BUILD
release(D) attempted ∧ ¬is_file(PDF(D))

PAPER_RELEASE_OVERWRITE_ATTEMPT
A release bundle for the same (D, version) already exists.

Determinism guarantees

All paper rules are:

filesystem-based

lexical

non-compiling

guard must report all violations in a single run.

fix must not attempt to resolve any violation listed above.

One-line closure (fits your philosophy)

A paper is not a directory with LaTeX files.
A paper is a directory that satisfies invariants.