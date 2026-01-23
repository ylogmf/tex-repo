"""
Generate index files for the Introduction book.

This module creates:
- build/chapters_index.tex which includes part.tex and chapter.tex files (structural spine)
- build/sections_index.tex which includes chapter prologues and section content files (content spine)

The introduction book uses real LaTeX \\part and \\chapter commands.
"""
from pathlib import Path
import re
import sys


def format_title(raw: str) -> str:
    """
    Format a folder name into a human-readable title for LaTeX display.
    
    Applies book-style capitalization rules:
    1. Strip numeric prefix if present (e.g., "01_")
    2. Replace hyphens and underscores with spaces
    3. Apply book-style capitalization:
       - First word is always capitalized
       - Connector words (vs, and, or, of, in, on, for, to, the, a, an) are lowercase unless first
       - All-uppercase words (acronyms) are preserved
       - Short lowercase tokens (1-2 chars) treated as acronyms and uppercased, unless they are connectors
       - All other words are capitalized
       - Numeric tokens are preserved as-is
    
    Examples:
        "section-1" → "Section 1"
        "np_vs_p" → "NP vs P"
        "law_of_motion" → "Law of Motion"
        "in_the_beginning" → "In the Beginning"
    
    Args:
        raw: Raw folder name (with or without numeric prefix)
        
    Returns:
        Formatted title string
    """
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
        
        # Check if this is an all-uppercase acronym in the original
        if word.isupper() and len(word) >= 1:
            # Preserve acronyms (e.g., "NP", "P", "AI", "HTTP")
            formatted_words.append(word)
        elif word.isdigit():
            # Preserve numbers as-is
            formatted_words.append(word)
        elif len(word) <= 2 and word.islower() and word.isalpha() and word_lower not in connectors:
            # Short lowercase words that aren't connectors: likely acronyms (e.g., "np" → "NP")
            formatted_words.append(word.upper())
        elif is_first:
            # First word: always capitalize
            formatted_words.append(word.capitalize())
        elif word_lower in connectors:
            # Connector word (not first): lowercase
            formatted_words.append(word_lower)
        else:
            # Regular word: capitalize
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)


def die(msg: str):
    """Print error and exit."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def generate_chapters_index(intro_dir: Path) -> Path:
    """
    Generate build/chapters_index.tex for the Introduction book.
    
    This file includes part.tex and chapter.tex files to establish the 
    structural spine of the book with real \\part and \\chapter commands.
    
    Args:
        intro_dir: Path to 00_introduction directory
        
    Returns:
        Path to the generated chapters_index.tex file
    """
    # Enforce new parts/parts/ structure only - no backward compatibility
    parts_dir = intro_dir / "parts"
    parts_root = parts_dir / "parts"
    appendix_dir = parts_dir / "appendix"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory at {parts_dir}")
    
    build_dir = intro_dir / "build"
    output_file = build_dir / "chapters_index.tex"
    
    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate the index file
    lines = []
    lines.append("% Auto-generated chapter index for Introduction book")
    lines.append("% DO NOT EDIT - this file is regenerated on each build")
    lines.append("% Contains structural spine: \\part and \\chapter commands")
    lines.append("")
    
    if not parts_root.exists() or not any(parts_root.iterdir()):
        # No parts yet - write minimal file
        output_file.write_text('\n'.join(lines) + '\n')
        return output_file
    
    # Find all part folders matching NN_<name>
    part_pattern = re.compile(r'^(\d{2})_(.+)$')
    parts = []
    
    for item in parts_root.iterdir():
        if not item.is_dir():
            continue
        match = part_pattern.match(item.name)
        if match:
            part_num = int(match.group(1))
            parts.append((part_num, item))
    
    # Sort by part number
    parts.sort(key=lambda x: x[0])
    
    for part_num, part_dir in parts:
        # Include part.tex (contains \part{...} command)
        part_tex = part_dir / "part.tex"
        if part_tex.exists():
            latex_path = f"parts/parts/{part_dir.name}/part.tex"
            lines.append(f"\\input{{{latex_path}}}")
            lines.append("")
        
        # Find all chapters in this part
        chapters_dir = part_dir / "chapters"
        if not chapters_dir.exists():
            continue
        
        chapter_pattern = re.compile(r'^(\d{2})_(.+)$')
        chapters = []
        
        for item in chapters_dir.iterdir():
            if not item.is_dir():
                continue
            match = chapter_pattern.match(item.name)
            if match:
                chapter_num = int(match.group(1))
                chapters.append((chapter_num, item))
        
        # Sort by chapter number
        chapters.sort(key=lambda x: x[0])
        
        for chapter_num, chapter_dir in chapters:
            # Include chapter.tex (contains \chapter{...} command and optional prologue)
            chapter_tex = chapter_dir / "chapter.tex"
            if chapter_tex.exists():
                latex_path = f"parts/parts/{part_dir.name}/chapters/{chapter_dir.name}/chapter.tex"
                lines.append(f"\\input{{{latex_path}}}")
                lines.append("")
    
    # Check for appendix directory
    if appendix_dir.exists() and appendix_dir.is_dir():
        # Find all .tex files in appendix directory
        appendix_files = sorted([f for f in appendix_dir.iterdir() if f.suffix == '.tex' and f.is_file()])
        
        if appendix_files:
            # Add appendix section
            lines.append("% Appendix section")
            lines.append("\\appendix")
            lines.append("")
            
            for appendix_file in appendix_files:
                latex_path = f"parts/appendix/{appendix_file.name}"
                lines.append(f"\\input{{{latex_path}}}")
            
            lines.append("")
    
    # Write the file
    output_file.write_text('\n'.join(lines) + '\n')
    return output_file


def generate_introduction_index(intro_dir: Path) -> Path:
    r"""
    Generate build/sections_index.tex for the Introduction book.
    
    This is the content spine. It includes:
    - Frontmatter files
    - For each chapter: chapter.tex (prologue) followed by section files (1-*.tex)
    - Appendix files
    - Backmatter files
    
    Args:
        intro_dir: Path to 00_introduction directory
        
    Returns:
        Path to the generated sections_index.tex file
        
    The generated file contains:
    - Frontmatter includes (title, preface, how_to_read, toc)
    - For each part/chapter: chapter.tex followed by section files in order
    - \appendix and appendix includes if parts/appendix/ exists
    - Backmatter includes (scope_limits, closing_notes)
    """
    # Enforce new parts/parts/ structure only - no backward compatibility
    parts_dir = intro_dir / "parts"
    parts_root = parts_dir / "parts"
    appendix_dir = parts_dir / "appendix"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory at {parts_dir}")
    
    build_dir = intro_dir / "build"
    output_file = build_dir / "sections_index.tex"
    
    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate the index file header
    lines = []
    lines.append("% Auto-generated section index for Introduction book")
    lines.append("% DO NOT EDIT - this file is regenerated on each build")
    lines.append("% Contains content spine: chapter prologues and section files")
    lines.append("")
    
    # Include frontmatter at the start
    for fname in ["title", "preface", "how_to_read", "toc"]:
        lines.append(f"\\input{{parts/frontmatter/{fname}}}")
    lines.append("")
    
    if not parts_root.exists() or not any(parts_root.iterdir()):
        # No parts directory - write minimal file with frontmatter/backmatter
        for fname in ["scope_limits", "closing_notes"]:
            lines.append(f"\\input{{parts/backmatter/{fname}}}")
        lines.append("")
        output_file.write_text('\n'.join(lines) + '\n')
        return output_file
    
    # Find all part folders matching NN_<name>
    part_pattern = re.compile(r'^(\d{2})_(.+)$')
    parts = []
    
    for item in parts_root.iterdir():
        if not item.is_dir():
            continue
        match = part_pattern.match(item.name)
        if match:
            part_num = int(match.group(1))
            parts.append((part_num, item))
    
    # Sort by part number
    parts.sort(key=lambda x: x[0])
    
    for part_num, part_dir in parts:
        # Find all chapters in this part
        chapters_dir = part_dir / "chapters"
        if not chapters_dir.exists():
            continue
        
        chapter_pattern = re.compile(r'^(\d{2})_(.+)$')
        chapters = []
        
        for item in chapters_dir.iterdir():
            if not item.is_dir():
                continue
            match = chapter_pattern.match(item.name)
            if match:
                chapter_num = int(match.group(1))
                chapters.append((chapter_num, item))
        
        # Sort by chapter number
        chapters.sort(key=lambda x: x[0])
        
        for chapter_num, chapter_dir in chapters:
            # Include chapter.tex first (contains \chapter and optional prologue)
            chapter_tex = chapter_dir / "chapter.tex"
            if chapter_tex.exists():
                latex_path = f"parts/parts/{part_dir.name}/chapters/{chapter_dir.name}/chapter.tex"
                lines.append(f"\\input{{{latex_path}}}")
                lines.append("")
            
            # Find all section files N-K.tex where N matches chapter_num
            section_pattern = re.compile(rf'^({chapter_num})-(\d+)\.tex$')
            sections = []
            
            for tex_file in chapter_dir.iterdir():
                if not tex_file.is_file():
                    continue
                match = section_pattern.match(tex_file.name)
                if match:
                    section_num = int(match.group(2))
                    sections.append((section_num, tex_file))
            
            # Sort by section number
            sections.sort(key=lambda x: x[0])
            
            # Add input commands for section files
            for _, tex_file in sections:
                # Path relative to 00_introduction.tex
                latex_path = f"parts/parts/{part_dir.name}/chapters/{chapter_dir.name}/{tex_file.name}".replace('\\', '/')
                lines.append(f"\\input{{{latex_path}}}")
            
            lines.append("")
    
    # Check for appendix directory
    if appendix_dir.exists() and appendix_dir.is_dir():
        # Find all .tex files in appendix directory
        appendix_files = sorted([f for f in appendix_dir.iterdir() if f.suffix == '.tex' and f.is_file()])
        
        if appendix_files:
            # Add appendix section
            lines.append("% Appendix section")
            lines.append("\\appendix")
            lines.append("")
            
            for appendix_file in appendix_files:
                latex_path = f"parts/appendix/{appendix_file.name}"
                lines.append(f"\\input{{{latex_path}}}")
            
            lines.append("")
    
    # Include backmatter at the end
    for fname in ["scope_limits", "closing_notes"]:
        lines.append(f"\\input{{parts/backmatter/{fname}}}")
    lines.append("")
    
    # Write the file
    output_file.write_text('\n'.join(lines) + '\n')
    return output_file
