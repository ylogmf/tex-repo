# tex-repo: LaTeX Theory Repository Manager

A powerful tool for organizing mathematical theories and research papers using a structured, staged development approach. Think Git for mathematical research organization.

## 🌟 Overview

tex-repo helps mathematicians and researchers organize their work into structured repositories with:

- **Staged Development**: Core → Derivations → Interpretations → Applications → Testbeds
- **Metadata Integration**: Automatic author info, affiliations, and bibliography management
- **Smart Building**: Incremental compilation with dependency tracking
- **Consistent Structure**: Enforced organization with flexibility

## Design Principles

`tex-repo` is intentionally minimal. Its design prioritizes structural correctness,
long-term clarity, and low cognitive overhead over convenience features.

The following principles guide all design decisions.

### 1. Immutable Core

The core paper (`00_core/core`) is unique and immutable by design.

- There is exactly one core paper per repository.
- No domains or additional papers may exist under `00_core`.
- The core defines foundational assumptions and constraints.
- All other work must build *from* the core, never around it.

This prevents foundational drift and enforces a clear epistemic base.

---

### 2. Irreversible Staged Pipeline

The repository is organized as an ordered, irreversible pipeline:

    00_core → 01_derivations → 02_interpretations → 03_applications → 04_testbeds

Each stage has a distinct role:

- **Derivations** formalize consequences of the core.
- **Interpretations** assign meaning to derivations.
- **Applications** use stabilized interpretations.
- **Testbeds** validate applications experimentally or numerically.

Work may depend on earlier stages, but never bypass or reorder them.

---

### 3. Explicit Structure over Implicit Convention

`tex-repo` avoids hidden defaults and implicit assumptions.

- Domains must be explicitly placed under a parent stage.
- Numbered domains enforce local ordering and readability.
- Papers must live inside domains, never directly under stages.

This favors predictability and prevents accidental structural errors.

---

### 4. Status as Structural Firewall

The `tex-repo status` command acts as a structural validator, not a linter.

- Structural violations are errors.
- Missing or placeholder metadata is reported as warnings.
- A repository can be *incomplete* but still structurally valid.

This allows uninterrupted work while preserving long-term correctness.

---

### 5. Metadata Defined Once, Consumed Everywhere

Author and project metadata live in `.paperrepo` and are compiled into
`shared/identity.tex`.

- Metadata is written once.
- All papers inherit it automatically.
- Changing metadata never requires editing individual papers.

This minimizes repetition and prevents divergence.

---

### 6. Tooling Should Never Interrupt Thinking

The tool is designed to stay out of the way:

- Initialization never blocks on missing information.
- Reasonable defaults are provided where possible.
- Warnings inform without stopping progress.

If the tool interrupts thinking, the design is considered flawed.

---

### 7. Simplicity over Automation

Advanced automation (environment setup, installers, CI integration) is
intentionally deferred.

The current system favors:
- Transparency
- Manual control
- Easy inspection and modification

Automation can be added later, but complexity is difficult to remove.

---

These principles are not implementation details.
They define the expected behavior of the repository over time.


## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tex-repo.git
cd tex-repo

# Make executable and add to PATH
chmod +x tex-repo
ln -s $(pwd)/tex-repo /usr/local/bin/tex-repo

# Or add to your shell profile
echo 'export PATH="$PATH:'$(pwd)'"' >> ~/.bashrc  # or ~/.zshrc
```

## 🚀 Quick Start

### 1. Initialize a New Repository

```bash
tex-repo init my-theory
# or bootstrap from a plain text file (repo name defaults to filename)
tex-repo init notes/rough-plan.txt
# or specify both
tex-repo init my-theory notes/rough-plan.txt
```

This will:
- Create the staged directory structure (00_core through 04_testbeds)
- Prompt for metadata (author, organization, etc.)
- Generate shared LaTeX resources with identity integration
- Create the core paper template
- Seed `00_core/core/sections/section_1.tex` with the contents of the provided `.txt` file (escaped for LaTeX)
- Refuse to run inside an existing directory to avoid overwriting files

### 2. Create Your First Paper

```bash
cd my-theory
tex-repo np 01_derivations fundamental-lemma "Fundamental Lemma on Spaces"
```

### 3. Build Papers

```bash
# Build current paper (if in paper directory)
tex-repo b

# Build specific paper
tex-repo b 01_derivations/fundamental-lemma

# Build all papers in correct order
tex-repo b all

# Force rebuild (ignore cache)
tex-repo b --force

# Use different engine
tex-repo b --engine pdflatex
```

## 📁 Repository Structure

```
my-theory/
├── .paperrepo              # Repository metadata
├── .texrepo-config         # Configuration (optional)
├── scripts/                # Project-level helper scripts
├── shared/                 # Shared LaTeX resources
│   ├── preamble.tex        # Common packages and settings
│   ├── macros.tex          # Custom LaTeX macros
│   ├── notation.tex        # Mathematical notation
│   └── identity.tex        # Auto-generated author/metadata
├── 00_core/               # Core theory
│   └── core/              # Main theory paper
├── 01_derivations/        # Theoretical derivations
├── 02_interpretations/    # Theory interpretations
├── 03_applications/       # Practical applications
├── 04_testbeds/          # Experimental validation
├── 98_context/           # User-managed context and references
└── 99_legacy/            # Archived or deprecated content
```

## 🔧 Commands Reference

### Repository Management

| Command | Description | Example |
|---------|-------------|---------|
| `tex-repo init <name>` | Initialize new repository | `tex-repo init quantum-theory` |
| `tex-repo init <text.txt>` | Initialize from plain text (repo name defaults to the filename) | `tex-repo init notes/outline.txt` |
| `tex-repo init <name> <text.txt>` | Initialize named repository seeded from a text file | `tex-repo init quantum-theory notes/outline.txt` |
| `tex-repo status` | Check repository compliance | `tex-repo status` |
| `tex-repo fix` | Repair missing repository structure | `tex-repo fix` |
| `tex-repo fix --dry-run` | Show what would be repaired | `tex-repo fix --dry-run` |
| `tex-repo sync-meta` | Regenerate identity.tex | `tex-repo sync-meta` |

### Domain Management

| Command | Description | Example |
|---------|-------------|---------|
| `tex-repo nd <parent> <name>` | Create numbered domain | `tex-repo nd 01_derivations algebra` |

### Paper Management

| Command | Description | Example |
|---------|-------------|---------|
| `tex-repo np <domain> <slug> [title]` | Create new paper | `tex-repo np 01_derivations lemma1 "Key Lemma"` |
| `tex-repo np <domain>/<slug> [title]` | Alternative syntax | `tex-repo np 01_derivations/lemma1 "Key Lemma"` |

### Building

| Command | Description | Example |
|---------|-------------|---------|
| `tex-repo b` | Build current paper | `tex-repo b` |
| `tex-repo b <paper>` | Build specific paper | `tex-repo b 01_derivations/lemma1` |
| `tex-repo b all` | Build all papers in order | `tex-repo b all` |
| `tex-repo b --clean` | Clean build before compiling | `tex-repo b --clean` |
| `tex-repo b --force` | Force rebuild (ignore cache) | `tex-repo b --force` |
| `tex-repo b --engine pdflatex` | Use pdflatex instead of latexmk | `tex-repo b --engine pdflatex` |

### Releases

| Command | Description | Example |
|---------|-------------|---------|
| `tex-repo release <paper>` | Create release bundle with timestamp | `tex-repo release 00_core/core` |
| `tex-repo release <paper> --label <name>` | Create labeled release bundle | `tex-repo release 01_derivations/lemma1 --label submitted` |
| `tex-repo release <paper> --engine pdflatex` | Use specific build engine | `tex-repo release 00_core/core --engine pdflatex` |

## ⚙️ Configuration

Create a `.texrepo-config` file in your repository root to customize behavior:

```ini
[paper]
section_count = 15          # Number of sections to create
document_class = article    # LaTeX document class
document_options = 12pt     # Document class options
include_abstract = true     # Include abstract section

[build]
default_engine = latexmk    # Default build engine
parallel_builds = true     # Enable parallel building (future)
```

## 📝 Metadata System

The metadata system automatically manages author information, affiliations, and document settings:

### Interactive Setup
During `tex-repo init`, you'll be prompted for:
- Project name
- Author name and email  
- Organization and affiliations
- License information
- Date policy (today vs fixed)
- Bibliography style preferences

### Available Macros
In your LaTeX documents, use these auto-generated macros:
- `\RepoProjectName` - Project name
- `\RepoAuthorName` - Author name
- `\RepoAuthorEmail` - Author email
- `\RepoOrganization` - Organization
- `\RepoAuthorAffil` - Full affiliation
- `\RepoShortAffil` - Short affiliation
- `\RepoORCID` - ORCID identifier
- `\RepoLicense` - License information

### Manual Updates
Edit `.paperrepo` directly and run `tex-repo sync-meta` to regenerate `shared/identity.tex`.

## 🔄 Build System Features

### Smart Caching
tex-repo only rebuilds papers when necessary:
- Source files (.tex) have changed
- Bibliography (refs.bib) has changed
- Shared resources have changed
- Output PDF doesn't exist

### Build Engines
- **latexmk**: Automatically reruns LaTeX until references and citations stabilize
- **pdflatex**: Runs twice in sequence to resolve references and citations

### Build All Papers
Papers are built in logical order:
1. `00_core` - Core theory
2. `01_derivations` - Mathematical derivations  
3. `02_interpretations` - Theory interpretations
4. `03_applications` - Practical applications
5. `04_testbeds` - Experimental validation

Within each stage, numbered domains (00_, 01_, etc.) are built in order.

## 📦 Release System

The release system creates immutable bundles for paper publication and archival, ensuring reproducibility by snapshotting built PDFs with all source dependencies. Releases are stored at the repository level with paper-aware naming and comprehensive tracking.

### Creating Releases

```bash
# Create timestamped release
tex-repo release 00_core/core

# Create labeled release
tex-repo release 01_derivations/lemma1 --label submitted

# Different engines supported
tex-repo release 00_core/core --engine pdflatex --label camera-ready
```

### Release Storage

Releases are stored in the repository-level `releases/` directory:

```
repo_root/
├── releases/
│   ├── index.jsonl                                    # Audit log of all releases
│   ├── 20260112-143022__quantum_field_theory/         # Timestamped release
│   ├── 20260112-143155__submitted__quantum_field_theory/  # Labeled release
│   └── ...
```

### Release Bundle Contents

Each release bundle contains:

- **`main.pdf`** - The compiled paper
- **`sources/`** - Complete source snapshot:
  - `paper/` - Paper files (main.tex, refs.bib, sections/)
  - `shared/` - Shared dependencies (preamble.tex, macros.tex, etc.)
  - `repo.paperrepo` - Repository metadata
- **`MANIFEST.json`** - Structured file inventory with sizes and hashes
- **`SHA256SUMS`** - Plain text checksums for verification
- **`RELEASE.txt`** - Release metadata and build information

### Release Naming

Release directories use paper-aware naming:
- **Release ID**: `YYYYMMDD-HHMMSS` or `YYYYMMDD-HHMMSS__<label>`
- **Release Title**: Automatically extracted from LaTeX `\title{...}` and normalized
- **Directory Name**: `<release_id>__<release_title>`

Example: A paper titled "Quantum Field Theory Applications" becomes `quantum_field_theory_applications`

### Release Tracking

All releases are tracked in `releases/index.jsonl` (JSON Lines format):
- Append-only audit log
- Each release gets one line with complete metadata
- Includes paper path, timestamps, hashes, and build information
- Enables programmatic analysis and verification

### Release Immutability

Releases are immutable by convention:
- Each release gets a unique directory name with timestamp
- Existing release directories cannot be overwritten
- Source modifications require creating a new release
- Checksums enable verification of bundle integrity
- Index updates are atomic - failed releases are cleaned up

## 📊 Status Checking

Use `tex-repo status` to check repository health and structural compliance:

```bash
tex-repo status
```

### What Status Checks

**Structural Compliance** (Errors):
- ✅ Required stages present (00_core through 04_testbeds)
- ✅ Core paper exists and is properly placed
- ✅ Domains follow numbering conventions (00_, 01_, etc.)
- ✅ Papers are inside domains, not directly under stages

**Metadata Warnings** (Non-blocking):
- ⚠️ Author name or organization missing/placeholder
- ⚠️ Missing identity.tex file

**Ignored Items** (Silently allowed):
- Files matched by `.gitignore` patterns
- OS artifacts (`.DS_Store`, `Thumbs.db`)
- Reserved folders (`98_context/`, `99_legacy/`)

### Reserved Folders

tex-repo recognizes special top-level folders that are **allowed but non-structural**:

- **`98_context/`**: User-managed context and reference materials
- **`99_legacy/`**: Deprecated or archived content

These folders:
- ✅ **Allowed** at repository root
- ℹ️ **Ignored** by structural validation
- 🔓 **Unrestricted** - can contain any user content
- 📁 **Optional** - not required to exist

### Gitignore Integration

Status checking respects `.gitignore` patterns:
- Ignored files **don't trigger** "unexpected item" warnings
- Common patterns automatically ignored (`.DS_Store`, build artifacts)
- Custom patterns from your `.gitignore` are honored

### Version Control Policy

- Only `releases/` (and its contents) are intended for long-term version control.
- All intermediate LaTeX build outputs (`**/build/` and temp files) are ephemeral and should never be committed.

### Status Output

Example output with summary:
```
📂 Repository: /path/to/repo

🔍 Checking top-level stages...
  ✅ 00_core
  ✅ 01_derivations
  ℹ️ ignored 3 items

Status summary:
  errors: 0
  warnings: 1
  ignored: 3

✅ Repository structure is fully compliant!
```

Status severity levels:
- **Errors**: Structural violations that break tex-repo conventions
- **Warnings**: Missing metadata that should be filled in
- **Ignored**: Files/folders silently skipped (not problems)

## 🔧 Repository Repair

The `tex-repo fix` command repairs incomplete repository structure by creating missing files and folders. It follows a strict conservative policy to build user trust.

### Conservative Policy

`tex-repo fix` **NEVER**:
- Overwrites existing files
- Modifies file contents  
- Renames or deletes anything

If a file exists but differs from defaults, it's treated as intentional and left untouched.

### What Can Be Repaired

`tex-repo fix` creates missing structure elements:

**Folders:**
- Stage directories (00_core, 01_derivations, etc.)
- Support directories (shared, scripts, 98_context, 99_legacy)

**Configuration Files:**
- `.paperrepo` (minimal placeholder)
- `.gitignore` (standard LaTeX ignore rules)
- `.texrepo-config` (default settings)

**Shared LaTeX Files:**
- `shared/preamble.tex`, `shared/macros.tex`, `shared/notation.tex`
- `shared/identity.tex` (generated from .paperrepo if available)

**Core Paper Skeleton:**
- `00_core/core/` directory structure
- `main.tex`, `refs.bib`, section files, build directory

### Dry-Run Mode

Use `--dry-run` to preview changes without making them:

```bash
# See what would be created
tex-repo fix --dry-run

# Example output:
➕ would create: shared/macros.tex  
ℹ️ exists: .paperrepo (already present)
⚠️ cannot create: scripts/ - permission denied

Fix summary:
  would be created: 3
  skipped: 8
  warnings: 1
```

### Usage Examples

```bash
# Repair repository structure
tex-repo fix

# Preview changes first  
tex-repo fix --dry-run

# Use after partial repository corruption or incomplete setup
```

## 🎯 Best Practices

### Repository Organization
1. **Start with core theory** in `00_core/core`
2. **Build incrementally** through the stages
3. **Use descriptive paper names** (slug format: lowercase, hyphens)
4. **Maintain bibliography** in each paper's `refs.bib`

### Paper Development
1. **Use the abstract** (section_0.tex) effectively
2. **Leverage shared macros** for consistency
3. **Reference other papers** with relative paths
4. **Build frequently** to catch LaTeX errors early

### Collaboration
1. **Commit .paperrepo** for metadata sharing
2. **Ignore build/ directories** (already in .gitignore)
3. **Share configuration** via .texrepo-config
4. **Use meaningful commit messages** for paper evolution

## � Environment Support (Optional)

tex-repo provides optional commands to help set up and verify your LaTeX environment. These tools are designed for personal use and follow a conservative, explicit approach.

### Environment Checking

```bash
# Check system readiness for tex-repo
tex-repo env check
```

This command:
- ✅ **Safe**: Never modifies your system
- 📊 **Reports**: OS, Python version, and tool availability  
- 🔍 **Detects**: latexmk (required) and pdflatex (optional)
- 💡 **Suggests**: Installation steps for missing tools

Example output:
```
Environment check:
  OS: macOS 13.0
  Python: 3.11.5

  latexmk: ✅ found at /usr/local/bin/latexmk
  pdflatex: ❌ not found

Suggested next steps:
  macOS:
    brew install --cask mactex
```

### Setup Guide Generation

```bash
# Generate installation guide for your system
tex-repo env guide
```

This creates `env_guide.txt` with:
- **System-specific** installation instructions
- **Detailed explanations** of why tools are needed
- **Multiple installation options** (full vs. minimal)
- **Verification steps** to confirm successful setup

The guide file is automatically regenerated and safe to overwrite.

### Installation Assistance

```bash 
# Execute installation commands from generated guide
tex-repo install env_guide.txt
```

⚠️ **IMPORTANT WARNINGS**:
- This command **modifies your system**
- Requires **explicit user confirmation**  
- Intended for **personal use only**
- May require **administrator privileges**
- Should only be used on **systems you own**

The install command:
1. **Validates** the guide file was generated by tex-repo
2. **Shows all commands** that will be executed
3. **Asks for confirmation**: "Continue? [y/N]"
4. **Stops immediately** if any command fails
5. **Supports** Ubuntu/Debian (apt) and macOS (brew) only

### Why These Tools Exist

- **tex-repo standardizes on latexmk** for reliable compilation
- **Environment setup varies** significantly across systems
- **Manual installation** can be complex and error-prone
- **Personal automation** saves time for frequent users
- **Conservative design** builds trust through transparency

### When NOT to Use

These commands are **NOT intended for**:
- Production or shared environments
- Unattended/scripted installation
- Systems you don't own or control
- CI/CD pipelines (use containerization instead)

## �🔍 Troubleshooting

### Common Issues

**"Not inside a tex repo"**
- Ensure `.paperrepo` exists in repository root
- Use `tex-repo init` to create new repository

**"Domain path not found"**
- Create the domain first: `tex-repo nd <parent> <domain_name>`
- Check path spelling and structure

**"Paper already exists"**
- Choose a different paper name
- Or remove existing directory if intended

**LaTeX compilation errors**
- Check `build/main.log` for detailed errors
- Ensure all referenced packages are installed
- Verify bibliography entries in `refs.bib`

**Build cache issues**
- Use `--force` to ignore cache: `tex-repo b --force`
- Use `--clean` to clear build directory: `tex-repo b --clean`
- For reference/citation issues with pdflatex: Tool automatically runs twice

**Release creation issues**
- "Release directory already exists": Wait a moment and retry (timestamp-based naming)
- "Paper path does not exist": Verify path is correct relative to repository root
- "Not a paper directory": Ensure directory contains `main.tex`
- PDF build failures: Check LaTeX compilation errors in paper's build log
- "Failed to update release index": Check write permissions for releases/ directory

### Getting Help

```bash
tex-repo --help              # General help
tex-repo <command> --help    # Command-specific help
tex-repo status              # Check repository health
tex-repo env check           # Check system environment
tex-repo env guide           # Generate setup guide
```

## 🤝 Contributing

This project welcomes contributions! Areas for enhancement:
- Cross-reference management between papers
- Template system for different paper types
- Citation synchronization across papers
- Export tools (arXiv packages, combined documents)
- IDE integration plugins

## 📄 License

MIT License - see LICENSE file for details.

## Migration from Bash Version

The Python implementation provides full compatibility with the existing bash version while adding new features:

- **Existing commands** (`init`, `nd`, `np`, `b`) work identically
- **Enhanced .gitignore** generation with better coverage
- **New status command** for structural validation
- **Better error handling** and user feedback
- **Cross-platform compatibility** (no bash dependencies)

The original bash script (`tex-repo`) remains in the repository as reference but is not used for execution.

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)

## Development

The Python package structure:
```
texrepo/
├── __init__.py
├── __main__.py           # Entry point
├── cli.py               # Command-line interface
├── init_cmd.py          # Repository initialization
├── domain_cmd.py        # Domain creation (nd)
├── paper_cmd.py         # Paper creation (np)
├── build_cmd.py         # Paper building (b)
├── status_cmd.py        # Structure validation (status)
├── common.py            # Shared utilities
└── rules.py            # Repository rules and constraints
```

Each command is implemented in its own module with a clean separation of concerns.

## TODO: Installation & Environment Setup

At present, `tex-repo` is designed to be used as a lightweight, user-managed CLI
(tool directory + symlink into PATH).

In the future, the following installation and environment features may be added:

- Automated installation via `pipx` or similar isolated Python tooling
- Environment checks for required LaTeX tools (e.g. `latexmk`, `pdflatex`)
- Optional environment bootstrap for TeX distributions (MacTeX / TeX Live)
- Versioned release and upgrade workflow
- Non-interactive install mode for CI or reproducible environments

These features are intentionally deferred to keep the current system minimal,
transparent, and under direct user control.

## Roadmap: Environment-Managed Builds (Engine Consolidation)

Once automated environment installation/checks are added, `tex-repo` will
standardize on a single build engine: **latexmk**.

Rationale:
- `latexmk` provides stable multi-pass compilation behavior
- Reduces support complexity across platforms and TeX distributions
- Avoids divergent build semantics between engines

Transition plan:
- Current versions may support `pdflatex` as a compatibility option.
- After env-managed builds land, `pdflatex` will be deprecated and eventually removed.
