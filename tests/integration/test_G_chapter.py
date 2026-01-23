"""Integration tests for tex-repo chapter command."""

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


class TestGChapter:
    """Test suite for tex-repo chapter command."""
    
    def test_chapter_creates_tex_file_in_part(self):
        """Test that chapter creates NN_<slug>.tex file inside part's chapters/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo, create book and part
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode == 0
            
            part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
            
            # Create chapter from part directory
            result = run_texrepo(['chapter', 'Overview'], cwd=part_dir)
            assert result.returncode == 0, f"chapter failed: {result.stderr}"
            
            chapter_dir = part_dir / 'chapters' / '01_overview'
            
            # Check chapter directory and required files exist
            assert chapter_dir.exists(), "Missing chapters/01_overview/ directory"
            assert chapter_dir.is_dir(), "Chapter should be a directory"
            
            chapter_file = chapter_dir / 'chapter.tex'
            assert chapter_file.is_file(), "Missing chapter.tex in chapter directory"
            
            # Check section placeholders exist (1-1.tex through 1-10.tex)
            for i in range(1, 11):
                section_file = chapter_dir / f'1-{i}.tex'
                assert section_file.is_file(), f"Missing section placeholder 1-{i}.tex"
            
            # Check chapter content
            chapter_content = chapter_file.read_text()
            assert r'\chapter{Overview}' in chapter_content, "Chapter should have correct \\chapter command"
    
    def test_chapter_numbering_is_contiguous(self):
        """Test that chapters are numbered contiguously starting from 01."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode == 0
            
            part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
            
            # Create multiple chapters
            result = run_texrepo(['chapter', 'First'], cwd=part_dir)
            assert result.returncode == 0
            
            result = run_texrepo(['chapter', 'Second'], cwd=part_dir)
            assert result.returncode == 0
            
            result = run_texrepo(['chapter', 'Third'], cwd=part_dir)
            assert result.returncode == 0
            
            chapters_dir = part_dir / 'chapters'
            assert (chapters_dir / '01_first').is_dir(), "Should create 01_first/ directory"
            assert (chapters_dir / '02_second').is_dir(), "Should create 02_second/ directory"
            assert (chapters_dir / '03_third').is_dir(), "Should create 03_third/ directory"
    
    def test_chapter_requires_part_context(self):
        """Test that chapter command must be run inside a part directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Try to create chapter from book directory (not in part)
            result = run_texrepo(['chapter', 'Test'], cwd=book_dir)
            assert result.returncode != 0, "Should fail when not inside part directory"
            assert 'part' in result.stderr.lower()
    
    def test_chapter_refuses_duplicate_slug(self):
        """Test that chapter refuses to create duplicate chapter file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode == 0
            
            part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
            
            # First chapter succeeds
            result = run_texrepo(['chapter', 'Overview'], cwd=part_dir)
            assert result.returncode == 0
            
            # Second chapter with same slug fails
            result = run_texrepo(['chapter', 'Overview'], cwd=part_dir)
            assert result.returncode != 0, "Should fail when chapter already exists"
            assert 'already exists' in result.stderr.lower()
    
    def test_chapter_slug_formatting(self):
        """Test that chapter file names follow slug rules."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
            assert result.returncode == 0
            
            part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
            
            # Test various title formats
            result = run_texrepo(['chapter', 'Structural Limits'], cwd=part_dir)
            assert result.returncode == 0
            assert (part_dir / 'chapters' / '01_structural_limits').is_dir()
            
            result = run_texrepo(['chapter', 'In the Beginning'], cwd=part_dir)
            assert result.returncode == 0
            assert (part_dir / 'chapters' / '02_in_the_beginning').is_dir()
