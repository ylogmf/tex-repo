# tex-repo: World-First LaTeX Repository Manager

A lightweight CLI that enforces a world-first, layered structure for research papers. The world layer (foundation + spec) is immutable; everything else depends on it without modifying it.

## Installation

For developers and contributors, install in editable mode:

```bash
cd tex-repo  # Navigate to this repository
pip install -e .
```

After installation, the `tex-repo` command will be available system-wide:

```bash
tex-repo init my-project
cd my-project
tex-repo status
```

Alternatively, you can use the module directly:
```bash
python -m texrepo <command>
```

## Structure and Semantics (world-first)
- **World (00_world)**: Immutable `00_foundation` (definitions and axioms) plus the core `01_spec` paper.
- **Formalism (01_formalism)**: Admissible forms grounded in the world layer. Papers live under `01_formalism/papers/`.
- **Process Regime (02_process_regime)**: Split into `process/` and `regime/`, each with its own `papers/` directory.
- **Function Application (03_function_application)**: Split into `function/` and `application/`, each with its own `papers/` directory.
- **Releases**: Immutable bundles collected in `releases/`.
- **Support**: `shared/`, `scripts/`, `98_context/`, and `99_legacy/` are allowed but not structural.

### README Policy (strict, non-destructive)
- Required at every level: `00_world/`, each world paper, every stage, every branch, every paper.
- Never overwritten; only created when missing.

### Required Layout
```
my-repo/
├── .paperrepo
├── .texrepo-config
├── 00_world/
│   ├── 00_foundation/
│   │   ├── README.md
│   │   ├── 00_foundation.tex
│   │   └── sections/
│   │       ├── 00_definitions.tex
│   │       └── 01_axioms.tex
│   └── 01_spec/
│       ├── README.md
│       ├── 01_spec.tex
│       ├── refs.bib
│       └── sections/
├── 01_formalism/
│   ├── README.md
│   └── papers/
│       └── 00_<topic>/
│           └── 00_<topic>.tex
├── 02_process_regime/
│   ├── README.md
│   ├── process/
│   │   └── papers/
│   │       └── 00_<subject>/
│   │           └── 00_<subject>.tex
│   └── regime/
│       └── papers/
│           └── 00_<subject>/
│               └── 00_<subject>.tex
├── 03_function_application/
│   ├── README.md
│   ├── function/
│   │   └── papers/
│   │       └── 00_<subject>/
│   │           └── 00_<subject>.tex
│   └── application/
│       └── papers/
│           └── 00_<subject>/
│               └── 00_<subject>.tex
└── releases/
```
Every paper's entry file matches the folder name (no `main.tex`).

## Commands
- `tex-repo init <name|text.txt>`: Create a repository with world foundation/spec, all stages/branches, and required READMEs (existing files are never overwritten). A `.txt` seed populates `00_world/01_spec/sections/section_1.tex`.
- `tex-repo status`: Validate structure. Errors when:
  - Required top-level directories missing
  - Stage or branch README missing
  - Paper README missing
  - Paper found outside the allowed `papers/` locations
  - Entry file missing (expects `<folder>.tex`, legacy `main.tex` only tolerated for older papers)
- `tex-repo fix [--dry-run]`: Create missing directories/READMEs without overwriting existing content.
- `tex-repo nd <layer_or_parent> <name>`: Create a numbered folder under the correct `papers/` root. Examples:
  - `tex-repo nd 01_formalism flows` -> `01_formalism/papers/00_flows`
  - `tex-repo nd 02_process_regime/process regimes` -> `02_process_regime/process/papers/00_regimes`
- `tex-repo np <path> [title]`: Create a paper at the requested path, auto-inserting `papers/` when omitted. Examples:
  - `tex-repo np 00_world/00_foundation`
  - `tex-repo np 01_formalism/00_logic "Logic Paper"`
  - `tex-repo np 02_process_regime/process/00_flows`
  - `tex-repo np 03_function_application/application/00_models`
- `tex-repo b [path|all]`: Build a paper (defaults to `00_world/01_spec` when run at repo root). On failure, tex-repo summarizes the primary LaTeX error and prints concise suggestions instead of dumping full logs (use `--verbose` for more output).
- `tex-repo release <paper>`: Create an immutable release bundle.
- `tex-repo sync-meta`: Regenerate `shared/identity.tex` from `.paperrepo`.
- `tex-repo config`: Create `.texrepo-config` if missing.

## Design Rules
- World papers anchor everything else.
- Dependency direction: world → formalism → process/regime → function/application.
- Papers stay inside their `papers/` roots; process/regime and function/application splits are enforced.
- Entry file names mirror their folders (no new `main.tex`).
- Commands are conservative: no overwrites, no deletions.

## Quick Start
```bash
tex-repo init my-spec-repo
cd my-spec-repo
tex-repo nd 01_formalism admissible-forms
tex-repo np 01_formalism/00_admissible-forms "Admissible Forms"
tex-repo status
```

## Status and Fix Expectations
- `status` fails when any required README is missing or when a paper is misplaced.
- `fix` adds missing directories and READMEs while leaving all existing content untouched.

## Metadata & Build Notes
- Repository metadata lives in `.paperrepo`; `sync-meta` regenerates `shared/identity.tex`.
- Paper templates honor `.texrepo-config` for section counts, document class, and options.
- Shared LaTeX inputs live under `shared/` and are referenced relative to each paper.
