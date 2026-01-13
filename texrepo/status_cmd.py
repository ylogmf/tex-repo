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


class StatusSummary(NamedTuple):
    errors: int
    warnings: int 
    ignored: int


def load_gitignore_patterns(repo_root: Path) -> Set[str]:
    """Load gitignore patterns from repository root.
    
    Returns:
        Set of patterns to ignore
    """
    patterns = set()
    
    # Always ignore common OS artifacts
    patterns.add('.DS_Store')
    patterns.add('Thumbs.db')
    
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
    messages = []
    is_compliant = True
    errors = 0
    warnings = 0
    ignored = 0

    # Load gitignore patterns
    ignore_patterns = load_gitignore_patterns(repo_root)

    messages.append(f"📂 Repository: {repo_root}")
    messages.append("")

    # Check top-level stages
    stage_status = check_stages(repo_root, ignore_patterns)
    messages.extend(stage_status.messages)
    is_compliant &= stage_status.is_compliant
    errors += sum(1 for msg in stage_status.messages if "❌" in msg)
    ignored += sum(1 for msg in stage_status.messages if "ignored" in msg.lower())

    # Check core stage specifically
    core_status = check_core_stage(repo_root)
    messages.extend(core_status.messages)
    is_compliant &= core_status.is_compliant
    errors += sum(1 for msg in core_status.messages if "❌" in msg)

    # Check domains in stages 01-04
    domains_status = check_domains(repo_root)
    messages.extend(domains_status.messages)
    is_compliant &= domains_status.is_compliant
    errors += sum(1 for msg in domains_status.messages if "❌" in msg)

    # Check papers
    papers_status = check_papers(repo_root)
    messages.extend(papers_status.messages)
    is_compliant &= papers_status.is_compliant
    errors += sum(1 for msg in papers_status.messages if "❌" in msg)

    # Check metadata warnings (doesn't affect compliance)
    metadata_status = check_metadata_warnings(repo_root)
    messages.extend(metadata_status.messages)
    warnings += sum(1 for msg in metadata_status.messages if "⚠️" in msg)
    # Note: metadata warnings don't affect compliance status

    # Report ignored items summary if any
    if ignored > 0:
        messages.append(f"ℹ️ Ignoring {ignored} files matched by .gitignore")
        messages.append("")

    # Status summary
    messages.append("Status summary:")
    messages.append(f"  errors: {errors}")
    messages.append(f"  warnings: {warnings}")
    messages.append(f"  ignored: {ignored}")
    messages.append("")

    if is_compliant:
        messages.append("✅ Repository structure is fully compliant!")
    else:
        messages.append("❌ Repository structure has violations!")

    return StatusResult(is_compliant, messages)


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


def check_core_stage(repo_root: Path) -> StatusResult:
    """Check core stage compliance."""
    messages = ["🔍 Checking core stage (00_core)..."]
    is_compliant = True

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
            messages.append(f"  ⚠️  Unexpected item in 00_core: {item.name}")
            is_compliant = False

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