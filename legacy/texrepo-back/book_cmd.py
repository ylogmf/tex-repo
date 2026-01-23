"""tex-repo book command - create a new book-class document at repo root."""
from __future__ import annotations

from pathlib import Path

from .common import find_repo_root, next_prefix, die, write_text
from .section_cmd import format_chapter_title


# Book entry template with frontmatter/mainmatter separation
BOOK_ENTRY_TEMPLATE = r"""\documentclass[11pt,letterpaper]{{book}}

\input{{../shared/preamble.tex}}

\title{{{{{title}}}}}
\author{{{{}}}}
\date{{{{}}}}

\begin{{document}}

\frontmatter
\maketitle
\input{{{{build/sections_index.tex}}}}

\mainmatter
\input{{{{build/chapters_index.tex}}}}

\backmatter
% Backmatter is included via chapters_index.tex

\end{{document}}
"""

BOOK_FRONTMATTER = {
    "title.tex": r"""\begin{{{{titlepage}}}}
\centering

{{{{\LARGE {title}}}}}\\[1.5em]
{{{{\large Structural orientation}}}}\\[2.0em]

\textit{{{{Navigation-only front matter; substantive content begins in chapters.}}}}

\vfill

\end{{{{titlepage}}}}
""",
    "preface.tex": r"""\section*{{{{Preface}}}}

This preface sets the reader contract for the book. It explains why the material is ordered, how navigation works, and what will not be provided here.

\begin{{{{itemize}}}}
\item \textbf{{{{Purpose}}}}: provide a book-scale map and orientation.
\item \textbf{{{{Audience stance}}}}: assume readers are new to this material and need a stable entry point.
\item \textbf{{{{Non-goals}}}}: no claims, results, or conclusions are presented in this front matter; it only frames how to use the chapters that follow.
\end{{{{itemize}}}}
""",
    "how_to_read.tex": r"""\section*{{{{How to Read This Book}}}}

This book is organized as a progressive training sequence.

\begin{{{{itemize}}}}
\item \textbf{{{{Progressive spine}}}}: chapters are arranged so later material depends on constraints set earlier; read in order.
\item \textbf{{{{Partial definitions}}}}: early chapters may leave terms intentionally partial so that later chapters can refine or restrict them.
\item \textbf{{{{Recognition goals}}}}: each chapter names what readers should be able to recognize when finishing it and what it avoids claiming.
\item \textbf{{{{Separation of roles}}}}: structure lives in this entry file and front matter; substantive content stays inside chapter subsections.
\end{{{{itemize}}}}
""",
    "toc.tex": r"""\clearpage
\tableofcontents
\clearpage
""",
}

BOOK_BACKMATTER = {
    "scope_limits.tex": r"""\section*{{{{Scope Limits}}}}

\begin{{{{itemize}}}}
\item This book is limited to framing, navigation, and learning objectives; it does not assert theoretical results.
\item Items that require proofs, data, or full formalism are deferred to specialized documents.
\item Chapters may reference constraints established earlier but do not extend them beyond what is stated in those chapters.
\end{{{{itemize}}}}
""",
}


def cmd_book(args) -> int:
    """Create a new book at the repository root."""
    repo_root = find_repo_root()
    
    # Must run from repo root
    if Path.cwd().resolve() != repo_root:
        die("Must run 'tex-repo book' from repository root")
    
    # Get next prefix for the book
    prefix = next_prefix(repo_root)
    title = args.title
    
    # Create slug from title
    import re
    slug = re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')
    
    book_dir = repo_root / f"{prefix}_{slug}"
    if book_dir.exists():
        die(f"Book directory already exists: {book_dir.relative_to(repo_root)}")
    
    # Create book structure
    book_dir.mkdir(parents=True)
    
    # Create main .tex file (book class)
    book_name = book_dir.name
    entry_tex = book_dir / f"{book_name}.tex"
    write_text(entry_tex, BOOK_ENTRY_TEMPLATE.format(title=title))
    
    # Create build directory
    build_dir = book_dir / "build"
    build_dir.mkdir()
    
    # Create parts structure
    parts_dir = book_dir / "parts"
    parts_dir.mkdir()
    
    # Create frontmatter
    frontmatter_dir = parts_dir / "frontmatter"
    frontmatter_dir.mkdir()
    for filename, content in BOOK_FRONTMATTER.items():
        write_text(frontmatter_dir / filename, content.format(title=title))
    
    # Create backmatter
    backmatter_dir = parts_dir / "backmatter"
    backmatter_dir.mkdir()
    for filename, content in BOOK_BACKMATTER.items():
        write_text(backmatter_dir / filename, content)
    
    # Create parts/parts directory for actual parts
    parts_root = parts_dir / "parts"
    parts_root.mkdir()
    
    # Create README.md
    readme = book_dir / "README.md"
    write_text(readme, f"# {title}\n\nBook-class document in tex-repo.\n")
    
    # Create initial empty indices
    sections_index = build_dir / "sections_index.tex"
    chapters_index = build_dir / "chapters_index.tex"
    write_text(sections_index, "% Frontmatter spine - auto-generated\n")
    write_text(chapters_index, "% Mainmatter spine - auto-generated\n")
    
    print(f"✅ Created book: {book_dir.relative_to(repo_root)}")
    print(f"   Entry file: {entry_tex.relative_to(repo_root)}")
    print(f"   Use 'tex-repo part' to add parts")
    return 0
