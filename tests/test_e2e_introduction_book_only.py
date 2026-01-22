#!/usr/bin/env python3
"""
End-to-end test for book-only introduction workflow.
Tests the strict parts/ structure enforcement in status, fix, and build commands.
"""
import subprocess
import os
from pathlib import Path
import pytest


def run_texrepo(args, cwd, input_text=None):
    """Run tex-repo command and return result"""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / 'tex-repo'
    
    cmd = [str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd, 
            input=input_text,
            text=True,
            capture_output=True,
            cwd=str(cwd),
            timeout=30
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        raise


def test_book_only_introduction_workflow(tmp_path):
    """
    E2E test mirroring manual aa repo workflow.
    Tests strict enforcement of parts/ structure for introduction book.
    """
    
    # Step 1: Init repo in tmp_path
    init_input = "\n".join([
        "Test Project",
        "Test Author",
        "Test Org",
        "test@test.com",
        "",                  # default affiliation
        "TestOrg",
        "",                  # no ORCID
        "MIT",
        "today",
        "plain"
    ]) + "\n"
    
    result = run_texrepo(['init', 'test-repo'], cwd=tmp_path, input_text=init_input)
    assert result.returncode == 0, f"Init failed: {result.stderr}"
    
    repo_path = tmp_path / 'test-repo'
    assert repo_path.exists()
    assert (repo_path / '00_introduction').exists()
    
    # Step 2: Baseline status and fix
    print("Step 2: Baseline status and fix")
    result = run_texrepo(['status'], cwd=repo_path)
    assert result.returncode == 0, f"Initial status failed: {result.stderr}"
    
    result = run_texrepo(['fix'], cwd=repo_path)
    assert result.returncode == 0, f"Initial fix failed: {result.stderr}"
    
    # Step 3: Inject legacy dir and assert rejection
    print("Step 3: Inject legacy dir and assert rejection")
    legacy_dir = repo_path / '00_introduction' / 'sections'
    legacy_dir.mkdir(parents=True)
    
    # status should reject with non-zero exit and E[UNEXPECTED_ITEM]
    result = run_texrepo(['status'], cwd=repo_path)
    assert result.returncode != 0, "Status should fail with legacy structure"
    assert 'E[UNEXPECTED_ITEM]' in result.stdout, f"Status should show UNEXPECTED_ITEM error, got: {result.stdout}"
    
    # fix should reject with non-zero exit and E[UNEXPECTED_ITEM]
    result = run_texrepo(['fix'], cwd=repo_path)
    assert result.returncode != 0, "Fix should fail with legacy structure"
    assert 'E[UNEXPECTED_ITEM]' in result.stdout, f"Fix should show UNEXPECTED_ITEM error, got: {result.stdout}"
    
    # Remove legacy dir
    import shutil
    shutil.rmtree(legacy_dir)
    
    # Verify fix works after removal
    result = run_texrepo(['fix'], cwd=repo_path)
    assert result.returncode == 0, f"Fix should succeed after removing legacy dir: {result.stderr}"
    
    # Step 4: Build intro and assert indices created
    print("Step 4: Build intro and assert indices created")
    build_dir = repo_path / '00_introduction' / 'build'
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    result = run_texrepo(['b'], cwd=repo_path)
    # Build may fail without LaTeX, but should create index files
    # We care that indices are generated, not that PDF builds
    
    chapters_index = repo_path / '00_introduction' / 'build' / 'chapters_index.tex'
    sections_index = repo_path / '00_introduction' / 'build' / 'sections_index.tex'
    
    assert chapters_index.exists(), f"chapters_index.tex should be created at {chapters_index}"
    assert sections_index.exists(), f"sections_index.tex should be created at {sections_index}"
    
    # Step 5: Add chapter and title override, then rebuild
    print("Step 5: Add chapter and title override, then rebuild")
    result = run_texrepo(['ns', 'np_vs_p'], cwd=repo_path)
    assert result.returncode == 0, f"New section failed: {result.stderr}"
    
    # Write title override
    title_path = repo_path / '00_introduction' / 'parts' / 'sections' / '01_np_vs_p' / 'title.tex'
    title_path.parent.mkdir(parents=True, exist_ok=True)
    title_path.write_text(r'$\alpha$ vs NP')
    
    # Rebuild
    result = run_texrepo(['b'], cwd=repo_path)
    # Again, may fail without LaTeX, but index should be regenerated
    
    # Read sections_index.tex and assert it contains the override
    sections_index_content = sections_index.read_text()
    assert r'\section{$\alpha$ vs NP}' in sections_index_content, \
        f"sections_index.tex should contain custom title, got:\n{sections_index_content}"
    
    print("✅ All e2e workflow steps passed!")


if __name__ == '__main__':
    import sys
    pytest.main([__file__] + sys.argv[1:])
