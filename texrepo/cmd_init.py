"""Initialize a new tex-repo repository."""

import sys
from pathlib import Path
from .utils import ensure_dir, write_file


def parse_text_manuscript(text_path):
    """
    Parse a plain text manuscript file to extract metadata and content.
    
    Expected format:
      Line 1: Title (first non-empty line)
      Line 2: Author (second non-empty line)
      Line 3+: Optional metadata or blank
      Remaining: Body content
    
    Returns:
        dict with keys: 'title', 'author', 'body', 'repo_name'
    """
    text_file = Path(text_path)
    if not text_file.exists():
        raise FileNotFoundError(f"Text manuscript not found: {text_path}")
    
    content = text_file.read_text(encoding='utf-8')
    lines = content.splitlines()
    
    # Extract non-empty lines for metadata
    non_empty = [line.strip() for line in lines if line.strip()]
    
    if len(non_empty) < 2:
        raise ValueError("Manuscript must contain at least a title and author")
    
    title = non_empty[0]
    author = non_empty[1]
    
    # Find where body content starts (after first 2 non-empty lines in original)
    found_count = 0
    body_start_idx = 0
    for i, line in enumerate(lines):
        if line.strip():
            found_count += 1
            if found_count == 2:
                body_start_idx = i + 1
                break
    
    # Body is everything after the author line
    body_lines = lines[body_start_idx:]
    body = '\n'.join(body_lines).strip()
    
    # Generate repo name from manuscript filename (without extension)
    repo_name = text_file.stem
    
    return {
        'title': title,
        'author': author,
        'body': body,
        'repo_name': repo_name
    }


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

SHARED_MACROS = r"""% Custom macros
"""

SHARED_NOTATION = r"""% Notation definitions
"""

SHARED_IDENTITY = r"""% Document identity
\author{Author Name}
\date{\today}
"""


def load_template(filename):
    """Load a template file from texrepo/templates/."""
    template_dir = Path(__file__).parent / 'templates'
    template_path = template_dir / filename
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text()


def cmd_init(args):
    """
    Initialize a new tex-repo repository.
    
    Two modes:
    1. tex-repo init <repo_name> - creates empty repository
    2. tex-repo init <manuscript.txt> - creates repository from text file
    
    Creates canonical baseline structure:
    - .paperrepo marker
    - shared/ directory with preamble, macros, notation, identity
    - 00_introduction/ (empty or with initial content from manuscript)
    - Stage directories: 01_process_regime, 02_function_application, 03_hypophysis
    - releases/ directory
    - .gitignore
    """
    name_or_file = args.name
    
    # Determine if this is a text manuscript or plain repository name
    manuscript_data = None
    manuscript_path = Path(name_or_file)
    
    if manuscript_path.exists() and manuscript_path.suffix in ['.txt', '.text', '.md']:
        # Text manuscript mode
        try:
            manuscript_data = parse_text_manuscript(name_or_file)
            name = manuscript_data['repo_name']
            # Create repository in same directory as manuscript
            target_dir = (manuscript_path.parent / name).resolve()
        except Exception as e:
            print(f"Error parsing manuscript: {e}", file=sys.stderr)
            return 1
    else:
        # Regular repository name
        name = name_or_file
        target_dir = Path(name).resolve()
    
    if target_dir.exists():
        print(f"Error: Directory '{name}' already exists", file=sys.stderr)
        return 1
    
    # Create repository root
    ensure_dir(target_dir)
    
    # Create .paperrepo marker
    (target_dir / '.paperrepo').touch()
    
    # Load template content
    packages_content = load_template('shared_packages.tex')
    preamble_content = load_template('shared_preamble.tex')
    
    # Create shared/ directory
    shared_dir = target_dir / 'shared'
    ensure_dir(shared_dir)
    write_file(shared_dir / 'packages.tex', packages_content)
    write_file(shared_dir / 'preamble.tex', preamble_content)
    write_file(shared_dir / 'macros.tex', SHARED_MACROS)
    write_file(shared_dir / 'notation.tex', SHARED_NOTATION)
    
    # Generate identity.tex with manuscript metadata if available
    if manuscript_data:
        identity_content = f"""% Document identity
\\title{{{manuscript_data['title']}}}
\\author{{{manuscript_data['author']}}}
\\date{{\\today}}
"""
    else:
        identity_content = SHARED_IDENTITY
    
    write_file(shared_dir / 'identity.tex', identity_content)
    
    # Create baseline directories
    intro_dir = target_dir / '00_introduction'
    ensure_dir(intro_dir)
    ensure_dir(target_dir / '01_process_regime')
    ensure_dir(target_dir / '02_function_application')
    ensure_dir(target_dir / '03_hypophysis')
    ensure_dir(target_dir / 'releases')
    
    # If manuscript mode, create initial document with content
    if manuscript_data:
        intro_tex_path = intro_dir / '00_introduction.tex'
        intro_content = f"""\\documentclass[11pt]{{article}}
\\input{{../shared/preamble.tex}}
\\input{{../shared/macros.tex}}
\\input{{../shared/notation.tex}}
\\input{{../shared/identity.tex}}

\\begin{{document}}

\\maketitle

{manuscript_data['body']}

\\end{{document}}
"""
        write_file(intro_tex_path, intro_content)
        
        # Create build directory for introduction
        ensure_dir(intro_dir / 'build')
    
    # Create .gitignore
    write_file(target_dir / '.gitignore', GITIGNORE_CONTENT)
    
    if manuscript_data:
        print(f"✅ Initialized repository from manuscript: {target_dir}")
        print(f"   Title: {manuscript_data['title']}")
        print(f"   Author: {manuscript_data['author']}")
    else:
        print(f"✅ Initialized repository: {target_dir}")
    
    return 0
