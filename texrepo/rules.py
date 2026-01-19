from __future__ import annotations

from pathlib import Path

from .common import die
from .errors import ErrorCode, format_error

# Stage and layer names
WORLD_DIR = "00_world"
FOUNDATION_DIRNAME = "00_foundation"
SPEC_DIRNAME = "01_spec"
FORMALISM_DIR = "01_formalism"
PROCESS_REGIME_DIR = "02_process_regime"
FUNCTION_APPLICATION_DIR = "03_function_application"
PAPERS_DIRNAME = "papers"

# Structured subdomains
PROCESS_BRANCHES = ("process", "regime")
FUNCTION_BRANCHES = ("function", "application")

# Pipelines and allowed top-level stages (in order)
STAGE_PIPELINE = [
    WORLD_DIR,
    FORMALISM_DIR,
    PROCESS_REGIME_DIR,
    FUNCTION_APPLICATION_DIR,
]
STAGES = STAGE_PIPELINE

# Canonical world paper paths
FOUNDATION_REL = Path(WORLD_DIR) / FOUNDATION_DIRNAME
SPEC_REL = Path(WORLD_DIR) / SPEC_DIRNAME


def is_under(path: Path, maybe_parent: Path) -> bool:
    try:
        path.resolve().relative_to(maybe_parent.resolve())
        return True
    except Exception:
        return False


def _expect_no_extra(parts: tuple[str, ...], ctx: str) -> None:
    if parts:
        die(format_error(ErrorCode.INVALID_PARENT, f"Unexpected extra path under {ctx}: {'/'.join(parts)}"))


def _extract_slug(parts: tuple[str, ...], ctx: str, allow_papers_prefix: bool = True) -> str:
    if not parts:
        die(format_error(ErrorCode.INVALID_PARENT, f"Missing target name under {ctx}"))
    remainder = parts
    if allow_papers_prefix and remainder[0] == PAPERS_DIRNAME:
        remainder = remainder[1:]
    if len(remainder) != 1:
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{ctx}/<name>' or '{ctx}/papers/<name>'"))
    slug = remainder[0]
    if not slug:
        die(format_error(ErrorCode.INVALID_PARENT, f"Invalid empty name under {ctx}"))
    return slug


def _extract_branch_and_slug(parts: tuple[str, ...], ctx: str, allowed_branches: tuple[str, ...]) -> tuple[str, str]:
    if not parts:
        branches = ", ".join(allowed_branches)
        die(format_error(ErrorCode.INVALID_PARENT, f"{ctx} requires one of: {branches}"))
    branch = parts[0]
    if branch not in allowed_branches:
        branches = ", ".join(allowed_branches)
        die(format_error(ErrorCode.INVALID_PARENT, f"{ctx} requires one of: {branches}"))
    slug = _extract_slug(tuple(parts[1:]), f"{ctx}/{branch}", allow_papers_prefix=True)
    return branch, slug


def resolve_domain_parent(parent_rel: Path) -> Path:
    """Return canonical parent directory where a new numbered folder should be created.
    Automatically inserts papers/ where required and enforces process/regime splits.
    """
    if not parent_rel.parts:
        die(format_error(ErrorCode.INVALID_PARENT, "Parent path cannot be empty"))

    top = parent_rel.parts[0]

    if top == WORLD_DIR:
        die(format_error(ErrorCode.INVALID_PARENT, "Cannot create numbered domains under 00_world"))

    if top == FORMALISM_DIR:
        tail = parent_rel.parts[1:]
        if not tail:
            return Path(FORMALISM_DIR) / PAPERS_DIRNAME
        if tail[0] == PAPERS_DIRNAME:
            _expect_no_extra(tuple(tail[1:]), f"{FORMALISM_DIR}/{PAPERS_DIRNAME}")
            return parent_rel
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{FORMALISM_DIR}/papers' as parent for new topics"))

    if top == PROCESS_REGIME_DIR:
        branch = parent_rel.parts[1] if len(parent_rel.parts) > 1 else None
        if branch not in PROCESS_BRANCHES:
            branches = ", ".join(PROCESS_BRANCHES)
            die(format_error(ErrorCode.INVALID_PARENT, f"{PROCESS_REGIME_DIR} requires subdomain: {branches}"))
        tail = parent_rel.parts[2:]
        if not tail:
            return Path(PROCESS_REGIME_DIR) / branch / PAPERS_DIRNAME
        if tail[0] == PAPERS_DIRNAME:
            _expect_no_extra(tuple(tail[1:]), f"{PROCESS_REGIME_DIR}/{branch}/{PAPERS_DIRNAME}")
            return parent_rel
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{PROCESS_REGIME_DIR}/{branch}/papers' as parent for new subjects"))

    if top == FUNCTION_APPLICATION_DIR:
        branch = parent_rel.parts[1] if len(parent_rel.parts) > 1 else None
        if branch not in FUNCTION_BRANCHES:
            branches = ", ".join(FUNCTION_BRANCHES)
            die(format_error(ErrorCode.INVALID_PARENT, f"{FUNCTION_APPLICATION_DIR} requires subdomain: {branches}"))
        tail = parent_rel.parts[2:]
        if not tail:
            return Path(FUNCTION_APPLICATION_DIR) / branch / PAPERS_DIRNAME
        if tail[0] == PAPERS_DIRNAME:
            _expect_no_extra(tuple(tail[1:]), f"{FUNCTION_APPLICATION_DIR}/{branch}/{PAPERS_DIRNAME}")
            return parent_rel
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{FUNCTION_APPLICATION_DIR}/{branch}/papers' as parent for new subjects"))

    stages = ", ".join(STAGE_PIPELINE)
    die(format_error(ErrorCode.INVALID_PARENT, f"Parent must be under known stages: {stages}"))


def resolve_paper_path(user_rel: Path) -> Path:
    """Return canonical paper directory path given a user-supplied relative path."""
    if not user_rel.parts:
        die(format_error(ErrorCode.INVALID_PARENT, "Paper path cannot be empty"))

    top = user_rel.parts[0]

    if top == WORLD_DIR:
        if len(user_rel.parts) == 2 and user_rel.parts[1] in {FOUNDATION_DIRNAME, SPEC_DIRNAME}:
            return user_rel
        die(format_error(ErrorCode.INVALID_PARENT, "Only 00_foundation and 01_spec are allowed under 00_world"))

    if top == FORMALISM_DIR:
        slug = _extract_slug(tuple(user_rel.parts[1:]), FORMALISM_DIR, allow_papers_prefix=True)
        return Path(FORMALISM_DIR) / PAPERS_DIRNAME / slug

    if top == PROCESS_REGIME_DIR:
        branch, slug = _extract_branch_and_slug(tuple(user_rel.parts[1:]), PROCESS_REGIME_DIR, PROCESS_BRANCHES)
        return Path(PROCESS_REGIME_DIR) / branch / PAPERS_DIRNAME / slug

    if top == FUNCTION_APPLICATION_DIR:
        branch, slug = _extract_branch_and_slug(tuple(user_rel.parts[1:]), FUNCTION_APPLICATION_DIR, FUNCTION_BRANCHES)
        return Path(FUNCTION_APPLICATION_DIR) / branch / PAPERS_DIRNAME / slug

    stages = ", ".join(STAGE_PIPELINE)
    die(format_error(ErrorCode.INVALID_PARENT, f"Paper must be under stages: {stages}"))


def entry_tex_candidates(paper_dir: Path) -> list[Path]:
    """Return possible entrypoint tex paths for a paper directory (new-first)."""
    return [
        paper_dir / f"{paper_dir.name}.tex",
        paper_dir / "main.tex",
    ]


def entry_tex_path(paper_dir: Path) -> Path:
    """Return the existing entry tex path, preferring folder-named files."""
    for candidate in entry_tex_candidates(paper_dir):
        if candidate.exists():
            return candidate
    # Default to preferred naming even if missing, for callers creating files
    return paper_dir / f"{paper_dir.name}.tex"
