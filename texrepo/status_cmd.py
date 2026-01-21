from __future__ import annotations

from pathlib import Path
import re
from typing import NamedTuple, List, Set
import fnmatch

from .common import find_repo_root, TexRepoError
from .rules import (
    PAPERS_DIRNAME,
    entry_tex_candidates,
)
from .layouts import (
    allowed_top_level,
    get_function_branches,
    get_layout,
    get_process_branches,
    required_dirs,
    stage_dir,
    world_paths_for_layout,
)
from .meta_cmd import parse_paperrepo_metadata
from .errors import ErrorCode, format_error


class StatusResult(NamedTuple):
    is_compliant: bool
    messages: List[str]


class StatusReport:
    """Unified status report that tracks all findings."""
    def __init__(self):
        self.errors = 0
        self.warnings = 0
        self.violations = 0
        self.ignored = 0
        self.messages = []
    
    def add_error(self, message: str):
        """Add an error message and increment error count."""
        self.errors += 1
        self.messages.append(message)
    
    def add_warning(self, message: str):
        """Add a warning message and increment warning count."""
        self.warnings += 1
        self.messages.append(message)
    
    def add_violation(self, message: str):
        """Add a violation message and increment violation count."""
        self.violations += 1
        self.messages.append(message)
    
    def add_ignored(self, message: str = None):
        """Add an ignored item and increment ignored count."""
        self.ignored += 1
        if message:
            self.messages.append(message)
    
    def add_info(self, message: str):
        """Add an informational message."""
        self.messages.append(message)
    
    def is_success(self) -> bool:
        """Return True if there are no errors or violations."""
        return self.errors == 0 and self.violations == 0
    
    def extend_from_result(self, result: 'StatusResult', ignore_patterns: Set[str] = None, repo_root: Path = None):
        """Extend this report with results from a StatusResult, properly categorizing messages."""
        for msg in result.messages:
            if msg.strip().startswith("E[") or "❌" in msg:
                self.add_error(msg)
            elif "ignored" in msg.lower() and "ℹ️" in msg:
                import re
                match = re.search(r'ignored (\d+)', msg)
                if match:
                    self.ignored += int(match.group(1))
                self.add_info(msg)
            elif "⚠️" in msg and "Unexpected item" in msg and ignore_patterns and repo_root:
                # Try to re-classify unexpected items based on ignore patterns
                self.add_violation(msg)
            elif "⚠️" in msg:
                self.add_warning(msg)
            else:
                self.add_info(msg)


def load_gitignore_patterns(repo_root: Path) -> Set[str]:
    """Load gitignore patterns from repository root.
    
    Returns:
        Set of patterns to ignore
    """
    patterns = set()
    
    # Always ignore common OS artifacts
    patterns.add('.DS_Store')
    patterns.add('Thumbs.db')
    patterns.add('Desktop.ini')
    patterns.add('._*')
    patterns.add('.AppleDouble')
    patterns.add('.LSOverride')
    
    gitignore_path = repo_root / '.gitignore'
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if line and not line.startswith('#'):
                        patterns.add(line)
        except Exception:
            # If we can't read .gitignore, just use defaults
            pass
    
    return patterns


def is_ignored_by_patterns(path: Path, repo_root: Path, patterns: Set[str]) -> bool:
    """Check if a path matches any gitignore pattern.
    
    Args:
        path: Path to check
        repo_root: Repository root for relative path calculation
        patterns: Set of ignore patterns
        
    Returns:
        True if path should be ignored
    """
    try:
        relative_path = path.relative_to(repo_root)
        path_str = str(relative_path)
        name = path.name
        
        for pattern in patterns:
            # Remove trailing slash for directory patterns
            clean_pattern = pattern.rstrip('/')
            
            # Match against filename
            if fnmatch.fnmatch(name, clean_pattern):
                return True
            # Match against relative path
            if fnmatch.fnmatch(path_str, clean_pattern):
                return True
            # Match against path with leading slash (gitignore style)
            if pattern.startswith('/'):
                clean_pattern = pattern[1:].rstrip('/')
                if fnmatch.fnmatch(path_str, clean_pattern):
                    return True
    except ValueError:
        # Path is not relative to repo_root
        return False
    
    return False


def _find_entry_tex(paper_dir: Path) -> Path | None:
    """Return the entry tex file if present (folder-named preferred)."""
    for candidate in entry_tex_candidates(paper_dir):
        if candidate.exists():
            return candidate
    return None


def _check_paper(paper_dir: Path, repo_root: Path, messages: List[str]) -> bool:
    """Validate a paper directory structure."""
    is_ok = True
    rel_path = paper_dir.relative_to(repo_root)
    entry = _find_entry_tex(paper_dir)
    if not entry:
        messages.append(f"  {format_error(ErrorCode.MAIN_TEX_MISSING, 'Entry .tex file missing', str(rel_path))}")
        return False
    if entry.name == "main.tex":
        messages.append(f"  ⚠️  Legacy entry file main.tex detected (expected {paper_dir.name}.tex): {rel_path}")
    if not (paper_dir / "README.md").exists():
        messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', str(rel_path))}")
        is_ok = False
    return is_ok


def cmd_status(args) -> int:
    """Inspect repository structure and report compliance."""
    try:
        repo_root = find_repo_root()
    except TexRepoError as e:
        print(f"❌ Error: {e}")
        return 1

    result = check_repo_status(repo_root)
    
    # Print all messages
    for msg in result.messages:
        print(msg)
    
    # Return appropriate exit code
    return 0 if result.is_compliant else 1


def check_repo_status(repo_root: Path) -> StatusResult:
    """Check repository structural compliance."""
    report = StatusReport()

    # Load gitignore patterns
    ignore_patterns = load_gitignore_patterns(repo_root)
    layout_name = get_layout(repo_root)
    process_branches = get_process_branches(layout_name)
    function_branches = get_function_branches(layout_name)

    report.add_info(f"📂 Repository: {repo_root}")
    report.add_info(f"📐 Layout: {layout_name}")
    report.add_info("")

    checks = [check_top_level_structure(repo_root, ignore_patterns, layout_name)]

    world_paths = world_paths_for_layout(layout_name)
    world_dir = stage_dir(layout_name, "world")
    if world_dir and world_paths:
        foundation_rel, spec_rel = world_paths
        checks.append(check_world_area(repo_root, ignore_patterns, world_dir, foundation_rel, spec_rel))

    intro_dir = stage_dir(layout_name, "introduction")
    if intro_dir:
        checks.append(check_introduction_area(repo_root, intro_dir, ignore_patterns))

    formalism_dir = stage_dir(layout_name, "formalism")
    if formalism_dir:
        checks.append(check_stage_with_papers(repo_root, formalism_dir, ignore_patterns))

    process_dir = stage_dir(layout_name, "process_regime")
    if process_dir:
        checks.append(check_process_regime_area(repo_root, ignore_patterns, process_dir, process_branches))

    function_dir = stage_dir(layout_name, "function_application")
    if function_dir:
        checks.append(check_function_application_area(repo_root, ignore_patterns, function_dir, function_branches))

    hypnosis_dir = stage_dir(layout_name, "hypnosis")
    if hypnosis_dir:
        checks.append(check_stage_with_papers(repo_root, hypnosis_dir, ignore_patterns))

    checks.append(check_metadata_warnings(repo_root))

    for result in checks:
        report.extend_from_result(result, ignore_patterns, repo_root)

    # Report ignored items summary if any
    if report.ignored > 0:
        report.add_info(f"ℹ️ Ignoring {report.ignored} files matched by .gitignore")
        report.add_info("")

    # Status summary
    report.add_info("Status summary:")
    report.add_info(f"  errors: {report.errors}")
    report.add_info(f"  warnings: {report.warnings}")
    report.add_info(f"  violations: {report.violations}")
    report.add_info(f"  ignored: {report.ignored}")
    report.add_info("")

    if report.is_success():
        report.add_info("✅ Repository structure is fully compliant!")
    else:
        report.add_info("❌ Repository structure has violations!")

    return StatusResult(report.is_success(), report.messages)


def check_top_level_structure(repo_root: Path, ignore_patterns: Set[str], layout_name: str) -> StatusResult:
    """Check required top-level directories and unexpected items."""
    messages = ["🔍 Checking top-level structure..."]
    is_compliant = True
    ignored_count = 0

    required = required_dirs(layout_name)
    allowed = allowed_top_level(layout_name)
    for name in required:
        path = repo_root / name
        if path.is_dir():
            messages.append(f"  ✅ {name}")
        else:
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{name} (missing)')}")
            is_compliant = False

    for item in repo_root.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            if item.name in allowed:
                continue
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1
                continue
            messages.append(f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected top-level directory', item.name)}")
            is_compliant = False
        else:
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1

    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items")

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_world_area(
    repo_root: Path, ignore_patterns: Set[str], world_dir: str, foundation_rel: Path, spec_rel: Path
) -> StatusResult:
    """Validate 00_world with foundation and spec."""
    messages = ["🔍 Checking world layer..."]
    is_compliant = True
    ignored_count = 0

    world_root = repo_root / world_dir
    if not world_root.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{world_dir} directory missing')}")
        messages.append("")
        return StatusResult(False, messages)

    world_readme = world_root / "README.md"
    if not world_readme.exists():
        messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', world_dir)}")
        is_compliant = False

    foundation_dir = repo_root / foundation_rel
    if foundation_dir.exists():
        if not (foundation_dir / "README.md").exists():
            messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', str(foundation_rel))}")
            is_compliant = False
        entry = _find_entry_tex(foundation_dir)
        if not entry:
            messages.append(f"  {format_error(ErrorCode.MAIN_TEX_MISSING, 'Entry .tex file missing', str(foundation_rel))}")
            is_compliant = False
        elif entry.name == "main.tex":
            messages.append(f"  ⚠️  Legacy entry file main.tex detected (expected {foundation_dir.name}.tex): {foundation_rel}")
        for section_name in ["00_definitions.tex", "01_axioms.tex"]:
            if not (foundation_dir / "sections" / section_name).exists():
                messages.append(
                    f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'Missing {section_name}', str(foundation_rel))}"
                )
                is_compliant = False
    else:
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'Foundation directory missing', str(foundation_rel))}")
        is_compliant = False

    spec_dir = repo_root / spec_rel
    if spec_dir.exists():
        if not (spec_dir / "README.md").exists():
            messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', str(spec_rel))}")
            is_compliant = False
        entry = _find_entry_tex(spec_dir)
        if not entry:
            messages.append(f"  {format_error(ErrorCode.MAIN_TEX_MISSING, 'Entry .tex file missing', str(spec_rel))}")
            is_compliant = False
        elif entry.name == "main.tex":
            messages.append(f"  ⚠️  Legacy entry file main.tex detected (expected {spec_dir.name}.tex): {spec_rel}")
        if not (spec_dir / "refs.bib").exists():
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'refs.bib missing', str(spec_rel))}")
            is_compliant = False
    else:
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'World spec directory missing', str(spec_rel))}")
        is_compliant = False

    for item in world_root.iterdir():
        if item.name.startswith("."):
            continue
        if item.name in {foundation_rel.name, spec_rel.name, "README.md"}:
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            ignored_count += 1
            continue
        messages.append(f"  {format_error(ErrorCode.UNEXPECTED_ITEM, f'Unexpected item in {world_dir}/', item.name)}")
        is_compliant = False

    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items in {world_dir}/")

    messages.append("")
    return StatusResult(is_compliant, messages)


def _parse_section_dirname(name: str) -> int | None:
    m = re.match(r"^(\d\d)_.+$", name)
    if not m:
        return None
    return int(m.group(1))


def check_introduction_area(repo_root: Path, intro_dir: str, ignore_patterns: Set[str]) -> StatusResult:
    """Validate introduction as book-scale (requires entry .tex, sections/ dir, forbids papers/)."""
    messages = [f"🔍 Checking {intro_dir} (book-scale)..."]
    is_compliant = True
    intro_root = repo_root / intro_dir

    if not intro_root.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{intro_dir} directory missing')}")
        messages.append("")
        return StatusResult(False, messages)

    # Check README.md
    readme = intro_root / "README.md"
    if not readme.exists():
        messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', intro_dir)}")
        is_compliant = False

    # Check entry .tex file
    entry_tex = intro_root / f"{intro_dir}.tex"
    if not entry_tex.exists():
        messages.append(f"  {format_error(ErrorCode.MAIN_TEX_MISSING, f'{intro_dir}.tex missing (book entry file)', intro_dir)}")
        is_compliant = False

    # Check sections/ directory
    sections_dir = intro_root / "sections"
    if not sections_dir.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'sections/ directory missing', intro_dir)}")
        is_compliant = False
    else:
        # Validate section folders under sections/
        for item in sections_dir.iterdir():
            if item.name.startswith("."):
                continue
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                continue
            if item.is_dir():
                section_num = _parse_section_dirname(item.name)
                if section_num is None:
                    messages.append(f"  {format_error(ErrorCode.INVALID_PARENT, 'Section folders must be numbered NN_<name>', str(item.relative_to(repo_root)))}")
                    is_compliant = False
                    continue
                # Validate subsection files: S-1.tex through S-10.tex
                expected_files = [f"{section_num}-{i}.tex" for i in range(1, 11)]
                missing = [fn for fn in expected_files if not (item / fn).exists()]
                for fn in missing:
                    messages.append(
                        f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'Missing subsection file {fn}', str(item.relative_to(repo_root)))}"
                    )
                    is_compliant = False
                # Check for unexpected items in section folder
                for child in item.iterdir():
                    if child.name.startswith("."):
                        continue
                    if is_ignored_by_patterns(child, repo_root, ignore_patterns):
                        continue
                    if child.is_dir():
                        messages.append(
                            f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected directory under introduction section', str(child.relative_to(repo_root)))}"
                        )
                        is_compliant = False
                        continue
                    if child.name == "README.md":
                        continue
                    if child.name not in expected_files:
                        messages.append(
                            f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected file under introduction section', str(child.relative_to(repo_root)))}"
                        )
                        is_compliant = False
            else:
                # Unexpected file directly under sections/
                messages.append(
                    f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected file in sections/', str(item.relative_to(repo_root)))}"
                )
                is_compliant = False

    # Check for forbidden items directly under introduction root
    for item in intro_root.iterdir():
        if item.name.startswith("."):
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            continue
        if item.name == "README.md":
            continue
        if item.name == f"{intro_dir}.tex":
            continue
        if item.name == "sections":
            continue
        if item.name == "refs.bib":  # Optional refs.bib is allowed
            continue
        if item.name == "build":  # Generated build/ is allowed
            continue
        if item.name == "papers":
            messages.append(f"  {format_error(ErrorCode.INVALID_PLACEMENT, 'papers/ not allowed under introduction', str(item.relative_to(repo_root)))}")
            is_compliant = False
            continue
        if item.is_dir():
            messages.append(
                f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected directory in introduction (sections must be under sections/)', str(item.relative_to(repo_root)))}"
            )
            is_compliant = False
        else:
            messages.append(
                f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected file in introduction', str(item.relative_to(repo_root)))}"
            )
            is_compliant = False

    messages.append("")
    return StatusResult(is_compliant, messages)


def _check_stage_readme(stage_path: Path, stage_label: str, messages: List[str]) -> bool:
    readme = stage_path / "README.md"
    if not readme.exists():
        messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', stage_label)}")
        return False
    return True


def check_stage_with_papers(repo_root: Path, stage_dir: str, ignore_patterns: Set[str]) -> StatusResult:
    messages = [f"🔍 Checking {stage_dir}..."]
    is_compliant = True
    stage_path = repo_root / stage_dir

    if not stage_path.exists():
        messages.append("")
        return StatusResult(is_compliant, messages)

    if not _check_stage_readme(stage_path, stage_dir, messages):
        is_compliant = False

    papers_root = stage_path / PAPERS_DIRNAME
    if not papers_root.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'papers/ missing', f'{stage_dir}/')}")
        is_compliant = False
    else:
        for paper_dir in papers_root.iterdir():
            if not paper_dir.is_dir() or is_ignored_by_patterns(paper_dir, repo_root, ignore_patterns):
                continue
            if not _check_paper(paper_dir, repo_root, messages):
                is_compliant = False

    for item in stage_path.iterdir():
        if item.name.startswith(".") or item.name == PAPERS_DIRNAME or item.name == "README.md":
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            continue
        if item.is_dir() and _find_entry_tex(item):
            rel_path = item.relative_to(repo_root)
            messages.append(f"  {format_error(ErrorCode.INVALID_PLACEMENT, 'Paper outside papers/ directory', str(rel_path))}")
            is_compliant = False

    messages.append("")
    return StatusResult(is_compliant, messages)


def _check_branch_papers(repo_root: Path, branch_root: Path, branch_label: str, messages: List[str],
                         ignore_patterns: Set[str]) -> bool:
    ok = True
    papers_root = branch_root / PAPERS_DIRNAME
    if not papers_root.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'papers/ missing', f'{branch_label}/')}")
        return False

    for item in branch_root.iterdir():
        if item.name.startswith(".") or item.name in {PAPERS_DIRNAME, "README.md"}:
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            continue
        if item.is_dir() and _find_entry_tex(item):
            rel_path = item.relative_to(repo_root)
            messages.append(f"  {format_error(ErrorCode.INVALID_PLACEMENT, 'Paper outside papers/', str(rel_path))}")
            ok = False

    for paper_dir in papers_root.iterdir():
        if not paper_dir.is_dir() or is_ignored_by_patterns(paper_dir, repo_root, ignore_patterns):
            continue
        if not _check_paper(paper_dir, repo_root, messages):
            ok = False
    return ok


def check_process_regime_area(
    repo_root: Path, ignore_patterns: Set[str], stage_dir: str, branches: tuple[str, ...]
) -> StatusResult:
    messages = [f"🔍 Checking {stage_dir}..."]
    is_compliant = True
    stage_path = repo_root / stage_dir

    if not stage_path.exists():
        messages.append("")
        return StatusResult(is_compliant, messages)

    if not _check_stage_readme(stage_path, stage_dir, messages):
        is_compliant = False

    for branch in branches:
        branch_root = stage_path / branch
        if not branch_root.exists():
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{branch} missing', stage_dir)}")
            is_compliant = False
            continue
        if not _check_stage_readme(branch_root, f"{stage_dir}/{branch}", messages):
            is_compliant = False
        if not _check_branch_papers(repo_root, branch_root, f"{stage_dir}/{branch}", messages, ignore_patterns):
            is_compliant = False

    for item in stage_path.iterdir():
        if item.name.startswith(".") or item.name in branches or item.name == "README.md":
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            continue
        if item.is_dir() and _find_entry_tex(item):
            rel_path = item.relative_to(repo_root)
            messages.append(f"  {format_error(ErrorCode.INVALID_PLACEMENT, 'Paper outside process/regime branches', str(rel_path))}")
            is_compliant = False

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_function_application_area(
    repo_root: Path, ignore_patterns: Set[str], stage_dir: str, branches: tuple[str, ...]
) -> StatusResult:
    messages = [f"🔍 Checking {stage_dir}..."]
    is_compliant = True
    stage_path = repo_root / stage_dir

    if not stage_path.exists():
        messages.append("")
        return StatusResult(is_compliant, messages)

    if not _check_stage_readme(stage_path, stage_dir, messages):
        is_compliant = False

    for branch in branches:
        branch_root = stage_path / branch
        if not branch_root.exists():
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{branch} missing', stage_dir)}")
            is_compliant = False
            continue
        if not _check_stage_readme(branch_root, f"{stage_dir}/{branch}", messages):
            is_compliant = False
        if not _check_branch_papers(repo_root, branch_root, f"{stage_dir}/{branch}", messages, ignore_patterns):
            is_compliant = False

    for item in stage_path.iterdir():
        if item.name.startswith(".") or item.name in branches or item.name == "README.md":
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            continue
        if item.is_dir() and _find_entry_tex(item):
            rel_path = item.relative_to(repo_root)
            messages.append(f"  {format_error(ErrorCode.INVALID_PLACEMENT, 'Paper outside function/application branches', str(rel_path))}")
            is_compliant = False

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_metadata_warnings(repo_root: Path) -> StatusResult:
    """Check for metadata warnings (but don't affect compliance)."""
    messages = []
    
    # Parse metadata
    metadata = parse_paperrepo_metadata(repo_root)
    
    # Check for missing or placeholder author_name
    author_name = metadata.get('author_name', '')
    if not author_name or author_name == 'TODO_AUTHOR':
        messages.append("  ⚠️  Author name is missing or placeholder (TODO_AUTHOR)")
    
    # Check for missing or placeholder organization
    organization = metadata.get('organization', '')
    if not organization or organization == 'TODO_ORG':
        messages.append("  ⚠️  Organization is missing or placeholder (TODO_ORG)")
    
    # Check for missing identity.tex
    identity_tex_path = repo_root / "shared" / "identity.tex"
    if not identity_tex_path.exists():
        messages.append("  ⚠️  shared/identity.tex missing (run 'tex-repo sync-meta')")
    
    if messages:
        messages.insert(0, "📝 Metadata warnings:")
        messages.append("")
    
    # Warnings never affect compliance
    return StatusResult(True, messages)
