from __future__ import annotations

from pathlib import Path

from .common import write_text
from .layouts import (
    DEFAULT_LAYOUT,
    LAYOUTS,
    get_function_branches,
    get_process_branches,
    required_dirs,
    stage_dir,
    world_paths_for_layout,
)
from .rules import PAPERS_DIRNAME
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


INTRO_ENTRY_TEMPLATE = r"""\documentclass[11pt]{article}
\input{../shared/preamble}
\input{../shared/macros}
\input{../shared/notation}
\input{../shared/identity}

\title{Introduction}
\date{}

\begin{document}
\maketitle

\input{build/sections_index.tex}

\end{document}
"""

INTRO_FRONTMATTER = {
    "title.tex": r"""\begin{titlepage}
\centering

{\LARGE Book-Scale Introduction}\\[1.5em]
{\large Structural orientation for staged tex-repo work}\\[2.0em]

\textit{Navigation-only front matter; substantive content begins in chapters.}

\vfill

\end{titlepage}
""",
    "preface.tex": r"""\section*{Preface}

This preface sets the reader contract for the introduction. It explains why the material is ordered, how navigation works, and what will not be provided here.

\begin{itemize}
\item \textbf{Purpose}: provide a book-scale map and orientation, not a paper-scale argument or proofs.
\item \textbf{Audience stance}: assume readers are new to this repository’s staging and need a stable entry point.
\item \textbf{Non-goals}: no claims, results, or conclusions are presented in this front matter; it only frames how to use the chapters that follow.
\end{itemize}
""",
    "how_to_read.tex": r"""\section*{How to Read This Book}

This introduction is organized as training sequence rather than a single extended paper.

\begin{itemize}
\item \textbf{Progressive spine}: chapters are arranged so later material depends on constraints set earlier; read in order.
\item \textbf{Partial definitions}: early chapters may leave terms intentionally partial so that later chapters can refine or restrict them.
\item \textbf{Recognition goals}: each chapter names what readers should be able to recognize when finishing it and what it avoids claiming.
\item \textbf{Separation of roles}: structure lives in this entry file and front matter; substantive content stays inside chapter subsections.
\end{itemize}
""",
    "toc.tex": r"""\clearpage
\tableofcontents
\clearpage
""",
}

INTRO_BACKMATTER = {
    "scope_limits.tex": r"""\section*{Scope Limits}

\begin{itemize}
\item This book-scale introduction is limited to framing, navigation, and learning objectives; it does not assert theoretical results.
\item Items that require proofs, data, or full formalism are deferred to stage-specific papers and are outside the admissible scope here.
\item Chapters may reference constraints established earlier but do not extend them beyond what is stated in those chapters.
\end{itemize}
""",
    "closing_notes.tex": r"""\section*{Closing Notes}

This back matter closes the scope without adding conclusions. It reiterates that open questions, unresolved definitions, and any claims requiring validation are intentionally left to later stages. Readers should treat this book as a map and onboarding spine rather than a terminal argument.
""",
}


def cmd_init(args) -> int:
    source_text_path = None
    text_content = None
    layout_name = getattr(args, "layout", DEFAULT_LAYOUT)
    if layout_name not in LAYOUTS:
        print(f"Error: Unknown layout '{layout_name}'. Choose from: {', '.join(LAYOUTS)}")
        return 1

    # Determine repo name and optional text seed
    legacy_seed = getattr(args, "legacy_seed_text", None)
    if legacy_seed:
        source_text_path = Path(legacy_seed)
        if source_text_path.suffix.lower() != ".txt":
            print("Error: --legacy-seed-text must be a .txt file")
            return 1
    
    repo_name = args.target

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
        f"paperrepo=1\nversion=3\nlayout={layout_name}\n",
    )
    
    # Add metadata to .paperrepo
    write_paperrepo_metadata(repo, metadata)

    # gitignore - policy block from template (only when absent)
    gitignore_path = repo / ".gitignore"
    write_text(gitignore_path, _gitignore_policy_block())

    # staged directories
    for stage in required_dirs(layout_name):
        (repo / stage).mkdir(parents=True, exist_ok=True)

    # shared + misc
    for extra in LAYOUTS[layout_name].extras:
        (repo / extra).mkdir(parents=True, exist_ok=True)

    # world layer
    world_paths = world_paths_for_layout(layout_name)
    foundation_dir = None
    spec_dir = None
    if world_paths:
        foundation_rel, spec_rel = world_paths
        foundation_dir = repo / foundation_rel
        spec_dir = repo / spec_rel
        foundation_dir.mkdir(parents=True, exist_ok=True)
        spec_dir.mkdir(parents=True, exist_ok=True)

    # paper locations
    formalism_dir = stage_dir(layout_name, "formalism")
    if formalism_dir:
        (repo / formalism_dir / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)

    intro_dir = stage_dir(layout_name, "introduction")

    process_dir = stage_dir(layout_name, "process_regime")
    if process_dir:
        for branch in get_process_branches(layout_name):
            (repo / process_dir / branch / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)

    function_dir = stage_dir(layout_name, "function_application")
    if function_dir:
        for branch in get_function_branches(layout_name):
            (repo / function_dir / branch / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)

    hypnosis_dir = stage_dir(layout_name, "hypnosis")
    if hypnosis_dir:
        (repo / hypnosis_dir / PAPERS_DIRNAME).mkdir(parents=True, exist_ok=True)

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

    # Seed world papers when applicable
    if foundation_dir and spec_dir:
        write_foundation_paper(repo, foundation_dir, "Foundation")
        write_spec_paper(repo, spec_dir, "Spec")

        if text_content is not None:
            section_path = spec_dir / "sections" / "section_1.tex"
            safe_text = escape_latex_string(text_content)
            if not safe_text.endswith("\n"):
                safe_text += "\n"
            write_text(section_path, f"\\section{{Section 1}}\n\n{safe_text}")
    elif text_content is not None:
        print("⚠️  Source text provided but layout has no spec target; seed was ignored.")

    # Seed required READMEs without overwriting existing content
    world_dir = stage_dir(layout_name, "world")
    if world_dir and foundation_dir and spec_dir:
        _write_readme_if_missing(
            repo / world_dir / "README.md",
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

    # Create book structure for introduction (new layout)
    if intro_dir:
        intro_path = repo / intro_dir
        # Create parts/ container structure
        parts_dir = intro_path / "parts"
        (parts_dir / "sections").mkdir(parents=True, exist_ok=True)
        (parts_dir / "frontmatter").mkdir(parents=True, exist_ok=True)
        (parts_dir / "backmatter").mkdir(parents=True, exist_ok=True)
        (parts_dir / "appendix").mkdir(parents=True, exist_ok=True)
        (intro_path / "build").mkdir(parents=True, exist_ok=True)

        # Frontmatter files
        for name, content in INTRO_FRONTMATTER.items():
            target = parts_dir / "frontmatter" / name
            if not target.exists():
                write_text(target, content)

        # Backmatter files
        for name, content in INTRO_BACKMATTER.items():
            target = parts_dir / "backmatter" / name
            if not target.exists():
                write_text(target, content)

        # Entry file for buildable book
        intro_entry = intro_path / f"{intro_dir}.tex"
        if not intro_entry.exists():
            write_text(intro_entry, INTRO_ENTRY_TEMPLATE)

    stage_readmes = {}
    if formalism_dir:
        stage_readmes[formalism_dir] = (
            "# Formalism\n\nAdmissible forms, closures, and representations grounded in the world layer.\n"
        )
    if intro_dir:
        stage_readmes[intro_dir] = "# Introduction\n\nBook-scale introduction with numbered sections. Use 'tex-repo ns <section-name>' to create sections.\n"
    if process_dir:
        stage_readmes[process_dir] = "# Process Regime\n\nNatural processes and governing regimes built on the formalism.\n"
    if function_dir:
        stage_readmes[function_dir] = (
            "# Function Application\n\nFunctions and applications that depend on process/regime outputs.\n"
        )
    if hypnosis_dir:
        stage_readmes[hypnosis_dir] = "# Hypnosis\n\nHypnosis research and downstream analyses live here.\n"

    for stage, content in stage_readmes.items():
        _write_readme_if_missing(repo / stage / "README.md", content)

    # Subdomain READMEs
    if process_dir:
        for branch in get_process_branches(layout_name):
            label = branch.capitalize()
            _write_readme_if_missing(
                repo / process_dir / branch / "README.md",
                f"# {label}\n\n{label}-focused subjects belong here.\n",
            )
    if function_dir:
        for branch in get_function_branches(layout_name):
            label = branch.capitalize()
            _write_readme_if_missing(
                repo / function_dir / branch / "README.md",
                f"# {label}\n\n{label}-focused subjects belong here.\n",
            )

    print(f"✅ Initialized repo: {repo}")
    return 0
