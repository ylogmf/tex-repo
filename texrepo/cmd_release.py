"""Release command: package build outputs into immutable bundles."""

import sys
import shutil
import datetime
from pathlib import Path
from .utils import find_repo_root


def cmd_release(args):
    """
    Create immutable release bundle for a built document.
    
    Never triggers build; only packages existing build outputs.
    Release is allowed only if the PDF exists.
    """
    repo_root = find_repo_root()
    if repo_root is None:
        print("Error: Not in a tex-repo repository", file=sys.stderr)
        return 1
    
    target = args.target
    target_path = repo_root / target
    
    if not target_path.exists() or not target_path.is_dir():
        print(f"Error: Target not found: {target}", file=sys.stderr)
        return 1
    
    # Find the entry PDF
    entry_name = target_path.name
    pdf_file = target_path / 'build' / f"{entry_name}.pdf"
    
    if not pdf_file.exists():
        print(f"Error: PDF not found: {pdf_file}", file=sys.stderr)
        print("Run 'tex-repo build' first", file=sys.stderr)
        return 1
    
    # Create release directory with structure: releases/<target>/<timestamp>/
    releases_dir = repo_root / 'releases'
    target_releases = releases_dir / entry_name
    target_releases.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp-based version directory
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    release_dir = target_releases / timestamp
    
    if release_dir.exists():
        print(f"Error: Release bundle already exists: {release_dir.relative_to(repo_root)}", file=sys.stderr)
        return 1
    
    # Create release bundle
    release_dir.mkdir()
    
    # Copy PDF
    release_pdf = release_dir / f"{entry_name}.pdf"
    shutil.copy2(pdf_file, release_pdf)
    rel_path = release_dir.relative_to(repo_root)
    print(f"✓ Created release: {rel_path}", file=sys.stderr)
    print(f"  PDF: {rel_path / release_pdf.name}", file=sys.stderr)
    
    return 0
