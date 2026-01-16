from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from .common import find_repo_root, die, write_text
from .config import DEFAULT_CONFIG, create_default_config
from .meta_cmd import parse_paperrepo_metadata, sync_identity_tex
from .rules import STAGES, SPEC_DIR, SPEC_PAPER_REL, STAGE_PIPELINE

POLICY_START = "# >>> tex-repo policy"
POLICY_END = "# <<< tex-repo policy"
_GITIGNORE_TEMPLATE = """############################
# tex-repo build artifacts
############################

# All intermediate build outputs
**/build/

############################
# LaTeX temporary files
############################

*.aux
*.log
*.out
*.toc
*.lof
*.lot
*.fls
*.fdb_latexmk
*.synctex.gz
*.synctex(busy)
*.synctex.gz(busy)

# Bibliography / biber
*.bbl
*.blg
*.bcf
*.run.xml
*.bib.bak

# Indices / glossaries
*.idx
*.ilg
*.ind
*.ist
*.glg
*.glo
*.gls
*.glsdefs
*.acn
*.acr
*.alg
*.loa
*.nlo
*.nls

# minted / pygments
_minted*
*.pyg

############################
# OS / editor noise
############################

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*
.Spotlight-V100
.Trashes
.fseventsd

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# IDEs
.vscode/
.idea/
*.iml

############################
# tex-repo local files
############################

# Generated environment guide
env_guide.txt

# Internal tool state
.texrepo/

############################
# Explicitly keep releases
############################

!releases/
!releases/**
"""

class FixResult:
    def __init__(self):
        self.created = 0
        self.skipped = 0
        self.warnings = 0
        self.actions: List[Tuple[str, str]] = []  # (status, path)
    
    def add_created(self, path: str):
        self.created += 1
        self.actions.append(("created", path))
    
    def add_would_create(self, path: str):
        self.created += 1
        self.actions.append(("would_create", path))
    
    def add_skipped(self, path: str, reason: str = ""):
        self.skipped += 1
        reason_suffix = f" ({reason})" if reason else ""
        self.actions.append(("skipped", f"{path}{reason_suffix}"))
    
    def add_warning(self, path: str, reason: str):
        self.warnings += 1
        self.actions.append(("warning", f"{path} - {reason}"))


def _gitignore_policy_block() -> str:
    """Return gitignore policy template wrapped with markers."""
    template = _GITIGNORE_TEMPLATE.rstrip() + "\n"
    return f"{POLICY_START}\n{template}{POLICY_END}\n"


def ensure_readme(path: Path, content: str, result: FixResult, dry_run: bool = False) -> None:
    """Create README.md if missing without overwriting existing files."""
    check_and_create_file(path, content, result, dry_run)


def _apply_gitignore_policy(path: Path, result: FixResult, dry_run: bool = False) -> None:
    """Ensure .gitignore contains the policy block."""
    policy_block = _gitignore_policy_block()

    if not path.exists():
        if dry_run:
            result.add_would_create(str(path))
        else:
            write_text(path, policy_block)
            result.add_created(str(path))
        return

    current = path.read_text(encoding="utf-8")
    start = current.find(POLICY_START)
    end = current.find(POLICY_END)

    if start != -1 and end != -1 and end > start:
        block_end = end + len(POLICY_END)
        after = current[block_end:].lstrip("\n")
        new_content = current[:start] + policy_block
        if after:
            if not new_content.endswith("\n"):
                new_content += "\n"
            new_content += after
    else:
        # Append policy block with spacing
        new_content = current
        if not new_content.endswith("\n"):
            new_content += "\n"
        new_content += "\n" + policy_block

    if new_content == current:
        result.add_skipped(str(path), "policy already present")
        return

    if dry_run:
        result.add_would_create(str(path))
    else:
        write_text(path, new_content)
        result.add_created(str(path))


def check_and_create_directory(path: Path, result: FixResult, dry_run: bool = False) -> None:
    """Check if directory exists and create if missing."""
    if path.exists():
        result.add_skipped(str(path), "already exists")
    else:
        if dry_run:
            result.add_would_create(str(path))
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                result.add_created(str(path))
            except PermissionError:
                result.add_warning(str(path), "cannot create (permission denied)")
            except Exception as e:
                result.add_warning(str(path), f"cannot create ({e})")


def check_and_create_file(path: Path, content: str, result: FixResult, dry_run: bool = False) -> None:
    """Check if file exists and create if missing."""
    if path.exists():
        result.add_skipped(str(path), "already exists")
    else:
        if dry_run:
            result.add_would_create(str(path))
        else:
            try:
                write_text(path, content)
                result.add_created(str(path))
            except PermissionError:
                result.add_warning(str(path), "cannot create (permission denied)")
            except Exception as e:
                result.add_warning(str(path), f"cannot create ({e})")


def fix_repository_structure(repo_root: Path, result: FixResult, dry_run: bool = False) -> None:
    """Fix repository folder structure."""
    print("Checking repository folder structure...")
    
    # Top-level stage folders
    for stage in STAGES:
        check_and_create_directory(repo_root / stage, result, dry_run)
    
    # Additional allowed folders
    extra_folders = ["98_context", "99_legacy", "shared", "scripts"]
    for folder in extra_folders:
        check_and_create_directory(repo_root / folder, result, dry_run)


def fix_repository_files(repo_root: Path, result: FixResult, dry_run: bool = False) -> None:
    """Fix repository configuration files."""
    print("Checking repository configuration files...")
    
    # .paperrepo (minimal placeholder)
    paperrepo_content = "paperrepo=1\nversion=3\nlayout=staged\n"
    check_and_create_file(repo_root / ".paperrepo", paperrepo_content, result, dry_run)
    
    # .gitignore policy block
    _apply_gitignore_policy(repo_root / ".gitignore", result, dry_run)
    
    # .texrepo-config (only create if missing)
    if not (repo_root / ".texrepo-config").exists():
        if dry_run:
            result.add_would_create(str(repo_root / ".texrepo-config"))
        else:
            try:
                create_default_config(repo_root)
                result.add_created(str(repo_root / ".texrepo-config"))
            except Exception as e:
                result.add_warning(str(repo_root / ".texrepo-config"), f"cannot create ({e})")
    else:
        result.add_skipped(str(repo_root / ".texrepo-config"), "already exists")


def fix_shared_files(repo_root: Path, result: FixResult, dry_run: bool = False) -> None:
    """Fix shared LaTeX files."""
    print("Checking shared LaTeX files...")
    
    shared_dir = repo_root / "shared"
    
    # preamble.tex
    preamble_content = r"""\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
\usepackage[nameinlink,noabbrev]{cleveref}
\usepackage[numbers]{natbib}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.8em}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{Corollary}
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{remark}{Remark}
"""
    check_and_create_file(shared_dir / "preamble.tex", preamble_content, result, dry_run)
    
    # macros.tex
    macros_content = r"""\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\set}[1]{\left\{#1\right\}}
\newcommand{\abs}[1]{\left|#1\right|}
\newcommand{\norm}[1]{\left\|#1\right\|}
\newcommand{\dd}{\,\mathrm{d}}
\newcommand{\pd}[2]{\frac{\partial #1}{\partial #2}}
\DeclareMathOperator{\tr}{tr}
"""
    check_and_create_file(shared_dir / "macros.tex", macros_content, result, dry_run)
    
    # notation.tex
    notation_content = r"""\newcommand{\AFC}{\alpha}
\newcommand{\cLight}{c}
\newcommand{\grad}{\nabla}
"""
    check_and_create_file(shared_dir / "notation.tex", notation_content, result, dry_run)
    
    # identity.tex (only if .paperrepo exists)
    if (repo_root / ".paperrepo").exists():
        if not (shared_dir / "identity.tex").exists():
            if dry_run:
                result.add_would_create(str(shared_dir / "identity.tex"))
            else:
                try:
                    sync_identity_tex(repo_root)
                    result.add_created(str(shared_dir / "identity.tex"))
                except Exception as e:
                    result.add_warning(str(shared_dir / "identity.tex"), f"cannot create ({e})")
    else:
        result.add_skipped(str(shared_dir / "identity.tex"), "already exists")


def fix_readmes(repo_root: Path, result: FixResult, dry_run: bool = False) -> None:
    """Ensure required README.md files exist without overwriting."""
    print("Checking required README files...")

    ensure_readme(
        repo_root / SPEC_DIR / "README.md",
        "# Spec\n\nThis directory holds the Spec: primitives, constructors, forbidden constructs, and dependency direction. Everything else depends on it without modifying it.\n",
        result,
        dry_run,
    )
    ensure_readme(
        repo_root / SPEC_PAPER_REL / "README.md",
        "# Spec Paper\n\nThe unique Spec paper for this repository. It must remain at SPEC/spec and is the immutable constraint layer.\n",
        result,
        dry_run,
    )

    stage_readmes = {
        "01_formalism": "# Formalism\n\nAdmissible forms, closures, and representations derived from the Spec.\n",
        "02_processes": "# Processes\n\nNatural processes grounded in the Spec and expressed through the formalism.\n",
        "03_applications": "# Applications\n\nHuman-built functions, models, and tools that depend on the Spec via the formalism and processes.\n",
        "04_testbeds": "# Testbeds\n\nExperiments and validation environments for applications derived from the Spec.\n",
    }

    # Stage README files
    for stage in STAGE_PIPELINE:
        ensure_readme(repo_root / stage / "README.md", stage_readmes.get(stage, ""), result, dry_run)

    # Domain and paper README files
    for stage in STAGE_PIPELINE:
        stage_path = repo_root / stage
        if not stage_path.exists():
            continue
        for domain in stage_path.iterdir():
            if not domain.is_dir():
                continue
            ensure_readme(
                domain / "README.md",
                f"# {domain.name}\n\nDomain under {stage} that inherits constraints from the Spec.\n",
                result,
                dry_run,
            )
            for paper_dir in domain.iterdir():
                if not paper_dir.is_dir():
                    continue
                if (paper_dir / "main.tex").exists():
                    ensure_readme(
                        paper_dir / "README.md",
                        "# Paper\n\nThis paper depends on the Spec via its enclosing domain and stage.\n",
                        result,
                        dry_run,
                    )

def fix_spec_paper(repo_root: Path, result: FixResult, dry_run: bool = False) -> None:
    """Fix Spec paper skeleton."""
    print("Checking Spec paper skeleton...")
    
    spec_dir = repo_root / SPEC_PAPER_REL
    
    # Spec directory structure
    check_and_create_directory(spec_dir, result, dry_run)
    check_and_create_directory(spec_dir / "sections", result, dry_run)
    check_and_create_directory(spec_dir / "build", result, dry_run)
    
    # refs.bib
    refs_content = "% BibTeX entries here\n"
    check_and_create_file(spec_dir / "refs.bib", refs_content, result, dry_run)
    
    # main.tex
    main_tex_content = r"""\documentclass[11pt]{article}

\input{../../shared/preamble.tex}
\input{../../shared/macros.tex}
\input{../../shared/notation.tex}
\input{../../shared/identity.tex}

\title{Spec}
\author{Author Name \\ Organization}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
\input{sections/section_0}
\end{abstract}

\input{sections/section_1}
\input{sections/section_2}
\input{sections/section_3}
\input{sections/section_4}
\input{sections/section_5}
\input{sections/section_6}
\input{sections/section_7}
\input{sections/section_8}
\input{sections/section_9}
\input{sections/section_10}

\bibliographystyle{plainnat}
\bibliography{refs}

\end{document}
"""
    check_and_create_file(spec_dir / "main.tex", main_tex_content, result, dry_run)
    
    # Section files
    sections_dir = spec_dir / "sections"
    
    # Abstract (section_0.tex)
    abstract_content = "% Abstract\n\nWrite abstract here.\n"
    check_and_create_file(sections_dir / "section_0.tex", abstract_content, result, dry_run)
    
    # Content sections (section_1.tex to section_10.tex)
    for i in range(1, 11):
        section_content = f"\\section{{Section {i}}}\n\nWrite here.\n"
        check_and_create_file(sections_dir / f"section_{i}.tex", section_content, result, dry_run)


def print_fix_results(result: FixResult, dry_run: bool = False) -> None:
    """Print fix results with clear formatting."""
    print()
    
    # Print actions
    for status, path in result.actions:
        if status == "created":
            print(f"✅ created: {path}")
        elif status == "would_create":
            print(f"➕ would create: {path}")
        elif status == "skipped":
            print(f"ℹ️ exists: {path}")
        elif status == "warning":
            print(f"⚠️ cannot create: {path}")
    
    # Print summary
    print()
    action_word = "would be " if dry_run else ""
    print(f"Fix summary:")
    print(f"  {action_word}created: {result.created}")
    print(f"  skipped: {result.skipped}")
    if result.warnings > 0:
        print(f"  warnings: {result.warnings}")


def cmd_fix(args) -> int:
    """Handle the fix command."""
    try:
        repo_root = find_repo_root()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    dry_run = getattr(args, 'dry_run', False)
    
    if dry_run:
        print("Running in dry-run mode - no files will be modified")
        print()
    
    result = FixResult()
    
    try:
        # Check and fix various components
        fix_repository_structure(repo_root, result, dry_run)
        fix_repository_files(repo_root, result, dry_run)
        fix_shared_files(repo_root, result, dry_run)
        fix_spec_paper(repo_root, result, dry_run)
        fix_readmes(repo_root, result, dry_run)
        
        # Print results
        print_fix_results(result, dry_run)
        
        return 0
        
    except Exception as e:
        print(f"Error during fix: {e}")
        return 1
