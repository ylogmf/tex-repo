# tex-repo: LaTeX Repository Manager

A lightweight CLI that enforces a disciplined, layered structure for research writing.
The repository is governed by explicit structural rules rather than usage conventions.

---

## Structure

tex-repo enforces a single canonical repository layout and a strict README policy.

### Repository Layout (Top Level)

Top-level directories:

- `00_introduction/`
- `01_process_regime/`
- `02_function_application/`
- `03_hypnosis/`
- `shared/`
- `scripts/`
- `98_context/`
- `99_legacy/`
- `releases/`
- `.paperrepo`
- `.texrepo-config`

README policy:
A `README.md` is required at every stage, branch, and paper level.
Required READMEs are created only when missing and are never overwritten.

Paper placement and entry rule:
Papers live under their allowed `papers/` roots.
Each paper’s entry file matches its folder name (`<paper>/<paper>.tex`);
the `main.tex` convention is not used.

Paper skeleton rule:
Each paper directory contains:
- `README.md`
- `<paper>.tex` (entry file, same name as the paper folder)
- `sections/` (section files)
- `refs.bib` (paper bibliography file)

Generated build outputs belong under `build/` and are not treated as required structure.

Layout selection:
Layout is determined by `.paperrepo` when present, otherwise by auto-detection
(using the presence of `00_introduction/`).
`init --layout new` may be used to force the new layout at initialization time.

When configuration is absent and auto-detection does not determine a layout, the default layout is `new`.

### Required Layout

```
my-repo/
├── .paperrepo
├── .texrepo-config
├── 00_introduction/
│   ├── README.md
│   ├── 00_introduction.tex
│   ├── sections/
│   │   ├── 01_<section-name>/
│   │   │   ├── 1-1.tex
│   │   │   ├── 1-2.tex
│   │   │   ├── ...
│   │   │   └── 1-10.tex
│   │   ├── 02_<section-name>/
│   │   │   ├── 2-1.tex
│   │   │   ├── 2-2.tex
│   │   │   ├── ...
│   │   │   └── 2-10.tex
│   │   └── ...
│   ├── refs.bib (optional)
│   └── build/ (generated)
├── 01_process_regime/
│   ├── README.md
│   ├── process/
│   │   ├── README.md
│   │   └── papers/
│   │       └── 00_<subject>/
│   │           ├── README.md
│   │           ├── 00_<subject>.tex
│   │           ├── refs.bib
│   │           └── sections/
│   └── regime/
│       ├── README.md
│       └── papers/
│           └── 00_<subject>/
│               ├── README.md
│               ├── 00_<subject>.tex
│               ├── refs.bib
│               └── sections/
├── 02_function_application/
│   ├── README.md
│   ├── function/
│   │   ├── README.md
│   │   └── papers/
│   │       └── 00_<subject>/
│   │           ├── README.md
│   │           ├── 00_<subject>.tex
│   │           ├── refs.bib
│   │           └── sections/
│   └── application/
│       ├── README.md
│       └── papers/
│           └── 00_<subject>/
│               ├── README.md
│               ├── 00_<subject>.tex
│               ├── refs.bib
│               └── sections/
├── 03_hypnosis/
│   ├── README.md
│   └── papers/
│       └── 00_<topic>/
│           ├── README.md
│           ├── 00_<topic>.tex
│           ├── refs.bib
│           └── sections/
├── shared/
├── scripts/
├── 98_context/
├── 99_legacy/
└── releases/
```
### Paper Structure (Paper-Scale)

All components other than `00_introduction/` are **paper-scale**.
Paper-scale components are organized as collections of independent papers.

Structural rules for paper-scale components:

- Papers live under a `papers/` directory.
- Each paper is represented by a **single directory** under `papers/`.
- Paper directories are numbered and named, e.g.:
  - `00_<paper-name>/`, `01_<paper-name>/`, …
- Each paper directory contains the following required elements:
  - `README.md` — paper metadata and description.
  - `<paper-name>.tex` — the paper’s entry file.
  - `sections/` — directory containing section `.tex` files.
  - `refs.bib` — bibliography file for the paper.
- Section files under `sections/` are ordered numerically
  (e.g. `01_intro.tex`, `02_method.tex`), and are included by the entry file.
- Build artifacts (such as `build/`) are generated outputs and are not part
  of the required paper structure.

This structure applies to all paper-scale components, including:
`01_process_regime/`, `02_function_application/`, and `03_hypnosis/`.

### Introduction Structure (Book-Scale)

`00_introduction/` is a book-scale component and is also buildable like a paper.
It is structured as a book composed of sections and subsections,
not as a collection of independent papers.

Structural rules for `00_introduction/`:

- The book has an **entry file** for building: `00_introduction.tex`
- All sections live under the **`sections/` directory**.
- Each section is represented by a **directory** under `00_introduction/sections/`.
- Each section directory contains approximately **ten subsections**.
- Each subsection is represented by a **single `.tex` file**.
- Subsection files are named using numeric order, e.g.:
  - `1-1.tex`, `1-2.tex`, …, `1-10.tex`
- Subsection files contain content only; ordering is determined by filename.
- No `papers/` directory is used inside `00_introduction/`.
- `refs.bib` is optional.
- `build/` contains generated outputs and is not part of the required structure.

This structure applies **only** to `00_introduction/`.
All other components in the repository are paper-scale and follow paper structure rules.


---

## Commands

Commands define structural guarantees and conservative behavior.
They do not delete, overwrite, or rename user content.

### init

**Purpose**  
Establish a repository that conforms to the selected layout.

**Guarantees**
- Creates required top-level directories.
- Creates required stage, branch, and paper `README.md` files when missing.
- Scaffolds the required paper skeleton (`<paper>.tex`, `sections/`, `refs.bib`) when creating new papers.
- Never overwrites existing files or directories.

**Non-goals**
- Does not infer or generate paper content beyond scaffolding.
- Does not reorganize existing repositories.

---

### status

**Purpose**  
Validate repository structure against layout rules.

**Guarantees**
- Errors when required top-level directories are missing.
- Errors when required READMEs are missing.
- Errors when papers are found outside allowed `papers/` locations.

**Non-goals**
- Does not modify repository contents.

---

### fix

**Purpose**  
Complete missing structural elements required by the layout.

**Guarantees**
- Creates missing required directories and READMEs.
- Preserves all existing files and directories.

**Non-goals**
- Never deletes, renames, or overwrites user content.

---

### nd

**Purpose**  
Create a numbered paper folder under the correct `papers/` root.

**Guarantees**
- Creates the appropriate `00_<name>` directory under the correct `papers/` root.

**Non-goals**
- Does not create a full paper unless combined with `np`.

---

### np

**Purpose**  
Create a paper at a requested logical path.

**Guarantees**
- Creates the paper directory and required paper skeleton.
- Auto-inserts `papers/` into the path when omitted.

**Non-goals**
- Does not place papers outside allowed `papers/` locations.

---

### b

**Purpose**  
Build a paper.

**Guarantees**
- Attempts to build the specified paper path (or `all`).
- On failure, summarizes the primary LaTeX error.
- `--verbose` increases output verbosity.

---

### release

**Purpose**  
Create an immutable release bundle for a paper.

---

### sync-meta

**Purpose**  
Regenerate `shared/identity.tex` from `.paperrepo`.

---

### config

**Purpose**  
Create `.texrepo-config` if missing.

---

## Design Rules

- Dependency direction: introduction → process/regime → function/application → hypnosis.
- Papers remain inside their designated `papers/` roots.
- Entry file names mirror their folders.
- Commands are conservative by design.
