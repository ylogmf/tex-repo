# Invariants Checklist

The following rules are invariants. Violations are reported by `tex-repo status` and fail under `tex-repo guard`.

## Global invariants

- [ ] All directory names are lowercase.
- [ ] Words are separated by underscores (`_`) or hyphens (`-`).
- [ ] Numbering prefixes (`NN_`) appear only where explicitly allowed.
- [ ] Numbering prefixes are assigned by tex-repo and must not be edited manually.
- [ ] Directory names are semantically meaningful; placeholder names are invalid.

## Stage directory invariants

- [ ] The following top-level directories exist:
  ```
  00_introduction
  01_process_regime
  02_function_application
  03_hypophysis
  ```
- [ ] Stage directory names are fixed and must not be renamed.
- [ ] No additional numbered stage directories are permitted.

## Introduction book invariants

### Entry

- [ ] `00_introduction/00_introduction.tex` exists.
- [ ] The entry file uses `\documentclass{book}`.
- [ ] `\frontmatter`, `\mainmatter`, and `\backmatter` are defined.

### Parts

- [ ] All parts live under: `00_introduction/parts/parts/`
- [ ] Each part directory is named: `NN_<part_name>`
- [ ] `<part_name>` is a semantic slug.
- [ ] Each part contains:
  - `part.tex`
  - `chapters/`
- [ ] Part numbering is contiguous and starts at 01.

### Chapters

- [ ] All chapters live under: `chapters/`
- [ ] Each chapter directory is named: `NN_<chapter_name>`
- [ ] `<chapter_name>` is a semantic slug.
- [ ] Each chapter contains: `chapter.tex`
- [ ] Chapter numbering is contiguous within each part.

## Paper invariants

- [ ] Paper directories are named: `NN_<paper_name>`
- [ ] Papers are not placed under `00_introduction`.
- [ ] Each paper directory contains:
  - an entry `.tex` file named after the directory
  - `sections/`
  - `refs.bib`
  - `build/`
- [ ] Paper numbering is contiguous within its parent directory.

## Title derivation invariants

- [ ] Display titles are derived from directory names.
- [ ] Underscores and hyphens are treated as word separators.
- [ ] The first word is capitalized.
- [ ] Connector words are lowercased unless first: `vs, and, or, of, in, on, for, to, the, a, an`
- [ ] All-uppercase tokens are preserved.
- [ ] Numeric tokens are preserved.

## Generated content invariants

- [ ] All generated files are written under `build/`.
- [ ] No user-authored content is written to `build/`.
- [ ] `build/` directories are ignored by git.
- [ ] `releases/` is tracked by git.

## Enforcement invariants

- [ ] `tex-repo status` reports all invariant violations.
- [ ] `tex-repo guard` exits non-zero on any violation.
- [ ] `tex-repo fix` does not rename or delete user content.

## Build → Release invariants

- [ ] `tex-repo release <target>` is permitted only if `<target>` is a valid document root and its build artifacts exist.
- [ ] A target is considered built only if its `build/` directory contains the expected primary output:
  - book targets: a PDF matching the entry file basename
  - paper targets: a PDF matching the entry file basename
- [ ] `tex-repo release` never triggers a build. It only packages existing build outputs.
- [ ] Release bundles are written only under `releases/` and do not modify authored source files.
- [ ] A release bundle is immutable once created: re-running release for the same (target, version) must fail rather than overwrite.

## Why this checklist exists

This checklist is not documentation. It is the structural contract enforced by tex-repo.

If a repository violates these invariants, it is considered structurally invalid.
