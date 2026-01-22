"""
Generate index files for the Introduction book.

This module creates:
- build/sections_index.tex which lists all sections with formatted titles and their subsection files
- build/chapters_index.tex which lists chapter entry files in numeric order
"""
from pathlib import Path
import re
import sys


def format_section_title(raw: str) -> str:
    """
    Format a section folder name into a human-readable title for LaTeX display.
    
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
        raw: Raw section folder name (with or without numeric prefix)
        
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


def generate_introduction_index(intro_dir: Path) -> Path:
    r"""
    Generate build/sections_index.tex for the Introduction book.
    
    Scans intro_dir/parts/sections/ for numbered section folders (01_name, 02_name, etc.) 
    and creates a LaTeX file that includes all subsection files in order with formatted titles.
    
    Args:
        intro_dir: Path to 00_introduction directory
        
    Returns:
        Path to the generated sections_index.tex file
        
    The generated file contains:
    - Frontmatter includes (title, preface, how_to_read, toc)
    - \section{...} headers for each section folder (using book-style formatting or title.tex override)
    - \input{...} commands for each subsection file (S-K.tex)
    - \appendix and appendix includes if parts/appendix/ exists
    - Backmatter includes (scope_limits, closing_notes)
    """
    # Enforce new parts/ structure only - no backward compatibility
    parts_dir = intro_dir / "parts"
    sections_dir = parts_dir / "sections"
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
    lines.append("")
    
    # Include frontmatter at the start
    for fname in ["title", "preface", "how_to_read", "toc"]:
        lines.append(f"\\input{{parts/frontmatter/{fname}}}")
    lines.append("")
    
    if not sections_dir.exists():
        # No sections directory - write minimal file with frontmatter/backmatter
        for fname in ["scope_limits", "closing_notes"]:
            lines.append(f"\\input{{parts/backmatter/{fname}}}")
        lines.append("")
        output_file.write_text('\n'.join(lines) + '\n')
        return output_file
    
    # Find all section folders matching NN_<name>
    section_pattern = re.compile(r'^(\d{2})_(.+)$')
    sections = []
    
    for item in sections_dir.iterdir():
        if not item.is_dir():
            continue
        match = section_pattern.match(item.name)
        if match:
            section_num = int(match.group(1))
            section_name = match.group(2)
            sections.append((section_num, section_name, item))
    
    # Sort by section number
    sections.sort(key=lambda x: x[0])
    
    for section_num, section_name, section_dir in sections:
        # Check for title override file (for mathematical notation, etc.)
        title_override_file = section_dir / "title.tex"
        if title_override_file.exists() and title_override_file.is_file():
            title_content = title_override_file.read_text(encoding='utf-8').strip()
            if title_content:
                # Validate: reject overrides containing structural commands
                structural_commands = [r'\\section', r'\\subsection', r'\\chapter', r'\\input', r'\\include']
                contains_structural = any(re.search(cmd, title_content) for cmd in structural_commands)
                
                if contains_structural:
                    # Invalid override: emit warning and fall back
                    print(f"Warning: title.tex in section '{section_dir.name}' contains structural commands; ignoring override",
                          file=sys.stderr)
                    display_name = format_section_title(section_name)
                else:
                    # Valid override: use content directly
                    display_name = title_content
            else:
                # Empty override file: fall back to formatted name
                display_name = format_section_title(section_name)
        else:
            # No override: use formatted folder name
            display_name = format_section_title(section_name)
        
        lines.append(f"\\section{{{display_name}}}")
        lines.append("")
        
        # Find all subsection files S-K.tex where S matches section_num
        subsection_pattern = re.compile(rf'^({section_num})-(\d+)\.tex$')
        subsections = []
        
        for tex_file in section_dir.iterdir():
            if not tex_file.is_file():
                continue
            match = subsection_pattern.match(tex_file.name)
            if match:
                subsection_num = int(match.group(2))
                subsections.append((subsection_num, tex_file))
        
        # Sort by subsection number
        subsections.sort(key=lambda x: x[0])
        
        # Add input commands
        for _, tex_file in subsections:
            # Path relative to 00_introduction.tex
            latex_path = f"parts/sections/{section_dir.name}/{tex_file.name}".replace('\\', '/')
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


def generate_chapters_index(intro_dir: Path) -> Path:
    """Generate build/chapters_index.tex listing chapter.tex files in order."""
    # Enforce new parts/ structure only - no backward compatibility
    parts_dir = intro_dir / "parts"
    sections_dir = parts_dir / "sections"
    appendix_dir = parts_dir / "appendix"
    
    if not parts_dir.exists():
        die(f"Introduction must have parts/ subdirectory at {parts_dir}")
    
    build_dir = intro_dir / "build"
    output_file = build_dir / "chapters_index.tex"

    build_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "% Auto-generated chapter include list for Introduction book",
        "% DO NOT EDIT - regenerated on each build",
        "",
    ]

    if not sections_dir.exists():
        output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return output_file

    section_pattern = re.compile(r"^(\d{2})_(.+)$")
    sections = []

    for item in sections_dir.iterdir():
        if not item.is_dir():
            continue
        match = section_pattern.match(item.name)
        if match:
            section_num = int(match.group(1))
            sections.append((section_num, item))

    sections.sort(key=lambda x: x[0])

    for section_num, section_dir in sections:
        chapter_file = section_dir / "chapter.tex"
        if chapter_file.exists():
            latex_path = f"parts/sections/{section_dir.name}/chapter.tex"
            lines.append(f"\\input{{{latex_path}}}")

    # Check for appendix directory
    if appendix_dir.exists() and appendix_dir.is_dir():
        # Find all .tex files in appendix directory
        appendix_files = sorted([f for f in appendix_dir.iterdir() if f.suffix == '.tex' and f.is_file()])
        
        if appendix_files:
            # Add appendix section
            lines.append("")
            lines.append("% Appendix section")
            lines.append("\\appendix")
            lines.append("")
            
            for appendix_file in appendix_files:
                latex_path = f"parts/appendix/{appendix_file.name}"
                lines.append(f"\\input{{{latex_path}}}")

    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_file
