# tex-repo Integration Test Report

## Scope

This document validates the **invariant-based implementation** of `tex-repo`.

It verifies that the repository manager enforces structural rules,
respects command boundaries, and produces deterministic build and release artifacts.

Legacy behavior is explicitly excluded.

---

## Tested command surface

The following commands are part of the **current tex-repo contract**
and are covered by integration tests:

### Repository lifecycle
- `tex-repo init`
- `tex-repo status`
- `tex-repo guard`
- `tex-repo fix`

### Authoring
- `tex-repo book`
- `tex-repo paper`
- `tex-repo part`
- `tex-repo chapter`

### Build and release
- `tex-repo build`
- `tex-repo release`

---

## Explicitly excluded behavior

The following behaviors are **not supported** and are not tested:

- Legacy commands: `ns`, `nd`, `np`, `npart`
- Layout switching (`old` / `new`)
- Automatic README scaffolding
- Implicit branch inference
- Legacy directories (`scripts/`, `98_context/`, `99_legacy/`)
- Source mutation during `build`

---

## Repository baseline

All tests assume the canonical repository layout:

```sh
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


The presence of `.paperrepo` is the sole repository identifier.

---

## Invariants under test

Integration tests enforce the invariants defined in:

- Naming invariant checklist
- Book invariants
- Paper invariants
- Build → Release invariants
- Guard violation codes

Any violation constitutes a test failure.

---

## Integration test matrix

### A) Repository initialization (`init`)

**Expected behavior**

- Creates a new repository directory
- Writes `.paperrepo`
- Creates fixed stage directories and `shared/`
- Refuses to initialize into an existing directory

**Validated invariants**

- Stage directory invariants
- No overwrite on failure
- No extraneous directories created

---

### B) Structure validation (`status`)

**Expected behavior**

- Passes on a structurally valid repository
- Reports all detected violations
- Does not modify filesystem state

---

### C) Enforcement gate (`guard`)

**Expected behavior**

- Emits one line per violation:

```sh
<CODE>\t<PATH>\t<MESSAGE>
```

- Exits non-zero on any violation
- Reports all violations in a single run

---

### D) Repair (`fix`)

**Expected behavior**

- Creates missing required directories and files
- Never deletes or overwrites user-authored content
- Safe to run repeatedly

---

### E) Book creation (`book`)

**Expected behavior**

- Creates a book-class document at repository root
- Produces `00_introduction/` when title is “Introduction”
- Initializes entry file, parts, frontmatter, backmatter, and build directories

---

### F) Part creation (`part`)

**Expected behavior**

- Must be run inside a book directory
- Creates:

```sh
parts/parts/NN_<slug>/
├── part.tex
└── chapters/
```

- Assigns contiguous numbering

---

### G) Chapter creation (`chapter`)

**Expected behavior**

- Must be run inside a part directory
- Creates:

```sh
chapters/NN_<slug>.tex
```

- Assigns contiguous numbering

---

### H) Paper creation (`paper`)

**Expected behavior**

- Creates a paper-scale document
- Initializes entry file, sections, refs, and build directories
- Refuses placement under `00_introduction`

---

### I) Build (`build`)

**Expected behavior**

- Builds a single target or all documents
- Writes output exclusively to `build/`
- Does not modify authored source files

---

### J) Release (`release`)

**Expected behavior**

- Requires an existing successful build
- Creates an immutable bundle under `releases/`
- Never triggers a build implicitly

---

## Determinism guarantees

All integration tests assert that:

- Results depend only on filesystem state
- No network access is required
- No background mutation occurs
- Re-running tests yields identical outcomes

---

## Conclusion

This report confirms that `tex-repo` enforces its declared structural invariants.

All tested commands operate within defined boundaries.
Violations are detected deterministically and reported with stable codes.

`tex-repo` is a structural authority, not a content generator.

---

## Legacy reference

Historical behavior and legacy test coverage are preserved separately in:

```sh
tex-repo-back/
```


They do not define current behavior.

## Integration test structure contract

The integration test suite mirrors the Integration Test Report (A–J).
Test file names, class names, and primary test case names are part of the contract.

### File layout

All integration tests live under:


```sh
tests/integration/
```


Each report section maps to exactly one test module:

| Report section | Module | Primary class |
|---|---|---|
| A) init | `tests/integration/test_A_init.py` | `TestAInit` |
| B) status | `tests/integration/test_B_status.py` | `TestBStatus` |
| C) guard | `tests/integration/test_C_guard.py` | `TestCGuard` |
| D) fix | `tests/integration/test_D_fix.py` | `TestDFix` |
| E) book | `tests/integration/test_E_book.py` | `TestEBook` |
| F) part | `tests/integration/test_F_part.py` | `TestFPart` |
| G) chapter | `tests/integration/test_G_chapter.py` | `TestGChapter` |
| H) paper | `tests/integration/test_H_paper.py` | `TestHPaper` |
| I) build | `tests/integration/test_I_build.py` | `TestIBuild` |
| J) release | `tests/integration/test_J_release.py` | `TestJRelease` |

No other files in `tests/integration/` are permitted.

---

### Class naming rules

- Each module contains exactly one primary class named `Test<Letter><Topic>`.
- The primary class may contain nested logical groupings using comments, not additional classes.
- Shared fixtures and helpers must live in:
  - `tests/conftest.py` (global fixtures)
  - `tests/integration/conftest.py` (integration-only fixtures)

---

### Test case naming rules

Each primary class must contain at least the following canonical test functions.
These names are stable and must not be changed.

#### A) init (`TestAInit`)
- `test_init_creates_repo_baseline`
- `test_init_refuses_existing_directory`
- `test_init_is_idempotent_failure_no_partial_writes`

#### B) status (`TestBStatus`)
- `test_status_passes_on_valid_repo`
- `test_status_reports_missing_required_paths`
- `test_status_does_not_modify_repo`

#### C) guard (`TestCGuard`)
- `test_guard_exits_zero_on_valid_repo`
- `test_guard_exits_nonzero_on_violation`
- `test_guard_emits_tab_separated_violations`
- `test_guard_reports_all_violations_in_one_run`

#### D) fix (`TestDFix`)
- `test_fix_creates_missing_required_structure`
- `test_fix_never_overwrites_authored_content`
- `test_fix_is_safe_to_rerun`

#### E) book (`TestEBook`)
- `test_book_creates_introduction_book`
- `test_book_enforces_repo_root`
- `test_book_initializes_required_subtrees`

#### F) part (`TestFPart`)
- `test_part_requires_book_directory`
- `test_part_creates_numbered_part_dir`
- `test_part_numbering_is_contiguous`

#### G) chapter (`TestGChapter`)
- `test_chapter_requires_part_directory`
- `test_chapter_creates_numbered_chapter`
- `test_chapter_numbering_is_contiguous`

#### H) paper (`TestHPaper`)
- `test_paper_creates_paper_at_repo_root`
- `test_paper_enforces_repo_root`
- `test_paper_refuses_under_introduction`

#### I) build (`TestIBuild`)
- `test_build_single_target_writes_only_build_dir`
- `test_build_all_discovers_all_documents`
- `test_build_does_not_modify_authored_sources`

#### J) release (`TestJRelease`)
- `test_release_requires_successful_build`
- `test_release_creates_immutable_bundle`
- `test_release_never_triggers_build`

---

### Fixture contract

Integration tests use the following fixtures (stable names):

- `repo_root`  
  Creates a minimal repository via `tex-repo init`.

- `repo_with_book`  
  A repo_root with `tex-repo book "Introduction"` created.

- `repo_with_paper`  
  A repo_root with `tex-repo paper "<title>"` created.

- `repo_built_book`  
  A repo_with_book with `tex-repo build 00_introduction` completed.

- `repo_built_paper`  
  A repo_with_paper with build completed.

Fixtures must use `sys.executable -m texrepo` rather than relying on PATH entrypoints.

---

### Enforcement

- Changes to module names, class names, or canonical test names are breaking changes.
- New tests may be added, but only as additional `test_*` functions inside the mapped class.
- No test is permitted to depend on legacy commands or legacy directory layouts.

---

### Recommended invocation

Run integration tests:

```sh
python -m pytest tests/integration -q
```

Run full suite:

python -m pytest -q


---

