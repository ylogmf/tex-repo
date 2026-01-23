# Automation Specification (tex-repo)

This document defines the **allowed automation scope** of tex-repo.

Automation in tex-repo is limited to **mechanical, structural, and verifiable**
operations. Every automated action must be:

- deterministic
- repeatable
- auditable
- independent of semantic interpretation

If an action is not listed here, it is outside the automation scope.

---

## 1. Structural scaffolding automation

tex-repo automates the creation of **structural containers and slots**.

### 1.1 Repository baseline

`tex-repo init <name>` automates:

- creation of the repository root
- creation of the canonical directory layout
- creation of required marker files

This automation is purely structural and does not generate content.

#### Planned: Initialization from text manuscript

**Status: Not yet implemented**

`tex-repo init manuscript.txt` (planned) will:

- Parse a plain text file as a manuscript source
- Extract metadata from initial non-empty lines:
  - Title (first line)
  - Author (second line)
  - Optional free-form metadata (subsequent lines before body)
- Populate `shared/identity.tex` with extracted title and author
- Import remaining content as the initial manuscript body
- Perform all normal structural scaffolding (directories, markers, etc.)

Constraints:
- No LaTeX parsing or semantic interpretation
- Content import occurs only at initialization time
- Structure remains fully editable after import
- No ongoing synchronization with source file

---

### 1.2 Book scaffolding

`tex-repo book "<title>"` automates:

- creation or population of a book container
- creation of the book entry file
- creation of required subdirectories:
  - `parts/frontmatter/`
  - `parts/backmatter/`
  - `parts/parts/`
  - `build/`
- creation of empty or minimal spine files:
  - `build/sections_index.tex`
  - `build/chapters_index.tex`

This automation establishes **where content belongs**, not what content is.

---

### 1.3 Part scaffolding

`tex-repo part "<title>"` automates:

- creation of a new Part directory under a book
- assignment of the next available numeric prefix
- creation of `part.tex` as the Part introduction slot
- creation of an empty `chapters/` directory

This automation defines the **existence and position** of a Part.

---

### 1.4 Chapter scaffolding

`tex-repo chapter "<title>"` automates:

- creation of a new Chapter under a Part
- assignment of the next available numeric prefix
- creation of a dedicated chapter container
- creation of a chapter prologue slot (`chapter.tex`)
- creation of a fixed number of section placeholders
  (e.g. `1-1.tex` … `1-10.tex`)

This automation creates **structural writing slots** only.

---

## 2. Numbering and ordering automation

tex-repo automates all numeric ordering.

### 2.1 Prefix allocation

Automation assigns numeric prefixes (`NN_`) for:

- books (top-level documents)
- parts
- chapters

The numbering process is:

- contiguous
- stable
- derived from the filesystem state

---

### 2.2 Ordering resolution

Automation determines:

- Part order
- Chapter order
- Build order

Ordering is derived solely from numeric prefixes.

---

## 3. Spine generation automation

tex-repo automates the generation of LaTeX spine files.

### 3.1 Frontmatter spine

Automation generates `build/sections_index.tex` as a **navigation spine**.

This spine contains only frontmatter-level navigation constructs
(e.g. table of contents and similar entries).

---

### 3.2 Mainmatter spine

Automation generates `build/chapters_index.tex` as the **content spine**.

This spine reflects:

- Part order
- Chapter order
- inclusion of chapter prologues
- inclusion of chapter section files in sequence

Spine files are fully regenerable and never hand-edited.

---

## 4. Build automation

`tex-repo build` automates the compilation pipeline.

Automation includes:

- discovery of buildable documents
- invocation of LaTeX in non-interactive mode
- deterministic output placement under `build/`
- timeout enforcement
- log capture and surfacing

Build automation never modifies authored source files.

---

## 5. Release automation

`tex-repo release` automates release packaging.

Automation includes:

- verification of existing build artifacts
- creation of immutable release bundles
- deterministic naming (e.g. timestamped directories)
- prevention of overwrites

Release automation packages artifacts only.

---

## 6. Structural repair automation

`tex-repo fix` automates **structural completion**.

Automation includes:

- creation of missing required directories
- creation of missing required empty files
- restoration of required spine files

Repair automation does not alter existing authored content.

---

## 7. Validation automation

tex-repo automates structural validation.

### 7.1 Status inspection

`tex-repo status` automates:

- detection of invariant violations
- reporting of violations in a readable form

---

### 7.2 Guard enforcement

`tex-repo guard` automates:

- strict invariant enforcement
- deterministic violation reporting
- CI-safe exit behavior

Validation automation is declarative and non-mutating.

---

## 8. Automation invariants

All automation in tex-repo satisfies:

- No semantic inference
- No aesthetic judgment
- No content generation
- No hidden state
- No irreversible mutation

Automation exists to maintain structure, not to interpret meaning.

---

## 9. Summary

tex-repo automates:

- structure
- ordering
- containment
- repetition
- verification

tex-repo does not automate:

- authorship
- argumentation
- interpretation
- style decisions beyond initial scaffolding

Automation is finite, explicit, and enumerable.

---

**Principle:**  
Automation replaces repetition, not responsibility.
