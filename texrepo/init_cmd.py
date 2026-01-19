from __future__ import annotations

from pathlib import Path

from .common import write_text
from .rules import (
    STAGE_PIPELINE,
    FOUNDATION_REL,
    SPEC_REL,
    PAPERS_DIRNAME,
    PROCESS_BRANCHES,
    FUNCTION_BRANCHES,
    WORLD_DIR,
    FORMALISM_DIR,
    PROCESS_REGIME_DIR,
    FUNCTION_APPLICATION_DIR,
)
from .meta_cmd import (
    escape_latex_string,
    prompt_for_metadata,
    sync_identity_tex,
    write_paperrepo_metadata,
)
from .paper_cmd import write_foundation_paper, write_spec_paper

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


def _gitignore_policy_block() -> str:
    """Return gitignore policy template wrapped with markers."""
    template = _GITIGNORE_TEMPLATE.rstrip() + "\n"
    return f"{POLICY_START}\n{template}{POLICY_END}\n"


def _write_readme_if_missing(path: Path, content: str) -> None:
    if path.exists():
        return
    write_text(path, content)


def cmd_init(args) -> int:
    source_text_path = None
    text_content = None

    # Determine repo name and optional text seed
    if getattr(args, "source_text", None):
        source_text_path = Path(args.source_text)
        repo_name = args.target
    elif str(args.target).lower().endswith(".txt"):
        source_text_path = Path(args.target)
        repo_name = Path(args.target).stem
    else:
        repo_name = args.target

    if source_text_path and source_text_path.suffix.lower() != ".txt":
        print("Error: Source document must be a .txt file")
        return 1

    repo = Path(repo_name).expanduser().resolve()
    
    # Check if this is an existing directory
    if repo.exists():
        # Existing directory - always refuse to avoid destructive changes
        if (repo / ".paperrepo").exists():
            print(f"Error: {repo} is already a tex-repo")
        else:
            print(f"Error: target directory already exists: {repo}")
            if (repo / ".gitignore").exists():
                print("Will not overwrite existing .gitignore file.")
        return 1

    # Load text content (if provided) before making any changes
    if source_text_path:
        source_text_path = source_text_path.expanduser().resolve()
        if not source_text_path.exists():
            print(f"Error: Source text file not found: {source_text_path}")
            return 1
        try:
            text_content = source_text_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error: Could not read source text file: {e}")
            return 1
    else:
        source_text_path = None

    if not repo.exists():
        # New directory
        repo.mkdir(parents=True, exist_ok=False)

    # Prompt for metadata interactively
    metadata = prompt_for_metadata(repo.name)
    
    # Create .paperrepo with basic repo info
    write_text(
        repo / ".paperrepo",
        "paperrepo=1\nversion=3\nlayout=staged\n",
    )
    
    # Add metadata to .paperrepo
    write_paperrepo_metadata(repo, metadata)

    # gitignore - policy block from template (only when absent)
    gitignore_path = repo / ".gitignore"
    write_text(gitignore_path, _gitignore_policy_block())

    # staged directories
    (repo / WORLD_DIR).mkdir(parents=True, exist_ok=True)
    (repo / FORMALISM_DIR).mkdir(parents=True, exist_ok=True)
    (repo / PROCESS_REGIME_DIR).mkdir(parents=True, exist_ok=True)
    (repo / FUNCTION_APPLICATION_DIR).mkdir(parents=True, exist_ok=True)

    # shared + misc
    (repo / "shared").mkdir(parents=True, exist_ok=True)
    (repo / "scripts").mkdir(parents=True, exist_ok=True)
    (repo / "98_context").mkdir(parents=True, exist_ok=True)
    (repo / "99_legacy").mkdir(parents=True, exist_ok=True)
    (repo / "releases").mkdir(parents=True, exist_ok=True)

    # world layer
    foundation_dir = repo / FOUNDATION_REL
    spec_dir = repo / SPEC_REL
    foundation_dir.mkdir(parents=True, exist_ok=True)
    spec_dir.mkdir(parents=True, exist_ok=True)

    # paper locations
    (repo / FORMALISM_DIR / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)
    for branch in PROCESS_BRANCHES:
        (repo / PROCESS_REGIME_DIR / branch / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)
    for branch in FUNCTION_BRANCHES:
        (repo / FUNCTION_APPLICATION_DIR / branch / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)

    # Generate identity.tex from metadata
    sync_identity_tex(repo)

    write_text(
        repo / "shared" / "preamble.tex",
        r"""\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
\usepackage{nameinlink,noabbrev]{cleveref}
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
""",
    )

    write_text(
        repo / "shared" / "macros.tex",
        r"""\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\set}[1]{\left\{#1\right\}}
\newcommand{\abs}[1]{\left|#1\right|}
\newcommand{\norm}[1]{\left\|#1\right\|}
\newcommand{\dd}{\,\mathrm{d}}
\newcommand{\pd}[2]{\frac{\partial #1}{\partial #2}}
\DeclareMathOperator{\tr}{tr}
""",
    )

    write_text(
        repo / "shared" / "notation.tex",
        r"""\newcommand{\AFC}{\alpha}
\newcommand{\cLight}{c}
\newcommand{\grad}{\nabla}
""",
    )

    # Seed world papers
    write_foundation_paper(repo, foundation_dir, "Foundation")
    write_spec_paper(repo, spec_dir, "Spec")

    if text_content is not None:
        section_path = spec_dir / "sections" / "section_1.tex"
        safe_text = escape_latex_string(text_content)
        if not safe_text.endswith("\n"):
            safe_text += "\n"
        write_text(section_path, f"\\section{{Section 1}}\n\n{safe_text}")

    # Seed required READMEs without overwriting existing content
    _write_readme_if_missing(
        repo / WORLD_DIR / "README.md",
        "# World\n\nShared foundation and spec papers live here.\n",
    )
    _write_readme_if_missing(
        foundation_dir / "README.md",
        "# Foundation\n\nImmutable foundations that all other layers rely on.\n",
    )
    _write_readme_if_missing(
        spec_dir / "README.md",
        "# Spec\n\nThe primary specification paper for this repository.\n",
    )
    stage_readmes = {
        FORMALISM_DIR: "# Formalism\n\nAdmissible forms, closures, and representations grounded in the world layer.\n",
        PROCESS_REGIME_DIR: "# Process Regime\n\nNatural processes and governing regimes built on the formalism.\n",
        FUNCTION_APPLICATION_DIR: "# Function Application\n\nFunctions and applications that depend on process/regime outputs.\n",
    }
    for stage in STAGE_PIPELINE[1:]:
        _write_readme_if_missing(repo / stage / "README.md", stage_readmes.get(stage, ""))

    # Subdomain READMEs
    _write_readme_if_missing(
        repo / PROCESS_REGIME_DIR / "process" / "README.md",
        "# Process\n\nProcess-focused subjects belong here.\n",
    )
    _write_readme_if_missing(
        repo / PROCESS_REGIME_DIR / "regime" / "README.md",
        "# Regime\n\nRegime-focused subjects belong here.\n",
    )
    _write_readme_if_missing(
        repo / FUNCTION_APPLICATION_DIR / "function" / "README.md",
        "# Function\n\nFunction-focused subjects belong here.\n",
    )
    _write_readme_if_missing(
        repo / FUNCTION_APPLICATION_DIR / "application" / "README.md",
        "# Application\n\nApplication-focused subjects belong here.\n",
    )

    print(f"✅ Initialized repo: {repo}")
    return 0
