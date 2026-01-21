from __future__ import annotations

import subprocess
from pathlib import Path

from .common import find_repo_root, die, normalize_rel_path
from .rules import STAGE_PIPELINE, entry_tex_candidates
from .latex_log_hints import extract_primary_error, suggest_fixes
from .layouts import get_layout


def needs_rebuild(paper_dir: Path) -> bool:
    """Check if a paper needs to be rebuilt based on file modification times.
    
    Returns True if:
    - PDF output doesn't exist
    - Any .tex file is newer than the PDF
    - Bibliography files are newer than the PDF
    """
    entry = None
    for candidate in entry_tex_candidates(paper_dir):
        if candidate.exists():
            entry = candidate
            break
    if entry is None:
        die(f"Not a paper directory (missing {paper_dir.name}.tex or main.tex): {paper_dir}")

    pdf_output = paper_dir / "build" / f"{entry.stem}.pdf"

    if not pdf_output.exists():
        return True

    pdf_mtime = pdf_output.stat().st_mtime

    # Check all .tex files in the paper directory
    for tex_file in paper_dir.rglob("*.tex"):
        if tex_file.stat().st_mtime > pdf_mtime:
            return True

    # Check bibliography file
    refs_bib = paper_dir / "refs.bib"
    if refs_bib.exists() and refs_bib.stat().st_mtime > pdf_mtime:
        return True

    # Check shared files (preamble, macros, etc.) - they affect all papers
    repo_root = find_repo_root()
    shared_dir = repo_root / "shared"
    if shared_dir.exists():
        for shared_file in shared_dir.glob("*.tex"):
            if shared_file.stat().st_mtime > pdf_mtime:
                return True

    return False


def is_repo_root(path: Path) -> bool:
    """Check if path is a repo root (contains .paperrepo)."""
    return (path / ".paperrepo").is_file()


def is_paper_dir(path: Path) -> bool:
    """Check if path is a paper directory (contains entry tex)."""
    for candidate in entry_tex_candidates(path):
        if candidate.is_file():
            return True
    return False


def is_introduction_book(path: Path) -> bool:
    """Check if path is the introduction book directory (00_introduction)."""
    # Check if this is 00_introduction with an entry file
    if path.name == "00_introduction":
        entry_file = path / f"{path.name}.tex"
        return entry_file.is_file()
    return False


def discover_papers(repo_root: Path) -> list[Path]:
    """Find all paper directories and the introduction book by searching for entry tex files under repo root."""
    papers = []
    seen = set()
    for tex_file in repo_root.rglob("*.tex"):
        parent = tex_file.parent
        # Introduction book: 00_introduction/00_introduction.tex
        if parent.name == "00_introduction" and tex_file.name == "00_introduction.tex":
            seen.add(parent)
        # Regular papers: folder_name/folder_name.tex or folder_name/main.tex
        elif tex_file.name == f"{parent.name}.tex" or tex_file.name == "main.tex":
            seen.add(parent)
    return list(seen)


def sort_papers_by_stage_and_domain(papers: list[Path]) -> list[Path]:
    """Sort papers by stage order, then domain number, then lexicographic order."""
    stage_order = {stage: idx for idx, stage in enumerate(STAGE_PIPELINE)}
    
    def sort_key(paper: Path):
        parts = paper.parts
        
        # Find the stage part
        stage_idx = -1
        stage_priority = 999  # Default for unknown stages
        for i, part in enumerate(parts):
            if part in stage_order:
                stage_idx = i
                stage_priority = stage_order[part]
                break
        
        # Extract domain number if present (format: XX_domain_name)
        domain_num = 999  # Default for non-numbered domains
        if stage_idx + 1 < len(parts):
            domain_part = parts[stage_idx + 1]
            if len(domain_part) >= 3 and domain_part[:2].isdigit() and domain_part[2] == "_":
                domain_num = int(domain_part[:2])
        
        # Use the full path for lexicographic sorting within same stage/domain
        path_str = str(paper)
        
        return (stage_priority, domain_num, path_str)
    
    return sorted(papers, key=sort_key)


def build_single_paper(paper_dir: Path, repo_root: Path, args) -> None:
    """Build a single paper with given arguments."""
    # Handle introduction book (00_introduction)
    if is_introduction_book(paper_dir):
        entry = paper_dir / f"{paper_dir.name}.tex"
    else:
        # Regular paper: look for entry file
        entry = None
        for candidate in entry_tex_candidates(paper_dir):
            if candidate.exists():
                entry = candidate
                break
        if entry is None:
            die(
                f"Not a paper directory (missing {paper_dir.name}.tex or main.tex): {paper_dir}\n"
                f"Hint: Run 'tex-repo np <domain>/<paper-name>' to create a new paper"
            )
    
    log_path = paper_dir / "build" / f"{entry.stem}.log"
    
    # Check if rebuild is needed (unless --clean or --force is specified)
    if not args.clean and not getattr(args, 'force', False) and not needs_rebuild(paper_dir):
        rel_path = paper_dir.relative_to(repo_root)
        print(f"✅ Up-to-date: {rel_path}")
        return
    
    build_dir = paper_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    
    if args.clean and build_dir.exists():
        for f in build_dir.iterdir():
            if f.is_file():
                f.unlink()
    
    try:
        if args.engine == "latexmk":
            cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-outdir=build", entry.name]
            print("▶", " ".join(cmd))
            subprocess.run(
                cmd,
                cwd=str(paper_dir),
                check=True,
                capture_output=not getattr(args, "verbose", False),
                text=True,
            )
        else:
            # pdflatex requires multiple passes for references and citations
            cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=build", entry.name]
            
            print("▶ pdflatex pass 1/2")
            subprocess.run(
                cmd,
                cwd=str(paper_dir),
                check=True,
                capture_output=not getattr(args, "verbose", False),
                text=True,
            )
            
            print("▶ pdflatex pass 2/2") 
            subprocess.run(
                cmd,
                cwd=str(paper_dir),
                check=True,
                capture_output=not getattr(args, "verbose", False),
                text=True,
            )
        
        print(f"✅ Built: {paper_dir.relative_to(repo_root)} (output: build/)")
    except subprocess.CalledProcessError:
        _print_error_card(paper_dir, repo_root, entry, args)
        rel_path = paper_dir.relative_to(repo_root)
        die(f"Build failed for: {rel_path}")


def cmd_build(args) -> int:
    repo = find_repo_root()
    
    # Handle "all" target - build all papers
    if args.target == "all":
        papers = discover_papers(repo)
        if not papers:
            die("No papers found in repository")
        
        sorted_papers = sort_papers_by_stage_and_domain(papers)
        
        for paper_dir in sorted_papers:
            rel_path = paper_dir.relative_to(repo)
            print(f"▶ Building: {rel_path}")
            try:
                build_single_paper(paper_dir, repo, args)
            except subprocess.CalledProcessError:
                die(f"Build failed for: {rel_path}")
        
        print(f"✅ Built all {len(sorted_papers)} papers successfully")
        return 0
    
    # Handle single paper build
    target = Path(normalize_rel_path(args.target))
    
    if str(target) == ".":
        # No target specified, current directory
        current_dir = Path.cwd().resolve()
        
        if is_paper_dir(current_dir):
            # Current directory is a paper directory - build it
            paper_dir = current_dir
        elif is_introduction_book(current_dir):
            # Current directory is the introduction book - build it
            paper_dir = current_dir
        elif is_repo_root(current_dir):
            # Current directory is repo root - use layout-aware default
            layout = get_layout(repo)
            
            if layout == "new":
                # New layout: default to 00_introduction
                intro_path = repo / "00_introduction"
                if not is_introduction_book(intro_path):
                    die("No default build target found. In new layout, expected 00_introduction/ with 00_introduction.tex")
                paper_dir = intro_path
            else:
                # Old layout: default to 00_world/01_spec
                spec_path = repo / "00_world" / "01_spec"
                if not is_paper_dir(spec_path):
                    die(f"Default Spec paper not found: {spec_path}")
                paper_dir = spec_path
        else:
            die(f"Not a paper directory (missing {current_dir.name}.tex or main.tex): {current_dir}")
    else:
        # Target specified
        paper_dir = (repo / target).resolve()
    
    build_single_paper(paper_dir, repo, args)
    return 0


def _print_error_card(paper_dir: Path, repo_root: Path, entry: Path, args) -> None:
    log_path = paper_dir / "build" / f"{entry.stem}.log"
    print("Build failed.")
    if log_path.exists():
        try:
            log_text = log_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            log_text = None
    else:
        log_text = None

    if log_text:
        err = extract_primary_error(log_text)
        primary_msg = err.get("message") or "No primary error detected"
        line_info = f" (line {err.get('line')})" if err.get("line") else ""
        print(f"Primary error: {primary_msg}{line_info}")

        suggestions = suggest_fixes(err)
        if suggestions:
            print("Suggested action(s):")
            for s in suggestions:
                print(f"  - {s}")
    else:
        print("Primary error: log file not found")

    if getattr(args, "verbose", False) and log_text:
        print("\n--- LaTeX log (truncated) ---")
        snippet = "\n".join(log_text.splitlines()[-50:])
        print(snippet)
