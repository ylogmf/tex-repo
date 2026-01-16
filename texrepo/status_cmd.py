from __future__ import annotations

from pathlib import Path
from typing import NamedTuple, List, Set
import fnmatch

from .common import find_repo_root, TexRepoError
from .rules import STAGES, CORE_STAGE, CORE_PAPER_REL
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

    # Check top-level stages
    stage_status = check_stages(repo_root, ignore_patterns)
    for msg in stage_status.messages:
        if "❌" in msg:
            report.add_error(msg)
        elif "⚠️" in msg:
            report.add_violation(msg)
        elif "ignored" in msg.lower() and "ℹ️" in msg:
            # Extract ignored count from message
            import re
            match = re.search(r'ignored (\d+)', msg)
            if match:
                count = int(match.group(1))
                report.ignored += count
            report.add_info(msg)
        else:
            report.add_info(msg)

    # Check core stage specifically  
    core_status = check_core_stage(repo_root, ignore_patterns)
    for msg in core_status.messages:
        if "❌" in msg:
            report.add_error(msg)
        elif "⚠️" in msg and "Unexpected item" in msg:
            report.add_violation(msg)
        elif "ignored" in msg.lower() and "ℹ️" in msg:
            # Extract ignored count from message
            import re
            match = re.search(r'ignored (\d+)', msg)
            if match:
                count = int(match.group(1))
                report.ignored += count
            report.add_info(msg)
        else:
            report.add_info(msg)

    # Check domains in stages 01-04
    domains_status = check_domains(repo_root)
    for msg in domains_status.messages:
        if "❌" in msg:
            report.add_error(msg)
        elif "⚠️" in msg:
            report.add_violation(msg)
        else:
            report.add_info(msg)

    # Check papers
    papers_status = check_papers(repo_root)
    for msg in papers_status.messages:
        if "❌" in msg:
            report.add_error(msg)
        elif "⚠️" in msg:
            report.add_warning(msg)  # Paper issues are warnings, not violations
        else:
            report.add_info(msg)

    # Check metadata warnings (doesn't affect compliance)
    metadata_status = check_metadata_warnings(repo_root)
    for msg in metadata_status.messages:
        if "⚠️" in msg:
            report.add_warning(msg)
        else:
            report.add_info(msg)

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


def check_stages(repo_root: Path, ignore_patterns: Set[str]) -> StatusResult:
    """Check presence and order of top-level stages."""
    messages = ["🔍 Checking top-level stages..."]
    is_compliant = True
    ignored_count = 0

    for stage in STAGES:
        stage_path = repo_root / stage
        if stage_path.exists() and stage_path.is_dir():
            messages.append(f"  ✅ {stage}")
        else:
            messages.append(f"  ❌ {stage} (missing)")
            is_compliant = False

    # Check for unexpected top-level directories
    allowed_extras = ["shared", "scripts", "98_context", "99_legacy"]
    for item in repo_root.iterdir():
        if item.name.startswith('.'):
            # Skip hidden files/directories (like .git, .paperrepo, etc.)
            continue
            
        if item.is_dir() and item.name not in STAGES and item.name not in allowed_extras:
            # Check if this item should be ignored
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1
                continue
                
            # Check if it looks like a stage (NN_name pattern)
            name = item.name
            if len(name) >= 3 and name[:2].isdigit() and name[2] == "_":
                messages.append(f"  ⚠️  {name} (unexpected stage)")
                is_compliant = False
            else:
                messages.append(f"  ⚠️  {name} (unexpected directory)")
                is_compliant = False
        elif item.is_file():
            # Check if top-level files should be ignored  
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1

    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items")

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_core_stage(repo_root: Path, ignore_patterns: Set[str] = None) -> StatusResult:
    """Check core stage compliance."""
    messages = ["🔍 Checking core stage (00_core)..."]
    is_compliant = True
    violations = 0
    ignored_count = 0

    if ignore_patterns is None:
        ignore_patterns = load_gitignore_patterns(repo_root)

    core_stage_path = repo_root / CORE_STAGE
    if not core_stage_path.exists():
        messages.append("  ❌ 00_core stage missing")
        messages.append("")
        return StatusResult(False, messages)

    # Check that core paper exists
    core_paper_path = repo_root / CORE_PAPER_REL
    if core_paper_path.exists() and core_paper_path.is_dir():
        messages.append("  ✅ core paper directory exists")
        
        # Check main.tex in core paper
        main_tex = core_paper_path / "main.tex"
        if main_tex.exists():
            messages.append("  ✅ core/main.tex exists")
        else:
            messages.append("  ❌ core/main.tex missing")
            is_compliant = False
    else:
        messages.append("  ❌ core paper directory missing")
        is_compliant = False

    # Check for unexpected items in 00_core
    for item in core_stage_path.iterdir():
        if item.name != "core":
            # Check if this item should be ignored
            if is_ignored_by_patterns(item, repo_root, ignore_patterns):
                ignored_count += 1
                continue
            
            # This is a violation - unexpected item that's not ignored
            messages.append(f"  ⚠️  Unexpected item in 00_core: {item.name}")
            violations += 1
            is_compliant = False
    
    # Add ignored count info if any
    if ignored_count > 0:
        messages.append(f"  ℹ️ ignored {ignored_count} items in 00_core")

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_domains(repo_root: Path) -> StatusResult:
    """Check domain structure in stages 01-04."""
    messages = ["🔍 Checking domains in stages 01-04..."]
    is_compliant = True

    for stage in STAGES[1:]:  # Skip 00_core
        stage_path = repo_root / stage
        if not stage_path.exists():
            continue  # Already reported in check_stages
            
        messages.append(f"  📁 {stage}:")
        
        # Get all domain directories
        domain_dirs = []
        for item in stage_path.iterdir():
            if item.is_dir():
                domain_dirs.append(item)
        
        if not domain_dirs:
            messages.append("    ℹ️  No domains")
            continue

        # Check domain numbering
        domain_numbers = []
        for domain in domain_dirs:
            name = domain.name
            if len(name) >= 3 and name[:2].isdigit() and name[2] == "_":
                domain_numbers.append(int(name[:2]))
                messages.append(f"    ✅ {name}")
            else:
                messages.append(f"    ❌ {name} (invalid domain format)")
                is_compliant = False

        # Check for contiguous numbering starting from 00
        if domain_numbers:
            domain_numbers.sort()
            expected = list(range(len(domain_numbers)))
            if domain_numbers != expected:
                messages.append(f"    ⚠️  Domain numbering not contiguous: {domain_numbers} (expected: {expected})")
                # Note: Non-contiguous numbering is a violation, not just a warning
                is_compliant = False

    messages.append("")
    return StatusResult(is_compliant, messages)


def check_papers(repo_root: Path) -> StatusResult:
    """Check paper structure and placement."""
    messages = ["🔍 Checking papers..."]
    is_compliant = True

    # Check that papers don't exist directly under stages (except core)
    for stage in STAGES[1:]:  # Skip 00_core
        stage_path = repo_root / stage
        if not stage_path.exists():
            continue

        for item in stage_path.iterdir():
            if item.is_dir():
                # If this looks like a paper (has main.tex), it's misplaced
                main_tex = item / "main.tex"
                if main_tex.exists():
                    messages.append(f"  ❌ Paper directly under stage: {stage}/{item.name}")
                    messages.append(f"     Papers must be inside domains, not directly under stages")
                    is_compliant = False

    # Check papers in domains
    paper_count = 0
    for stage in STAGES[1:]:  # Skip 00_core
        stage_path = repo_root / stage
        if not stage_path.exists():
            continue

        for domain in stage_path.iterdir():
            if not domain.is_dir():
                continue
                
            # Check papers in this domain
            for item in domain.iterdir():
                if item.is_dir():
                    main_tex = item / "main.tex"
                    if main_tex.exists():
                        paper_count += 1
                        relative_path = item.relative_to(repo_root)
                        messages.append(f"  ✅ Paper: {relative_path}")
                    else:
                        # Directory without main.tex - might be a subdomain or other structure
                        # Check if it has numbered domain format
                        name = item.name
                        if len(name) >= 3 and name[:2].isdigit() and name[2] == "_":
                            # This is likely a subdomain, don't report as missing main.tex
                            continue
                        else:
                            relative_path = item.relative_to(repo_root)
                            messages.append(f"  ⚠️  Directory without main.tex: {relative_path}")

    # Include core paper in count
    core_paper = repo_root / CORE_PAPER_REL
    if core_paper.exists() and (core_paper / "main.tex").exists():
        paper_count += 1
        messages.append(f"  ✅ Paper: {CORE_PAPER_REL}")

    messages.append(f"  📊 Total papers found: {paper_count}")
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