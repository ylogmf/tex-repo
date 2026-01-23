# Automation → Command Responsibility Map

This section maps each allowed automation item to the exact command
responsible for implementing it.

Automation is considered correct only if it is implemented by the
designated command listed below.

---

## 1. Repository baseline automation

### Implemented by: `tex-repo init`

The following automation items are the responsibility of `init`:

- Create repository root directory
- Create `.paperrepo` marker file
- Create canonical top-level structure:
  - `shared/`
  - `00_introduction/`
  - `01_process_regime/`
  - `02_function_application/`
  - `03_hypophysis/`
  - `releases/`
- Create `.gitignore` with build artifacts ignored and `releases/` tracked
- Create baseline files under `shared/`:
  - `preamble.tex`
  - `packages.tex`
  - `macros.tex`
  - `notation.tex`
  - `identity.tex`

No other command may create or modify the repository baseline.

---

## 2. Book scaffolding automation

### Implemented by: `tex-repo book "<title>"`

The following automation items are the responsibility of `book`:

- Create or populate a book container
- Resolve whether the target is:
  - the fixed `00_introduction/` book (when title is `"Introduction"`), or
  - a new top-level numbered book directory
- Create the book entry file (`<book_dir>/<book_dir>.tex` or `00_introduction.tex`)
- Create required book subdirectories:
  - `parts/frontmatter/`
  - `parts/backmatter/`
  - `parts/parts/`
  - `build/`
- Create minimal spine files:
  - `build/sections_index.tex`
  - `build/chapters_index.tex`
- Wire the book entry file to:
  - shared preamble
  - frontmatter spine
  - mainmatter spine

Book automation establishes **book existence and structure**, not book content.

---

## 3. Part scaffolding automation

### Implemented by: `tex-repo part "<title>"`

The following automation items are the responsibility of `part`:

- Verify the current working directory is inside a book container
- Determine the next available numeric prefix for Parts
- Create a new Part directory under:
  - `parts/parts/NN_<part_slug>/`
- Create:
  - `part.tex` (Part introduction slot)
  - `chapters/` directory
- Ensure Part numbering is contiguous within the book

No other command may create Part directories or `part.tex`.

---

## 4. Chapter scaffolding automation

### Implemented by: `tex-repo chapter "<title>"`

The following automation items are the responsibility of `chapter`:

- Verify the current working directory is inside a Part directory
- Determine the next available numeric prefix for Chapters
- Create a Chapter container under:
  - `chapters/NN_<chapter_slug>/`
- Create required files:
  - `chapter.tex` (Chapter prologue slot)
  - `1-1.tex` … `1-10.tex` (section placeholders)
- Ensure Chapter numbering is contiguous within the Part

Chapter automation creates **writing slots**, not written content.

---

## 5. Numbering and ordering automation

### Implemented by:
- `book`
- `part`
- `chapter`

The following automation items are shared responsibilities:

- Scan filesystem state to determine existing numeric prefixes
- Assign the next contiguous prefix
- Preserve ordering stability across runs
- Never renumber existing items

No command may allow manual numeric prefix assignment.

---

## 6. Spine generation automation

### Implemented by: `tex-repo build`

The following automation items are the responsibility of `build`:

- Generate `build/sections_index.tex` as the frontmatter navigation spine
- Generate `build/chapters_index.tex` as the mainmatter content spine
- Determine inclusion order from numeric prefixes:
  - Part order
  - Chapter order
  - Section file order
- Include `part.tex` and `chapter.tex` before section files
- Enforce frontmatter/mainmatter separation during generation

Spine files are fully regenerable and must not be hand-edited.

---

## 7. Build pipeline automation

### Implemented by: `tex-repo build`

The following automation items are the responsibility of `build`:

- Discover buildable documents
- Invoke LaTeX in non-interactive mode
- Enforce build timeouts
- Capture logs under `build/`
- Write all build outputs under `build/`

Build automation must not modify authored source files.

---

## 8. Release automation

### Implemented by: `tex-repo release`

The following automation items are the responsibility of `release`:

- Verify the existence of built PDF artifacts
- Create immutable release bundles under `releases/`
- Apply deterministic naming (e.g. timestamp-based)
- Prevent overwriting of existing release bundles

Release automation packages artifacts only.

---

## 9. Structural repair automation

### Implemented by: `tex-repo fix`

The following automation items are the responsibility of `fix`:

- Create missing required directories
- Create missing required empty files
- Restore missing spine files
- Restore missing shared files

Repair automation restores **structure only** and does not alter existing content.

---

## 10. Validation automation

### Implemented by:
- `tex-repo status`
- `tex-repo guard`

The following automation items are shared responsibilities:

- Detect invariant violations
- Report violations with stable codes
- Provide deterministic output ordering

Additional responsibilities:

- `status` reports without failing
- `guard` enforces invariants and exits non-zero on violations

---

## 11. Automation ownership principle

Each automation item belongs to exactly one command.

If an automation behavior does not map to a command listed here,
it is outside the automation scope of tex-repo.

---

**Principle:**  
Automation is assigned, not inferred.
