"""Integration tests for tex-repo release command."""

import sys
import subprocess
import tempfile
import time
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


class TestJRelease:
    """Test suite for tex-repo release command."""
    
    def test_release_requires_built_pdf(self):
        """Test that release fails if PDF does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Try to release without building
            result = run_texrepo(['release', '04_test_paper'], cwd=repo_path)
            assert result.returncode != 0, "Release should fail without PDF"
            assert 'no pdf found' in result.stderr.lower() or 'build' in result.stderr.lower()
    
    def test_release_creates_immutable_bundle(self):
        """Test that release creates timestamped bundle in releases/."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper_dir = repo_path / '04_test_paper'
            entry_file = paper_dir / 'entry.tex'
            
            # Make paper buildable
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Content
\end{document}
""")
            
            # Build the paper
            result = run_texrepo(['build', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0, f"build failed: {result.stderr}"
            
            # Release the paper
            result = run_texrepo(['release', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0, f"release failed: {result.stderr}"
            
            # Check release directory structure: releases/<target>/<timestamp>/
            releases_dir = repo_path / 'releases'
            assert releases_dir.is_dir(), "releases/ directory not created"
            
            target_releases = releases_dir / '04_test_paper'
            assert target_releases.is_dir(), "releases/04_test_paper/ not created"
            
            # Should have exactly one timestamped subdirectory
            timestamp_dirs = [d for d in target_releases.iterdir() if d.is_dir()]
            assert len(timestamp_dirs) == 1, "Should have exactly one timestamp directory"
            
            bundle_dir = timestamp_dirs[0]
            # Verify timestamp format (YYYYMMDD_HHMMSS)
            assert len(bundle_dir.name) == 15, "Timestamp should be YYYYMMDD_HHMMSS format"
            assert bundle_dir.name[8] == '_', "Timestamp format should have underscore"
            
            # Check PDF was copied to bundle
            pdf_file = bundle_dir / '04_test_paper.pdf'
            assert pdf_file.exists(), f"PDF not copied to bundle: {pdf_file}"
    
    def test_release_does_not_trigger_build(self):
        """Test that release never triggers a build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper_dir = repo_path / '04_test_paper'
            entry_file = paper_dir / 'entry.tex'
            
            # Write valid content but don't build
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Content
\end{document}
""")
            
            # Try to release without building
            result = run_texrepo(['release', '04_test_paper'], cwd=repo_path)
            assert result.returncode != 0, "Release should fail, not trigger build"
            
            # Verify no PDF was created
            assert not (paper_dir / 'build' / '04_test_paper.pdf').exists(), "Release should not create PDF"
    
    def test_release_multiple_creates_separate_bundles(self):
        """Test that multiple releases create separate timestamped bundles."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper_dir = repo_path / '04_test_paper'
            entry_file = paper_dir / 'entry.tex'
            
            # Make paper buildable
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Version 1
\end{document}
""")
            
            # Build and release first version
            result = run_texrepo(['build', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            result = run_texrepo(['release', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Wait a second to ensure different timestamp
            time.sleep(1.1)
            
            # Update content, rebuild, and release again
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Version 2
\end{document}
""")
            result = run_texrepo(['build', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            result = run_texrepo(['release', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Check that two bundles exist
            target_releases = repo_path / 'releases' / '04_test_paper'
            timestamp_dirs = sorted([d for d in target_releases.iterdir() if d.is_dir()])
            assert len(timestamp_dirs) == 2, "Should have two separate release bundles"
            
            # Verify both have PDFs
            assert (timestamp_dirs[0] / '04_test_paper.pdf').exists()
            assert (timestamp_dirs[1] / '04_test_paper.pdf').exists()
    
    def test_release_works_for_books(self):
        """Test that release works for book documents."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create book
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            entry_file = book_dir / '00_introduction.tex'
            
            # Make book buildable
            entry_file.write_text(r"""
\documentclass{book}
\begin{document}
\frontmatter
Front
\mainmatter
Main
\backmatter
Back
\end{document}
""")
            
            # Build the book
            result = run_texrepo(['build', '00_introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Release the book
            result = run_texrepo(['release', '00_introduction'], cwd=repo_path)
            assert result.returncode == 0, f"release failed: {result.stderr}"
            
            # Check release bundle
            target_releases = repo_path / 'releases' / '00_introduction'
            assert target_releases.is_dir(), "Book release directory not created"
            
            timestamp_dirs = [d for d in target_releases.iterdir() if d.is_dir()]
            assert len(timestamp_dirs) == 1
            
            # Book PDF should be named after the book (00_introduction.pdf)
            pdf_file = timestamp_dirs[0] / '00_introduction.pdf'
            assert pdf_file.exists(), f"Book PDF not in bundle: {pdf_file}"
    
    def test_release_nonexistent_target(self):
        """Test that release fails for non-existent target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Try to release non-existent document
            result = run_texrepo(['release', '99_nonexistent'], cwd=repo_path)
            assert result.returncode != 0
            assert 'not found' in result.stderr.lower()
    
    def test_release_preserves_pdf_content(self):
        """Test that release bundle contains exact copy of PDF."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper_dir = repo_path / '04_test_paper'
            entry_file = paper_dir / 'entry.tex'
            
            # Make paper buildable
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Specific content for comparison
\end{document}
""")
            
            # Build
            result = run_texrepo(['build', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Get original PDF content
            original_pdf = paper_dir / 'build' / '04_test_paper.pdf'
            original_content = original_pdf.read_bytes()
            
            # Release
            result = run_texrepo(['release', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Find bundle PDF
            target_releases = repo_path / 'releases' / '04_test_paper'
            timestamp_dirs = [d for d in target_releases.iterdir() if d.is_dir()]
            bundle_pdf = timestamp_dirs[0] / '04_test_paper.pdf'
            
            # Compare content
            bundle_content = bundle_pdf.read_bytes()
            assert bundle_content == original_content, "Released PDF differs from original"
