"""Validators for structural invariants and guard codes."""

import re
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from .utils import get_numbered_dirs


@dataclass
class Violation:
    """Represents a structural invariant violation."""
    code: str
    path: str
    message: str
    
    def format(self) -> str:
        """Format as tab-separated guard output."""
        return f"{self.code}\t{self.path}\t{self.message}"


class BookValidator:
    """Validates book structure invariants."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.book_root = repo_root / '00_introduction'
        self.entry_file = self.book_root / '00_introduction.tex'
        self.parts_dir = self.book_root / 'parts'
        self.parts_parts_dir = self.parts_dir / 'parts'
        self.build_dir = self.book_root / 'build'
        self.sections_index = self.build_dir / 'sections_index.tex'
        self.chapters_index = self.build_dir / 'chapters_index.tex'
    
    def validate_all(self) -> List[Violation]:
        """Run all book validations."""
        violations = []
        violations.extend(self.validate_root_and_entry())
        violations.extend(self.validate_required_subtrees())
        violations.extend(self.validate_spine_files())
        violations.extend(self.validate_entry_inclusion())
        violations.extend(self.validate_parts())
        violations.extend(self.validate_chapters())
        violations.extend(self.validate_build_pollution())
        return violations
    
    def validate_root_and_entry(self) -> List[Violation]:
        """Validate book root and entry file."""
        violations = []
        
        if not self.book_root.is_dir():
            violations.append(Violation(
                'BOOK_ROOT_MISSING',
                str(self.book_root),
                '00_introduction/ missing'
            ))
            return violations  # Can't proceed
        
        if not self.entry_file.is_file():
            violations.append(Violation(
                'BOOK_ENTRY_MISSING',
                str(self.entry_file),
                'Missing book entry file'
            ))
        else:
            # Check for multiple .tex files
            tex_files = list(self.book_root.glob('*.tex'))
            if len(tex_files) > 1:
                violations.append(Violation(
                    'BOOK_ENTRY_NOT_UNIQUE',
                    str(self.book_root),
                    f'Multiple .tex files found: {[f.name for f in tex_files]}'
                ))
        
        if not self.build_dir.is_dir():
            violations.append(Violation(
                'BOOK_BUILD_DIR_MISSING',
                str(self.build_dir),
                'build/ directory missing'
            ))
        
        if not self.parts_dir.is_dir():
            violations.append(Violation(
                'BOOK_PARTS_DIR_MISSING',
                str(self.parts_dir),
                'parts/ directory missing'
            ))
        
        return violations
    
    def validate_required_subtrees(self) -> List[Violation]:
        """Validate required subdirectories."""
        violations = []
        
        frontmatter = self.parts_dir / 'frontmatter'
        if not frontmatter.is_dir():
            violations.append(Violation(
                'BOOK_FRONTMATTER_DIR_MISSING',
                str(frontmatter),
                'frontmatter/ directory missing'
            ))
        
        backmatter = self.parts_dir / 'backmatter'
        if not backmatter.is_dir():
            violations.append(Violation(
                'BOOK_BACKMATTER_DIR_MISSING',
                str(backmatter),
                'backmatter/ directory missing'
            ))
        
        if not self.parts_parts_dir.is_dir():
            violations.append(Violation(
                'BOOK_PARTS_PARTS_DIR_MISSING',
                str(self.parts_parts_dir),
                'parts/parts/ directory missing'
            ))
        
        # Check appendix if it exists
        appendix = self.parts_dir / 'appendix'
        if appendix.exists():
            if not appendix.is_dir():
                violations.append(Violation(
                    'BOOK_APPENDIX_INVALID',
                    str(appendix),
                    'appendix exists but is not a directory'
                ))
            else:
                for child in appendix.iterdir():
                    if not child.name.endswith('.tex'):
                        violations.append(Violation(
                            'BOOK_APPENDIX_INVALID',
                            str(child),
                            f'Invalid file in appendix: {child.name}'
                        ))
        
        return violations
    
    def validate_spine_files(self) -> List[Violation]:
        """Validate generated spine (index) files."""
        violations = []
        
        if not self.sections_index.is_file():
            violations.append(Violation(
                'BOOK_SECTIONS_INDEX_MISSING',
                str(self.sections_index),
                'sections_index.tex missing'
            ))
        else:
            # Check for sectioning commands in sections_index
            content = self.sections_index.read_text()
            sectioning = ['\\part', '\\chapter', '\\section']
            if any(cmd in content for cmd in sectioning):
                violations.append(Violation(
                    'BOOK_SECTIONS_INDEX_SECTIONING_LEAK',
                    str(self.sections_index),
                    'Frontmatter index must not contain \\part/\\chapter/\\section'
                ))
        
        if not self.chapters_index.is_file():
            violations.append(Violation(
                'BOOK_CHAPTERS_INDEX_MISSING',
                str(self.chapters_index),
                'chapters_index.tex missing'
            ))
        
        # Check for spine files outside build/
        for tex_file in self.book_root.rglob('*.tex'):
            if tex_file.name in ['sections_index.tex', 'chapters_index.tex']:
                if tex_file.parent != self.build_dir:
                    violations.append(Violation(
                        'BOOK_SPINE_WRITTEN_OUTSIDE_BUILD',
                        str(tex_file),
                        f'{tex_file.name} found outside build/'
                    ))
        
        return violations
    
    def validate_entry_inclusion(self) -> List[Violation]:
        """Validate entry file inclusion rules."""
        violations = []
        
        if not self.entry_file.is_file():
            return violations  # Already reported
        
        content = self.entry_file.read_text()
        
        # Check for required markers
        if '\\frontmatter' not in content:
            violations.append(Violation(
                'BOOK_ENTRY_MISSING_FRONTMATTER',
                str(self.entry_file),
                'Entry file does not define \\frontmatter'
            ))
        
        if '\\mainmatter' not in content:
            violations.append(Violation(
                'BOOK_ENTRY_MISSING_MAINMATTER',
                str(self.entry_file),
                'Entry file does not define \\mainmatter'
            ))
        
        if '\\backmatter' not in content:
            violations.append(Violation(
                'BOOK_ENTRY_MISSING_BACKMATTER',
                str(self.entry_file),
                'Entry file does not define \\backmatter'
            ))
        
        # Check for spine includes
        has_sections_include = 'build/sections_index.tex' in content
        has_chapters_include = 'build/chapters_index.tex' in content
        
        if not has_sections_include or not has_chapters_include:
            violations.append(Violation(
                'BOOK_ENTRY_SPINE_INCLUDE_MISSING',
                str(self.entry_file),
                'Entry file does not include required spine files'
            ))
        
        # Check ordering (simplified: just check relative positions)
        if '\\frontmatter' in content and '\\mainmatter' in content and '\\backmatter' in content:
            idx_front = content.index('\\frontmatter')
            idx_main = content.index('\\mainmatter')
            idx_back = content.index('\\backmatter')
            
            if has_sections_include:
                idx_sections = content.index('build/sections_index.tex')
                if not (idx_front < idx_sections < idx_main):
                    violations.append(Violation(
                        'BOOK_ENTRY_SPINE_INCLUDE_WRONG_PHASE',
                        str(self.entry_file),
                        'sections_index.tex must be included in \\frontmatter'
                    ))
            
            if has_chapters_include:
                idx_chapters = content.index('build/chapters_index.tex')
                if not (idx_main < idx_chapters < idx_back):
                    violations.append(Violation(
                        'BOOK_ENTRY_SPINE_INCLUDE_WRONG_PHASE',
                        str(self.entry_file),
                        'chapters_index.tex must be included in \\mainmatter'
                    ))
        
        return violations
    
    def validate_parts(self) -> List[Violation]:
        """Validate part structure."""
        violations = []
        
        if not self.parts_parts_dir.is_dir():
            return violations  # Already reported
        
        parts = get_numbered_dirs(self.parts_parts_dir)
        
        # Check part naming
        for child in self.parts_parts_dir.iterdir():
            if not child.is_dir():
                continue
            if not re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*$', child.name):
                violations.append(Violation(
                    'BOOK_PART_DIR_INVALID_NAME',
                    str(child),
                    f'Invalid part name: {child.name}'
                ))
        
        # Check numbering (should start at 01, no gaps)
        if parts:
            nums = [num for num, slug, path in parts]
            expected = list(range(1, len(nums) + 1))
            if nums != expected:
                violations.append(Violation(
                    'BOOK_PART_NUMBER_GAP',
                    str(self.parts_parts_dir),
                    f'Part numbering not contiguous: {nums}'
                ))
        
        # Check for duplicate slugs
        slugs = [slug for num, slug, path in parts]
        if len(slugs) != len(set(slugs)):
            violations.append(Violation(
                'BOOK_PART_DUPLICATE_SLUG',
                str(self.parts_parts_dir),
                f'Duplicate part slugs found'
            ))
        
        # Check each part's contents
        for num, slug, part_dir in parts:
            part_tex = part_dir / 'part.tex'
            if not part_tex.is_file():
                violations.append(Violation(
                    'BOOK_PART_TEX_MISSING',
                    str(part_tex),
                    'part.tex missing'
                ))
            
            chapters_dir = part_dir / 'chapters'
            if not chapters_dir.is_dir():
                violations.append(Violation(
                    'BOOK_PART_CHAPTERS_DIR_MISSING',
                    str(chapters_dir),
                    'chapters/ directory missing'
                ))
        
        return violations
    
    def validate_chapters(self) -> List[Violation]:
        """Validate chapter structure within all parts."""
        violations = []
        
        if not self.parts_parts_dir.is_dir():
            return violations
        
        parts = get_numbered_dirs(self.parts_parts_dir)
        
        for part_num, part_slug, part_dir in parts:
            chapters_dir = part_dir / 'chapters'
            if not chapters_dir.is_dir():
                continue  # Already reported
            
            chapters = get_numbered_dirs(chapters_dir)
            
            # Check chapter naming
            for child in chapters_dir.iterdir():
                if not child.is_dir():
                    continue
                if not re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*$', child.name):
                    violations.append(Violation(
                        'BOOK_CHAPTER_DIR_INVALID_NAME',
                        str(child),
                        f'Invalid chapter name: {child.name}'
                    ))
            
            # Check numbering
            if chapters:
                nums = [num for num, slug, path in chapters]
                expected = list(range(1, len(nums) + 1))
                if nums != expected:
                    violations.append(Violation(
                        'BOOK_CHAPTER_NUMBER_GAP',
                        str(chapters_dir),
                        f'Chapter numbering not contiguous: {nums}'
                    ))
            
            # Check for duplicate slugs
            slugs = [slug for num, slug, path in chapters]
            if len(slugs) != len(set(slugs)):
                violations.append(Violation(
                    'BOOK_CHAPTER_DUPLICATE_SLUG',
                    str(chapters_dir),
                    'Duplicate chapter slugs found'
                ))
            
            # Check each chapter's contents
            for ch_num, ch_slug, ch_dir in chapters:
                chapter_tex = ch_dir / 'chapter.tex'
                if not chapter_tex.is_file():
                    violations.append(Violation(
                        'BOOK_CHAPTER_TEX_MISSING',
                        str(chapter_tex),
                        'chapter.tex missing'
                    ))
        
        return violations
    
    def validate_build_pollution(self) -> List[Violation]:
        """Validate build directory pollution."""
        violations = []
        
        if not self.build_dir.is_dir():
            return violations
        
        # Check for authored content in build/
        for tex_file in self.build_dir.rglob('*.tex'):
            if tex_file.name not in ['sections_index.tex', 'chapters_index.tex']:
                violations.append(Violation(
                    'BOOK_BUILD_CONTAINS_AUTHORED_CONTENT',
                    str(tex_file),
                    f'Authored content in build/: {tex_file.name}'
                ))
        
        return violations


class PaperValidator:
    """Validates paper structure invariants."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.intro_dir = repo_root / '00_introduction'
    
    def find_paper_dirs(self) -> List[Path]:
        """Find all paper directories in the repository."""
        papers = []
        
        # Look in stage directories
        stage_dirs = [
            self.repo_root / '01_process_regime',
            self.repo_root / '02_function_application',
            self.repo_root / '03_hypophysis'
        ]
        
        for stage in stage_dirs:
            if stage.is_dir():
                for child in stage.iterdir():
                    if child.is_dir() and re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*$', child.name):
                        papers.append(child)
        
        return papers
    
    def validate_all(self) -> List[Violation]:
        """Run all paper validations."""
        violations = []
        papers = self.find_paper_dirs()
        
        for paper_dir in papers:
            violations.extend(self.validate_paper(paper_dir))
        
        # Check for papers under introduction
        if self.intro_dir.is_dir():
            for child in self.intro_dir.rglob('*'):
                if child.is_dir() and child != self.intro_dir:
                    if re.match(r'^\d\d_[a-z0-9][a-z0-9_-]*$', child.name):
                        # Check if it looks like a paper (has paper.tex or similar)
                        entry_name = f"{child.name}.tex"
                        if (child / entry_name).exists():
                            violations.append(Violation(
                                'PAPER_PLACEMENT_FORBIDDEN_UNDER_INTRO',
                                str(child),
                                'Paper directories must not be under 00_introduction'
                            ))
        
        return violations
    
    def validate_paper(self, paper_dir: Path) -> List[Violation]:
        """Validate a single paper directory."""
        violations = []
        
        entry_name = f"{paper_dir.name}.tex"
        entry_file = paper_dir / entry_name
        sections_dir = paper_dir / 'sections'
        build_dir = paper_dir / 'build'
        refs_bib = paper_dir / 'refs.bib'
        
        # Entry file
        if not entry_file.is_file():
            violations.append(Violation(
                'PAPER_ENTRY_MISSING',
                str(entry_file),
                f'Missing paper entry file: {entry_name}'
            ))
        
        # Check for multiple .tex files
        tex_files = list(paper_dir.glob('*.tex'))
        if len(tex_files) > 1:
            violations.append(Violation(
                'PAPER_ENTRY_NOT_UNIQUE',
                str(paper_dir),
                f'Multiple .tex files found: {[f.name for f in tex_files]}'
            ))
        
        # Sections directory
        if not sections_dir.is_dir():
            violations.append(Violation(
                'PAPER_SECTIONS_DIR_MISSING',
                str(sections_dir),
                'sections/ directory missing'
            ))
        
        # Build directory
        if not build_dir.is_dir():
            violations.append(Violation(
                'PAPER_BUILD_DIR_MISSING',
                str(build_dir),
                'build/ directory missing'
            ))
        
        # refs.bib
        if not refs_bib.is_file():
            violations.append(Violation(
                'PAPER_REFS_MISSING',
                str(refs_bib),
                'refs.bib missing'
            ))
        
        # Build pollution
        if build_dir.is_dir():
            for tex_file in build_dir.rglob('*.tex'):
                violations.append(Violation(
                    'PAPER_BUILD_CONTAINS_AUTHORED_CONTENT',
                    str(tex_file),
                    f'Authored content in build/: {tex_file.name}'
                ))
        
        return violations


def validate_repository(repo_root: Path) -> List[Violation]:
    """
    Run all validations on a repository.
    
    Args:
        repo_root: Path to repository root
        
    Returns:
        List of violations (empty if all validations pass)
    """
    violations = []
    
    # Validate book
    book_validator = BookValidator(repo_root)
    violations.extend(book_validator.validate_all())
    
    # Validate papers
    paper_validator = PaperValidator(repo_root)
    violations.extend(paper_validator.validate_all())
    
    # Sort by code for determinism
    violations.sort(key=lambda v: (v.code, v.path))
    
    return violations
