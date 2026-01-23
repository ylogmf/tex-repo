"""Integration tests for tex-repo paper command."""

import sys
import subprocess
import tempfile
from pathlib import Path
import pytest


def run_texrepo(args, cwd=None):
    """Run tex-repo command using sys.executable -m texrepo."""
    cmd = [sys.executable, '-m', 'texrepo'] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


class TestHPaper:
    """Test suite for tex-repo paper command."""
    
    def test_paper_creates_structure_at_repo_root(self):
        """Test that paper creates correct structure with article documentclass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create paper
            result = run_texrepo(['paper', 'Process Notes'], cwd=repo_path)
            assert result.returncode == 0, f"paper failed: {result.stderr}"
            
            paper_dir = repo_path / '04_process_notes'
            
            # Check paper directory exists (numbered after stage dirs 00-03)
            assert paper_dir.is_dir(), "Missing paper directory"
            
            # Check entry .tex file (name must match directory)
            entry_file = paper_dir / '04_process_notes.tex'
            assert entry_file.exists(), "Missing entry .tex file"
            entry_content = entry_file.read_text()
            assert r'\documentclass{article}' in entry_content, "Paper should use article documentclass"
            assert r'\title{Process Notes}' in entry_content, "Entry should have correct title"
            assert r'\begin{abstract}' in entry_content, "Paper should have abstract"
            
            # Check sections directory
            assert (paper_dir / 'sections').is_dir(), "Missing sections/ directory"
            
            # Check build directory
            assert (paper_dir / 'build').is_dir(), "Missing build/ directory"
            
            # Check refs.bib
            assert (paper_dir / 'refs.bib').exists(), "Missing refs.bib file"
    
    def test_paper_numbering_is_contiguous(self):
        """Test that papers are numbered contiguously."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create book first (00_introduction)
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Create multiple papers
            result = run_texrepo(['paper', 'First Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            result = run_texrepo(['paper', 'Second Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Papers should be numbered 04, 05 (after 00,01,02,03)
            assert (repo_path / '04_first_paper').exists(), "Should create 04_first_paper/"
            assert (repo_path / '05_second_paper').exists(), "Should create 05_second_paper/"
    
    def test_paper_requires_repo_root(self):
        """Test that paper command must be run from repository root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Try to run from subdirectory
            subdir = repo_path / '01_process_regime'
            result = run_texrepo(['paper', 'Test'], cwd=subdir)
            assert result.returncode != 0, "Should fail when not run from repo root"
            assert 'repository root' in result.stderr.lower()
    
    def test_paper_refuses_duplicate_slug(self):
        """Test that paper refuses to create duplicate paper directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # First paper succeeds
            result = run_texrepo(['paper', 'Process Notes'], cwd=repo_path)
            assert result.returncode == 0
            
            # Second paper with same slug fails
            result = run_texrepo(['paper', 'Process Notes'], cwd=repo_path)
            assert result.returncode != 0, "Should fail when paper already exists"
            assert 'already exists' in result.stderr.lower()
    
    def test_paper_slug_formatting(self):
        """Test that paper directory names follow slug rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Test various title formats
            result = run_texrepo(['paper', 'Hypothesis Review'], cwd=repo_path)
            assert result.returncode == 0
            assert (repo_path / '04_hypothesis_review').exists()
            assert (repo_path / '04_hypothesis_review' / '04_hypothesis_review.tex').exists()
            
            result = run_texrepo(['paper', 'NP vs P'], cwd=repo_path)
            assert result.returncode == 0
            assert (repo_path / '05_np_vs_p').exists()
            assert (repo_path / '05_np_vs_p' / '05_np_vs_p.tex').exists()
