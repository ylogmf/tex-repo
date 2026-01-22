from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, write_text
from .layouts import get_layout, stage_dir


def cmd_ns(args) -> int:
    """Create a numbered section within the introduction book (00_introduction/parts/sections/) with 10 subsection files."""
    repo_root = find_repo_root()
    layout_name = get_layout(repo_root)
    intro_dir = stage_dir(layout_name, "introduction")
    if not intro_dir:
        die("Introduction stage is not defined for this layout.")

    intro_root = repo_root / intro_dir
    if not intro_root.exists():
        die(f"Introduction directory does not exist: {intro_dir}")

    # Enforce new parts/sections/ structure only - no backward compatibility
    parts_dir = intro_root / "parts"
    sections_root = parts_dir / "sections"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory. Run 'tex-repo fix' to repair structure.")
    
    sections_root.mkdir(parents=True, exist_ok=True)

    prefix = next_prefix(sections_root)
    if prefix == "00":
        prefix = "01"
    section_path = sections_root / f"{prefix}_{args.section_name}"
    if section_path.exists():
        die(f"Section already exists: {section_path.relative_to(repo_root)}")

    section_path.mkdir(parents=True, exist_ok=True)
    section_num = int(prefix)

    # Create chapter file that includes subsections in order
    chapter_path = section_path / "chapter.tex"
    if not chapter_path.exists():
        # chapter.tex just includes the subsections - titles are generated in sections_index.tex
        include_lines = []
        for i in range(1, 11):
            include_lines.append(f"\\input{{parts/sections/{prefix}_{args.section_name}/{section_num}-{i}.tex}}")
        include_lines.append("")
        write_text(chapter_path, "\n".join(include_lines))

    for i in range(1, 11):
        subsection = section_path / f"{section_num}-{i}.tex"
        if not subsection.exists():
            write_text(subsection, f"% Section {section_num}, subsection {i}\n")

    return 0
