"""Integration tests for tex-repo part command."""

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


class TestFPart:
    """Test suite for tex-repo part command."""
    
    def test_part_creates_structure_in_book(self):
        """Test that part creates correct structure inside book."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo and create book
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Create part from book directory
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode == 0, f"part failed: {result.stderr}"
            
            part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
            
            # Check part directory exists
            assert part_dir.is_dir(), "Missing parts/parts/01_foundations/ directory"
            
            # Check part.tex
            part_file = part_dir / 'part.tex'
            assert part_file.exists(), "Missing part.tex file"
            part_content = part_file.read_text()
            assert r'\part{Foundations}' in part_content, "part.tex should have correct \\part command"
            
            # Check chapters directory
            assert (part_dir / 'chapters').is_dir(), "Missing chapters/ directory"
    
    def test_part_numbering_is_contiguous(self):
        """Test that parts are numbered contiguously starting from 01."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Create multiple parts
            result = run_texrepo(['part', 'First'], cwd=book_dir)
            assert result.returncode == 0
            
            result = run_texrepo(['part', 'Second'], cwd=book_dir)
            assert result.returncode == 0
            
            result = run_texrepo(['part', 'Third'], cwd=book_dir)
            assert result.returncode == 0
            
            parts_dir = book_dir / 'parts' / 'parts'
            assert (parts_dir / '01_first').exists(), "Should create 01_first/"
            assert (parts_dir / '02_second').exists(), "Should create 02_second/"
            assert (parts_dir / '03_third').exists(), "Should create 03_third/"
    
    def test_part_requires_book_context(self):
        """Test that part command must be run inside a book directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Try to create part from repo root (not in book)
            result = run_texrepo(['part', 'Test'], cwd=repo_path)
            assert result.returncode != 0, "Should fail when not inside book directory"
            assert 'book' in result.stderr.lower()
    
    def test_part_refuses_duplicate_slug(self):
        """Test that part refuses to create duplicate part directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # First part succeeds
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode == 0
            
            # Second part with same slug fails
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode != 0, "Should fail when part already exists"
            assert 'already exists' in result.stderr.lower()
    
    def test_part_slug_formatting(self):
        """Test that part directory names follow slug rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Test various title formats
            result = run_texrepo(['part', 'Type Consistency'], cwd=book_dir)
            assert result.returncode == 0
            assert (book_dir / 'parts' / 'parts' / '01_type_consistency').exists()
            
            result = run_texrepo(['part', 'NP vs P'], cwd=book_dir)
            assert result.returncode == 0
            assert (book_dir / 'parts' / 'parts' / '02_np_vs_p').exists()
