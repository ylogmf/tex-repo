import argparse
from pathlib import Path

from .init_simple_cmd import cmd_init_simple
from .book_cmd import cmd_book
from .paper_cmd import cmd_paper, cmd_np
from .part_cmd import cmd_part
from .chapter_cmd import cmd_chapter
from .build_cmd import cmd_build
from .status_cmd import cmd_status
from .meta_cmd import cmd_sync_meta
from .config_cmd import cmd_config
from .release_cmd import cmd_release
from .fix_cmd import cmd_fix
from .env_cmd import check_environment, generate_guide
from .install_cmd import execute_guide


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tex-repo",
        description="LaTeX repository manager with book-class documents, article-class papers, and immutable releases"
    )
    sub = p.add_subparsers(dest="cmd", required=True, title="Available commands", metavar="COMMAND")

    # Initialize repository
    p_init = sub.add_parser(
        "init",
        help="Initialize a new tex-repo with minimal structure",
        description="Create a new repository with .paperrepo, .gitignore, and shared/ directory. Use 'book' and 'paper' to create documents.",
    )
    p_init.add_argument("name", help="Repository name")
    p_init.set_defaults(fn=cmd_init_simple)

    # New simplified commands
    p_book = sub.add_parser(
        "book",
        help="Create a new book-class document at repository root",
        description="Create a new top-level book with parts/, chapters/, frontmatter, and backmatter structure. Must run from repository root.",
    )
    p_book.add_argument("title", help="Book title")
    p_book.set_defaults(fn=cmd_book)

    p_paper = sub.add_parser(
        "paper",
        help="Create a new article-class paper at repository root",
        description="Create a new top-level paper with article class. Must run from repository root.",
    )
    p_paper.add_argument("title", help="Paper title")
    p_paper.set_defaults(fn=cmd_paper)

    p_part = sub.add_parser(
        "part",
        help="Create a new part inside a book",
        description="Create a new part with part.tex inside a book directory. Must run inside a book folder (detects parts/ or book-class .tex).",
    )
    p_part.add_argument("title", help="Part title")
    p_part.set_defaults(fn=cmd_part)

    p_chapter = sub.add_parser(
        "chapter",
        help="Create a new chapter inside a part",
        description="Create a new chapter.tex file inside a part's chapters/ directory. Must run inside a part folder.",
    )
    p_chapter.add_argument("title", help="Chapter title")
    p_chapter.set_defaults(fn=cmd_chapter)

    p_b = sub.add_parser("b", help="Compile LaTeX papers to PDF with smart caching and dependency tracking",
                        description="""
Build LaTeX papers with automatic dependency detection and smart caching. 
The latexmk engine auto-reruns until references stabilize. The pdflatex engine 
runs twice automatically to resolve references and citations.
""")
    p_b.add_argument("target", nargs="?", default=".", help="Paper path relative to repo root, '.' for current directory, or 'all' for all papers")
    p_b.add_argument("--engine", default="latexmk", choices=["latexmk", "pdflatex"], help="LaTeX compilation engine. latexmk auto-reruns until stable, pdflatex runs twice")
    p_b.add_argument("--clean", action="store_true", help="Remove build artifacts before compilation")
    p_b.add_argument("--force", action="store_true", help="Force rebuild even if output is up-to-date")
    p_b.add_argument("--verbose", action="store_true", help="Show full build output and trailing log snippet on failure")
    p_b.set_defaults(fn=cmd_build)

    p_status = sub.add_parser("status", help="Validate repository structure and show compliance with tex-repo conventions")
    p_status.set_defaults(fn=cmd_status)

    p_sync_meta = sub.add_parser("sync-meta", help="Update shared/identity.tex with current author and repository metadata")
    p_sync_meta.set_defaults(fn=cmd_sync_meta)

    p_config = sub.add_parser("config", help="Generate .texrepo-config file with customizable paper and build settings")
    p_config.set_defaults(fn=cmd_config)

    p_release = sub.add_parser("release", help="Create immutable release bundle for a paper with PDF, sources, and metadata",
                               description="""
Create an immutable release bundle for a paper by snapshotting the built PDF plus all inputs 
required to reproduce it. Release bundles contain the compiled PDF, complete source snapshot, 
and cryptographic hashes for verification.

Release bundles are stored at the repository level in releases/ directory and tracked in 
index.jsonl for audit trail. Each release creates a unique directory with paper-aware naming.
""")
    p_release.add_argument("paper_path", 
                          help="Path to paper directory relative to repository root (e.g., '00_world/01_spec', '01_formalism/papers/00_topic')")
    p_release.add_argument("--label", 
                          help="Descriptive label for the release (e.g., 'submitted', 'camera-ready'). Optional.")
    p_release.add_argument("--engine", default="latexmk", choices=["latexmk", "pdflatex"], 
                          help="LaTeX compilation engine for building PDF if needed (default: latexmk)")
    p_release.add_argument("--clean", action="store_true", 
                          help="Remove build artifacts before compilation to ensure clean build")
    p_release.set_defaults(fn=cmd_release)

    p_fix = sub.add_parser("fix", help="Repair repository structure by creating missing files and folders",
                          description="""
Repair repository structure by creating missing files and folders. This command follows a 
conservative policy: it NEVER overwrites, modifies, or deletes existing files. It only 
creates missing structure elements like folders, configuration files, and templates.

Use --dry-run to see what would be created without making any changes.
""")
    p_fix.add_argument("--dry-run", action="store_true", 
                      help="Show what would be created without making any changes")
    p_fix.set_defaults(fn=cmd_fix)

    # Environment support commands
    p_env = sub.add_parser("env", help="Environment checking and setup assistance",
                          description="""
Environment support tools for tex-repo. These commands help verify system readiness
and generate setup guides for required LaTeX tools.
""")
    env_sub = p_env.add_subparsers(dest="env_cmd", required=True, title="Environment commands", metavar="SUBCOMMAND")
    
    p_env_check = env_sub.add_parser("check", help="Check system environment for tex-repo readiness",
                                    description="""
Inspect the local environment and report readiness for using tex-repo. This command
does NOT modify the system or install anything - it only reports the current state
of required tools and suggests next steps if tools are missing.
""")
    p_env_check.set_defaults(fn=lambda args: check_environment())
    
    p_env_guide = env_sub.add_parser("guide", help="Generate system-specific setup guide",
                                    description="""
Generate env_guide.txt with installation instructions tailored to your current system.
This command writes documentation, not code. The generated guide can be used with
'tex-repo install' command for automated setup (personal use only).
""")
    p_env_guide.set_defaults(fn=lambda args: generate_guide())

    p_install = sub.add_parser("install", help="Execute installation commands from tex-repo generated guide",
                              description="""
Execute system installation commands from a tex-repo generated guide. This command
is EXPLICITLY UNSAFE by default and intended for personal use only.

IMPORTANT WARNINGS:
- Only accepts guides generated by tex-repo env guide
- Requires explicit user confirmation before executing any commands
- May require administrator privileges (sudo)
- Can modify your system and install large packages
- Should only be used on systems you own and control

Use 'tex-repo env guide' to generate a guide first.
""")
    p_install.add_argument("guide_path", help="Path to env_guide.txt file generated by 'tex-repo env guide'")
    p_install.set_defaults(fn=lambda args: execute_guide(args.guide_path))

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    from .common import TexRepoError
    try:
        return int(args.fn(args) or 0)
    except TexRepoError as e:
        if getattr(args, "verbose", False):
            import traceback
            traceback.print_exc()
        else:
            print(f"ERROR: {e}")
        return 1
