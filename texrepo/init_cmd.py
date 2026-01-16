from __future__ import annotations

from pathlib import Path

from .common import write_text
from .rules import STAGES, SPEC_PAPER_REL, SPEC_DIR, STAGE_PIPELINE
from .meta_cmd import (
    escape_latex_string,
    prompt_for_metadata,
    sync_identity_tex,
    write_paperrepo_metadata,
)
from .config import get_paper_config

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

    # stages
    for s in STAGES:
        (repo / s).mkdir(parents=True, exist_ok=True)

    # shared
    (repo / "shared").mkdir(parents=True, exist_ok=True)
    (repo / "scripts").mkdir(parents=True, exist_ok=True)
    (repo / "98_context").mkdir(parents=True, exist_ok=True)
    (repo / "99_legacy").mkdir(parents=True, exist_ok=True)
    
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

    # create Spec paper (SPEC/spec)
    spec_dir = repo / SPEC_PAPER_REL
    (spec_dir / "sections").mkdir(parents=True, exist_ok=True)
    (spec_dir / "build").mkdir(parents=True, exist_ok=True)

    write_text(spec_dir / "refs.bib", "% BibTeX entries here\n")

    # Generate Spec paper main.tex with identity integration
    config = get_paper_config(repo)
    date_macro = r"\date{\today}" if metadata.get('date_policy', 'today') == 'today' else r"\date{}"
    bib_style = metadata.get('default_bibliography_style', 'plainnat')
    
    section_count = config['section_count']
    doc_class = config['document_class']
    doc_options = config['document_options']
    include_abstract = config['include_abstract']
    
    main_tex_content = rf"""\documentclass[{doc_options}]{{{doc_class}}}

\input{{../../shared/preamble.tex}}
\input{{../../shared/macros.tex}}
\input{{../../shared/notation.tex}}
\input{{../../shared/identity.tex}}

\title{{\RepoProjectName Spec}}
\author{{\RepoAuthorName \\ \RepoAuthorAffil}}
{date_macro}

\begin{{document}}
\maketitle
"""
    
    if include_abstract:
        main_tex_content += r"""
\begin{abstract}
\input{sections/section_0}
\end{abstract}
"""
    
    # Add section inputs based on configuration
    section_inputs = "\n".join([rf"\input{{sections/section_{i}}}" for i in range(1, section_count + 1)])
    main_tex_content += f"\n{section_inputs}\n"
    
    main_tex_content += rf"""
\bibliographystyle{{{bib_style}}}
\bibliography{{refs}}

\end{{document}}
"""
    
    write_text(spec_dir / "main.tex", main_tex_content)

    if include_abstract:
        write_text(spec_dir / "sections" / "section_0.tex", "% Abstract\n\nWrite abstract here.\n")
    
    for i in range(1, section_count + 1):
        section_path = spec_dir / "sections" / f"section_{i}.tex"
        if i == 1 and text_content is not None:
            safe_text = escape_latex_string(text_content)
            if not safe_text.endswith("\n"):
                safe_text += "\n"
            write_text(section_path, f"\\section{{Section {i}}}\n\n{safe_text}")
        else:
            write_text(section_path, f"\\section{{Section {i}}}\n\nWrite here.\n")

    # Seed required READMEs without overwriting existing content
    _write_readme_if_missing(
        repo / SPEC_DIR / "README.md",
        "# Spec\n\nThis directory holds the Spec: primitives, constructors, forbidden constructs, and dependency direction. Everything else depends on it without modifying it.\n",
    )
    _write_readme_if_missing(
        spec_dir / "README.md",
        "# Spec Paper\n\nThe unique Spec paper for this repository. It must remain at SPEC/spec and is the immutable constraint layer.\n",
    )
    stage_readmes = {
        "01_formalism": "# Formalism\n\nAdmissible forms, closures, and representations derived from the Spec.\n",
        "02_processes": "# Processes\n\nNatural processes grounded in the Spec and expressed through the formalism.\n",
        "03_applications": "# Applications\n\nHuman-built functions, models, and tools that depend on the Spec via the formalism and processes.\n",
        "04_testbeds": "# Testbeds\n\nExperiments and validation environments for applications derived from the Spec.\n",
    }
    for stage in STAGE_PIPELINE:
        _write_readme_if_missing(repo / stage / "README.md", stage_readmes.get(stage, ""))

    print(f"✅ Initialized repo: {repo}")
    return 0
