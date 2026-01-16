from __future__ import annotations
from pathlib import Path

from .common import die

SPEC_DIR = "SPEC"
SPEC_PAPER_REL = Path(SPEC_DIR) / "spec"
STAGE_PIPELINE = [
    "01_formalism",
    "02_processes",
    "03_applications",
    "04_testbeds",
]
STAGES = [SPEC_DIR, *STAGE_PIPELINE]


def is_under(path: Path, maybe_parent: Path) -> bool:
    try:
        path.resolve().relative_to(maybe_parent.resolve())
        return True
    except Exception:
        return False


def assert_stage_parent_allowed(parent_rel: Path) -> None:
    # nd allowed only under stages 01-04 (or any subdir inside them)
    top = parent_rel.parts[0] if parent_rel.parts else ""
    if top == SPEC_DIR:
        die("Cannot create domains under Spec. Spec is unique and immutable.")
    if top not in STAGE_PIPELINE:
        die(f"Parent must be under a known stage: {', '.join(STAGE_PIPELINE)}")


def assert_paper_allowed(domain_rel: Path) -> None:
    # np allowed only under stages 01-04
    top = domain_rel.parts[0] if domain_rel.parts else ""
    if top == SPEC_DIR:
        die("Cannot create papers under Spec. The Spec paper already exists.")
    if top not in STAGE_PIPELINE:
        die(f"Paper must be inside stages 01-04. Known stages: {', '.join(STAGE_PIPELINE)}")
