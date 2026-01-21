# tex-repo

## A) One-line Description
SPEC-first LaTeX repository manager that scaffolds staged papers, validates structure, builds PDFs, and cuts immutable release bundles.

## B) Installation / Invocation
- Requires Python 3.8+ and a LaTeX toolchain with `latexmk` available for builds (`tex-repo env check` reports readiness).
- Install from this repository root with `pip install .`; this registers the `tex-repo` console script (entry point: `texrepo.__main__:main` in `pyproject.toml`).
- From a checkout you can also run `./tex-repo ...` (bash wrapper that sets `PYTHONPATH` then runs `python3 -m texrepo`) or `python -m texrepo ...`.

## C) Quick Start
1. `pip install .`
2. `tex-repo env check`
3. `tex-repo init demo-repo` (interactive metadata prompts; press Enter to accept defaults)
4. `cd demo-repo`
5. `tex-repo ns basics`
6. `tex-repo b` (builds `00_introduction` by default in the new layout; output in `00_introduction/build/`)

## D) CLI Commands

### tex-repo init
- Purpose: create a new tex-repo with staged layout, shared assets, and metadata.
- Required arguments: `target` (new repository path/name).
- Optional arguments: `--layout {new,old}` (default: `new`), `--legacy-seed-text PATH` (old layout only; must be a `.txt` file to seed `00_world/01_spec/sections/section_1.tex`).
- Defaults/behavior: writes `.paperrepo` with metadata collected via prompts, adds the gitignore policy block, creates shared preamble/macros/notation/identity files, scaffolds stage folders per layout, and seeds foundation/spec papers for the old layout.
- Example: `tex-repo init my-repo`
- Common failures: target directory already exists (including an existing tex-repo), invalid layout name, missing or non-`.txt` seed file, seed ignored when layout is `new`.

### tex-repo nd
- Purpose: create the next numbered domain folder under a valid `papers/` root (including process/regime and function/application branches).
- Required arguments: `parent_path` (e.g., `01_process_regime/process`), `domain_name` (slug without numbering).
- Behavior: resolves the canonical parent based on layout rules, picks the next `NN_` prefix, creates the folder, and writes a simple `README.md` if absent.
- Example: `tex-repo nd 01_process_regime/process my-topic`
- Common failures: not inside a repo, parent outside allowed stages/branches, or target folder already exists.

### tex-repo np
- Purpose: create a new paper skeleton outside the introduction book.
- Required arguments: `path_or_domain`; optional `maybe_slug`; optional `title` (default: `Untitled Paper`).
- Behavior: resolves the path according to layout rules (world layout only allows `00_foundation`/`01_spec`; introduction is rejected), ensures no entry file exists, then writes refs/sections/build/README plus an entry `.tex` file. Paper content uses `.texrepo-config` defaults (`section_count=10`, `document_class=article`, `document_options=11pt`, `include_abstract=true`) and metadata from `.paperrepo` for author macros; foundation/spec use specialized skeletons. If only two args are supplied, the second is treated as a title when the slug is embedded in the first path.
- Example: `tex-repo np 01_process_regime/process/papers/00_topic "Process Paper"`
- Common failures: invalid stage/branch, attempting to place papers under `00_introduction`, or an existing entry file in the target directory.

### tex-repo ns
- Purpose: add a numbered section (chapter) to the introduction book with ten subsection files.
- Required arguments: `section_name`.
- Behavior: creates `00_introduction/sections/NN_<section_name>/` (skipping `00_`), adds `chapter.tex` plus `N-1.tex` through `N-10.tex` placeholders, and errors if the section already exists.
- Example: `tex-repo ns overview`
- Common failures: introduction stage missing for the current layout or duplicate section name.

### tex-repo b
- Purpose: compile a paper (or all papers) to PDF with caching and log hints.
- Required arguments: none; positional `target` is optional (default: `.`), accepts `all` to build every discovered paper.
- Optional arguments: `--engine {latexmk,pdflatex}` (default: `latexmk`), `--clean` (remove `build/` contents first), `--force` (rebuild even when up to date), `--verbose` (show full output and log tail on failure).
- Defaults/behavior: resolves the target relative to repo root; when run from the root with the `new` layout the default target is `00_introduction`, and with the `old` layout it is `00_world/01_spec`. Skips rebuilding if outputs are newer unless `--clean`/`--force` is set. `latexmk` runs once; `pdflatex` runs twice. On failure prints a primary log error with suggested fixes. For the book-scale introduction, build regenerates `build/chapters_index.tex` (chapter includes) and `build/sections_index.tex` (subsection spine) before compiling.
- Example: `tex-repo b 01_process_regime/process/papers/00_topic --engine pdflatex --force`
- Common failures: not inside a repo, target without an entry `.tex`, missing LaTeX toolchain, or `all` with no papers found.

### tex-repo status
- Purpose: validate repository structure against the selected layout.
- Arguments: none.
- Behavior: checks required top-level directories, required `README.md` files, presence of entry `.tex` files, introduction section structure, and that papers live under allowed `papers/` roots; respects `.gitignore` patterns when counting unexpected items. Warns on placeholder metadata; exit code is non-zero when errors/violations exist.
- Example: `tex-repo status`
- Common failures: running outside a tex-repo (missing `.paperrepo`) or missing required structure.

### tex-repo sync-meta
- Purpose: regenerate `shared/identity.tex` from `.paperrepo` metadata.
- Arguments: none.
- Behavior: parses `.paperrepo` and rewrites `shared/identity.tex` with escaped metadata macros.
- Example: `tex-repo sync-meta`
- Common failures: not inside a repo or write errors.

### tex-repo config
- Purpose: create or overwrite `.texrepo-config` with default settings.
- Arguments: none.
- Behavior: writes paper defaults (`section_count=10`, `document_class=article`, `document_options=11pt`, `include_abstract=true`) and build defaults (`default_engine=latexmk`, `parallel_builds=true`) to the repo root.
- Example: `tex-repo config`
- Common failures: not inside a repo or file write errors.

### tex-repo release
- Purpose: create an immutable release bundle for a paper.
- Required arguments: `paper_path` (relative to repo root).
- Optional arguments: `--label LABEL` (appended to the timestamped release ID), `--engine {latexmk,pdflatex}` (default: `latexmk`), `--clean` (clean before building).
- Behavior: verifies the paper directory, builds the PDF if missing using the chosen engine (honoring `--clean`), derives a sanitized title from `\title{}` for naming, writes a release directory under `releases/` containing the PDF, `sources/` (paper + shared files + `repo.paperrepo`), `RELEASE.txt` (metadata including git commit when available), `MANIFEST.json`, and `SHA256SUMS`, then appends a record to `releases/index.jsonl`.
- Example: `tex-repo release 01_process_regime/process/papers/00_topic --label submitted`
- Common failures: invalid paper path, existing release directory with the same ID/title, or build failures.

### tex-repo fix
- Purpose: repair repository structure by creating missing files and folders without deleting user content.
- Optional arguments: `--dry-run` (report actions without writing).
- Behavior: ensures required stage folders, branch `papers/` folders, `.paperrepo`, `.texrepo-config` (only when missing), shared preamble/macros/notation, `shared/identity.tex` (when `.paperrepo` exists), introduction entry/sections, world foundation/spec skeleton for the old layout, and required `README.md` files. Updates `.gitignore` to include the policy block. Existing files are left in place.
- Example: `tex-repo fix --dry-run`
- Common failures: not inside a repo or permission errors when creating files.

### tex-repo env (subcommands)
- `tex-repo env check`: prints OS/Python info, checks for `latexmk` (required) and `pdflatex` (optional), suggests install commands on failure, and returns non-zero when required tools are missing.
- `tex-repo env guide`: writes `env_guide.txt` in the current directory with OS-specific installation commands and current tool status.

### tex-repo install
- Purpose: execute installation commands from a generated `env_guide.txt`.
- Required arguments: `guide_path`.
- Behavior: validates the guide signature, supports only apt/dnf (Linux) or Homebrew (macOS), extracts commands from the OS-specific bash blocks, asks for confirmation (`y`), then executes commands sequentially until one fails.
- Example: `tex-repo install env_guide.txt`
- Common failures: guide not generated by `tex-repo env guide`, unsupported OS/package manager, user cancels confirmation, or an installation command exits non-zero.

## E) Repository Structure & Conventions
- Repo root is identified by `.paperrepo`; layout comes from its `layout` field or defaults to `new` when `00_introduction/` exists (`texrepo/layouts.py` and `texrepo/status_cmd.py`).
- New layout requires `00_introduction`, `01_process_regime`, `02_function_application`, `03_hypnosis`; old layout requires `00_world` (with `00_foundation` and `01_spec`), `01_formalism`, `02_process_regime`, `03_function_application`. Allowed extras: `shared`, `scripts`, `98_context`, `99_legacy`, `releases`.
- Papers belong under `papers/` beneath each stage/branch (process/regime and function/application split into named branches). Each paper is expected to have an entry `.tex` named after the folder (legacy `main.tex` is tolerated but reported), `sections/`, `refs.bib`, and `README.md`. Build outputs live in `build/`.
- The introduction book uses `00_introduction/00_introduction.tex` with book-scale scaffolding organized under a `parts/` container directory:
  - `parts/frontmatter/` (title.tex, preface.tex, how_to_read.tex, toc.tex)
  - `parts/sections/NN_name/` with `chapter.tex` plus `N-1.tex` … `N-10.tex`
  - `parts/backmatter/` (scope_limits.tex, closing_notes.tex)
  - `parts/appendix/` (optional `.tex` files, sorted lexicographically)
  - `build/` (generated output, not under parts/)
  - Entry file `00_introduction.tex` contains only `\input{build/sections_index.tex}`
- `tex-repo b` regenerates `build/sections_index.tex` (which includes frontmatter, all sections with subsections, optional appendix, and backmatter) before compiling.
- **Backward compatibility**: Existing repos with the old flat structure (`sections/`, `frontmatter/`, `backmatter/`, `appendix/` at the introduction root level) will continue to work. The build system prefers `parts/` when it exists, but falls back to the old paths. `tex-repo status` will issue a warning for old structures but will not fail. `tex-repo fix` will not auto-migrate old structures to avoid destructive changes.
- `.texrepo-config` in the repo root controls new paper scaffolding (section count, document class/options, abstract inclusion) and stores build defaults; `shared/` holds the LaTeX preamble/macros/notation/identity included by generated papers.
- Releases are stored under `releases/` with per-release folders and an audit log at `releases/index.jsonl`.

## F) Git Policy (as implemented)
- `tex-repo init` and `tex-repo fix` enforce a `.gitignore` policy block that ignores LaTeX/build artifacts (`**/build/`, `.aux`, `.log`, etc.), editor/OS noise, `env_guide.txt`, and `.texrepo/`, while explicitly keeping `releases/`.
- Build artifacts remain untracked under each paper’s `build/` directory; release bundles are meant to be retained under `releases/`.
- `tex-repo fix` only creates missing files/directories and adds the gitignore policy block; it does not delete or overwrite user content.

## G) Development & Testing
- Run the full suite from the repository root with `python -m pytest` or `python tests/run_tests.py` (the runner sets `PYTHONPATH` for the checkout).
- No linters/formatters are configured in the repo; tests live under `tests/` and cover CLI behavior, layouts, and LaTeX build hints.

### Title Formatting Contract (Introduction Sections)

Section titles in the Introduction book are **display-only** and are derived from
section folder names under:

`00_introduction/parts/sections/NN_<raw-name>/`

This formatting affects only the generated `\section{...}` text in
`00_introduction/build/sections_index.tex`. It never changes folder names,
file paths, ordering, or any user-authored `.tex` content.

#### Normalization

- The section title source is the folder suffix `<raw-name>` after the `NN_` prefix.
- Hyphens (`-`) and underscores (`_`) are treated as word separators and rendered as spaces.

#### Book-Style Capitalization

The formatter applies book-style capitalization to the normalized words:

1. The **first word** is always capitalized.
2. The following connector words are **lowercase unless first**:
   `vs`, `and`, `or`, `of`, `in`, `on`, `for`, `to`, `the`, `a`, `an`
3. Acronyms are preserved:
   - Words that are all-uppercase remain all-uppercase.
   - Short lowercase tokens of length 1–2 are treated as acronyms and uppercased
     **unless they are connector words**.
4. Numeric tokens are preserved as-is.

#### Examples

- `01_section-1` → `\section{Section 1}`
- `02_np_vs_p` → `\section{NP vs P}`
- `03_law_of_motion` → `\section{Law of Motion}`
- `04_in_the_beginning` → `\section{In the Beginning}`

#### Title Overrides (Mathematical Notation)

**Policy**: Directory names are structural identifiers and MUST NOT encode mathematical notation.

When you need mathematical notation or complex LaTeX in a section title (e.g., `$\alpha$ vs NP`),
use an **explicit override file** instead of embedding symbols in folder names.

**Override Mechanism**:

For any section directory:
```
00_introduction/parts/sections/NN_<raw-name>/
```

If a file named `title.tex` exists inside that directory, its content will be used
**verbatim** as the section title, replacing the formatted folder name.

**Rules**:

1. `title.tex` contains **only** the LaTeX content for the title.
   - Do NOT include `\section{}` or other structural commands.
   - The generator emits: `\section{<content of title.tex>}`

2. `title.tex` may contain math mode, formatting commands, or any valid LaTeX.

3. If `title.tex` is missing or empty (whitespace-only), the system falls back
   to the book-style formatted folder name.

**Example**:

```
00_introduction/parts/sections/01_np_vs_p/
├── title.tex          ← Contains: $\alpha$ vs NP
├── 1-1.tex
├── 1-2.tex
└── ...
```

Generated output in `sections_index.tex`:
```latex
\section{$\alpha$ vs NP}
```

Without `title.tex`, the folder name `01_np_vs_p` would generate:
```latex
\section{NP vs P}
```
