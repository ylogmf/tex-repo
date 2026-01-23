"""tex-repo init command - initialize a minimal repository."""
from __future__ import annotations

from pathlib import Path

from .common import write_text, die
from .meta_cmd import prompt_for_metadata, write_paperrepo_metadata


GITIGNORE_TEMPLATE = """############################
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

# Other LaTeX outputs
*.dvi
*.ps
*.pdf.tmp

############################
# OS / editor noise
############################

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*

# Windows
Thumbs.db
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


def cmd_init_simple(args) -> int:
    """Initialize a new tex-repo with minimal structure."""
    repo_name = args.name
    repo = Path(repo_name).expanduser().resolve()
    
    # Check if directory exists
    if repo.exists():
        if (repo / ".paperrepo").exists():
            die(f"Error: {repo} is already a tex-repo")
        else:
            die(f"Error: target directory already exists: {repo}")
    
    # Create new directory
    repo.mkdir(parents=True, exist_ok=False)
    
    # Prompt for metadata interactively
    metadata = prompt_for_metadata(repo.name)
    
    # Create .paperrepo with basic repo info
    write_text(
        repo / ".paperrepo",
        "paperrepo=1\nversion=3\n",
    )
    
    # Add metadata to .paperrepo
    write_paperrepo_metadata(repo, metadata)
    
    # Create .gitignore
    gitignore_path = repo / ".gitignore"
    write_text(gitignore_path, GITIGNORE_TEMPLATE)
    
    # Create shared/ directory with minimal files
    shared_dir = repo / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    
    # Create minimal preamble.tex
    preamble = shared_dir / "preamble.tex"
    write_text(preamble, r"""%% Shared preamble for all documents
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{amssymb}
\usepackage{hyperref}

% Add your custom packages and macros here
""")
    
    # Create empty macros.tex
    macros = shared_dir / "macros.tex"
    write_text(macros, "% Shared macros\n")
    
    # Create empty identity.tex
    identity = shared_dir / "identity.tex"
    write_text(identity, "% Author and repository metadata\n")
    
    print(f"✅ Initialized tex-repo: {repo}")
    print(f"   Use 'tex-repo book' to create book-class documents")
    print(f"   Use 'tex-repo paper' to create article-class papers")
    return 0
