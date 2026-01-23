from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, normalize_rel_path, write_text
from .layouts import get_layout
from .rules import resolve_domain_parent


def cmd_nd(args) -> int:
    repo = find_repo_root()
    layout_name = get_layout(repo)
    parent_rel = Path(normalize_rel_path(args.parent_path))
    canonical_parent_rel = resolve_domain_parent(parent_rel, layout_name)

    parent_abs = (repo / canonical_parent_rel).resolve()
    parent_abs.mkdir(parents=True, exist_ok=True)

    prefix = next_prefix(parent_abs)
    target = parent_abs / f"{prefix}_{args.domain_name}"
    if target.exists():
        die(f"Domain already exists: {target.relative_to(repo)}")

    target.mkdir(parents=True)
    readme_path = target / "README.md"
    if not readme_path.exists():
        write_text(
            readme_path,
            f"# {target.name}\n\nDomain under {canonical_parent_rel}.\n",
        )
    print(f"✅ New domain: {canonical_parent_rel}/{prefix}_{args.domain_name}")
    return 0
