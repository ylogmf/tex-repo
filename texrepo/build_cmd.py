from __future__ import annotations

import subprocess
from pathlib import Path

from .common import find_repo_root, die, normalize_rel_path


def needs_rebuild(paper_dir: Path) -> bool:
    """Check if a paper needs to be rebuilt based on file modification times.
    
    Returns True if:
    - PDF output doesn't exist
    - Any .tex file is newer than the PDF
    - Bibliography files are newer than the PDF
    """
    pdf_output = paper_dir / "build" / "main.pdf"
    
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
    """Check if path is a paper directory (contains main.tex)."""
    return (path / "main.tex").is_file()


def discover_papers(repo_root: Path) -> list[Path]:
    """Find all paper directories by searching for main.tex under repo root."""
    papers = []
    for main_tex in repo_root.rglob("main.tex"):
        papers.append(main_tex.parent)
    return papers


def sort_papers_by_stage_and_domain(papers: list[Path]) -> list[Path]:
    """Sort papers by stage order, then domain number, then lexicographic order."""
    stage_order = {
        "00_core": 0,
        "01_derivations": 1,
        "02_interpretations": 2,
        "03_applications": 3,
        "04_testbeds": 4,
    }
    
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
    if not is_paper_dir(paper_dir):
        die(f"Not a paper directory (missing main.tex): {paper_dir}\n"
            f"Hint: Run 'tex-repo np <domain> <paper-name>' to create a new paper")
    
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
    
    if args.engine == "latexmk":
        cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-outdir=build", "main.tex"]
        print("▶", " ".join(cmd))
        subprocess.run(cmd, cwd=str(paper_dir), check=True)
    else:
        # pdflatex requires multiple passes for references and citations
        cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-output-directory=build", "main.tex"]
        
        print("▶ pdflatex pass 1/2")
        subprocess.run(cmd, cwd=str(paper_dir), check=True)
        
        print("▶ pdflatex pass 2/2") 
        subprocess.run(cmd, cwd=str(paper_dir), check=True)
    
    print(f"✅ Built: {paper_dir.relative_to(repo_root)} (output: build/)")


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
        elif is_repo_root(current_dir):
            # Current directory is repo root - default to 00_core/core
            core_path = repo / "00_core" / "core"
            if not is_paper_dir(core_path):
                die(f"Default core paper not found: {core_path}")
            paper_dir = core_path
        else:
            die(f"Not a paper directory (missing main.tex): {current_dir}")
    else:
        # Target specified
        paper_dir = (repo / target).resolve()
    
    build_single_paper(paper_dir, repo, args)
    return 0
