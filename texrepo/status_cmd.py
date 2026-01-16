from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, List, Set
import fnmatch

from .common import find_repo_root, TexRepoError
from .rules import SPEC_DIR, SPEC_PAPER_REL, STAGE_PIPELINE
from .meta_cmd import parse_paperrepo_metadata


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
            if "❌" in msg:
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
        check_spec_area(repo_root, ignore_patterns),
        check_stages_domains_and_papers(repo_root, ignore_patterns),
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

    required = [SPEC_DIR, *STAGE_PIPELINE]
    for name in required:
        path = repo_root / name
        if path.is_dir():
            messages.append(f"  ✅ {name}")
        else:
            messages.append(f"  ❌ {name} (missing)")
            is_compliant = False

    allowed_extras = {"shared", "scripts", "98_context", "99_legacy", "releases"}
    for item in repo_root.iterdir():
        if item.name.startswith("."):
            continue
        if item.is_dir():
            if item.name in required or item.name in allowed_extras:
                continue
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1
                continue
            messages.append(f"  ❌ Unexpected top-level directory: {item.name}")
            is_compliant = False
        else:
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1

    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items")

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_spec_area(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    """Validate SPEC directory, uniqueness, and README requirements."""
    messages = ["🔍 Checking Spec..."]
    is_compliant = True
    ignored_count = 0

    spec_root = repo_root / SPEC_DIR
    if not spec_root.exists():
        messages.append("  ❌ SPEC directory missing")
        messages.append("")
        return StatusResult(False, messages)

    spec_readme = spec_root / "README.md"
    if not spec_readme.exists():
        messages.append("  ❌ Missing README.md in SPEC/")
        is_compliant = False

    spec_paper_dir = repo_root / SPEC_PAPER_REL
    if spec_paper_dir.exists():
        if not (spec_paper_dir / "README.md").exists():
            messages.append("  ❌ Missing README.md in SPEC/spec")
            is_compliant = False
        if not (spec_paper_dir / "main.tex").exists():
            messages.append("  ❌ SPEC/spec/main.tex missing")
            is_compliant = False
    else:
        messages.append("  ❌ Spec paper directory missing at SPEC/spec")
        is_compliant = False

    for item in spec_root.iterdir():
        if item.name.startswith("."):
            continue
        if item.name in {"README.md", "spec"}:
            continue
        if is_ignored_by_patterns(item, repo_root, ignore_patterns):
            ignored_count += 1
            continue
        messages.append(f"  ❌ Unexpected item in SPEC/: {item.name}")
        is_compliant = False

    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items in SPEC/")

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_stages_domains_and_papers(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    """Validate stage, domain, and paper placement plus README requirements."""
    messages = ["🔍 Checking stages, domains, and papers..."]
    is_compliant = True

    for stage in STAGE_PIPELINE:
        stage_path = repo_root / stage
        if not stage_path.exists():
            continue

        stage_readme = stage_path / "README.md"
        if not stage_readme.exists():
            messages.append(f"  ❌ Missing README.md in {stage}")
            is_compliant = False

        for item in stage_path.iterdir():
            if item.name.startswith("."):
                continue
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                continue

            if item.is_dir():
                # Papers are not allowed directly under stages
                if (item / "main.tex").exists():
                    messages.append(f"  ❌ Paper directly under stage: {stage}/{item.name} (papers must live inside domains; Spec lives at SPEC/spec)")
                    is_compliant = False
                    continue

                # Domain folder
                domain_readme = item / "README.md"
                if not domain_readme.exists():
                    messages.append(f"  ❌ Missing README.md in domain: {stage}/{item.name}")
                    is_compliant = False

                for paper_dir in item.iterdir():
                    if not paper_dir.is_dir():
                        continue
                    if is_ignored_by_patterns(paper_dir, repo_root, ignore_patterns):
                        continue
                    if (paper_dir / "main.tex").exists():
                        if not (paper_dir / "README.md").exists():
                            rel_path = paper_dir.relative_to(repo_root)
                            messages.append(f"  ❌ Missing README.md in paper: {rel_path}")
                            is_compliant = False
                    # Non-paper subdirectories are allowed silently

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
