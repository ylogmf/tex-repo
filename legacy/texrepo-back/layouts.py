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

# Only new layout supported - no backward compatibility
LAYOUTS: Dict[str, LayoutDefinition] = {
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
    return None


def _layout(layout_name: str) -> LayoutDefinition:
    return LAYOUTS.get(layout_name, LAYOUTS[DEFAULT_LAYOUT])


def autodetect_layout(repo_root: Path) -> str:
    """Only 'new' layout is supported."""
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
    return set(layout.required_dirs) | set(layout.extras)


def stage_dir(layout_name: str, role: str) -> str | None:
    return _layout(layout_name).stage_dirs.get(role)


def stage_pipeline(layout_name: str) -> List[str]:
    return list(_layout(layout_name).required_dirs)


def world_paths_for_layout(layout_name: str) -> tuple[Path, Path] | None:
    """No world paths in new layout - returns None."""
    return None


def get_process_branches(layout_name: str) -> Tuple[str, ...]:
    return _layout(layout_name).branches.get("process_regime", tuple())


def get_function_branches(layout_name: str) -> Tuple[str, ...]:
    return _layout(layout_name).branches.get("function_application", tuple())
