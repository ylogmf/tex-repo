from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class TexRepoError(RuntimeError):
    pass


def die(msg: str) -> None:
    raise TexRepoError(msg)


def find_repo_root(start=None) -> Path:
    d = (start or Path.cwd()).resolve()
    for cur in [d, *d.parents]:
        if (cur / ".paperrepo").is_file():
            return cur
    die("Not inside a tex repo (missing .paperrepo). Run: tex-repo init <name>")


def normalize_rel_path(p: str) -> str:
    # Collapse repeated slashes + trim trailing slash
    while "//" in p:
        p = p.replace("//", "/")
    p = p.rstrip("/")
    return p


def next_prefix(parent: Path) -> str:
    max_n = -1
    for child in parent.iterdir():
        if not child.is_dir():
            continue
        name = child.name
        if len(name) >= 3 and name[:2].isdigit() and name[2] == "_":
            n = int(name[:2])
            max_n = max(max_n, n)
    return f"{max_n + 1:02d}"


def relpath_to_shared(repo_root: Path, paper_dir: Path) -> str:
    rel_to_root = Path(
        Path.relpath(repo_root, paper_dir)  # type: ignore[attr-defined]
    )
    # On some python builds, Path.relpath isn't present, so do:
    # rel_to_root = Path(__import__("os").path.relpath(repo_root, paper_dir))
    import os
    rel_to_root = Path(os.path.relpath(repo_root, paper_dir))
    return str(rel_to_root / "shared")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
