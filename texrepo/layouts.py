from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class LayoutDefinition:
    required_dirs: List[str]
    extras: Set[str]
    stage_dirs: Dict[str, str | None]
    branches: Dict[str, Tuple[str, ...]]
    world_subdirs: Tuple[str, str] | None = None


DEFAULT_LAYOUT = "new"
LEGACY_LAYOUT_ALIASES = {"staged": "old"}
ALLOWED_TOP_LEVEL_COMPAT = {"SPEC", "04_testbed", "04_testbeds"}


LAYOUTS: Dict[str, LayoutDefinition] = {
    "old": LayoutDefinition(
        required_dirs=[
            "00_world",
            "01_formalism",
            "02_process_regime",
            "03_function_application",
        ],
        extras={"shared", "scripts", "98_context", "99_legacy", "releases"},
        stage_dirs={
            "world": "00_world",
            "formalism": "01_formalism",
            "process_regime": "02_process_regime",
            "function_application": "03_function_application",
        },
        branches={
            "process_regime": ("process", "regime"),
            "function_application": ("function", "application"),
        },
        world_subdirs=("00_foundation", "01_spec"),
    ),
    "new": LayoutDefinition(
        required_dirs=[
            "00_introduction",
            "01_process_regime",
            "02_function_application",
            "03_hypnosis",
        ],
        extras={"shared", "scripts", "98_context", "99_legacy", "releases"},
        stage_dirs={
            "introduction": "00_introduction",
            "process_regime": "01_process_regime",
            "function_application": "02_function_application",
            "hypnosis": "03_hypnosis",
        },
        branches={
            "process_regime": ("process", "regime"),
            "function_application": ("function", "application"),
        },
    ),
}


def normalize_layout_name(name: str | None) -> str | None:
    if not name:
        return None
    normalized = name.strip().lower()
    if normalized in LAYOUTS:
        return normalized
    if normalized in LEGACY_LAYOUT_ALIASES:
        return LEGACY_LAYOUT_ALIASES[normalized]
    return None


def _layout(layout_name: str) -> LayoutDefinition:
    return LAYOUTS.get(layout_name, LAYOUTS[DEFAULT_LAYOUT])


def autodetect_layout(repo_root: Path) -> str:
    """Infer layout from on-disk structure."""
    new_root = _layout("new").stage_dirs.get("introduction")
    if new_root and (repo_root / new_root).exists():
        return "new"
    return DEFAULT_LAYOUT


def get_layout(repo_root: Path) -> str:
    """Return configured layout or fall back to auto-detection."""
    try:
        from .meta_cmd import parse_paperrepo_metadata
    except Exception:
        parse_paperrepo_metadata = None

    if parse_paperrepo_metadata:
        metadata = parse_paperrepo_metadata(repo_root)
        config_layout = normalize_layout_name(metadata.get("layout"))
        if config_layout:
            return config_layout

    return autodetect_layout(repo_root)


def required_dirs(layout_name: str) -> List[str]:
    return list(_layout(layout_name).required_dirs)


def allowed_top_level(layout_name: str) -> Set[str]:
    layout = _layout(layout_name)
    return set(layout.required_dirs) | set(layout.extras) | set(ALLOWED_TOP_LEVEL_COMPAT)


def stage_dir(layout_name: str, role: str) -> str | None:
    return _layout(layout_name).stage_dirs.get(role)


def stage_pipeline(layout_name: str) -> List[str]:
    return list(_layout(layout_name).required_dirs)


def world_paths_for_layout(layout_name: str) -> tuple[Path, Path] | None:
    layout = _layout(layout_name)
    world_dir = layout.stage_dirs.get("world")
    if not world_dir or not layout.world_subdirs:
        return None
    foundation, spec = layout.world_subdirs
    return Path(world_dir) / foundation, Path(world_dir) / spec


def get_process_branches(layout_name: str) -> Tuple[str, ...]:
    return _layout(layout_name).branches.get("process_regime", tuple())


def get_function_branches(layout_name: str) -> Tuple[str, ...]:
    return _layout(layout_name).branches.get("function_application", tuple())
