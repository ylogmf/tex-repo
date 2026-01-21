from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, write_text
from .layouts import get_layout, stage_dir


def cmd_ns(args) -> int:
    """Create a numbered section within the introduction book (00_introduction/) with 10 subsection files."""
    repo_root = find_repo_root()
    layout_name = get_layout(repo_root)
    intro_dir = stage_dir(layout_name, "introduction")
    if not intro_dir:
        die("Introduction stage is not defined for this layout.")

    intro_root = repo_root / intro_dir
    if not intro_root.exists():
        die(f"Introduction directory does not exist: {intro_dir}")

    # Sections must live under sections/ subdirectory
    sections_root = intro_root / "sections"
    sections_root.mkdir(parents=True, exist_ok=True)

    prefix = next_prefix(sections_root)
    if prefix == "00":
        prefix = "01"
    section_path = sections_root / f"{prefix}_{args.section_name}"
    if section_path.exists():
        die(f"Section already exists: {section_path.relative_to(repo_root)}")

    section_path.mkdir(parents=True, exist_ok=True)
    section_num = int(prefix)
    for i in range(1, 11):
        subsection = section_path / f"{section_num}-{i}.tex"
        if not subsection.exists():
            write_text(subsection, f"% Section {section_num}, subsection {i}\n")

    return 0
