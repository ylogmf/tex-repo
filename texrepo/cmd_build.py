"""Build command: generate spine files and compile LaTeX."""

import os
import sys
import subprocess
from pathlib import Path
from .utils import find_repo_root, get_numbered_dirs, write_file


def get_build_timeout() -> int:
    """Get build timeout in seconds from environment or use default."""
    try:
        return int(os.environ.get('TEXREPO_BUILD_TIMEOUT_SECONDS', '60'))
    except ValueError:
        return 60


def print_log_tail(log_path: Path, lines: int = 30) -> None:
    """Print the last N lines of a log file to stderr."""
    if not log_path.exists():
        return
    
    try:
        content = log_path.read_text(encoding='utf-8', errors='replace')
        log_lines = content.splitlines()
        tail = log_lines[-lines:] if len(log_lines) > lines else log_lines
        
        print("\n--- Build log (last 30 lines) ---", file=sys.stderr)
        for line in tail:
            print(line, file=sys.stderr)
        print("--- End of log ---\n", file=sys.stderr)
    except Exception as e:
        print(f"Could not read log file: {e}", file=sys.stderr)


def generate_sections_index(book_root: Path) -> str:
    """
    Generate frontmatter spine (sections_index.tex).
    
    This file is included in \\frontmatter and should NOT contain
    \\part, \\chapter, or \\section commands.
    """
    # For now, just a placeholder
    # In a full implementation, this would scan frontmatter/ for sections
    return "% Frontmatter spine\n% (Title page, TOC, preface, etc.)\n"


def generate_chapters_index(book_root: Path) -> str:
    """
    Generate mainmatter spine (chapters_index.tex).
    
    This file includes all parts and chapters from parts/parts/.
    """
    parts_dir = book_root / 'parts' / 'parts'
    if not parts_dir.exists():
        return "% No parts found\n"
    
    lines = ["% Mainmatter spine\n"]
    
    # Get all parts
    parts = get_numbered_dirs(parts_dir)
    
    for part_num, part_slug, part_dir in parts:
        # Include part.tex
        part_tex_rel = f"parts/parts/{part_num}_{part_slug}/part.tex"
        lines.append(f"\\input{{{part_tex_rel}}}\n")
        
        # Get all chapters in this part
        chapters_dir = part_dir / 'chapters'
        if chapters_dir.exists():
            chapters = get_numbered_dirs(chapters_dir)
            for ch_num, ch_slug, ch_dir in chapters:
                # Include chapter.tex
                ch_tex_rel = f"parts/parts/{part_num}_{part_slug}/chapters/{ch_num}_{ch_slug}/chapter.tex"
                lines.append(f"\\input{{{ch_tex_rel}}}\n")
        
        lines.append("\n")  # Blank line between parts
    
    return ''.join(lines)


def build_book(book_root: Path) -> int:
    """Build a book-class document."""
    entry_file = book_root / f"{book_root.name}.tex"
    if not entry_file.exists():
        print(f"Error: Entry file not found: {entry_file}", file=sys.stderr)
        return 1
    
    build_dir = book_root / 'build'
    build_dir.mkdir(exist_ok=True)
    
    # Generate spine files
    print("Generating spine files...")
    sections_content = generate_sections_index(book_root)
    write_file(build_dir / 'sections_index.tex', sections_content)
    print(f"  ✓ {build_dir / 'sections_index.tex'}")
    
    chapters_content = generate_chapters_index(book_root)
    write_file(build_dir / 'chapters_index.tex', chapters_content)
    print(f"  ✓ {build_dir / 'chapters_index.tex'}")
    
    # Run latexmk with non-interactive flags and timeout
    print(f"\nCompiling {entry_file.name}...")
    
    timeout = get_build_timeout()
    build_log = build_dir / 'texrepo_build.log'
    
    try:
        result = subprocess.run(
            [
                'latexmk',
                '-pdf',
                '-interaction=nonstopmode',
                '-halt-on-error',
                '-file-line-error',
                '-output-directory=build',
                entry_file.name
            ],
            cwd=book_root,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Save build output to log
        log_content = f"=== STDOUT ===\n{result.stdout}\n\n=== STDERR ===\n{result.stderr}\n"
        build_log.write_text(log_content, encoding='utf-8')
        
        if result.returncode != 0:
            print(f"Build failed! (exit code {result.returncode})", file=sys.stderr)
            print(f"Build log: {build_log}", file=sys.stderr)
            print_log_tail(build_log)
            return 1
        
        pdf_output = build_dir / f"{entry_file.stem}.pdf"
        if pdf_output.exists():
            print(f"✓ Build successful: {pdf_output}")
        else:
            print("Warning: Build completed but PDF not found", file=sys.stderr)
        
        return 0
        
    except subprocess.TimeoutExpired:
        print(f"Error: Build timed out after {timeout} seconds", file=sys.stderr)
        print(f"Check build logs at: {build_dir}", file=sys.stderr)
        print("Increase timeout with: export TEXREPO_BUILD_TIMEOUT_SECONDS=120", file=sys.stderr)
        if build_log.exists():
            print_log_tail(build_log)
        return 1
        
    except FileNotFoundError:
        print("Error: latexmk not found", file=sys.stderr)
        print("Install LaTeX toolchain with: brew install texlive", file=sys.stderr)
        return 1


def build_paper(paper_dir: Path) -> int:
    """Build a paper (article-class document)."""
    entry_file = paper_dir / f"{paper_dir.name}.tex"
    if not entry_file.exists():
        print(f"Error: Entry file not found: {entry_file}", file=sys.stderr)
        return 1
    
    build_dir = paper_dir / 'build'
    build_dir.mkdir(exist_ok=True)
    
    # Run latexmk with non-interactive flags and timeout
    print(f"Compiling {entry_file.name}...")
    
    timeout = get_build_timeout()
    build_log = build_dir / 'texrepo_build.log'
    
    try:
        result = subprocess.run(
            [
                'latexmk',
                '-pdf',
                '-interaction=nonstopmode',
                '-halt-on-error',
                '-file-line-error',
                '-output-directory=build',
                entry_file.name
            ],
            cwd=paper_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Save build output to log
        log_content = f"=== STDOUT ===\n{result.stdout}\n\n=== STDERR ===\n{result.stderr}\n"
        build_log.write_text(log_content, encoding='utf-8')
        
        if result.returncode != 0:
            print(f"Build failed! (exit code {result.returncode})", file=sys.stderr)
            print(f"Build log: {build_log}", file=sys.stderr)
            print_log_tail(build_log)
            return 1
        
        pdf_output = build_dir / f"{entry_file.stem}.pdf"
        if pdf_output.exists():
            print(f"✓ Build successful: {pdf_output}")
        else:
            print("Warning: Build completed but PDF not found", file=sys.stderr)
        
        return 0
        
    except subprocess.TimeoutExpired:
        print(f"Error: Build timed out after {timeout} seconds", file=sys.stderr)
        print(f"Check build logs at: {build_dir}", file=sys.stderr)
        print("Increase timeout with: export TEXREPO_BUILD_TIMEOUT_SECONDS=120", file=sys.stderr)
        if build_log.exists():
            print_log_tail(build_log)
        return 1
        
    except FileNotFoundError:
        print("Error: latexmk not found", file=sys.stderr)
        print("Install LaTeX toolchain with: brew install texlive", file=sys.stderr)
        return 1


def find_buildable_documents(repo_root: Path) -> list[Path]:
    """Find all buildable documents in the repository."""
    documents = []
    
    # Check all numbered directories at repo root
    for item in repo_root.iterdir():
        if not item.is_dir():
            continue
        
        # Skip special directories
        if item.name in {'.git', 'releases', 'shared', '98_context', '99_legacy', 'scripts'}:
            continue
        
        # Check for numbered directories (NN_slug format)
        if len(item.name) >= 3 and item.name[:2].isdigit() and item.name[2] == '_':
            # Check if entry file exists
            entry_file = item / f"{item.name}.tex"
            if entry_file.exists():
                documents.append(item)
    
    return sorted(documents, key=lambda d: d.name)


def cmd_build(args):
    """
    Build LaTeX documents.
    
    Generates spine files for books and runs latexmk.
    Never mutates authored sources; only writes under build/.
    """
    repo_root = find_repo_root()
    if repo_root is None:
        print("Error: Not in a tex-repo repository", file=sys.stderr)
        return 1
    
    # Determine target
    if args.target == 'all':
        documents = find_buildable_documents(repo_root)
        if not documents:
            print("No documents found to build", file=sys.stderr)
            return 1
        
        print(f"Building {len(documents)} document(s)...\n")
        failures = []
        for doc in documents:
            print(f"\n{'='*60}")
            print(f"Building: {doc.relative_to(repo_root)}")
            print('='*60)
            
            if doc.name == '00_introduction':
                result = build_book(doc)
            else:
                result = build_paper(doc)
            
            if result != 0:
                failures.append(doc)
        
        if failures:
            print(f"\n{len(failures)} build(s) failed:")
            for doc in failures:
                print(f"  ✗ {doc.relative_to(repo_root)}")
            return 1
        
        print(f"\n✓ All {len(documents)} documents built successfully")
        return 0
    
    elif args.target:
        # Build specific target
        target_path = repo_root / args.target
        if not target_path.exists():
            print(f"Error: Target not found: {args.target}", file=sys.stderr)
            return 1
        
        if target_path.name == '00_introduction':
            return build_book(target_path)
        else:
            return build_paper(target_path)
    
    else:
        # Build current directory
        cwd = Path.cwd()
        
        # Check if we're in a book directory
        if cwd.name == '00_introduction' or (cwd / 'parts' / 'parts').exists():
            return build_book(cwd)
        
        # Check if we're in a paper directory
        entry_file = cwd / f"{cwd.name}.tex"
        if entry_file.exists():
            return build_paper(cwd)
        
        print("Error: Current directory is not a buildable document", file=sys.stderr)
        print("Run from a document directory or specify a target", file=sys.stderr)
        return 1
