from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, die, normalize_rel_path, write_text, relpath_to_shared
from .rules import (
    entry_tex_candidates,
    entry_tex_path,
    resolve_paper_path,
    FOUNDATION_REL,
    SPEC_REL,
)
from .meta_cmd import parse_paperrepo_metadata
from .config import get_paper_config


def parse_np_args(path_or_domain: str, maybe_slug, provided_title: str | None):
    """Parse arguments for new paper command into a relative path and optional title override."""
    base = Path(normalize_rel_path(path_or_domain))
    inferred_title = None

    if maybe_slug is None:
        if not base.parts:
            die("Usage: tex-repo np <path>/<name> [title]")
        return base, inferred_title

    if provided_title and provided_title != "Untitled Paper":
        if not str(maybe_slug).strip():
            die("Invalid paper name (empty)")
        return base / normalize_rel_path(maybe_slug), inferred_title

    # Only two args were provided; decide whether second arg is a slug or a title
    if "/" in str(base):
        inferred_title = maybe_slug
        return base, inferred_title

    if not str(maybe_slug).strip():
        die("Invalid paper name (empty)")
    return base / normalize_rel_path(maybe_slug), inferred_title


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        write_text(path, content)


def _paper_metadata(repo: Path):
    metadata = parse_paperrepo_metadata(repo)
    date_macro = r"\date{\today}" if metadata.get("date_policy", "today") == "today" else r"\date{}"
    bib_style = metadata.get("default_bibliography_style", "plainnat")
    return metadata, date_macro, bib_style


def build_generic_main_content(repo: Path, paper_dir: Path, title: str):
    rel_to_shared = relpath_to_shared(repo, paper_dir)
    _metadata, date_macro, bib_style = _paper_metadata(repo)
    config = get_paper_config(repo)
    section_count = config["section_count"]
    doc_class = config["document_class"]
    doc_options = config["document_options"]
    include_abstract = config["include_abstract"]

    main = rf"""\documentclass[{doc_options}]{{{doc_class}}}

\input{{{rel_to_shared}/preamble.tex}}
\input{{{rel_to_shared}/macros.tex}}
\input{{{rel_to_shared}/notation.tex}}
\input{{{rel_to_shared}/identity.tex}}

\title{{{title}}}
\author{{\RepoAuthorName \\ \RepoAuthorAffil}}
{date_macro}

\begin{{document}}
\maketitle
"""

    if include_abstract:
        main += r"""
\begin{abstract}
\input{sections/section_0}
\end{abstract}
"""

    section_inputs = "\n".join(
        [rf"\input{{sections/section_{i}}}" for i in range(1, section_count + 1)]
    )
    main += f"\n{section_inputs}\n"

    main += rf"""
\bibliographystyle{{{bib_style}}}
\bibliography{{refs}}

\end{{document}}
"""
    return main, section_count, include_abstract


def build_foundation_main_content(repo: Path, paper_dir: Path, title: str) -> str:
    rel_to_shared = relpath_to_shared(repo, paper_dir)
    _metadata, date_macro, bib_style = _paper_metadata(repo)
    config = get_paper_config(repo)
    doc_class = config["document_class"]
    doc_options = config["document_options"]

    return rf"""\documentclass[{doc_options}]{{{doc_class}}}

\input{{{rel_to_shared}/preamble.tex}}
\input{{{rel_to_shared}/macros.tex}}
\input{{{rel_to_shared}/notation.tex}}
\input{{{rel_to_shared}/identity.tex}}

\title{{{title}}}
\author{{\RepoAuthorName \\ \RepoAuthorAffil}}
{date_macro}

\begin{{document}}
\maketitle

\input{{sections/00_definitions.tex}}
\input{{sections/01_axioms.tex}}

\bibliographystyle{{{bib_style}}}
\bibliography{{refs}}

\end{{document}}
"""


def write_generic_paper(repo: Path, paper_dir: Path, title: str) -> None:
    sections_dir = paper_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "build").mkdir(parents=True, exist_ok=True)

    _write_if_missing(paper_dir / "refs.bib", "% BibTeX entries here\n")

    entry_path = entry_tex_path(paper_dir)
    main, section_count, include_abstract = build_generic_main_content(repo, paper_dir, title)
    _write_if_missing(entry_path, main)

    if include_abstract:
        _write_if_missing(sections_dir / "section_0.tex", "% Abstract\n\nWrite abstract here.\n")

    for i in range(1, section_count + 1):
        _write_if_missing(
            sections_dir / f"section_{i}.tex",
            f"\\section{{Section {i}}}\n\nWrite here.\n",
        )

    if not (paper_dir / "README.md").exists():
        write_text(
            paper_dir / "README.md",
            "# Paper\n\nThis paper depends on the world layer and its enclosing domain.\n",
        )


def write_foundation_paper(repo: Path, paper_dir: Path, title: str) -> None:
    sections_dir = paper_dir / "sections"
    sections_dir.mkdir(parents=True, exist_ok=True)
    (paper_dir / "build").mkdir(parents=True, exist_ok=True)

    _write_if_missing(paper_dir / "refs.bib", "% BibTeX entries here\n")

    entry_path = entry_tex_path(paper_dir)
    main = build_foundation_main_content(repo, paper_dir, title)
    _write_if_missing(entry_path, main)

    _write_if_missing(
        sections_dir / "00_definitions.tex",
        "% Core definitions live here.\n",
    )
    _write_if_missing(
        sections_dir / "01_axioms.tex",
        "% Axioms and governing principles live here.\n",
    )

    if not (paper_dir / "README.md").exists():
        write_text(
            paper_dir / "README.md",
            "# Foundation\n\nImmutable foundations that all other layers rely on.\n",
        )


def write_spec_paper(repo: Path, paper_dir: Path, title: str) -> None:
    # Spec lives under 00_world/01_spec with full paper skeleton
    write_generic_paper(repo, paper_dir, title or "Spec")
    if not (paper_dir / "README.md").exists():
        write_text(
            paper_dir / "README.md",
            "# Spec\n\nThe primary specification paper for this repository.\n",
        )


def cmd_np(args) -> int:
    repo = find_repo_root()

    requested_rel, inferred_title = parse_np_args(args.path_or_domain, args.maybe_slug, args.title)
    paper_rel = resolve_paper_path(requested_rel)

    paper_dir = (repo / paper_rel).resolve()
    paper_dir.mkdir(parents=True, exist_ok=True)

    existing_entry = None
    for candidate in entry_tex_candidates(paper_dir):
        if candidate.exists():
            existing_entry = candidate
            break
    if existing_entry:
        die(
            f"Paper already exists: {paper_rel}\n"
            f"Hint: remove existing entry file ({existing_entry.name}) or choose a new path"
        )

    if args.title and args.title != "Untitled Paper":
        title = args.title
    elif inferred_title:
        title = inferred_title
    elif paper_rel == FOUNDATION_REL:
        title = "Foundation"
    elif paper_rel == SPEC_REL:
        title = "Spec"
    else:
        title = "Untitled Paper"
    if paper_rel == FOUNDATION_REL:
        write_foundation_paper(repo, paper_dir, title)
    elif paper_rel == SPEC_REL:
        write_spec_paper(repo, paper_dir, title)
    else:
        write_generic_paper(repo, paper_dir, title)

    print(f"✅ New paper: {paper_rel}")
    return 0
