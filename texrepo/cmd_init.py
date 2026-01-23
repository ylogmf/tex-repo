"""Initialize a new tex-repo repository."""

import sys
from pathlib import Path
from .utils import ensure_dir, write_file


GITIGNORE_CONTENT = """# Build outputs
**/build/
*.aux
*.log
*.out
*.toc
*.pdf
*.synctex.gz
*.fdb_latexmk
*.fls

# Editor files
.DS_Store
*.swp
*~
.vscode/
.idea/

# Python
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/

# Keep releases tracked
!releases/
"""

SHARED_PREAMBLE = r"""\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage{hyperref}
"""

SHARED_MACROS = r"""% Custom macros
"""

SHARED_NOTATION = r"""% Notation definitions
"""

SHARED_IDENTITY = r"""% Document identity
\author{Author Name}
\date{\today}
"""


def cmd_init(args):
    """
    Initialize a new tex-repo repository.
    
    Creates canonical baseline structure:
    - .paperrepo marker
    - shared/ directory with preamble, macros, notation, identity
    - 00_introduction/ (empty, ready for book structure)
    - Stage directories: 01_process_regime, 02_function_application, 03_hypophysis
    - releases/ directory
    - .gitignore
    """
    name = args.name
    target_dir = Path(name).resolve()
    
    if target_dir.exists():
        print(f"Error: Directory '{name}' already exists", file=sys.stderr)
        return 1
    
    # Create repository root
    ensure_dir(target_dir)
    
    # Create .paperrepo marker
    (target_dir / '.paperrepo').touch()
    
    # Create shared/ directory
    shared_dir = target_dir / 'shared'
    ensure_dir(shared_dir)
    write_file(shared_dir / 'preamble.tex', SHARED_PREAMBLE)
    write_file(shared_dir / 'macros.tex', SHARED_MACROS)
    write_file(shared_dir / 'notation.tex', SHARED_NOTATION)
    write_file(shared_dir / 'identity.tex', SHARED_IDENTITY)
    
    # Create baseline directories (including empty 00_introduction)
    ensure_dir(target_dir / '00_introduction')
    ensure_dir(target_dir / '01_process_regime')
    ensure_dir(target_dir / '02_function_application')
    ensure_dir(target_dir / '03_hypophysis')
    ensure_dir(target_dir / 'releases')
    
    # Create .gitignore
    write_file(target_dir / '.gitignore', GITIGNORE_CONTENT)
    
    return 0
