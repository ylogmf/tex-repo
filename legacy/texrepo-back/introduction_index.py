"""
Generate index files for the Introduction book.

This module creates:
- build/sections_index.tex: FRONTMATTER-ONLY spine (title, preface, TOC)
- build/chapters_index.tex: MAINMATTER spine (parts, chapters, sections, appendix, backmatter)

The introduction book uses real LaTeX \\part and \\chapter commands.

IMPORTANT: sections_index.tex must NOT contain any sectioning commands or mainmatter content.
This prevents duplicate TOC entries and wrong numbering (0.1, etc.) in frontmatter.
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
    
    This is the MAINMATTER spine. It includes:
    - part.tex files (\\part commands)
    - chapter.tex files (\\chapter commands and prologues)
    - section content files (1-*.tex)
    - appendix files (\\appendix and content)
    - backmatter files
    
    This file should be included in \\mainmatter.
    
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
    lines.append("% Auto-generated mainmatter index for Introduction book")
    lines.append("% DO NOT EDIT - this file is regenerated on each build")
    lines.append("% Contains mainmatter spine: \\part, \\chapter commands, section content, appendix, backmatter")
    lines.append("% Include this file in \\mainmatter")
    lines.append("")
    
    if not parts_root.exists() or not any(parts_root.iterdir()):
        # No parts yet - write minimal file with backmatter only
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


def generate_introduction_index(intro_dir: Path) -> Path:
    r"""
    Generate build/sections_index.tex for the Introduction book.
    
    This is the FRONTMATTER-ONLY spine. It includes ONLY:
    - Frontmatter navigation files (title, preface, how_to_read, toc)
    - NO chapter.tex files (those contain \chapter commands - mainmatter only!)
    - NO section content files (mainmatter only!)
    - NO appendix (mainmatter only!)
    - NO backmatter (moved to chapters_index.tex)
    
    This file should be included in \frontmatter.
    All mainmatter content (parts, chapters, sections, appendix, backmatter) 
    is in chapters_index.tex.
    
    Args:
        intro_dir: Path to 00_introduction directory
        
    Returns:
        Path to the generated sections_index.tex file
    """
    # Enforce new parts/parts/ structure only - no backward compatibility
    parts_dir = intro_dir / "parts"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory at {parts_dir}")
    
    build_dir = intro_dir / "build"
    output_file = build_dir / "sections_index.tex"
    
    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate the index file header
    lines = []
    lines.append("% Auto-generated frontmatter index for Introduction book")
    lines.append("% DO NOT EDIT - this file is regenerated on each build")
    lines.append("% Contains FRONTMATTER-ONLY: navigation pages (TOC, etc.)")
    lines.append("% NO chapters, sections, appendix, or backmatter here - those are in chapters_index.tex")
    lines.append("% Include this file in \\frontmatter")
    lines.append("")
    
    # Include ONLY frontmatter navigation files
    # These should NOT contain any \chapter, \section, or other sectioning commands
    for fname in ["title", "preface", "how_to_read", "toc"]:
        lines.append(f"\\input{{parts/frontmatter/{fname}}}")
    lines.append("")
    
    # Write the file
    content = '\n'.join(lines) + '\n'
    output_file.write_text(content)
    
    # VALIDATION: Ensure no forbidden sectioning commands in generated file
    _validate_frontmatter_only(output_file, content)
    
    return output_file


def _validate_frontmatter_only(filepath: Path, content: str) -> None:
    """
    Validate that sections_index.tex contains NO sectioning commands.
    
    This is a guardrail to prevent mainmatter content from leaking into frontmatter,
    which would cause duplicate TOC entries and wrong numbering (0.1, etc.).
    
    Args:
        filepath: Path to sections_index.tex for error messages
        content: Content of the file to validate
        
    Raises:
        SystemExit: If validation fails
    """
    # Forbidden sectioning commands that should never appear in frontmatter spine
    forbidden_commands = [
        r'\part{', r'\part[',
        r'\chapter{', r'\chapter[', r'\chapter*{',
        r'\section{', r'\section[', r'\section*{',
        r'\subsection{', r'\subsection[', r'\subsection*{',
        r'\subsubsection{', r'\subsubsection[', r'\subsubsection*{',
        r'\paragraph{', r'\paragraph[', r'\paragraph*{',
        r'\subparagraph{', r'\subparagraph[', r'\subparagraph*{',
        r'\appendix'
    ]
    
    errors = []
    for cmd in forbidden_commands:
        if cmd in content:
            errors.append(f"  - Found forbidden command: {cmd}")
    
    # Check for \input or \include of chapter/section content
    # Frontmatter should only include parts/frontmatter/* files
    input_pattern = re.compile(r'\\(?:input|include)\{([^}]+)\}')
    for match in input_pattern.finditer(content):
        path = match.group(1)
        # Allow only parts/frontmatter/* includes
        if not path.startswith('parts/frontmatter/'):
            errors.append(f"  - Found forbidden include: \\input{{{path}}} (only parts/frontmatter/* allowed)")
    
    # Check for \numberline in TOC (indicates numbered chapters/sections in frontmatter)
    if r'\numberline' in content:
        errors.append(f"  - Found \\numberline in TOC (indicates mainmatter content in frontmatter)")
    
    if errors:
        error_msg = f"\nERROR: {filepath} validation failed!\n"
        error_msg += "Frontmatter spine (sections_index.tex) must NOT contain mainmatter content.\n"
        error_msg += "This causes duplicate TOC entries and wrong numbering (0.1, etc.)\n\n"
        error_msg += "Violations found:\n"
        error_msg += '\n'.join(errors)
        error_msg += "\n\nAll chapters, sections, appendix, and backmatter belong in chapters_index.tex (mainmatter spine).\n"
        die(error_msg)
