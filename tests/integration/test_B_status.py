"""Integration tests for tex-repo status command."""

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


class TestBStatus:
    """Test suite for tex-repo status command."""
    
    def test_status_reports_no_violations_on_valid_repo(self):
        """Test that status reports no violations for valid repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid repository
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Populate book
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # status should report no violations
            result = run_texrepo(['status'], cwd=repo_path)
            assert result.returncode == 0, f"status failed: {result.stderr}"
            assert 'No violations' in result.stdout or '✓' in result.stdout
    
    def test_status_reports_missing_book_entry(self):
        """Test that status detects missing book entry file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # status should report BOOK_ENTRY_MISSING
            result = run_texrepo(['status'], cwd=repo_path)
            assert result.returncode == 0, "status should exit 0"
            assert 'BOOK_ENTRY_MISSING' in result.stdout
    
    def test_status_reports_missing_spine_files(self):
        """Test that status detects missing spine files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create partial book structure (no build/)
            book_dir = repo_path / '00_introduction'
            (book_dir / 'parts' / 'frontmatter').mkdir(parents=True)
            (book_dir / 'parts' / 'parts').mkdir(parents=True)
            (book_dir / 'parts' / 'backmatter').mkdir(parents=True)
            (book_dir / '00_introduction.tex').write_text(r'\documentclass{book}')
            
            # status should report missing spine files
            result = run_texrepo(['status'], cwd=repo_path)
            assert result.returncode == 0
            assert 'BOOK_SECTIONS_INDEX_MISSING' in result.stdout or 'BOOK_BUILD_DIR_MISSING' in result.stdout
    
    def test_status_reports_part_numbering_gap(self):
        """Test that status detects part numbering gaps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            parts_dir = book_dir / 'parts' / 'parts'
            
            # Create parts with gap (01, 03 - missing 02)
            part1 = parts_dir / '01_first'
            part1.mkdir()
            (part1 / 'part.tex').write_text(r'\part{First}')
            (part1 / 'chapters').mkdir()
            
            part3 = parts_dir / '03_third'
            part3.mkdir()
            (part3 / 'part.tex').write_text(r'\part{Third}')
            (part3 / 'chapters').mkdir()
            
            # status should report numbering gap
            result = run_texrepo(['status'], cwd=repo_path)
            assert result.returncode == 0
            assert 'BOOK_PART_NUMBER_GAP' in result.stdout
    
    def test_status_reports_paper_missing_structure(self):
        """Test that status detects missing paper structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Create paper directory manually (incomplete)
            paper_dir = repo_path / '04_test_paper'
            paper_dir.mkdir()
            (paper_dir / '04_test_paper.tex').write_text(r'\documentclass{article}')
            
            # status should report missing sections/, build/, refs.bib
            result = run_texrepo(['status'], cwd=repo_path)
            assert result.returncode == 0
            assert 'PAPER_SECTIONS_DIR_MISSING' in result.stdout
            assert 'PAPER_BUILD_DIR_MISSING' in result.stdout
            assert 'PAPER_REFS_MISSING' in result.stdout
    
    def test_status_exits_zero_always(self):
        """Test that status always exits 0 (informational only)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Even with violations, status should exit 0
            result = run_texrepo(['status'], cwd=repo_path)
            assert result.returncode == 0, "status should always exit 0"
