from __future__ import annotations

from pathlib import Path

from .common import die
from .errors import ErrorCode, format_error
from .layouts import (
    DEFAULT_LAYOUT,
    get_function_branches,
    get_process_branches,
    stage_dir,
    stage_pipeline,
    world_paths_for_layout,
)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def _suggest_closest_stage(invalid_stage: str, layout_name: str = DEFAULT_LAYOUT) -> str:
    """Find the closest valid stage name to the invalid one."""
    stages = stage_pipeline(layout_name)
    if not stages:
        return ""
    
    # Calculate distances and find the closest
    closest_stage = min(stages, key=lambda s: _levenshtein_distance(invalid_stage.lower(), s.lower()))
    distance = _levenshtein_distance(invalid_stage.lower(), closest_stage.lower())
    
    # Only suggest if the distance is reasonably small (e.g., 1-3 edits)
    if distance <= 3:
        return f" Did you mean '{closest_stage}'?"
    return ""

# Stage and layer names (default layout)
WORLD_DIR = stage_dir(DEFAULT_LAYOUT, "world") or "00_world"
FOUNDATION_REL, SPEC_REL = world_paths_for_layout(DEFAULT_LAYOUT) or (
    Path(WORLD_DIR) / "00_foundation",
    Path(WORLD_DIR) / "01_spec",
)
FOUNDATION_DIRNAME = FOUNDATION_REL.name
SPEC_DIRNAME = SPEC_REL.name
FORMALISM_DIR = stage_dir(DEFAULT_LAYOUT, "formalism") or "01_formalism"
PROCESS_REGIME_DIR = stage_dir(DEFAULT_LAYOUT, "process_regime") or "02_process_regime"
FUNCTION_APPLICATION_DIR = stage_dir(DEFAULT_LAYOUT, "function_application") or "03_function_application"
PAPERS_DIRNAME = "papers"

# Structured subdomains
PROCESS_BRANCHES = get_process_branches(DEFAULT_LAYOUT)
FUNCTION_BRANCHES = get_function_branches(DEFAULT_LAYOUT)

# Pipelines and allowed top-level stages (in order)
STAGE_PIPELINE = stage_pipeline(DEFAULT_LAYOUT)
STAGES = STAGE_PIPELINE


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


def resolve_domain_parent(parent_rel: Path, layout_name: str = DEFAULT_LAYOUT) -> Path:
    """Return canonical parent directory where a new numbered folder should be created.
    Automatically inserts papers/ where required and enforces process/regime splits.
    """
    if not parent_rel.parts:
        die(format_error(ErrorCode.INVALID_PARENT, "Parent path cannot be empty"))

    top = parent_rel.parts[0]

    intro_dir = stage_dir(layout_name, "introduction")
    if intro_dir and top == intro_dir:
        die(format_error(ErrorCode.INVALID_PARENT, f"Use dedicated section creation for {intro_dir} (no papers/ here)"))

    world_dir = stage_dir(layout_name, "world")
    if world_dir and top == world_dir:
        die(format_error(ErrorCode.INVALID_PARENT, f"Cannot create numbered domains under {world_dir}"))

    simple_stages = [s for s in (stage_dir(layout_name, "formalism"), stage_dir(layout_name, "hypnosis")) if s]

    if top in simple_stages:
        tail = parent_rel.parts[1:]
        if not tail:
            return Path(top) / PAPERS_DIRNAME
        if tail[0] == PAPERS_DIRNAME:
            _expect_no_extra(tuple(tail[1:]), f"{top}/{PAPERS_DIRNAME}")
            return parent_rel
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{top}/papers' as parent for new topics"))

    process_dir = stage_dir(layout_name, "process_regime")
    if process_dir and top == process_dir:
        process_branches = get_process_branches(layout_name)
        branch = parent_rel.parts[1] if len(parent_rel.parts) > 1 else None
        if branch not in process_branches:
            branches = ", ".join(process_branches)
            die(format_error(ErrorCode.INVALID_PARENT, f"{process_dir} requires subdomain: {branches}"))
        tail = parent_rel.parts[2:]
        if not tail:
            return Path(process_dir) / branch / PAPERS_DIRNAME
        if tail[0] == PAPERS_DIRNAME:
            _expect_no_extra(tuple(tail[1:]), f"{process_dir}/{branch}/{PAPERS_DIRNAME}")
            return parent_rel
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{process_dir}/{branch}/papers' as parent for new subjects"))

    function_dir = stage_dir(layout_name, "function_application")
    if function_dir and top == function_dir:
        function_branches = get_function_branches(layout_name)
        branch = parent_rel.parts[1] if len(parent_rel.parts) > 1 else None
        if branch not in function_branches:
            branches = ", ".join(function_branches)
            die(format_error(ErrorCode.INVALID_PARENT, f"{function_dir} requires subdomain: {branches}"))
        tail = parent_rel.parts[2:]
        if not tail:
            return Path(function_dir) / branch / PAPERS_DIRNAME
        if tail[0] == PAPERS_DIRNAME:
            _expect_no_extra(tuple(tail[1:]), f"{function_dir}/{branch}/{PAPERS_DIRNAME}")
            return parent_rel
        die(format_error(ErrorCode.INVALID_PARENT, f"Use '{function_dir}/{branch}/papers' as parent for new subjects"))

    stages = ", ".join(stage_pipeline(layout_name))
    suggestion = _suggest_closest_stage(top, layout_name)
    die(format_error(ErrorCode.INVALID_PARENT, f"Parent must be under known stages: {stages}{suggestion}"))


def resolve_paper_path(user_rel: Path, layout_name: str = DEFAULT_LAYOUT) -> Path:
    """Return canonical paper directory path given a user-supplied relative path."""
    if not user_rel.parts:
        die(format_error(ErrorCode.INVALID_PARENT, "Paper path cannot be empty"))

    top = user_rel.parts[0]

    intro_dir = stage_dir(layout_name, "introduction")
    if intro_dir and top == intro_dir:
        die(format_error(ErrorCode.INVALID_PARENT, f"Papers cannot be placed under {intro_dir}; create sections there instead"))

    world_dir = stage_dir(layout_name, "world")
    world_paths = world_paths_for_layout(layout_name)
    if world_dir and top == world_dir:
        if world_paths and len(user_rel.parts) == 2:
            allowed = {p.name for p in world_paths}
            if user_rel.parts[1] in allowed:
                return user_rel
        allowed = ", ".join(p.name for p in world_paths) if world_paths else ""
        die(format_error(ErrorCode.INVALID_PARENT, f"Only {allowed} are allowed under {world_dir}"))

    simple_stages = [s for s in (stage_dir(layout_name, "formalism"), stage_dir(layout_name, "introduction"), stage_dir(layout_name, "hypnosis")) if s]
    if top in simple_stages:
        slug = _extract_slug(tuple(user_rel.parts[1:]), top, allow_papers_prefix=True)
        return Path(top) / PAPERS_DIRNAME / slug

    process_dir = stage_dir(layout_name, "process_regime")
    if process_dir and top == process_dir:
        branch, slug = _extract_branch_and_slug(tuple(user_rel.parts[1:]), process_dir, get_process_branches(layout_name))
        return Path(process_dir) / branch / PAPERS_DIRNAME / slug

    function_dir = stage_dir(layout_name, "function_application")
    if function_dir and top == function_dir:
        branch, slug = _extract_branch_and_slug(tuple(user_rel.parts[1:]), function_dir, get_function_branches(layout_name))
        return Path(function_dir) / branch / PAPERS_DIRNAME / slug

    stages = ", ".join(stage_pipeline(layout_name))
    suggestion = _suggest_closest_stage(top, layout_name)
    die(format_error(ErrorCode.INVALID_PARENT, f"Paper must be under stages: {stages}{suggestion}"))


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
