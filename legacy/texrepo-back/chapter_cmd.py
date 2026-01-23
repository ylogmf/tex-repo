"""tex-repo chapter command - create a new chapter inside a part."""
from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, write_text
from .section_cmd import format_chapter_title


def find_part_root(start: Path) -> Path | None:
    """Find the part root directory by looking for part.tex file or chapters/ subdirectory."""
    d = start.resolve()
    for cur in [d, *d.parents]:
        # Check if this is a part directory (has part.tex or chapters/)
        if (cur / "part.tex").is_file():
            return cur
        if (cur / "chapters").is_dir():
            return cur
        # Stop at repo root
        if (cur / ".paperrepo").is_file():
            break
    return None


def cmd_chapter(args) -> int:
    """Create a new chapter inside a part directory."""
    repo_root = find_repo_root()
    
    # Find the part root from current directory
    part_root = find_part_root(Path.cwd())
    if not part_root:
        die("Must run 'tex-repo chapter' inside a part directory (must have part.tex or chapters/)")
    
    # Validate we're inside a part (has part.tex)
    if not (part_root / "part.tex").exists():
        die(f"Part directory must have part.tex file: {part_root.relative_to(repo_root)}")
    
    # Ensure chapters/ directory exists
    chapters_dir = part_root / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    # Get next chapter number - find max NN_*.tex in chapters/
    max_n = 0
    for child in chapters_dir.iterdir():
        if child.is_file() and child.suffix == ".tex":
            name = child.stem
            if len(name) >= 3 and name[:2].isdigit() and name[2] == "_":
                n = int(name[:2])
                max_n = max(max_n, n)
    
    prefix = f"{max_n + 1:02d}"
    if prefix == "00":
        prefix = "01"
    
    title = args.title
    
    # Create slug from title
    import re
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    
    chapter_file = chapters_dir / f"{prefix}_{slug}.tex"
    if chapter_file.exists():
        die(f"Chapter already exists: {chapter_file.relative_to(repo_root)}")
    
    # Create chapter.tex with \chapter command
    write_text(chapter_file, f"\\chapter{{{title}}}\n\n% Chapter content goes here.\n")
    
    print(f"✅ Created chapter: {chapter_file.relative_to(repo_root)}")
    return 0
