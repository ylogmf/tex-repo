"""Integration tests for tex-repo book command."""

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


class TestEBook:
    """Test suite for tex-repo book command."""
    
    def test_book_creates_introduction_structure(self):
        """Test that book 'Introduction' creates 00_introduction with correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0, f"init failed: {result.stderr}"
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create book with title "Introduction"
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0, f"book failed: {result.stderr}"
            
            book_dir = repo_path / '00_introduction'
            
            # Check book directory exists
            assert book_dir.is_dir(), "Missing 00_introduction/ directory"
            
            # Check entry .tex file (name must match directory)
            entry_file = book_dir / '00_introduction.tex'
            assert entry_file.exists(), "Missing 00_introduction.tex entry file"
            entry_content = entry_file.read_text()
            assert r'\documentclass{book}' in entry_content, "Entry should use book documentclass"
            assert r'\title{Introduction}' in entry_content, "Entry should have correct title"
            assert r'\frontmatter' in entry_content, "Entry should have frontmatter"
            assert r'\mainmatter' in entry_content, "Entry should have mainmatter"
            assert r'\backmatter' in entry_content, "Entry should have backmatter"
            
            # Check parts structure
            assert (book_dir / 'parts').is_dir(), "Missing parts/ directory"
            assert (book_dir / 'parts' / 'frontmatter').is_dir(), "Missing parts/frontmatter/"
            assert (book_dir / 'parts' / 'parts').is_dir(), "Missing parts/parts/"
            assert (book_dir / 'parts' / 'backmatter').is_dir(), "Missing parts/backmatter/"
            
            # Check build directory with spine files
            assert (book_dir / 'build').is_dir(), "Missing build/ directory"
            assert (book_dir / 'build' / 'sections_index.tex').exists(), "Missing build/sections_index.tex"
            assert (book_dir / 'build' / 'chapters_index.tex').exists(), "Missing build/chapters_index.tex"
            
            # Verify sections_index.tex contains no sectioning commands
            sections_content = (book_dir / 'build' / 'sections_index.tex').read_text()
            assert r'\part' not in sections_content, "sections_index.tex must not contain \\part"
            assert r'\chapter' not in sections_content, "sections_index.tex must not contain \\chapter"
            assert r'\section' not in sections_content, "sections_index.tex must not contain \\section"
    
    def test_book_introduction_is_fixed_name(self):
        """Test that 'Introduction' always creates 00_introduction (case-insensitive)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Test case-insensitive
            result = run_texrepo(['book', 'introduction'], cwd=repo_path)
            assert result.returncode == 0, f"book failed: {result.stderr}"
            
            # Should create 00_introduction (not 04_introduction or similar)
            assert (repo_path / '00_introduction').exists(), "Should create 00_introduction/"
            assert (repo_path / '00_introduction' / '00_introduction.tex').exists(), \
                "Entry file should be 00_introduction.tex"
    
    def test_book_refuses_duplicate_introduction(self):
        """Test that book refuses to create duplicate 00_introduction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # First book succeeds
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Second book with same title fails
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode != 0, "Should fail when 00_introduction already exists"
            assert 'already contains files' in result.stderr.lower() or 'already exists' in result.stderr.lower()
    
    def test_book_requires_repo_root(self):
        """Test that book command must be run from repository root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Try to run from subdirectory
            subdir = repo_path / '01_process_regime'
            result = run_texrepo(['book', 'Test'], cwd=subdir)
            assert result.returncode != 0, "Should fail when not run from repo root"
            assert 'repository root' in result.stderr.lower()
    
    def test_book_numbering_after_stages(self):
        """Test that books other than Introduction use contiguous numbering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create Introduction (00)
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Next book should be 04_ (after 00,01,02,03)
            result = run_texrepo(['book', 'Second Book'], cwd=repo_path)
            assert result.returncode == 0
            
            assert (repo_path / '04_second_book').exists(), "Should create 04_second_book/"
            assert (repo_path / '04_second_book' / '04_second_book.tex').exists()
