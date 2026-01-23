"""Validation commands: status, guard, fix."""

import re
import sys
from pathlib import Path
from typing import List
from .utils import find_repo_root, ensure_dir, write_file, slug_to_title


class Violation:
    """Represents a guard violation."""
    
    def __init__(self, code: str, path: Path, message: str):
        self.code = code
        self.path = path
        self.message = message
    
    def format_guard(self) -> str:
        """Format for guard command (tab-separated)."""
        return f"{self.code}\t{self.path}\t{self.message}"
    
    def format_status(self) -> str:
        """Format for status command (human-readable)."""
        return f"[{self.code}] {self.path}: {self.message}"
    
    def __lt__(self, other):
        """Sort by code then path."""
        if self.code != other.code:
            return self.code < other.code
        return str(self.path) < str(other.path)


def validate_book(repo_root: Path) -> List[Violation]:
    """Validate book (00_introduction) structure."""
    violations = []
    
    book_root = repo_root / '00_introduction'
    
    # BOOK_ROOT_MISSING
    if not book_root.is_dir():
        violations.append(Violation(
            'BOOK_ROOT_MISSING',
            book_root,
            '00_introduction/ missing'
        ))
        return violations  # Can't check further
    
    # BOOK_ENTRY_MISSING
    entry_file = book_root / '00_introduction.tex'
    if not entry_file.is_file():
        violations.append(Violation(
            'BOOK_ENTRY_MISSING',
            entry_file,
            'Missing book entry file'
        ))
    
    # BOOK_ENTRY_NOT_UNIQUE (check for multiple .tex files at root)
    tex_files = list(book_root.glob('*.tex'))
    if len(tex_files) > 1:
        violations.append(Violation(
            'BOOK_ENTRY_NOT_UNIQUE',
            book_root,
            f'Multiple .tex files found: {", ".join(f.name for f in tex_files)}'
        ))
    
    # BOOK_BUILD_DIR_MISSING
    build_dir = book_root / 'build'
    if not build_dir.is_dir():
        violations.append(Violation(
            'BOOK_BUILD_DIR_MISSING',
            build_dir,
            'build/ directory missing'
        ))
    
    # BOOK_PARTS_DIR_MISSING
    parts_dir = book_root / 'parts'
    if not parts_dir.is_dir():
        violations.append(Violation(
            'BOOK_PARTS_DIR_MISSING',
            parts_dir,
            'parts/ directory missing'
        ))
        return violations  # Can't check subtrees
    
    # BOOK_FRONTMATTER_DIR_MISSING
    if not (parts_dir / 'frontmatter').is_dir():
        violations.append(Violation(
            'BOOK_FRONTMATTER_DIR_MISSING',
            parts_dir / 'frontmatter',
            'parts/frontmatter/ directory missing'
        ))
    
    # BOOK_BACKMATTER_DIR_MISSING
    if not (parts_dir / 'backmatter').is_dir():
        violations.append(Violation(
            'BOOK_BACKMATTER_DIR_MISSING',
            parts_dir / 'backmatter',
            'parts/backmatter/ directory missing'
        ))
    
    # BOOK_PARTS_PARTS_DIR_MISSING
    parts_parts_dir = parts_dir / 'parts'
    if not parts_parts_dir.is_dir():
        violations.append(Violation(
            'BOOK_PARTS_PARTS_DIR_MISSING',
            parts_parts_dir,
            'parts/parts/ directory missing'
        ))
    else:
        # Validate parts structure
        violations.extend(validate_parts(parts_parts_dir))
    
    # Spine file validation
    if build_dir.is_dir():
        sections_index = build_dir / 'sections_index.tex'
        chapters_index = build_dir / 'chapters_index.tex'
        
        # BOOK_SECTIONS_INDEX_MISSING
        if not sections_index.is_file():
            violations.append(Violation(
                'BOOK_SECTIONS_INDEX_MISSING',
                sections_index,
                'build/sections_index.tex missing'
            ))
        else:
            # BOOK_SECTIONS_INDEX_SECTIONING_LEAK
            content = sections_index.read_text()
            if any(cmd in content for cmd in [r'\part', r'\chapter', r'\section']):
                violations.append(Violation(
                    'BOOK_SECTIONS_INDEX_SECTIONING_LEAK',
                    sections_index,
                    'sections_index.tex must not contain \\part, \\chapter, or \\section'
                ))
        
        # BOOK_CHAPTERS_INDEX_MISSING
        if not chapters_index.is_file():
            violations.append(Violation(
                'BOOK_CHAPTERS_INDEX_MISSING',
                chapters_index,
                'build/chapters_index.tex missing'
            ))
    
    # Entry file validation
    if entry_file.is_file():
        violations.extend(validate_book_entry(entry_file))
    
    return violations


def validate_parts(parts_parts_dir: Path) -> List[Violation]:
    """Validate parts structure."""
    violations = []
    
    # Get all part directories
    part_dirs = [d for d in parts_parts_dir.iterdir() if d.is_dir()]
    
    # BOOK_PART_DIR_INVALID_NAME
    valid_parts = []
    for part_dir in part_dirs:
        if not re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*$', part_dir.name):
            violations.append(Violation(
                'BOOK_PART_DIR_INVALID_NAME',
                part_dir,
                f'Part directory name invalid: {part_dir.name}'
            ))
        else:
            valid_parts.append(part_dir)
    
    # Sort and check numbering
    valid_parts.sort(key=lambda p: p.name)
    
    if valid_parts:
        # BOOK_PART_NUMBER_GAP
        numbers = [int(p.name[:2]) for p in valid_parts]
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            violations.append(Violation(
                'BOOK_PART_NUMBER_GAP',
                parts_parts_dir,
                f'Part numbering not contiguous: {numbers} (expected {expected})'
            ))
        
        # BOOK_PART_DUPLICATE_SLUG
        slugs = ['_'.join(p.name.split('_')[1:]) for p in valid_parts]
        if len(slugs) != len(set(slugs)):
            violations.append(Violation(
                'BOOK_PART_DUPLICATE_SLUG',
                parts_parts_dir,
                'Duplicate part slugs detected'
            ))
    
    # Check each part's required files
    for part_dir in valid_parts:
        # BOOK_PART_TEX_MISSING
        if not (part_dir / 'part.tex').is_file():
            violations.append(Violation(
                'BOOK_PART_TEX_MISSING',
                part_dir / 'part.tex',
                'part.tex missing'
            ))
        
        # BOOK_PART_CHAPTERS_DIR_MISSING
        chapters_dir = part_dir / 'chapters'
        if not chapters_dir.is_dir():
            violations.append(Violation(
                'BOOK_PART_CHAPTERS_DIR_MISSING',
                chapters_dir,
                'chapters/ directory missing'
            ))
        else:
            # Validate chapters within this part
            violations.extend(validate_chapters(part_dir, chapters_dir))
    
    return violations


def validate_chapters(part_dir: Path, chapters_dir: Path) -> List[Violation]:
    """Validate chapters structure within a part."""
    violations = []
    
    # Get all chapter files (NN_<slug>.tex)
    chapter_files = [f for f in chapters_dir.iterdir() 
                     if f.is_file() and f.suffix == '.tex']
    
    # BOOK_CHAPTER_DIR_INVALID_NAME (actually file invalid name)
    valid_chapters = []
    for chapter_file in chapter_files:
        if not re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*\.tex$', chapter_file.name):
            violations.append(Violation(
                'BOOK_CHAPTER_DIR_INVALID_NAME',
                chapter_file,
                f'Chapter filename invalid: {chapter_file.name}'
            ))
        else:
            valid_chapters.append(chapter_file)
    
    # Sort and check numbering
    valid_chapters.sort(key=lambda c: c.name)
    
    if valid_chapters:
        # BOOK_CHAPTER_NUMBER_GAP
        numbers = [int(c.name[:2]) for c in valid_chapters]
        expected = list(range(1, len(numbers) + 1))
        if numbers != expected:
            violations.append(Violation(
                'BOOK_CHAPTER_NUMBER_GAP',
                chapters_dir,
                f'Chapter numbering not contiguous in {part_dir.name}: {numbers} (expected {expected})'
            ))
        
        # BOOK_CHAPTER_DUPLICATE_SLUG
        slugs = [c.stem.split('_', 1)[1] if '_' in c.stem else c.stem 
                 for c in valid_chapters]
        if len(slugs) != len(set(slugs)):
            violations.append(Violation(
                'BOOK_CHAPTER_DUPLICATE_SLUG',
                chapters_dir,
                'Duplicate chapter slugs detected'
            ))
    
    return violations


def validate_book_entry(entry_file: Path) -> List[Violation]:
    """Validate book entry file content."""
    violations = []
    content = entry_file.read_text()
    
    # BOOK_ENTRY_MISSING_FRONTMATTER
    if r'\frontmatter' not in content:
        violations.append(Violation(
            'BOOK_ENTRY_MISSING_FRONTMATTER',
            entry_file,
            'Entry file missing \\frontmatter'
        ))
    
    # BOOK_ENTRY_MISSING_MAINMATTER
    if r'\mainmatter' not in content:
        violations.append(Violation(
            'BOOK_ENTRY_MISSING_MAINMATTER',
            entry_file,
            'Entry file missing \\mainmatter'
        ))
    
    # BOOK_ENTRY_MISSING_BACKMATTER
    if r'\backmatter' not in content:
        violations.append(Violation(
            'BOOK_ENTRY_MISSING_BACKMATTER',
            entry_file,
            'Entry file missing \\backmatter'
        ))
    
    # BOOK_ENTRY_SPINE_INCLUDE_MISSING
    has_sections = 'build/sections_index' in content
    has_chapters = 'build/chapters_index' in content
    if not has_sections or not has_chapters:
        violations.append(Violation(
            'BOOK_ENTRY_SPINE_INCLUDE_MISSING',
            entry_file,
            'Entry file missing spine includes'
        ))
    
    return violations


def validate_papers(repo_root: Path) -> List[Violation]:
    """Validate paper structures at repo root."""
    violations = []
    
    # Stage directories that should not be treated as papers
    STAGE_DIRS = {'01_process_regime', '02_function_application', '03_hypophysis'}
    
    # Find all paper directories (NN_<slug> pattern, not 00_introduction, not stage dirs)
    paper_dirs = []
    for item in repo_root.iterdir():
        if item.is_dir() and re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*$', item.name):
            if item.name != '00_introduction' and item.name not in STAGE_DIRS:
                paper_dirs.append(item)
    
    paper_dirs.sort(key=lambda p: p.name)
    
    # Check for duplicate slugs
    if paper_dirs:
        slugs = ['_'.join(p.name.split('_')[1:]) for p in paper_dirs]
        
        # PAPER_DUPLICATE_SLUG
        if len(slugs) != len(set(slugs)):
            violations.append(Violation(
                'PAPER_DUPLICATE_SLUG',
                repo_root,
                'Duplicate paper slugs detected'
            ))
    
    # Validate each paper
    for paper_dir in paper_dirs:
        violations.extend(validate_paper(paper_dir))
    
    return violations


def validate_paper(paper_dir: Path) -> List[Violation]:
    """Validate a single paper structure."""
    violations = []
    
    entry_name = f"{paper_dir.name}.tex"
    entry_file = paper_dir / entry_name
    
    # PAPER_ENTRY_MISSING
    if not entry_file.is_file():
        violations.append(Violation(
            'PAPER_ENTRY_MISSING',
            entry_file,
            'Paper entry file missing'
        ))
    
    # PAPER_ENTRY_NOT_UNIQUE
    tex_files = list(paper_dir.glob('*.tex'))
    if len(tex_files) > 1:
        violations.append(Violation(
            'PAPER_ENTRY_NOT_UNIQUE',
            paper_dir,
            f'Multiple .tex files found: {", ".join(f.name for f in tex_files)}'
        ))
    
    # PAPER_SECTIONS_DIR_MISSING
    sections_dir = paper_dir / 'sections'
    if not sections_dir.is_dir():
        violations.append(Violation(
            'PAPER_SECTIONS_DIR_MISSING',
            sections_dir,
            'sections/ directory missing'
        ))
    
    # PAPER_BUILD_DIR_MISSING
    build_dir = paper_dir / 'build'
    if not build_dir.is_dir():
        violations.append(Violation(
            'PAPER_BUILD_DIR_MISSING',
            build_dir,
            'build/ directory missing'
        ))
    
    # PAPER_REFS_MISSING
    refs_file = paper_dir / 'refs.bib'
    if not refs_file.is_file():
        violations.append(Violation(
            'PAPER_REFS_MISSING',
            refs_file,
            'refs.bib missing'
        ))
    
    return violations


def validate_repository(repo_root: Path) -> List[Violation]:
    """Validate entire repository structure."""
    violations = []
    
    # Validate book
    violations.extend(validate_book(repo_root))
    
    # Validate papers
    violations.extend(validate_papers(repo_root))
    
    # Sort violations
    violations.sort()
    
    return violations


def cmd_status(args):
    """
    Report repository structure violations.
    
    Exits 0 (informational only).
    """
    repo_root = find_repo_root()
    if repo_root is None:
        print("Error: Not in a tex-repo repository", file=sys.stderr)
        return 1
    
    violations = validate_repository(repo_root)
    
    if not violations:
        print("✓ No violations found")
        return 0
    
    print(f"Found {len(violations)} violation(s):\n")
    for violation in violations:
        print(violation.format_status())
    
    return 0


def cmd_guard(args):
    """
    Enforce repository invariants for CI.
    
    Output format: <CODE>\t<PATH>\t<MESSAGE>
    Exits non-zero if any violations found.
    """
    repo_root = find_repo_root()
    if repo_root is None:
        print("Error: Not in a tex-repo repository", file=sys.stderr)
        return 1
    
    violations = validate_repository(repo_root)
    
    if violations:
        for violation in violations:
            print(violation.format_guard())
        return 1
    
    return 0


def cmd_fix(args):
    """
    Create missing required structure.
    
    Never overwrites user content or renames directories.
    Safe to rerun.
    """
    repo_root = find_repo_root()
    if repo_root is None:
        print("Error: Not in a tex-repo repository", file=sys.stderr)
        return 1
    
    violations = validate_repository(repo_root)
    fixed_count = 0
    
    # Empty spine file templates
    SECTIONS_INDEX_TEMPLATE = "% Frontmatter sections index\n% This file is generated by tex-repo build\n"
    CHAPTERS_INDEX_TEMPLATE = "% Chapters index\n% This file is generated by tex-repo build\n"
    
    for violation in violations:
        code = violation.code
        path = violation.path
        
        # Fix missing directories
        if code in ['BOOK_BUILD_DIR_MISSING', 'BOOK_PARTS_DIR_MISSING',
                    'BOOK_FRONTMATTER_DIR_MISSING', 'BOOK_BACKMATTER_DIR_MISSING',
                    'BOOK_PARTS_PARTS_DIR_MISSING', 'BOOK_PART_CHAPTERS_DIR_MISSING',
                    'PAPER_SECTIONS_DIR_MISSING', 'PAPER_BUILD_DIR_MISSING']:
            if not path.exists():
                ensure_dir(path)
                print(f"Created directory: {path}")
                fixed_count += 1
        
        # Fix missing spine files
        elif code == 'BOOK_SECTIONS_INDEX_MISSING':
            if not path.exists():
                write_file(path, SECTIONS_INDEX_TEMPLATE)
                print(f"Created file: {path}")
                fixed_count += 1
        
        elif code == 'BOOK_CHAPTERS_INDEX_MISSING':
            if not path.exists():
                write_file(path, CHAPTERS_INDEX_TEMPLATE)
                print(f"Created file: {path}")
                fixed_count += 1
        
        # Fix missing part.tex
        elif code == 'BOOK_PART_TEX_MISSING':
            if not path.exists():
                part_name = path.parent.name.split('_', 1)[1] if '_' in path.parent.name else 'Part'
                title = slug_to_title(part_name)
                content = f"\\part{{{title}}}\n"
                write_file(path, content)
                print(f"Created file: {path}")
                fixed_count += 1
        
        # Fix missing refs.bib
        elif code == 'PAPER_REFS_MISSING':
            if not path.exists():
                write_file(path, '% References\n')
                print(f"Created file: {path}")
                fixed_count += 1
    
    if fixed_count == 0:
        print("No fixable violations found")
    else:
        print(f"\nFixed {fixed_count} issue(s)")
        print("Run 'tex-repo status' to check for remaining violations")
    
    return 0
