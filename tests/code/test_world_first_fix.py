#!/usr/bin/env python3
"""
Tests for world-first structure fixing with tex-repo fix.
Tests non-destructive addition of missing READMEs and directories.
"""

import subprocess
import tempfile
import unittest
import os
import sys
import shutil
from pathlib import Path

# Add the repo root to path so we can import texrepo
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from test_world_first_helpers import (
    check_required_readmes,
    FOUNDATION_REL,
    SPEC_REL,
    WORLD_DIR,
    FOUNDATION_DIRNAME,
    SPEC_DIRNAME,
    FORMALISM_DIR,
    PROCESS_REGIME_DIR,
    FUNCTION_APPLICATION_DIR,
    PAPERS_DIRNAME
)

DEFAULT_INPUT = "\n" * 10  # Accept defaults for metadata prompts


def run_texrepo_direct(args, cwd, input_text=DEFAULT_INPUT):
    """Run tex-repo by importing CLI directly."""
    from texrepo.cli import main
    
    old_cwd = os.getcwd()
    old_argv = sys.argv
    old_stdin = sys.stdin
    
    try:
        os.chdir(cwd)
        sys.argv = ['tex-repo'] + args
        
        if input_text:
            from io import StringIO
            sys.stdin = StringIO(input_text)
        
        from io import StringIO
        import contextlib
        
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            try:
                result_code = main()
            except SystemExit as e:
                result_code = e.code or 0
        
        class Result:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr
        
        return Result(
            returncode=result_code,
            stdout=stdout_capture.getvalue(),
            stderr=stderr_capture.getvalue()
        )
    
    finally:
        os.chdir(old_cwd)
        sys.argv = old_argv
        sys.stdin = old_stdin


def create_test_repo(tmp_path: Path, repo_name: str) -> Path:
    """Create a test repository using init."""
    result = run_texrepo_direct(["init", repo_name], cwd=tmp_path)
    if result.returncode != 0:
        raise Exception(f"Failed to create test repo: {result.stderr}")
    return tmp_path / repo_name


class WorldFirstFixTests(unittest.TestCase):
    """Test tex-repo fix adds missing components non-destructively."""
    
    def test_fix_adds_missing_readmes(self):
        """Test that fix adds missing READMEs without overwriting existing ones."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-readmes")
            
            # Remove some READMEs
            readmes_to_remove = [
                repo_path / WORLD_DIR / "README.md",
                repo_path / FORMALISM_DIR / "README.md",
                repo_path / PROCESS_REGIME_DIR / "README.md"
            ]
            
            for readme in readmes_to_remove:
                if readme.exists():
                    readme.unlink()
            
            # Verify they're missing
            all_exist, missing = check_required_readmes(repo_path)
            self.assertFalse(all_exist, "Some READMEs should be missing before fix")
            self.assertGreater(len(missing), 0, "Should have missing READMEs to fix")
            
            # Run fix
            result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix should succeed: {result.stderr}")
            
            # Verify READMEs are now present
            all_exist_after, missing_after = check_required_readmes(repo_path)
            self.assertTrue(all_exist_after, f"All READMEs should exist after fix. Missing: {missing_after}")
            
            # Check that fix output mentions what was created
            self.assertIn("README", result.stdout, "Fix output should mention README creation")
    
    def test_fix_non_destructive_behavior(self):
        """Test that fix does not overwrite existing files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-non-destructive")
            
            # Modify an existing README with custom content
            world_readme = repo_path / WORLD_DIR / "README.md"
            custom_content = "# Custom World Content\n\nThis is my custom content that should not be overwritten.\n"
            world_readme.write_text(custom_content)
            
            # Remove another README so fix has something to do
            formalism_readme = repo_path / FORMALISM_DIR / "README.md"
            formalism_readme.unlink()
            
            # Run fix
            result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix should succeed: {result.stderr}")
            
            # Verify custom content is preserved
            preserved_content = world_readme.read_text()
            self.assertEqual(preserved_content, custom_content, "Custom README content should be preserved")
            
            # Verify the missing README was created
            self.assertTrue(formalism_readme.exists(), "Missing README should be created")
    
    def test_fix_adds_missing_directories(self):
        """Test that fix creates missing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-directories")
            
            # Remove some directories
            dirs_to_remove = [
                repo_path / FORMALISM_DIR,
                repo_path / PROCESS_REGIME_DIR / "process" / PAPERS_DIRNAME,
                repo_path / FUNCTION_APPLICATION_DIR / "application"
            ]
            
            for dir_path in dirs_to_remove:
                if dir_path.exists():
                    shutil.rmtree(dir_path)
            
            # Verify directories are missing
            for dir_path in dirs_to_remove:
                self.assertFalse(dir_path.exists(), f"Directory {dir_path} should be missing before fix")
            
            # Run fix
            result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix should succeed: {result.stderr}")
            
            # Verify directories are created
            for dir_path in dirs_to_remove:
                self.assertTrue(dir_path.exists(), f"Directory {dir_path} should be created by fix")
    
    def test_fix_adds_missing_world_papers(self):
        """Test that fix recreates missing world paper structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-world-papers")
            
            # Remove foundation entry file and sections
            foundation_entry = repo_path / FOUNDATION_REL / f"{FOUNDATION_DIRNAME}.tex"
            foundation_sections = repo_path / FOUNDATION_REL / "sections"
            
            if foundation_entry.exists():
                foundation_entry.unlink()
            if foundation_sections.exists():
                shutil.rmtree(foundation_sections)
            
            # Remove spec refs.bib
            spec_refs = repo_path / SPEC_REL / "refs.bib"
            if spec_refs.exists():
                spec_refs.unlink()
            
            # Run fix
            result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix should succeed: {result.stderr}")
            
            # Verify foundation files are recreated
            self.assertTrue(foundation_entry.exists(), "Foundation entry file should be recreated")
            self.assertTrue((foundation_sections / "00_definitions.tex").exists(), 
                          "Foundation definitions section should be recreated")
            self.assertTrue((foundation_sections / "01_axioms.tex").exists(),
                          "Foundation axioms section should be recreated")
            
            # Verify spec files are recreated
            self.assertTrue(spec_refs.exists(), "Spec refs.bib should be recreated")
    
    def test_fix_dry_run_mode(self):
        """Test that fix dry-run mode shows what would be done without making changes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-dry-run")
            
            # Remove a README
            readme_to_remove = repo_path / FORMALISM_DIR / "README.md"
            readme_to_remove.unlink()
            
            # Run fix in dry-run mode
            result = run_texrepo_direct(["fix", "--dry-run"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix dry-run should succeed: {result.stderr}")
            
            # Verify the README is still missing (dry-run didn't create it)
            self.assertFalse(readme_to_remove.exists(), "Dry-run should not create files")
            
            # But output should indicate what would be done
            self.assertIn("would", result.stdout.lower(), "Dry-run output should indicate what 'would' be done")
    
    def test_fix_preserves_existing_paper_structure(self):
        """Test that fix doesn't interfere with existing paper structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-preserve-papers")
            
            # Create a paper with custom structure
            paper_dir = repo_path / FORMALISM_DIR / PAPERS_DIRNAME / "00_custom_paper"
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            custom_tex = paper_dir / "00_custom_paper.tex"
            custom_readme = paper_dir / "README.md"
            custom_file = paper_dir / "custom_notes.txt"
            
            custom_tex.write_text("\\documentclass{article}\n\\begin{document}\nCustom paper content\\end{document}")
            custom_readme.write_text("# Custom Paper\n\nMy custom paper description.\n")
            custom_file.write_text("Custom notes that should be preserved.\n")
            
            # Remove some top-level READMEs so fix has work to do
            (repo_path / PROCESS_REGIME_DIR / "README.md").unlink()
            
            # Run fix
            result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix should succeed: {result.stderr}")
            
            # Verify custom paper files are preserved
            self.assertTrue(custom_tex.exists(), "Custom paper tex file should be preserved")
            self.assertTrue(custom_readme.exists(), "Custom paper README should be preserved")
            self.assertTrue(custom_file.exists(), "Custom paper additional file should be preserved")
            
            # Verify content is unchanged
            self.assertIn("Custom paper content", custom_tex.read_text(), "Custom tex content should be preserved")
            self.assertIn("My custom paper description", custom_readme.read_text(), "Custom README content should be preserved")
            self.assertIn("Custom notes", custom_file.read_text(), "Custom notes should be preserved")
    
    def test_fix_status_cycle(self):
        """Test that fix resolves issues detected by status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-status-cycle")
            
            # Break the repository structure
            (repo_path / WORLD_DIR / "README.md").unlink()
            (repo_path / SPEC_REL / "refs.bib").unlink()
            shutil.rmtree(repo_path / FORMALISM_DIR)
            
            # Verify status fails
            status_result_before = run_texrepo_direct(["status"], cwd=repo_path)
            self.assertNotEqual(status_result_before.returncode, 0, "Status should fail before fix")
            
            # Run fix
            fix_result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(fix_result.returncode, 0, f"Fix should succeed: {fix_result.stderr}")
            
            # Verify status now passes
            status_result_after = run_texrepo_direct(["status"], cwd=repo_path)
            self.assertEqual(status_result_after.returncode, 0,
                           f"Status should pass after fix: {status_result_after.stdout}")
    
    def test_fix_creates_papers_directory_structure(self):
        """Test that fix creates the complete papers directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-fix-papers-structure")
            
            # Remove papers directory structure
            papers_dirs_to_remove = [
                repo_path / FORMALISM_DIR / PAPERS_DIRNAME,
                repo_path / PROCESS_REGIME_DIR / "process" / PAPERS_DIRNAME,
                repo_path / PROCESS_REGIME_DIR / "regime" / PAPERS_DIRNAME,
                repo_path / FUNCTION_APPLICATION_DIR / "function" / PAPERS_DIRNAME,
                repo_path / FUNCTION_APPLICATION_DIR / "application" / PAPERS_DIRNAME
            ]
            
            for papers_dir in papers_dirs_to_remove:
                if papers_dir.exists():
                    shutil.rmtree(papers_dir)
            
            # Run fix
            result = run_texrepo_direct(["fix"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Fix should succeed: {result.stderr}")
            
            # Verify all papers directories are recreated
            for papers_dir in papers_dirs_to_remove:
                self.assertTrue(papers_dir.exists(), f"Papers directory {papers_dir} should be recreated")
                self.assertTrue(papers_dir.is_dir(), f"{papers_dir} should be a directory")


if __name__ == "__main__":
    unittest.main()