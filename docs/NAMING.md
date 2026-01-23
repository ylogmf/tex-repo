# Naming Rules

tex-repo derives semantic structure from directory names. Naming rules are therefore part of the repository contract.

## General rules

- Directory names are lowercase.
- Words are separated by underscores (`_`) or hyphens (`-`).
- Numbering prefixes (`NN_`) are reserved for structural ordering and are managed by tex-repo.
- Users must not manually edit numbering prefixes.

## Stage directories

Top-level stage directories use fixed names and ordering:

```
00_introduction
01_process_regime
02_function_application
03_hypophysis
```

Stage directory names are fixed and must not be renamed.

## Book structure (Introduction)

Within `00_introduction/`, directory names carry semantic meaning.

### Parts

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

### Chapters

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

### Papers

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

## Title formatting

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

## Enforcement

- `tex-repo status` reports naming violations.
- `tex-repo guard` fails on naming violations.
- `tex-repo fix` does not rename user directories.
