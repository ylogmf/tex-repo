# tex-repo: SPEC-First LaTeX Repository Manager

A lightweight CLI that enforces a SPEC-centered structure for research papers. The Spec is the immutable constraint layer; all other work depends on it without modifying it.

## Structure and Semantics
- **SPEC**: Defines primitives, constructors, forbidden constructs, and dependency direction. Exactly one Spec paper lives at `SPEC/spec`.
- **FORMALISM (01_formalism)**: Admissible forms, closures, and representations grounded in the Spec.
- **PROCESSES (02_processes)**: Natural processes expressed through the formalism.
- **APPLICATIONS (03_applications)**: Human-built functions, models, and tools that rely on the Spec via formalism and processes.
- **TESTBEDS (04_testbeds)**: Experiments and validation environments for applications.
- **Context / Legacy**: `98_context/` and `99_legacy/` are allowed but not structural.

### README Policy (strict, non-destructive)
- Required at every level: `SPEC/`, `SPEC/spec/`, each stage directory, every domain, every paper.
- Never overwritten; only created when missing.

### Required Layout
```
my-repo/
├── .paperrepo
├── .texrepo-config
├── SPEC/
│   ├── README.md
│   └── spec/
│       ├── README.md
│       ├── main.tex
│       ├── refs.bib
│       └── sections/
├── 01_formalism/
│   └── README.md
├── 02_processes/
│   └── README.md
├── 03_applications/
│   └── README.md
├── 04_testbeds/
│   └── README.md
├── 98_context/
├── 99_legacy/
└── shared/, scripts/, releases/ ...
```
Papers must live inside numbered domains under stages (e.g., `01_formalism/00_domain/paper/`). The only allowed paper outside a domain is `SPEC/spec`.

## Commands
- `tex-repo init <name|text.txt>`: Create a repository with SPEC/spec, all stages, and required READMEs (existing files are never overwritten). A `.txt` seed populates `SPEC/spec/sections/section_1.tex`.
- `tex-repo status`: Validate structure. Errors when:
  - Required top-level directories missing
  - Stage README missing
  - Domain README missing
  - Paper README missing
  - Paper found directly under a stage (Spec is the only exception at `SPEC/spec`)
- `tex-repo fix [--dry-run]`: Create missing directories/READMEs without overwriting existing content.
- `tex-repo nd <stage_or_parent> <domain-name>`: Create a numbered domain under a stage and seed its README.
- `tex-repo np <domain> <slug> [title]`: Create a paper within a domain and seed its README.
- `tex-repo b [path|all]`: Build a paper (defaults to `SPEC/spec` when run at repo root).
- `tex-repo release <paper>`: Create an immutable release bundle.
- `tex-repo sync-meta`: Regenerate `shared/identity.tex` from `.paperrepo`.
- `tex-repo config`: Create `.texrepo-config` if missing.

## Design Rules
- Spec is unique and immutable.
- Dependency direction: SPEC → FORMALISM → PROCESSES → APPLICATIONS → TESTBEDS.
- Papers never sit directly under stages (only inside domains); Spec is the single exception.
- Commands are conservative: no overwrites, no deletions.

## Quick Start
```bash
tex-repo init my-spec-repo
cd my-spec-repo
tex-repo nd 01_formalism admissible-forms
tex-repo np 01_formalism/00_admissible-forms first-paper "Admissible Forms"
tex-repo status
```

## Status and Fix Expectations
- `status` fails when any required README is missing or when a paper is misplaced.
- `fix` adds missing directories and READMEs while leaving all existing content untouched.

## Metadata & Build Notes
- Repository metadata lives in `.paperrepo`; `sync-meta` regenerates `shared/identity.tex`.
- Paper templates honor `.texrepo-config` for section counts, document class, and options.
- Shared LaTeX inputs live under `shared/` and are referenced relative to each paper.
