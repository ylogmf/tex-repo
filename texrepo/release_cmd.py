from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .build_cmd import build_single_paper, is_paper_dir
from .common import find_repo_root, die, normalize_rel_path
from .meta_cmd import parse_paperrepo_metadata


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_git_commit(repo_root: Path) -> Optional[str]:
    """Get the current git commit hash if available."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def extract_latex_title(main_tex_path: Path) -> str:
    """Extract title from LaTeX main.tex file."""
    try:
        content = main_tex_path.read_text(encoding='utf-8')
        
        # Find \title{...} command (allowing for multiline titles)
        title_match = re.search(r'\\title\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}', content, re.DOTALL)
        
        if not title_match:
            return "unknown_title"
        
        title = title_match.group(1).strip()
        
        # Remove LaTeX commands (simple approach)
        title = re.sub(r'\\[a-zA-Z]+\*?(?:\[[^\]]*\])?\s*(?:\{[^}]*\})*', '', title)
        title = re.sub(r'[{}\\]', '', title)
        
        # Normalize to lowercase with separators
        title = title.lower()
        title = re.sub(r'[^a-z0-9\s]', '', title)
        title = re.sub(r'\s+', '_', title)
        title = re.sub(r'_+', '_', title)
        title = title.strip('_')
        
        return title if title else "unknown_title"
        
    except Exception:
        return "unknown_title"


def generate_release_id(label: Optional[str] = None) -> str:
    """Generate release ID with optional label."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    if label:
        return f"{timestamp}__{label}"
    return timestamp


def collect_file_info(release_dir: Path) -> list[dict]:
    """Collect file information for manifest."""
    files_info = []
    for file_path in release_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(release_dir)
            size = file_path.stat().st_size
            sha256 = compute_sha256(file_path)
            files_info.append({
                "relative_path": str(rel_path).replace("\\", "/"),
                "size_bytes": size,
                "sha256": sha256
            })
    return sorted(files_info, key=lambda x: x["relative_path"])


def write_manifest(release_dir: Path, files_info: list[dict]) -> str:
    """Write MANIFEST.json file and return its SHA256."""
    manifest_path = release_dir / "MANIFEST.json"
    manifest_data = {
        "files": files_info,
        "total_files": len(files_info),
        "total_size": sum(f["size_bytes"] for f in files_info)
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    
    return compute_sha256(manifest_path)


def write_sha256sums(release_dir: Path, files_info: list[dict]) -> None:
    """Write SHA256SUMS file."""
    sha256sums_path = release_dir / "SHA256SUMS"
    with open(sha256sums_path, "w", encoding="utf-8") as f:
        for file_info in files_info:
            f.write(f"{file_info['sha256']}  {file_info['relative_path']}\n")


def write_release_metadata(release_dir: Path, release_id: str, release_title: str,
                         paper_path_rel: str, engine: str, repo_root: Path) -> None:
    """Write RELEASE.txt metadata file."""
    repo_metadata = parse_paperrepo_metadata(repo_root)
    git_commit = get_git_commit(repo_root)
    build_time = datetime.now().isoformat()
    
    release_txt_path = release_dir / "RELEASE.txt"
    with open(release_txt_path, "w", encoding="utf-8") as f:
        f.write("tex-repo Release Metadata\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"release_id: {release_id}\n")
        f.write(f"release_title: {release_title}\n")
        f.write(f"paper_path: {paper_path_rel}\n")
        f.write(f"build_engine: {engine}\n")
        f.write(f"build_time: {build_time}\n")
        f.write(f"python_version: {sys.version.split()[0]}\n")
        f.write(f"platform: {sys.platform}\n")
        
        if git_commit:
            f.write(f"git_commit: {git_commit}\n")
        
        # Add author/org fields from .paperrepo if available
        if "author_name" in repo_metadata:
            f.write(f"author_name: {repo_metadata['author_name']}\n")
        if "author_email" in repo_metadata:
            f.write(f"author_email: {repo_metadata['author_email']}\n")
        if "organization" in repo_metadata:
            f.write(f"organization: {repo_metadata['organization']}\n")
        if "project_name" in repo_metadata:
            f.write(f"project_name: {repo_metadata['project_name']}\n")
        
        f.write("\nNote: Release bundle is immutable by convention; edit source and re-release for changes.\n")


def copy_paper_sources(paper_dir: Path, sources_dir: Path) -> None:
    """Copy paper source files to the sources directory."""
    paper_sources_dir = sources_dir / "paper"
    paper_sources_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy main.tex
    shutil.copy2(paper_dir / "main.tex", paper_sources_dir / "main.tex")
    
    # Copy refs.bib if it exists
    refs_bib = paper_dir / "refs.bib"
    if refs_bib.exists():
        shutil.copy2(refs_bib, paper_sources_dir / "refs.bib")
    
    # Copy sections/ directory if it exists
    sections_dir = paper_dir / "sections"
    if sections_dir.exists():
        shutil.copytree(sections_dir, paper_sources_dir / "sections")
    
    # Copy any other .tex files in paper root
    for tex_file in paper_dir.glob("*.tex"):
        if tex_file.name != "main.tex":  # main.tex already copied
            shutil.copy2(tex_file, paper_sources_dir / tex_file.name)


def copy_shared_sources(repo_root: Path, sources_dir: Path) -> None:
    """Copy shared dependency files to the sources directory."""
    shared_dir = repo_root / "shared"
    shared_sources_dir = sources_dir / "shared"
    
    if not shared_dir.exists():
        return
    
    shared_files = ["preamble.tex", "macros.tex", "notation.tex", "identity.tex"]
    
    for filename in shared_files:
        shared_file = shared_dir / filename
        if shared_file.exists():
            shared_sources_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(shared_file, shared_sources_dir / filename)


def append_to_release_index(repo_root: Path, release_record: dict) -> None:
    """Append release record to index.jsonl."""
    index_path = repo_root / "releases" / "index.jsonl"
    
    # Create releases directory if it doesn't exist
    index_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Append to index.jsonl
    with open(index_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(release_record) + "\n")


def create_release_bundle(paper_dir: Path, repo_root: Path, release_id: str, 
                        release_title: str, engine: str, label: Optional[str], 
                        args) -> None:
    """Create the complete release bundle."""
    releases_dir = repo_root / "releases"
    release_dir_name = f"{release_id}__{release_title}"
    release_dir = releases_dir / release_dir_name
    
    # Ensure release directory doesn't exist
    if release_dir.exists():
        die(f"Release directory already exists: {release_dir}\nHint: Choose a different label or wait a moment before retrying.")
    
    release_dir.mkdir(parents=True)
    
    # A) Copy PDF artifact
    pdf_source = paper_dir / "build" / "main.pdf"
    if not pdf_source.exists():
        # Build the paper first
        print(f"PDF not found, building paper...")
        build_single_paper(paper_dir, repo_root, args)
        if not pdf_source.exists():
            die(f"Build failed: PDF not found at {pdf_source}")
    
    shutil.copy2(pdf_source, release_dir / "main.pdf")
    pdf_sha256 = compute_sha256(release_dir / "main.pdf")
    
    # B) Create source snapshot
    sources_dir = release_dir / "sources"
    sources_dir.mkdir()
    
    # Copy paper sources
    copy_paper_sources(paper_dir, sources_dir)
    
    # Copy shared sources
    copy_shared_sources(repo_root, sources_dir)
    
    # Copy .paperrepo as repo.paperrepo
    paperrepo_file = repo_root / ".paperrepo"
    if paperrepo_file.exists():
        shutil.copy2(paperrepo_file, sources_dir / "repo.paperrepo")
    
    # C) Write release metadata
    paper_path_rel = paper_dir.relative_to(repo_root)
    write_release_metadata(release_dir, release_id, release_title, str(paper_path_rel), engine, repo_root)
    
    # D) Generate manifest and hashes
    files_info = collect_file_info(release_dir)
    manifest_sha256 = write_manifest(release_dir, files_info)
    write_sha256sums(release_dir, files_info)
    
    # E) Update release index
    repo_metadata = parse_paperrepo_metadata(repo_root)
    git_commit = get_git_commit(repo_root)
    
    release_record = {
        "release_id": release_id,
        "paper_path": str(paper_path_rel),
        "release_dir": f"releases/{release_dir_name}",
        "created_at": datetime.now().isoformat(),
        "engine": engine,
        "pdf_sha256": pdf_sha256,
        "manifest_sha256": manifest_sha256,
        "git_commit": git_commit,
        "author_name": repo_metadata.get("author_name", ""),
        "organization": repo_metadata.get("organization", ""),
        "notes": ""
    }
    
    try:
        append_to_release_index(repo_root, release_record)
    except Exception as e:
        # Clean up the release directory if index update fails
        shutil.rmtree(release_dir, ignore_errors=True)
        die(f"Failed to update release index: {e}")
    
    return release_dir


def cmd_release(args) -> int:
    """Handle the release command."""
    try:
        repo_root = find_repo_root()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    # Resolve paper directory
    paper_path_input = normalize_rel_path(args.paper_path)
    paper_dir = (repo_root / paper_path_input).resolve()
    
    if not paper_dir.exists():
        die(f"Paper path does not exist: {paper_path_input}")
    
    if not is_paper_dir(paper_dir):
        die(f"Not a paper directory (missing main.tex): {paper_path_input}")
    
    # Extract title from paper
    main_tex_path = paper_dir / "main.tex"
    release_title = extract_latex_title(main_tex_path)
    
    # Generate release ID
    release_id = generate_release_id(getattr(args, 'label', None))
    
    # Create the release bundle
    try:
        release_dir = create_release_bundle(
            paper_dir=paper_dir,
            repo_root=repo_root,
            release_id=release_id,
            release_title=release_title,
            engine=args.engine,
            label=getattr(args, 'label', None),
            args=args
        )
        
        rel_paper_path = paper_dir.relative_to(repo_root)
        rel_release_path = release_dir.relative_to(repo_root)
        
        print(f"✅ Created release: {rel_paper_path} -> {rel_release_path}")
        print(f"   Release ID: {release_id}")
        print(f"   Release title: {release_title}")
        print(f"   Contents: main.pdf, sources/, MANIFEST.json, SHA256SUMS, RELEASE.txt")
        
        return 0
        
    except Exception as e:
        die(f"Failed to create release: {e}")
