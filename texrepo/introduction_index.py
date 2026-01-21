"""
Generate the sections index file for the Introduction book.

This module creates build/sections_index.tex which lists all sections
and their subsection files in numeric order.
"""
from pathlib import Path
import re


def generate_introduction_index(intro_dir: Path) -> Path:
    r"""
    Generate build/sections_index.tex for the Introduction book.
    
    Scans intro_dir/sections/ for numbered section folders (01_name, 02_name, etc.)
    and creates a LaTeX file that includes all subsection files in order.
    
    Args:
        intro_dir: Path to 00_introduction directory
        
    Returns:
        Path to the generated sections_index.tex file
        
    The generated file contains:
    - \section{...} headers for each section folder
    - \input{...} commands for each subsection file (S-K.tex)
    """
    sections_dir = intro_dir / "sections"
    build_dir = intro_dir / "build"
    output_file = build_dir / "sections_index.tex"
    
    # Ensure build directory exists
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate the index file header
    lines = []
    lines.append("% Auto-generated section index for Introduction book")
    lines.append("% DO NOT EDIT - this file is regenerated on each build")
    lines.append("")
    
    if not sections_dir.exists():
        # No sections directory - write minimal file
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
        # Add section header
        # Convert underscores to spaces and title-case the name
        display_name = section_name.replace('_', ' ')
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
            rel_path = tex_file.relative_to(intro_dir)
            # Use forward slashes for LaTeX
            latex_path = str(rel_path).replace('\\', '/')
            lines.append(f"\\input{{{latex_path}}}")
        
        lines.append("")
    
    # Write the file
    output_file.write_text('\n'.join(lines) + '\n')
    return output_file
