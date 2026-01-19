from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, List, Set
import fnmatch

from .common import find_repo_root, TexRepoError
from .rules import (
    WORLD_DIR,
    FOUNDATION_REL,
    SPEC_REL,
    FORMALISM_DIR,
    PROCESS_REGIME_DIR,
    FUNCTION_APPLICATION_DIR,
    PAPERS_DIRNAME,
    PROCESS_BRANCHES,
    FUNCTION_BRANCHES,
    entry_tex_candidates,
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

    report.add_info(f"📂 Repository: {repo_root}")
    report.add_info("")

    checks = [
        check_top_level_structure(repo_root, ignore_patterns),
        check_world_area(repo_root, ignore_patterns),
        check_formalism_area(repo_root, ignore_patterns),
        check_process_regime_area(repo_root, ignore_patterns),
        check_function_application_area(repo_root, ignore_patterns),
        check_metadata_warnings(repo_root),
    ]

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


def check_top_level_structure(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    """Check required top-level directories and unexpected items."""
    messages = ["🔍 Checking top-level structure..."]
    is_compliant = True
    ignored_count = 0

    required = [WORLD_DIR, FORMALISM_DIR, PROCESS_REGIME_DIR, FUNCTION_APPLICATION_DIR]
    for name in required:
        path = repo_root / name
        if path.is_dir():
            messages.append(f"  ✅ {name}")
        else:
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{name} (missing)')}")
            is_compliant = False

    allowed_extras = {
        "shared",
        "scripts",
        "98_context",
        "99_legacy",
        "releases",
        "04_testbed",
        "04_testbeds",
        "SPEC",
    }
    for item in repo_root.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            if item.name in required or item.name in allowed_extras:
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


def check_world_area(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    """Validate 00_world with foundation and spec."""
    messages = ["🔍 Checking world layer..."]
    is_compliant = True
    ignored_count = 0

    world_root = repo_root / WORLD_DIR
    if not world_root.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, '00_world directory missing')}")
        messages.append("")
        return StatusResult(False, messages)

    world_readme = world_root / "README.md"
    if not world_readme.exists():
        messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', WORLD_DIR)}")
        is_compliant = False

    foundation_dir = repo_root / FOUNDATION_REL
    if foundation_dir.exists():
        if not (foundation_dir / "README.md").exists():
            messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', str(FOUNDATION_REL))}")
            is_compliant = False
        entry = _find_entry_tex(foundation_dir)
        if not entry:
            messages.append(f"  {format_error(ErrorCode.MAIN_TEX_MISSING, 'Entry .tex file missing', str(FOUNDATION_REL))}")
            is_compliant = False
        elif entry.name == "main.tex":
            messages.append(f"  ⚠️  Legacy entry file main.tex detected (expected {foundation_dir.name}.tex): {FOUNDATION_REL}")
        for section_name in ["00_definitions.tex", "01_axioms.tex"]:
            if not (foundation_dir / "sections" / section_name).exists():
                messages.append(
                    f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'Missing {section_name}', str(FOUNDATION_REL))}"
                )
                is_compliant = False
    else:
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'Foundation directory missing', str(FOUNDATION_REL))}")
        is_compliant = False

    spec_dir = repo_root / SPEC_REL
    if spec_dir.exists():
        if not (spec_dir / "README.md").exists():
            messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', str(SPEC_REL))}")
            is_compliant = False
        entry = _find_entry_tex(spec_dir)
        if not entry:
            messages.append(f"  {format_error(ErrorCode.MAIN_TEX_MISSING, 'Entry .tex file missing', str(SPEC_REL))}")
            is_compliant = False
        elif entry.name == "main.tex":
            messages.append(f"  ⚠️  Legacy entry file main.tex detected (expected {spec_dir.name}.tex): {SPEC_REL}")
        if not (spec_dir / "refs.bib").exists():
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'refs.bib missing', str(SPEC_REL))}")
            is_compliant = False
    else:
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'World spec directory missing', str(SPEC_REL))}")
        is_compliant = False

    for item in world_root.iterdir():
        if item.name.startswith("."):
            continue
        if item.name in {FOUNDATION_REL.name, SPEC_REL.name, "README.md"}:
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            ignored_count += 1
            continue
        messages.append(f"  {format_error(ErrorCode.UNEXPECTED_ITEM, 'Unexpected item in 00_world/', item.name)}")
        is_compliant = False

    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items in 00_world/")

    messages.append("")
    return StatusResult(is_compliant, messages)


def _check_stage_readme(stage_path: Path, stage_label: str, messages: List[str]) -> bool:
    readme = stage_path / "README.md"
    if not readme.exists():
        messages.append(f"  {format_error(ErrorCode.README_MISSING, 'README.md missing', stage_label)}")
        return False
    return True


def check_formalism_area(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    messages = ["🔍 Checking formalism..."]
    is_compliant = True
    stage_path = repo_root / FORMALISM_DIR

    if not stage_path.exists():
        messages.append("")
        return StatusResult(is_compliant, messages)

    if not _check_stage_readme(stage_path, FORMALISM_DIR, messages):
        is_compliant = False

    papers_root = stage_path / PAPERS_DIRNAME
    if not papers_root.exists():
        messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, 'papers/ missing', f'{FORMALISM_DIR}/')}")
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


def check_process_regime_area(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    messages = ["🔍 Checking process/regime..."]
    is_compliant = True
    stage_path = repo_root / PROCESS_REGIME_DIR

    if not stage_path.exists():
        messages.append("")
        return StatusResult(is_compliant, messages)

    if not _check_stage_readme(stage_path, PROCESS_REGIME_DIR, messages):
        is_compliant = False

    for branch in PROCESS_BRANCHES:
        branch_root = stage_path / branch
        if not branch_root.exists():
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{branch} missing', PROCESS_REGIME_DIR)}")
            is_compliant = False
            continue
        if not _check_stage_readme(branch_root, f"{PROCESS_REGIME_DIR}/{branch}", messages):
            is_compliant = False
        if not _check_branch_papers(repo_root, branch_root, f"{PROCESS_REGIME_DIR}/{branch}", messages, ignore_patterns):
            is_compliant = False

    for item in stage_path.iterdir():
        if item.name.startswith(".") or item.name in PROCESS_BRANCHES or item.name == "README.md":
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            continue
        if item.is_dir() and _find_entry_tex(item):
            rel_path = item.relative_to(repo_root)
            messages.append(f"  {format_error(ErrorCode.INVALID_PLACEMENT, 'Paper outside process/regime branches', str(rel_path))}")
            is_compliant = False

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_function_application_area(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    messages = ["🔍 Checking function/application..."]
    is_compliant = True
    stage_path = repo_root / FUNCTION_APPLICATION_DIR

    if not stage_path.exists():
        messages.append("")
        return StatusResult(is_compliant, messages)

    if not _check_stage_readme(stage_path, FUNCTION_APPLICATION_DIR, messages):
        is_compliant = False

    for branch in FUNCTION_BRANCHES:
        branch_root = stage_path / branch
        if not branch_root.exists():
            messages.append(f"  {format_error(ErrorCode.STRUCTURE_MISSING, f'{branch} missing', FUNCTION_APPLICATION_DIR)}")
            is_compliant = False
            continue
        if not _check_stage_readme(branch_root, f"{FUNCTION_APPLICATION_DIR}/{branch}", messages):
            is_compliant = False
        if not _check_branch_papers(repo_root, branch_root, f"{FUNCTION_APPLICATION_DIR}/{branch}", messages, ignore_patterns):
            is_compliant = False

    for item in stage_path.iterdir():
        if item.name.startswith(".") or item.name in FUNCTION_BRANCHES or item.name == "README.md":
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
