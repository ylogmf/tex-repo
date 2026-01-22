from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from .common import find_repo_root, die, write_text
from .config import create_default_config
from .meta_cmd import sync_identity_tex
from .layouts import (
    LAYOUTS,
    DEFAULT_LAYOUT,
    get_function_branches,
    get_layout,
    get_process_branches,
    required_dirs,
    stage_dir,
    world_paths_for_layout,
)
from .rules import (
    PAPERS_DIRNAME,
)
from .paper_cmd import build_generic_main_content, build_foundation_main_content
from .init_cmd import INTRO_ENTRY_TEMPLATE, INTRO_FRONTMATTER, INTRO_BACKMATTER

POLICY_START = "# >>> tex-repo policy"
POLICY_END = "# <<< tex-repo policy"
_GITIGNORE_TEMPLATE = """############################
# tex-repo build artifacts
############################

# All intermediate build outputs
**/build/

############################
# LaTeX temporary files
############################

*.aux
*.log
*.out
*.toc
*.lof
*.lot
*.fls
*.fdb_latexmk
*.synctex.gz
*.synctex(busy)
*.synctex.gz(busy)

# Bibliography / biber
*.bbl
*.blg
*.bcf
*.run.xml
*.bib.bak

# Indices / glossaries
*.idx
*.ilg
*.ind
*.ist
*.glg
*.glo
*.gls
*.glsdefs
*.acn
*.acr
*.alg
*.loa
*.nlo
*.nls

# minted / pygments
_minted*
*.pyg

############################
# OS / editor noise
############################

# macOS
.DS_Store
.AppleDouble
.LSOverride
._*
.Spotlight-V100
.Trashes
.fseventsd

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# IDEs
.vscode/
.idea/
*.iml

############################
# tex-repo local files
############################

# Generated environment guide
env_guide.txt

# Internal tool state
.texrepo/

############################
# Explicitly keep releases
############################

!releases/
!releases/**
"""

class FixResult:
    def __init__(self):
        self.created = 0
        self.skipped = 0
        self.warnings = 0
        self.actions: List[Tuple[str, str]] = []  # (status, path)
    
    def add_created(self, path: str):
        self.created += 1
        self.actions.append(("created", path))
    
    def add_would_create(self, path: str):
        self.created += 1
        self.actions.append(("would_create", path))
    
    def add_skipped(self, path: str, reason: str = ""):
        self.skipped += 1
        reason_suffix = f" ({reason})" if reason else ""
        self.actions.append(("skipped", f"{path}{reason_suffix}"))
    
    def add_warning(self, path: str, reason: str):
        self.warnings += 1
        self.actions.append(("warning", f"{path} - {reason}"))


def _gitignore_policy_block() -> str:
    """Return gitignore policy template wrapped with markers."""
    template = _GITIGNORE_TEMPLATE.rstrip() + "\n"
    return f"{POLICY_START}\n{template}{POLICY_END}\n"


def ensure_readme(path: Path, content: str, result: FixResult, dry_run: bool = False) -> None:
    """Create README.md if missing without overwriting existing files."""
    check_and_create_file(path, content, result, dry_run)


def _apply_gitignore_policy(path: Path, result: FixResult, dry_run: bool = False) -> None:
    """Ensure .gitignore contains the policy block."""
    policy_block = _gitignore_policy_block()

    if not path.exists():
        if dry_run:
            result.add_would_create(str(path))
        else:
            write_text(path, policy_block)
            result.add_created(str(path))
        return

    current = path.read_text(encoding="utf-8")
    start = current.find(POLICY_START)
    end = current.find(POLICY_END)

    if start != -1 and end != -1 and end > start:
        block_end = end + len(POLICY_END)
        after = current[block_end:].lstrip("\n")
        new_content = current[:start] + policy_block
        if after:
            if not new_content.endswith("\n"):
                new_content += "\n"
            new_content += after
    else:
        # Append policy block with spacing
        new_content = current
        if not new_content.endswith("\n"):
            new_content += "\n"
        new_content += "\n" + policy_block

    if new_content == current:
        result.add_skipped(str(path), "policy already present")
        return

    if dry_run:
        result.add_would_create(str(path))
    else:
        write_text(path, new_content)
        result.add_created(str(path))


def check_and_create_directory(path: Path, result: FixResult, dry_run: bool = False) -> None:
    """Check if directory exists and create if missing."""
    if path.exists():
        result.add_skipped(str(path), "already exists")
    else:
        if dry_run:
            result.add_would_create(str(path))
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                result.add_created(str(path))
            except PermissionError:
                result.add_warning(str(path), "cannot create (permission denied)")
            except Exception as e:
                result.add_warning(str(path), f"cannot create ({e})")


def check_and_create_file(path: Path, content: str, result: FixResult, dry_run: bool = False) -> None:
    """Check if file exists and create if missing."""
    if path.exists():
        result.add_skipped(str(path), "already exists")
    else:
        if dry_run:
            result.add_would_create(str(path))
        else:
            try:
                write_text(path, content)
                result.add_created(str(path))
            except PermissionError:
                result.add_warning(str(path), "cannot create (permission denied)")
            except Exception as e:
                result.add_warning(str(path), f"cannot create ({e})")


def fix_repository_structure(repo_root: Path, result: FixResult, layout_name: str, dry_run: bool = False) -> None:
    """Fix repository folder structure."""
    print("Checking repository folder structure...")
    
    # Top-level stage folders
    top_levels = required_dirs(layout_name)
    for stage in top_levels:
        check_and_create_directory(repo_root / stage, result, dry_run)

    layout_def = LAYOUTS.get(layout_name, LAYOUTS[DEFAULT_LAYOUT])

    # Additional allowed folders
    for folder in layout_def.extras:
        check_and_create_directory(repo_root / folder, result, dry_run)

    # No world layer in new layout

    # Paper parents - no formalism in new layout
    process_dir = stage_dir(layout_name, "process_regime")
    if process_dir:
        for branch in get_process_branches(layout_name):
            check_and_create_directory(repo_root / process_dir / branch / PAPERS_DIRNAME, result, dry_run)

    function_dir = stage_dir(layout_name, "function_application")
    if function_dir:
        for branch in get_function_branches(layout_name):
            check_and_create_directory(repo_root / function_dir / branch / PAPERS_DIRNAME, result, dry_run)

    hypnosis_dir = stage_dir(layout_name, "hypnosis")
    if hypnosis_dir:
        check_and_create_directory(repo_root / hypnosis_dir / PAPERS_DIRNAME, result, dry_run)
    
    # Introduction book structure (parts/ subdirectories)
    intro_dir = stage_dir(layout_name, "introduction")
    if intro_dir:
        intro_path = repo_root / intro_dir
        check_and_create_directory(intro_path / "parts" / "frontmatter", result, dry_run)
        check_and_create_directory(intro_path / "parts" / "sections", result, dry_run)
        check_and_create_directory(intro_path / "parts" / "backmatter", result, dry_run)
        check_and_create_directory(intro_path / "parts" / "appendix", result, dry_run)
        check_and_create_directory(intro_path / "build", result, dry_run)


def fix_repository_files(repo_root: Path, result: FixResult, layout_name: str, dry_run: bool = False) -> None:
    """Fix repository configuration files."""
    print("Checking repository configuration files...")
    
    # .paperrepo (minimal placeholder)
    paperrepo_content = f"paperrepo=1\nversion=3\nlayout={layout_name}\n"
    check_and_create_file(repo_root / ".paperrepo", paperrepo_content, result, dry_run)
    
    # .gitignore policy block
    _apply_gitignore_policy(repo_root / ".gitignore", result, dry_run)
    
    # .texrepo-config (only create if missing)
    if not (repo_root / ".texrepo-config").exists():
        if dry_run:
            result.add_would_create(str(repo_root / ".texrepo-config"))
        else:
            try:
                create_default_config(repo_root)
                result.add_created(str(repo_root / ".texrepo-config"))
            except Exception as e:
                result.add_warning(str(repo_root / ".texrepo-config"), f"cannot create ({e})")
    else:
        result.add_skipped(str(repo_root / ".texrepo-config"), "already exists")


def fix_shared_files(repo_root: Path, result: FixResult, dry_run: bool = False) -> None:
    """Fix shared LaTeX files."""
    print("Checking shared LaTeX files...")
    
    shared_dir = repo_root / "shared"
    
    # preamble.tex
    preamble_content = r"""\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage[margin=1in]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage[hidelinks]{hyperref}
\usepackage[nameinlink,noabbrev]{cleveref}
\usepackage[numbers]{natbib}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.8em}

\newtheorem{theorem}{Theorem}
\newtheorem{lemma}{Lemma}
\newtheorem{proposition}{Proposition}
\newtheorem{corollary}{Corollary}
\theoremstyle{definition}
\newtheorem{definition}{Definition}
\newtheorem{remark}{Remark}
"""
    check_and_create_file(shared_dir / "preamble.tex", preamble_content, result, dry_run)
    
    # macros.tex
    macros_content = r"""\newcommand{\R}{\mathbb{R}}
\newcommand{\N}{\mathbb{N}}
\newcommand{\set}[1]{\left\{#1\right\}}
\newcommand{\abs}[1]{\left|#1\right|}
\newcommand{\norm}[1]{\left\|#1\right\|}
\newcommand{\dd}{\,\mathrm{d}}
\newcommand{\pd}[2]{\frac{\partial #1}{\partial #2}}
\DeclareMathOperator{\tr}{tr}
"""
    check_and_create_file(shared_dir / "macros.tex", macros_content, result, dry_run)
    
    # notation.tex
    notation_content = r"""\newcommand{\AFC}{\alpha}
\newcommand{\cLight}{c}
\newcommand{\grad}{\nabla}
"""
    check_and_create_file(shared_dir / "notation.tex", notation_content, result, dry_run)
    
    # identity.tex (only if .paperrepo exists)
    if (repo_root / ".paperrepo").exists():
        if not (shared_dir / "identity.tex").exists():
            if dry_run:
                result.add_would_create(str(shared_dir / "identity.tex"))
            else:
                try:
                    sync_identity_tex(repo_root)
                    result.add_created(str(shared_dir / "identity.tex"))
                except Exception as e:
                    result.add_warning(str(shared_dir / "identity.tex"), f"cannot create ({e})")
    else:
        result.add_skipped(str(shared_dir / "identity.tex"), "already exists")


def fix_readmes(repo_root: Path, result: FixResult, layout_name: str, dry_run: bool = False) -> None:
    """Ensure required README.md files exist without overwriting."""
    print("Checking required README files...")

    world_paths = world_paths_for_layout(layout_name)
    world_dir = stage_dir(layout_name, "world")
    if world_dir and world_paths:
        foundation_rel, spec_rel = world_paths
        ensure_readme(
            repo_root / world_dir / "README.md",
            "# World\n\nShared foundation and spec papers live here.\n",
            result,
            dry_run,
        )
        ensure_readme(
            repo_root / foundation_rel / "README.md",
            "# Foundation\n\nImmutable foundations that all other layers rely on.\n",
            result,
            dry_run,
        )
        ensure_readme(
            repo_root / spec_rel / "README.md",
            "# Spec\n\nThe primary specification paper for this repository.\n",
            result,
            dry_run,
        )

    stage_readmes = {}

    intro_dir = stage_dir(layout_name, "introduction")
    if intro_dir:
        stage_readmes[intro_dir] = "# Introduction\n\nBook-scale introduction with numbered sections. Use 'tex-repo ns <section-name>' to create sections.\n"

    process_dir = stage_dir(layout_name, "process_regime")
    if process_dir:
        stage_readmes[process_dir] = "# Process Regime\n\nNatural processes and governing regimes.\n"

    function_dir = stage_dir(layout_name, "function_application")
    if function_dir:
        stage_readmes[function_dir] = (
            "# Function Application\n\nFunctions and applications that depend on process/regime outputs.\n"
        )

    hypnosis_dir = stage_dir(layout_name, "hypnosis")
    if hypnosis_dir:
        stage_readmes[hypnosis_dir] = "# Hypnosis\n\nHypnosis research and downstream analyses live here.\n"

    for stage, content in stage_readmes.items():
        ensure_readme(repo_root / stage / "README.md", content, result, dry_run)

    branch_readmes = {}
    if process_dir:
        for branch in get_process_branches(layout_name):
            label = branch.capitalize()
            branch_readmes[repo_root / process_dir / branch / "README.md"] = f"# {label}\n\n{label}-focused subjects belong here.\n"
    if function_dir:
        for branch in get_function_branches(layout_name):
            label = branch.capitalize()
            branch_readmes[repo_root / function_dir / branch / "README.md"] = (
                f"# {label}\n\n{label}-focused subjects belong here.\n"
            )
    for path, content in branch_readmes.items():
        ensure_readme(path, content, result, dry_run)

    paper_parents = []
    # No formalism in new layout
    if process_dir:
        for branch in get_process_branches(layout_name):
            paper_parents.append(repo_root / process_dir / branch / PAPERS_DIRNAME)
    if function_dir:
        for branch in get_function_branches(layout_name):
            paper_parents.append(repo_root / function_dir / branch / PAPERS_DIRNAME)
    if hypnosis_dir:
        paper_parents.append(repo_root / hypnosis_dir / PAPERS_DIRNAME)
    for parent in paper_parents:
        if not parent.exists():
            continue
        for paper_dir in parent.iterdir():
            if not paper_dir.is_dir():
                continue
            if (paper_dir / f"{paper_dir.name}.tex").exists() or (paper_dir / "main.tex").exists():
                ensure_readme(
                    paper_dir / "README.md",
                    "# Paper\n\nThis paper depends on the world layer via its enclosing domain.\n",
                    result,
                    dry_run,
                )

def fix_world_papers(
    repo_root: Path, result: FixResult, foundation_rel: Path, spec_rel: Path, dry_run: bool = False
) -> None:
    """No longer supported - world layer removed in new layout."""
    result.add_warning("World papers", "Not supported in new layout (no world/foundation/spec)")
    return


def fix_introduction_book(repo_root: Path, result: FixResult, intro_dir: str, dry_run: bool = False) -> None:
    """Fix introduction book structure (entry file, front/back matter under parts/)."""
    print("Checking introduction book structure...")
    
    intro_path = repo_root / intro_dir
    
    # Check if old structure exists - fail if detected (no backward compat)
    old_structure_exists = (
        (intro_path / "sections").exists() or 
        (intro_path / "frontmatter").exists() or 
        (intro_path / "backmatter").exists() or
        (intro_path / "appendix").exists()
    )
    
    if old_structure_exists:
        print(f"Error: Legacy introduction structure detected in {intro_path}")
        print("Legacy directories found (sections/, frontmatter/, backmatter/, or appendix/ at top level).")
        print("Only parts/ structure is supported. No backward compatibility.")
        print("Remove legacy directories manually and re-run 'tex-repo fix'.")

        import sys
        sys.exit(1)
    
    # Create new parts/ structure only
    parts_dir = intro_path / "parts"
    for d in ["frontmatter", "sections", "backmatter", "appendix"]:
        check_and_create_directory(parts_dir / d, result, dry_run)
    check_and_create_directory(intro_path / "build", result, dry_run)
    
    # Frontmatter/backmatter files in parts/ location
    for name, content in INTRO_FRONTMATTER.items():
        check_and_create_file(parts_dir / "frontmatter" / name, content, result, dry_run)
    for name, content in INTRO_BACKMATTER.items():
        check_and_create_file(parts_dir / "backmatter" / name, content, result, dry_run)

    # Create entry .tex file
    intro_entry = intro_path / f"{intro_dir}.tex"
    check_and_create_file(intro_entry, INTRO_ENTRY_TEMPLATE, result, dry_run)

    # Backfill chapter scaffolds without overwriting content
    # Check both new and old locations
    parts_sections_root = intro_path / "parts" / "sections"
    old_sections_root = intro_path / "sections"
    
    sections_root = parts_sections_root if parts_sections_root.exists() else old_sections_root
    sections_prefix = "parts/sections" if parts_sections_root.exists() else "sections"
    
    if sections_root.exists():
        for item in sections_root.iterdir():
            if not item.is_dir():
                continue
            name = item.name
            if len(name) < 3 or not name[:2].isdigit() or name[2] != "_":
                continue
            section_num = int(name[:2])
            chapter_path = item / "chapter.tex"
            rel_base = f"{sections_prefix}/{name}"
            if not chapter_path.exists():
                include_lines = [f"\\section*{{Chapter {section_num}: {name[3:].replace('_', ' ')}}}", ""]
                for i in range(1, 11):
                    include_lines.append(f"\\input{{{rel_base}/{section_num}-{i}.tex}}")
                include_lines.append("")
                check_and_create_file(chapter_path, "\n".join(include_lines), result, dry_run)
            for i in range(1, 11):
                check_and_create_file(
                    item / f"{section_num}-{i}.tex",
                    f"% Section {section_num}, subsection {i}\n",
                    result,
                    dry_run,
                )


def print_fix_results(result: FixResult, dry_run: bool = False) -> None:
    """Print fix results with clear formatting."""
    print()
    
    # Print actions
    for status, path in result.actions:
        if status == "created":
            print(f"✅ created: {path}")
        elif status == "would_create":
            print(f"➕ would create: {path}")
        elif status == "skipped":
            print(f"ℹ️ exists: {path}")
        elif status == "warning":
            print(f"⚠️ cannot create: {path}")
    
    # Print summary
    print()
    action_word = "would be " if dry_run else ""
    print(f"Fix summary:")
    print(f"  {action_word}created: {result.created}")
    print(f"  skipped: {result.skipped}")
    if result.warnings > 0:
        print(f"  warnings: {result.warnings}")


def cmd_fix(args) -> int:
    """Handle the fix command."""
    try:
        repo_root = find_repo_root()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    dry_run = getattr(args, 'dry_run', False)
    
    if dry_run:
        print("Running in dry-run mode - no files will be modified")
        print()
    
    result = FixResult()
    layout_name = get_layout(repo_root)
    
    try:
        # Check and fix various components
        fix_repository_structure(repo_root, result, layout_name, dry_run)
        fix_repository_files(repo_root, result, layout_name, dry_run)
        fix_shared_files(repo_root, result, dry_run)
        world_paths = world_paths_for_layout(layout_name)
        if world_paths:
            foundation_rel, spec_rel = world_paths
            fix_world_papers(repo_root, result, foundation_rel, spec_rel, dry_run)
        intro_dir = stage_dir(layout_name, "introduction")
        if intro_dir and (repo_root / intro_dir).exists():
            fix_introduction_book(repo_root, result, intro_dir, dry_run)
        fix_readmes(repo_root, result, layout_name, dry_run)
        
        # Print results
        print_fix_results(result, dry_run)
        
        return 0
        
    except Exception as e:
        print(f"Error during fix: {e}")
        return 1
