"""Integration tests for tex-repo guard command."""

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


class TestCGuard:
    """Test suite for tex-repo guard command."""
    
    def test_guard_exits_zero_on_valid_repo(self):
        """Test that guard exits 0 when no violations found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid repository
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Populate book
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # guard should exit 0
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode == 0, "guard should exit 0 when no violations"
            assert result.stdout == '', "guard should output nothing when no violations"
    
    def test_guard_exits_nonzero_on_violations(self):
        """Test that guard exits non-zero when violations found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # guard should exit non-zero (book entry missing)
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode != 0, "guard should exit non-zero when violations found"
    
    def test_guard_output_format_tab_separated(self):
        """Test that guard outputs violations in tab-separated format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create partial structure to trigger violations
            book_dir = repo_path / '00_introduction'
            (book_dir / 'parts' / 'frontmatter').mkdir(parents=True)
            (book_dir / 'parts' / 'parts').mkdir(parents=True)
            (book_dir / 'parts' / 'backmatter').mkdir(parents=True)
            
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode != 0
            
            # Check format: <CODE>\t<PATH>\t<MESSAGE>
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split('\t')
                assert len(parts) == 3, f"Each line should have 3 tab-separated parts: {line}"
                code, path, message = parts
                assert code.isupper(), f"Code should be uppercase: {code}"
                assert '_' in code, f"Code should contain underscores: {code}"
    
    def test_guard_output_sorted_by_code_then_path(self):
        """Test that guard outputs violations sorted by code then path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create structure with multiple violations
            book_dir = repo_path / '00_introduction'
            (book_dir / 'parts' / 'frontmatter').mkdir(parents=True)
            (book_dir / 'parts' / 'parts').mkdir(parents=True)
            (book_dir / 'parts' / 'backmatter').mkdir(parents=True)
            
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode != 0
            
            lines = result.stdout.strip().split('\n')
            codes = [line.split('\t')[0] for line in lines]
            
            # Codes should be sorted
            assert codes == sorted(codes), "Violations should be sorted by code"
    
    def test_guard_detects_book_entry_missing(self):
        """Test that guard detects BOOK_ENTRY_MISSING."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode != 0
            assert 'BOOK_ENTRY_MISSING' in result.stdout
    
    def test_guard_detects_paper_violations(self):
        """Test that guard detects paper structure violations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Create incomplete paper
            paper_dir = repo_path / '04_test'
            paper_dir.mkdir()
            (paper_dir / '04_test.tex').write_text(r'\documentclass{article}')
            
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode != 0
            assert 'PAPER_SECTIONS_DIR_MISSING' in result.stdout
            assert 'PAPER_BUILD_DIR_MISSING' in result.stdout
            assert 'PAPER_REFS_MISSING' in result.stdout
    
    def test_guard_detects_sectioning_leak(self):
        """Test that guard detects sectioning commands in sections_index.tex."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Corrupt sections_index.tex
            book_dir = repo_path / '00_introduction'
            sections_index = book_dir / 'build' / 'sections_index.tex'
            sections_index.write_text(r'\section{Bad}')
            
            result = run_texrepo(['guard'], cwd=repo_path)
            assert result.returncode != 0
            assert 'BOOK_SECTIONS_INDEX_SECTIONING_LEAK' in result.stdout
