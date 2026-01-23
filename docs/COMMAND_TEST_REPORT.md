# tex-repo Integration Test Report

## Scope

This report validates the **current, invariant-driven implementation** of `tex-repo`.

It verifies that the repository manager enforces declared structural invariants,
respects command boundaries, and produces deterministic build and release artifacts.

This report does **not** cover legacy behavior.

---

## Test Suite Overview

- **Test type**: End-to-end integration tests
- **Focus**: CLI behavior + filesystem invariants
- **Oracle**: README invariants and guard violation codes
- **Execution**: Local, deterministic, no network dependency

Legacy tests are explicitly excluded.

---

## Tested command surface

The following commands define the **current tex-repo contract** and are covered:

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

The following commands and behaviors are **not supported** and are not tested:

- Legacy commands: `ns`, `nd`, `np`, `npart`
- Layout switching (`old` / `new`)
- Automatic README scaffolding
- Implicit branch inference
- Legacy directories (`scripts/`, `98_context/`, `99_legacy/`)
- Source mutation during `build`
- Metadata regeneration commands (`sync-meta`, `config`, `install`, `env`)

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

Integration tests enforce the invariants defined in the README:

- Naming invariant checklist
- Book invariants
- Paper invariants
- Build → Release invariants
- Guard violation codes (book + paper)

Any violation constitutes a test failure.

---

## Integration test matrix

### A) Repository initialization (`init`)

**Validated behavior**

- Creates a new repository directory
- Writes `.paperrepo`
- Creates fixed stage directories and `shared/`
- Refuses to initialize into an existing directory

---

### B) Structure validation (`status`)

**Validated behavior**

- Passes on a structurally valid repository
- Reports all detected violations
- Does not modify filesystem state

---

### C) Enforcement gate (`guard`)

**Validated behavior**

- Emits violations as:
```sh
<CODE>\t<PATH>\t<MESSAGE>
```

- Exits non-zero on any violation
- Reports all violations in a single run

---

### D) Repair (`fix`)

**Validated behavior**

- Creates missing required directories and files
- Never deletes or overwrites user-authored content
- Safe to run repeatedly

---

### E) Book creation (`book`)

**Validated behavior**

- Creates a book-class document at repository root
- Produces `00_introduction/` when title is “Introduction”
- Initializes entry file, parts, frontmatter, backmatter, and build directories

---

### F) Part creation (`part`)

**Validated behavior**

- Must be run inside a book directory
- Creates:

```sh
chapters/NN_<slug>.tex
```

- Assigns contiguous numbering

---

### H) Paper creation (`paper`)

**Validated behavior**

- Creates a paper-scale document at repository root
- Initializes entry file, sections, refs, and build directories
- Refuses placement under `00_introduction`

---

### I) Build (`build`)

**Validated behavior**

- Builds a single target or all documents
- Writes output exclusively to `build/`
- Does not modify authored source files

---

### J) Release (`release`)

**Validated behavior**

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

All tested commands operate within strict, well-defined boundaries.
Violations are detected deterministically and reported with stable codes.

`tex-repo` is a structural authority, not a content generator.

---

## Legacy reference

Historical behavior and legacy command coverage are preserved separately in:

- Assigns contiguous numbering

---

### H) Paper creation (`paper`)

**Validated behavior**

- Creates a paper-scale document at repository root
- Initializes entry file, sections, refs, and build directories
- Refuses placement under `00_introduction`

---

### I) Build (`build`)

**Validated behavior**

- Builds a single target or all documents
- Writes output exclusively to `build/`
- Does not modify authored source files

---

### J) Release (`release`)

**Validated behavior**

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

All tested commands operate within strict, well-defined boundaries.
Violations are detected deterministically and reported with stable codes.

`tex-repo` is a structural authority, not a content generator.

---

## Legacy reference

Historical behavior and legacy command coverage are preserved separately in:

```sh
tex-repo-back/
```


They do not define current behavior.
