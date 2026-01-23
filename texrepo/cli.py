import argparse
from pathlib import Path

from .init_cmd import cmd_init
from .domain_cmd import cmd_nd
from .paper_cmd import cmd_np
from .build_cmd import cmd_build
from .status_cmd import cmd_status
from .meta_cmd import cmd_sync_meta
from .config_cmd import cmd_config
from .release_cmd import cmd_release
from .fix_cmd import cmd_fix
from .env_cmd import check_environment, generate_guide
from .install_cmd import execute_guide
from .section_cmd import cmd_ns, cmd_npart
from .layouts import DEFAULT_LAYOUT, LAYOUTS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tex-repo",
        description="LaTeX repository manager with book-scale Introduction (Part/Chapter structure), paper-scale stages, and immutable releases"
    )
    sub = p.add_subparsers(dest="cmd", required=True, title="Available commands", metavar="COMMAND")

    p_init = sub.add_parser(
        "init",
        help="Initialize a new LaTeX theory repository with Part/Chapter introduction structure",
        description="""
Initialize a new tex-repo with a book-scale introduction (00_introduction/) using Part/Chapter
structure and paper-scale stages (process, function, hypnosis). Use 'npart' to create parts
and 'ns' to add chapters within parts.
""",
    )
    p_init.add_argument(
        "target",
        help="Repository name for the new tex-repo",
    )
    p_init.add_argument(
        "--legacy-seed-text",
        metavar="PATH",
        help="[LEGACY] Path to a .txt file whose contents seed 00_world/01_spec/sections/section_1.tex (old layout only)",
    )
    p_init.add_argument(
        "--layout",
        choices=sorted(LAYOUTS.keys()),
        default="new",
        help="Choose repository layout (default: new; introduction is book-structured)",
    )
    p_init.set_defaults(fn=cmd_init)

    p_nd = sub.add_parser("nd", help="Create a new folder under the correct papers/ root with automatic numbering (00_, 01_, etc.)")
    p_nd.add_argument("parent_path", help="Parent path (e.g., '01_process_regime/process', '02_function_application/application'); not for 00_introduction (use ns).")
    p_nd.add_argument("domain_name", help="Descriptive name for the research domain or topic (e.g., 'quantum-mechanics')")
    p_nd.set_defaults(fn=cmd_nd)

    p_np = sub.add_parser("np", help="Create a new paper with LaTeX template, sections, and bibliography (entry file matches folder name)")
    # Supports: np domain_path slug [title]  OR  np domain_path/slug [title]
    p_np.add_argument("path_or_domain", help="Target domain path (e.g., '01_process_regime/process/00_topic') or full paper path; not for 00_introduction (use ns).")
    p_np.add_argument("maybe_slug", nargs="?", help="URL-friendly paper identifier (optional if included in first argument)")
    p_np.add_argument("title", nargs="?", default="Untitled Paper", help="Human-readable title for the paper (default: 'Untitled Paper')")
    p_np.set_defaults(fn=cmd_np)

    p_ns = sub.add_parser(
        "ns",
        help="Create a numbered Chapter within an Introduction Part (creates chapter.tex + 1-1..1-10)",
        description="Create a chapter inside a part of the introduction book with chapter.tex (chapter prologue) and section files (1-1.tex ... 1-10.tex). Use --part to specify target part.",
    )
    p_ns.add_argument("section_name", help="Chapter name (will be prefixed with the next number, e.g., 01_<name>)")
    p_ns.add_argument("--part", help="Target part name or number (default: 01_part-1, created if missing)")
    p_ns.set_defaults(fn=cmd_ns)

    p_npart = sub.add_parser(
        "npart",
        help="Create a new Part in the Introduction book (00_introduction/parts/parts/...)",
        description="Create a new part directory with part.tex (part introduction) and an empty chapters/ directory.",
    )
    p_npart.add_argument("part_name", help="Part name (will be prefixed with the next number, e.g., 01_<name>)")
    p_npart.set_defaults(fn=cmd_npart)

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
