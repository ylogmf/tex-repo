"""Integration tests for tex-repo init command."""

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


class TestAInit:
    """Test suite for tex-repo init command."""
    
    def test_init_creates_repo_baseline(self):
        """Test that init creates all baseline directories and files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_name = 'test-repo'
            result = run_texrepo(['init', repo_name], cwd=tmpdir)
            
            assert result.returncode == 0, f"init failed: {result.stderr}"
            
            repo_path = Path(tmpdir) / repo_name
            
            # Check marker file
            assert (repo_path / '.paperrepo').exists(), "Missing .paperrepo marker"
            assert (repo_path / '.paperrepo').is_file(), ".paperrepo should be a file"
            
            # Check shared/ directory and files
            assert (repo_path / 'shared').is_dir(), "Missing shared/ directory"
            assert (repo_path / 'shared' / 'preamble.tex').exists(), "Missing shared/preamble.tex"
            assert (repo_path / 'shared' / 'macros.tex').exists(), "Missing shared/macros.tex"
            assert (repo_path / 'shared' / 'notation.tex').exists(), "Missing shared/notation.tex"
            assert (repo_path / 'shared' / 'identity.tex').exists(), "Missing shared/identity.tex"
            
            # Check baseline directories
            assert (repo_path / '00_introduction').is_dir(), "Missing 00_introduction/"
            # 00_introduction should be empty (populated by book command)
            intro_contents = list((repo_path / '00_introduction').iterdir())
            assert len(intro_contents) == 0, "00_introduction/ should be empty after init"
            
            assert (repo_path / '01_process_regime').is_dir(), "Missing 01_process_regime/"
            assert (repo_path / '02_function_application').is_dir(), "Missing 02_function_application/"
            assert (repo_path / '03_hypophysis').is_dir(), "Missing 03_hypophysis/"
            assert (repo_path / 'releases').is_dir(), "Missing releases/"
            
            # Check .gitignore
            assert (repo_path / '.gitignore').exists(), "Missing .gitignore"
            gitignore_content = (repo_path / '.gitignore').read_text()
            assert '**/build/' in gitignore_content, ".gitignore should ignore build/ directories"
            assert '!releases/' in gitignore_content, ".gitignore should keep releases/ tracked"
            
            # Verify no extra directories created
            dirs = [d.name for d in repo_path.iterdir() if d.is_dir()]
            expected_dirs = {
                'shared',
                '00_introduction',
                '01_process_regime',
                '02_function_application',
                '03_hypophysis',
                'releases'
            }
            assert set(dirs) == expected_dirs, f"Unexpected directories: {set(dirs) - expected_dirs}"
    
    def test_init_refuses_existing_directory(self):
        """Test that init refuses to overwrite existing directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_name = 'existing-repo'
            existing_dir = Path(tmpdir) / repo_name
            existing_dir.mkdir()
            
            result = run_texrepo(['init', repo_name], cwd=tmpdir)
            
            assert result.returncode != 0, "init should fail when directory exists"
            assert 'already exists' in result.stderr.lower(), \
                "Error message should mention directory already exists"
    
    def test_init_is_idempotent_failure_no_partial_writes(self):
        """Test that init does not create partial structure on failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_name = 'test-repo'
            
            # First init should succeed
            result1 = run_texrepo(['init', repo_name], cwd=tmpdir)
            assert result1.returncode == 0, "First init should succeed"
            
            repo_path = Path(tmpdir) / repo_name
            
            # Record initial state
            initial_files = set(repo_path.rglob('*'))
            
            # Second init with same name should fail
            result2 = run_texrepo(['init', repo_name], cwd=tmpdir)
            assert result2.returncode != 0, "Second init should fail"
            
            # Verify no changes to existing repo
            final_files = set(repo_path.rglob('*'))
            assert initial_files == final_files, \
                "Failed init should not modify existing repository"
            
            # Try to init in a different location with a file of same name
            conflict_file = Path(tmpdir) / 'conflict-repo'
            conflict_file.write_text("existing file")
            
            result3 = run_texrepo(['init', 'conflict-repo'], cwd=tmpdir)
            assert result3.returncode != 0, "Init should fail when target is a file"
            
            # Verify the file wasn't modified
            assert conflict_file.read_text() == "existing file", \
                "Existing file should not be modified"
