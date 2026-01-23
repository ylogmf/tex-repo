"""Integration tests for tex-repo build command."""

import sys
import subprocess
import tempfile
from pathlib import Path
from unittest import mock
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


class TestIBuild:
    """Test suite for tex-repo build command."""
    
    def test_build_requires_latexmk(self):
        """Test that build fails gracefully if latexmk is not installed."""
        # This test is informational - we'll skip if latexmk is available
        import shutil
        if shutil.which('latexmk'):
            pytest.skip("latexmk is installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            # Try to build (should fail)
            result = run_texrepo(['build', '00_introduction'], cwd=repo_path)
            assert result.returncode != 0
            assert 'latexmk' in result.stderr.lower()
    
    def test_build_target_creates_pdf_in_build_dir(self):
        """Test that build <target> writes PDF to build/ directory only."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create a paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0, f"paper failed: {result.stderr}"
            
            paper_dir = repo_path / '04_test_paper'
            entry_file = paper_dir / 'entry.tex'
            build_dir = paper_dir / 'build'
            
            # Ensure entry file is buildable (minimal valid document)
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Hello World
\end{document}
""")
            
            # Build the paper
            result = run_texrepo(['build', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0, f"build failed: {result.stderr}"
            
            # Check that PDF was created in build directory
            pdf_file = build_dir / '04_test_paper.pdf'
            assert pdf_file.exists(), f"PDF not created in build directory: {pdf_file}"
            
            # Verify no PDF or build artifacts in paper root
            assert not (paper_dir / '04_test_paper.pdf').exists(), "PDF should not be in paper root"
            assert not (paper_dir / '04_test_paper.aux').exists(), "Build artifacts should not be in paper root"
    
    def test_build_all_discovers_and_builds_documents(self):
        """Test that build all discovers and builds all documents."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Create book
            result = run_texrepo(['book', 'Introduction'], cwd=repo_path)
            assert result.returncode == 0
            
            book_dir = repo_path / '00_introduction'
            book_entry = book_dir / '00_introduction.tex'
            
            # Make book buildable (minimal document)
            book_entry.write_text(r"""
\documentclass{book}
\begin{document}
\frontmatter
Front matter content
\mainmatter
Main content
\backmatter
Back matter content
\end{document}
""")
            
            # Create two papers
            result = run_texrepo(['paper', 'First Paper'], cwd=repo_path)
            assert result.returncode == 0
            result = run_texrepo(['paper', 'Second Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper1_dir = repo_path / '04_first_paper'
            paper2_dir = repo_path / '05_second_paper'
            
            # Make papers buildable (overwrite the generated entry files)
            for paper_dir in [paper1_dir, paper2_dir]:
                entry_file = paper_dir / f'{paper_dir.name}.tex'
                entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Content
\end{document}
""")
            
            # Build all documents
            result = run_texrepo(['build', 'all'], cwd=repo_path)
            assert result.returncode == 0, f"build all failed: {result.stderr}"
            
            # Verify all PDFs were created
            assert (book_dir / 'build' / '00_introduction.pdf').exists(), "Book PDF not created"
            assert (paper1_dir / 'build' / '04_first_paper.pdf').exists(), "Paper 1 PDF not created"
            assert (paper2_dir / 'build' / '05_second_paper.pdf').exists(), "Paper 2 PDF not created"
            
            # Verify count message (may be in stdout or stderr)
            output = result.stdout + result.stderr
            assert '3 document(s)' in output or '3 build' in output.lower()
    
    def test_build_from_current_directory(self):
        """Test that build without target builds current document."""
        import shutil
        if not shutil.which('latexmk'):
            pytest.skip("latexmk not installed")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'My Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper_dir = repo_path / '04_my_paper'
            entry_file = paper_dir / 'entry.tex'
            
            # Make paper buildable
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Content
\end{document}
""")
            
            # Build from within paper directory (no target specified)
            result = run_texrepo(['build'], cwd=paper_dir)
            assert result.returncode == 0, f"build failed: {result.stderr}"
            
            # Check PDF was created
            pdf_file = paper_dir / 'build' / '04_my_paper.pdf'
            assert pdf_file.exists(), "PDF not created"
    
    def test_build_fails_outside_document(self):
        """Test that build without target fails when not inside a document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize repo
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Try to build from repo root (no documents created yet)
            result = run_texrepo(['build'], cwd=repo_path)
            assert result.returncode != 0, "build should fail when not inside a document"
            assert 'not inside' in result.stderr.lower() or 'buildable' in result.stderr.lower()
    
    def test_build_nonexistent_target(self):
        """Test that build fails for non-existent target."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            
            # Try to build non-existent document
            result = run_texrepo(['build', '99_nonexistent'], cwd=repo_path)
            assert result.returncode != 0
            assert 'not found' in result.stderr.lower()
    
    def test_build_does_not_mutate_sources(self):
        """Test that build never modifies authored source files."""
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
            
            # Write content and record timestamp
            original_content = r"""
\documentclass{article}
\begin{document}
Original content
\end{document}
"""
            entry_file.write_text(original_content)
            original_mtime = entry_file.stat().st_mtime
            
            # Build
            result = run_texrepo(['build', '04_test_paper'], cwd=repo_path)
            assert result.returncode == 0
            
            # Verify source file unchanged
            assert entry_file.read_text() == original_content, "Build modified source file"
            # Note: mtime might change due to file system quirks, content is the important check
    
    def test_build_timeout_handling(self):
        """Test that build handles timeout gracefully with clear error message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Initialize and create paper
            result = run_texrepo(['init', 'test-repo'], cwd=tmpdir)
            assert result.returncode == 0
            
            repo_path = Path(tmpdir) / 'test-repo'
            result = run_texrepo(['paper', 'Test Paper'], cwd=repo_path)
            assert result.returncode == 0
            
            paper_dir = repo_path / '04_test_paper'
            entry_file = paper_dir / f'{paper_dir.name}.tex'
            
            # Write valid content
            entry_file.write_text(r"""
\documentclass{article}
\begin{document}
Test
\end{document}
""")
            
            # Mock subprocess.run to simulate timeout
            with mock.patch('texrepo.cmd_build.subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd=['latexmk'], timeout=60
                )
                
                # Import and call build function directly
                from texrepo.cmd_build import build_paper
                
                # Should handle timeout and return non-zero
                exit_code = build_paper(paper_dir)
                assert exit_code != 0, "Build should fail on timeout"
                
                # Check that subprocess.run was called with timeout parameter
                assert mock_run.called
                call_kwargs = mock_run.call_args.kwargs
                assert 'timeout' in call_kwargs, "subprocess.run should be called with timeout"
                assert call_kwargs['timeout'] > 0, "Timeout should be positive"
