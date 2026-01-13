from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, normalize_rel_path
from .rules import assert_stage_parent_allowed


def cmd_nd(args) -> int:
    repo = find_repo_root()
    parent_rel = Path(normalize_rel_path(args.parent_path))
    assert_stage_parent_allowed(parent_rel)

    parent_abs = (repo / parent_rel).resolve()
    if not parent_abs.is_dir():
        die(f"Parent path not found: {parent_rel}")

    prefix = next_prefix(parent_abs)
    target = parent_abs / f"{prefix}_{args.domain_name}"
    if target.exists():
        die(f"Domain already exists: {target}")

    target.mkdir(parents=True)
    print(f"✅ New domain: {parent_rel}/{prefix}_{args.domain_name}")
    return 0
