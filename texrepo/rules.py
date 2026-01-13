from __future__ import annotations
from pathlib import Path

from .common import die

STAGES = [
    "00_core",
    "01_derivations",
    "02_interpretations",
    "03_applications",
    "04_testbeds",
]

CORE_STAGE = "00_core"
CORE_PAPER_REL = Path("00_core") / "core"


def is_under(path: Path, maybe_parent: Path) -> bool:
    try:
        path.resolve().relative_to(maybe_parent.resolve())
        return True
    except Exception:
        return False


def assert_stage_parent_allowed(parent_rel: Path) -> None:
    # nd allowed only under stages 01-04 (or any subdir inside them)
    top = parent_rel.parts[0] if parent_rel.parts else ""
    if top == CORE_STAGE:
        die("Cannot create domains under 00_core. Core is unique and immutable.")
    if top not in STAGES:
        die(f"Parent must be under a known stage: {', '.join(STAGES)}")
    if top == "00_core":
        die("Cannot create domains under 00_core.")


def assert_paper_allowed(domain_rel: Path) -> None:
    # np allowed only under stages 01-04
    top = domain_rel.parts[0] if domain_rel.parts else ""
    if top == CORE_STAGE:
        die("Cannot create papers under 00_core. Core paper already exists.")
    if top not in STAGES:
        die(f"Paper must be inside stages 01-04. Known stages: {', '.join(STAGES)}")
    if top == "00_core":
        die("Cannot create papers under 00_core.")
