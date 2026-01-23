from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, write_text
from .layouts import get_layout, stage_dir


def format_chapter_title(raw: str) -> str:
    """Format a chapter folder name into a human-readable title (same rules as section titles)."""
    import re
    # Strip numeric prefix if present (e.g., "01_")
    text = re.sub(r'^\d+_', '', raw)
    
    # Replace hyphens and underscores with spaces
    text = text.replace('-', ' ').replace('_', ' ')
    
    # Book-style connectors that should be lowercase (unless first word)
    connectors = {'vs', 'and', 'or', 'of', 'in', 'on', 'for', 'to', 'the', 'a', 'an'}
    
    # Apply book-style capitalization
    words = text.split()
    formatted_words = []
    
    for i, word in enumerate(words):
        word_lower = word.lower()
        is_first = (i == 0)
        
        if word.isupper() and len(word) >= 1:
            formatted_words.append(word)
        elif word.isdigit():
            formatted_words.append(word)
        elif len(word) <= 2 and word.islower() and word.isalpha() and word_lower not in connectors:
            formatted_words.append(word.upper())
        elif is_first:
            formatted_words.append(word.capitalize())
        elif word_lower in connectors:
            formatted_words.append(word_lower)
        else:
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)


def cmd_ns(args) -> int:
    """Create a numbered chapter within a part of the introduction book."""
    repo_root = find_repo_root()
    layout_name = get_layout(repo_root)
    intro_dir = stage_dir(layout_name, "introduction")
    if not intro_dir:
        die("Introduction stage is not defined for this layout.")

    intro_root = repo_root / intro_dir
    if not intro_root.exists():
        die(f"Introduction directory does not exist: {intro_dir}")

    # Enforce new parts/parts/ structure only - no backward compatibility
    parts_dir = intro_root / "parts"
    parts_root = parts_dir / "parts"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory. Run 'tex-repo fix' to repair structure.")
    
    parts_root.mkdir(parents=True, exist_ok=True)

    # Determine target part
    part_spec = getattr(args, "part", None)
    if part_spec:
        # User specified a part - find it
        import re
        # Try to match as a number or as a part name
        if part_spec.isdigit():
            # User gave a number like "1" or "01"
            part_num = int(part_spec)
            part_prefix = f"{part_num:02d}"
            # Find part with this prefix
            target_part = None
            for item in parts_root.iterdir():
                if item.is_dir() and item.name.startswith(f"{part_prefix}_"):
                    target_part = item
                    break
            if not target_part:
                die(f"Part {part_prefix}_ not found in {parts_root.relative_to(repo_root)}")
        else:
            # User gave a name - find matching part
            target_part = None
            for item in parts_root.iterdir():
                if item.is_dir():
                    match = re.match(r'^\d{2}_(.+)$', item.name)
                    if match and match.group(1) == part_spec:
                        target_part = item
                        break
            if not target_part:
                die(f"Part '{part_spec}' not found in {parts_root.relative_to(repo_root)}")
    else:
        # Default to 01_part-1, create if missing
        target_part = parts_root / "01_part-1"
        if not target_part.exists():
            target_part.mkdir(parents=True, exist_ok=True)
            part_tex = target_part / "part.tex"
            write_text(part_tex, "\\part{Part 1}\n\n% Optional part introduction text goes here.\n")

    # Ensure part.tex exists
    part_tex = target_part / "part.tex"
    if not part_tex.exists():
        # Format part title from folder name
        import re
        match = re.match(r'^\d{2}_(.+)$', target_part.name)
        part_name = match.group(1) if match else target_part.name
        part_title = format_chapter_title(part_name)
        write_text(part_tex, f"\\part{{{part_title}}}\n\n% Optional part introduction text goes here.\n")

    # Create chapter inside the part
    chapters_dir = target_part / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    prefix = next_prefix(chapters_dir)
    if prefix == "00":
        prefix = "01"
    chapter_path = chapters_dir / f"{prefix}_{args.section_name}"
    if chapter_path.exists():
        die(f"Chapter already exists: {chapter_path.relative_to(repo_root)}")

    chapter_path.mkdir(parents=True, exist_ok=True)
    chapter_num = int(prefix)

    # Create chapter.tex with \chapter command and optional intro text
    chapter_tex = chapter_path / "chapter.tex"
    chapter_title = format_chapter_title(args.section_name)
    chapter_content = f"\\chapter{{{chapter_title}}}\n\n% Chapter introduction (prologue) goes here.\n% This text appears before the sections.\n\n"
    write_text(chapter_tex, chapter_content)

    # Create subsection files 1-1.tex through 1-10.tex
    for i in range(1, 11):
        subsection = chapter_path / f"{chapter_num}-{i}.tex"
        if not subsection.exists():
            write_text(subsection, f"\\section{{Section {i}}}\n\n% Content for section {i}\n")

    print(f"Created chapter: {chapter_path.relative_to(repo_root)}")
    return 0


def cmd_npart(args) -> int:
    """Create a new part in the introduction book."""
    repo_root = find_repo_root()
    layout_name = get_layout(repo_root)
    intro_dir = stage_dir(layout_name, "introduction")
    if not intro_dir:
        die("Introduction stage is not defined for this layout.")

    intro_root = repo_root / intro_dir
    if not intro_root.exists():
        die(f"Introduction directory does not exist: {intro_dir}")

    # Enforce new parts/parts/ structure
    parts_dir = intro_root / "parts"
    parts_root = parts_dir / "parts"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory. Run 'tex-repo fix' to repair structure.")
    
    parts_root.mkdir(parents=True, exist_ok=True)

    # Get next part number
    prefix = next_prefix(parts_root)
    if prefix == "00":
        prefix = "01"
    
    part_path = parts_root / f"{prefix}_{args.part_name}"
    if part_path.exists():
        die(f"Part already exists: {part_path.relative_to(repo_root)}")

    part_path.mkdir(parents=True, exist_ok=True)
    
    # Create part.tex with \part command
    part_tex = part_path / "part.tex"
    part_title = format_chapter_title(args.part_name)
    write_text(part_tex, f"\\part{{{part_title}}}\n\n% Optional part introduction text goes here.\n")
    
    # Create empty chapters directory
    chapters_dir = part_path / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Created part: {part_path.relative_to(repo_root)}")
    return 0
