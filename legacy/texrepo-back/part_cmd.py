"""tex-repo part command - create a new part inside a book."""
from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, write_text
from .section_cmd import format_chapter_title


def find_book_root(start: Path) -> Path | None:
    """Find the book root directory by looking for parts/ directory or book-class .tex file."""
    d = start.resolve()
    for cur in [d, *d.parents]:
        # Check if this is a book directory (has parts/ subdirectory)
        if (cur / "parts").is_dir():
            return cur
        # Check if there's a book-class .tex file
        for tex_file in cur.glob("*.tex"):
            content = tex_file.read_text(encoding="utf-8")
            if r"\documentclass" in content and "book" in content:
                return cur
        # Stop at repo root
        if (cur / ".paperrepo").is_file():
            break
    return None


def cmd_part(args) -> int:
    """Create a new part inside a book directory."""
    repo_root = find_repo_root()
    
    # Find the book root from current directory
    book_root = find_book_root(Path.cwd())
    if not book_root:
        die("Must run 'tex-repo part' inside a book directory (must have parts/ or book-class .tex file)")
    
    # Ensure parts/ structure exists
    parts_dir = book_root / "parts"
    if not parts_dir.exists():
        die(f"Book directory must have parts/ subdirectory: {book_root.relative_to(repo_root)}")
    
    # Create parts/parts/ if needed
    parts_root = parts_dir / "parts"
    parts_root.mkdir(parents=True, exist_ok=True)
    
    # Get next part number
    prefix = next_prefix(parts_root)
    if prefix == "00":
        prefix = "01"
    
    title = args.title
    
    # Create slug from title
    import re
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    
    part_path = parts_root / f"{prefix}_{slug}"
    if part_path.exists():
        die(f"Part already exists: {part_path.relative_to(repo_root)}")
    
    part_path.mkdir(parents=True, exist_ok=True)
    
    # Create part.tex with \part command
    part_tex = part_path / "part.tex"
    part_title = format_chapter_title(slug)
    write_text(part_tex, f"\\part{{{title}}}\n\n% Optional part introduction text goes here.\n")
    
    # Create empty chapters directory
    chapters_dir = part_path / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Created part: {part_path.relative_to(repo_root)}")
    print(f"   Use 'tex-repo chapter' to add chapters")
    return 0
