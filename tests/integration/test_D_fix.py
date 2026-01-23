"""Integration tests for tex-repo fix command."""

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


class TestDFix:
    """Test suite for tex-repo fix command."""
    
    def test_fix_creates_missing_directories(self):
        """Test that fix creates missing required directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create book first
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Remove some directories
            import shutil
            shutil.rmtree(book_dir / 'parts' / 'frontmatter')
            
            # fix should recreate them
            result = run_texrepo(['fix'], cwd=repo_path)
            assert result.returncode == 0
            assert (book_dir / 'parts' / 'frontmatter').is_dir(), "fix should create missing directories"
    
    def test_fix_creates_missing_spine_files(self):
        """Test that fix creates missing spine files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Remove spine files
            (book_dir / 'build' / 'sections_index.tex').unlink()
            (book_dir / 'build' / 'chapters_index.tex').unlink()
            
            # fix should recreate them
            result = run_texrepo(['fix'], cwd=repo_path)
            assert result.returncode == 0
            assert (book_dir / 'build' / 'sections_index.tex').exists()
            assert (book_dir / 'build' / 'chapters_index.tex').exists()
    
    def test_fix_creates_missing_part_files(self):
        """Test that fix creates missing part.tex files."""
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
            
            # Remove part.tex
            (part_dir / 'part.tex').unlink()
            
            # fix should recreate it
            result = run_texrepo(['fix'], cwd=repo_path)
            assert result.returncode == 0
            assert (part_dir / 'part.tex').exists()
            
            # Check content is correct
            content = (part_dir / 'part.tex').read_text()
            assert r'\part{Foundations}' in content
    
    def test_fix_creates_missing_paper_structure(self):
        """Test that fix creates missing paper directories and files."""
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
            
            # fix should create missing structure
            result = run_texrepo(['fix'], cwd=repo_path)
            assert result.returncode == 0
            assert (paper_dir / 'sections').is_dir()
            assert (paper_dir / 'build').is_dir()
            assert (paper_dir / 'refs.bib').exists()
    
    def test_fix_does_not_overwrite_existing_files(self):
        """Test that fix never overwrites existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            sections_index = book_dir / 'build' / 'sections_index.tex'
            
            # Write custom content
            custom_content = "% Custom content\n\\section{Test}"
            sections_index.write_text(custom_content)
            
            # fix should not overwrite
            result = run_texrepo(['fix'], cwd=repo_path)
            assert result.returncode == 0
            assert sections_index.read_text() == custom_content, "fix should not overwrite existing files"
    
    def test_fix_is_idempotent(self):
        """Test that fix can be run multiple times safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            
            # Remove something
            (book_dir / 'build' / 'sections_index.tex').unlink()
            
            # fix once
            result1 = run_texrepo(['fix'], cwd=repo_path)
            assert result1.returncode == 0
            
            # fix again should be safe
            result2 = run_texrepo(['fix'], cwd=repo_path)
            assert result2.returncode == 0
            assert 'No fixable violations' in result2.stdout
    
    def test_fix_does_not_rename_directories(self):
        """Test that fix never renames directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            parts_dir = book_dir / 'parts' / 'parts'
            
            # Create part with gap (01, 03 - missing 02)
            part1 = parts_dir / '01_first'
            part1.mkdir()
            (part1 / 'part.tex').write_text(r'\part{First}')
            (part1 / 'chapters').mkdir()
            
            part3 = parts_dir / '03_third'
            part3.mkdir()
            (part3 / 'part.tex').write_text(r'\part{Third}')
            (part3 / 'chapters').mkdir()
            
            # fix should not rename 03 to 02
            result = run_texrepo(['fix'], cwd=repo_path)
            assert result.returncode == 0
            assert part3.exists(), "fix should not rename directories"
            assert part3.name == '03_third', "Directory name should not change"
