from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, die, normalize_rel_path, write_text
from .rules import assert_paper_allowed
from .meta_cmd import parse_paperrepo_metadata
from .config import get_paper_config


def parse_np_args(path_or_domain: str, maybe_slug):
    """Parse arguments for new paper command. Supports both 'domain slug' and 'domain/slug' formats."""
    p = normalize_rel_path(path_or_domain)
    
    # If maybe_slug is provided, always use 2-arg form: domain_path + slug
    if maybe_slug is not None:
        return Path(p), maybe_slug
    
    # If maybe_slug is None, try to parse path_or_domain as domain/slug format
    if "/" in p:
        domain = Path(p).parent
        slug = Path(p).name
        if not slug:
            die("Invalid paper path: missing paper slug.\n"
                "Hint: Use 'tex-repo np <domain> <paper-name>' or 'tex-repo np <domain>/<paper-name>'")
        return domain, slug
    
    # Neither 2-arg form nor domain/slug format provided
    die("Usage: tex-repo np <domain_path> <paper_slug> [title] OR tex-repo np <domain_path>/<paper_slug> [title]")


def write_paper_skeleton(repo: Path, paper_dir: Path, title: str) -> None:
    """Create a new paper structure with main.tex and section files.
    
    Args:
        repo: Repository root path
        paper_dir: Target directory for the new paper
        title: Paper title for LaTeX document
        
    Creates:
        - main.tex with proper imports and metadata integration
        - refs.bib for bibliography
        - sections/ directory with 11 section files (0=abstract, 1-10=content)
        - build/ directory for LaTeX output
    """
    (paper_dir / "sections").mkdir(parents=True, exist_ok=True)
    (paper_dir / "build").mkdir(parents=True, exist_ok=True)

    # compute rel path to shared
    import os
    rel_to_shared = Path(os.path.relpath(repo / "shared", paper_dir)).as_posix()
    
    # Get metadata for date policy and bibliography style
    metadata = parse_paperrepo_metadata(repo)
    date_macro = r"\date{\today}" if metadata.get('date_policy', 'today') == 'today' else r"\date{}"
    bib_style = metadata.get('default_bibliography_style', 'plainnat')
    
    # Get paper configuration
    config = get_paper_config(repo)
    section_count = config['section_count']
    doc_class = config['document_class']
    doc_options = config['document_options']
    include_abstract = config['include_abstract']

    write_text(paper_dir / "refs.bib", "% BibTeX entries here\n")

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
    
    # Add section inputs based on configuration
    section_inputs = "\n".join([rf"\input{{sections/section_{i}}}" for i in range(1, section_count + 1)])
    main += f"\n{section_inputs}\n"
    
    main += rf"""
\bibliographystyle{{{bib_style}}}
\bibliography{{refs}}

\end{{document}}
"""
    write_text(paper_dir / "main.tex", main)

    if include_abstract:
        write_text(paper_dir / "sections" / "section_0.tex", "% Abstract\n\nWrite abstract here.\n")
    
    for i in range(1, section_count + 1):
        write_text(paper_dir / "sections" / f"section_{i}.tex", f"\\section{{Section {i}}}\n\nWrite here.\n")

    if not (paper_dir / "README.md").exists():
        write_text(
            paper_dir / "README.md",
            "# Paper\n\nThis paper depends on the Spec through its enclosing domain and stage.\n",
        )


def cmd_np(args) -> int:
    repo = find_repo_root()

    domain_rel, slug = parse_np_args(args.path_or_domain, args.maybe_slug)
    assert_paper_allowed(domain_rel)

    domain_abs = (repo / domain_rel).resolve()
    if not domain_abs.is_dir():
        die(f"Domain path not found: {domain_rel}\n"
            f"Hint: Create the domain first with 'tex-repo nd {domain_rel.parent} {domain_rel.name}' if it's a numbered domain")

    paper_dir = domain_abs / slug
    if paper_dir.exists():
        die(f"Paper already exists: {domain_rel}/{slug}\n"
            f"Hint: Use a different paper name or remove the existing directory first")

    write_paper_skeleton(repo, paper_dir, args.title or "Untitled Paper")
    print(f"✅ New paper: {domain_rel}/{slug}")
    return 0
