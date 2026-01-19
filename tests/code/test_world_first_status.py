#!/usr/bin/env python3
"""
Tests for world-first structure status validation with tex-repo status.
Tests world terminology, entry file naming rule validation, and error detection.
"""

import subprocess
import tempfile
import unittest
import os
import sys
from pathlib import Path

# Add the repo root to path so we can import texrepo
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from test_world_first_helpers import (
    get_world_terminology,
    get_legacy_terminology,
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


def run_texrepo_subprocess(args, cwd, input_text=DEFAULT_INPUT):
    """Run tex-repo via subprocess."""
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{env.get('PYTHONPATH', '')}"
    
    result = subprocess.run(
        [sys.executable, "-m", "texrepo"] + args,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=cwd,
        env=env
    )
    return result


def create_test_repo(tmp_path: Path, repo_name: str) -> Path:
    """Create a test repository using init."""
    result = run_texrepo_direct(["init", repo_name], cwd=tmp_path)
    if result.returncode != 0:
        raise Exception(f"Failed to create test repo: {result.stderr}")
    return tmp_path / repo_name


class WorldFirstStatusTests(unittest.TestCase):
    """Test tex-repo status validates world-first structure."""
    
    def test_status_succeeds_on_fresh_repo(self):
        """Test that status succeeds on a freshly initialized repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-status")
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertEqual(result.returncode, 0, 
                           f"Status should succeed on fresh repo: stdout={result.stdout} stderr={result.stderr}")
    
    def test_status_uses_world_terminology(self):
        """Test that status output uses world-first terminology."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-terminology")
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            self.assertEqual(result.returncode, 0, f"Status failed: {result.stderr}")
            
            output = result.stdout.lower()
            
            # Check for world-first terminology
            world_terms = get_world_terminology()
            found_terms = [term for term in world_terms if term in output]
            self.assertGreater(len(found_terms), 0, 
                             f"Status output should contain world terminology. Output: {result.stdout}")
            
            # Check that legacy terminology is NOT present
            legacy_terms = get_legacy_terminology()
            for term in legacy_terms:
                self.assertNotIn(term, result.stdout,
                               f"Status output should not contain legacy term '{term}'. Output: {result.stdout}")
    
    def test_status_validates_entry_file_naming(self):
        """Test that status validates the entry file naming rule."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-naming")
            
            # Create a paper with main.tex instead of proper name
            test_paper_dir = repo_path / FORMALISM_DIR / PAPERS_DIRNAME / "00_test_paper"
            test_paper_dir.mkdir(parents=True, exist_ok=True)
            
            # Create main.tex instead of 00_test_paper.tex (violation)
            (test_paper_dir / "main.tex").write_text("\\documentclass{article}\n\\begin{document}\nTest\\end{document}")
            (test_paper_dir / "README.md").write_text("# Test Paper\n")
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            # Status should succeed but show warning about legacy naming
            self.assertEqual(result.returncode, 0, 
                           f"Status should succeed but show warning: {result.stdout}")
            self.assertIn("main.tex", result.stdout, 
                         "Status output should mention main.tex legacy warning")
            self.assertIn("⚠️", result.stdout, 
                         "Status output should show warning symbol for legacy main.tex")
    
    def test_status_detects_missing_readmes(self):
        """Test that status detects missing required READMEs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-missing-readme")
            
            # Remove a required README
            readme_to_remove = repo_path / WORLD_DIR / "README.md"
            readme_to_remove.unlink()
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertNotEqual(result.returncode, 0,
                              f"Status should fail with missing README: {result.stdout}")
            self.assertIn("README", result.stdout,
                         "Status output should mention missing README")
    
    def test_status_detects_missing_foundation_sections(self):
        """Test that status detects missing foundation sections."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-missing-sections")
            
            # Remove a required section file
            section_to_remove = repo_path / FOUNDATION_REL / "sections" / "00_definitions.tex"
            section_to_remove.unlink()
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertNotEqual(result.returncode, 0,
                              f"Status should fail with missing foundation section: {result.stdout}")
            self.assertIn("definitions", result.stdout.lower(),
                         "Status output should mention missing definitions section")
    
    def test_status_detects_missing_spec_files(self):
        """Test that status detects missing spec files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-missing-spec")
            
            # Remove refs.bib from spec
            refs_to_remove = repo_path / SPEC_REL / "refs.bib"
            refs_to_remove.unlink()
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertNotEqual(result.returncode, 0,
                              f"Status should fail with missing refs.bib: {result.stdout}")
            self.assertIn("refs.bib", result.stdout,
                         "Status output should mention missing refs.bib")
    
    def test_status_detects_missing_top_level_directories(self):
        """Test that status detects missing top-level directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-missing-dirs")
            
            # Remove a top-level directory
            import shutil
            shutil.rmtree(repo_path / FORMALISM_DIR)
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertNotEqual(result.returncode, 0,
                              f"Status should fail with missing top-level directory: {result.stdout}")
            self.assertIn(FORMALISM_DIR, result.stdout,
                         f"Status output should mention missing {FORMALISM_DIR}")
    
    def test_status_subprocess_execution(self):
        """Test status via subprocess to match real usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-status-subprocess")
            
            # Run status via subprocess
            result = run_texrepo_subprocess(["status"], cwd=repo_path)
            
            self.assertEqual(result.returncode, 0,
                           f"Subprocess status should succeed: stdout={result.stdout} stderr={result.stderr}")
            
            # Check for world terminology in subprocess output  
            output = result.stdout.lower()
            world_terms = get_world_terminology()
            found_terms = [term for term in world_terms if term in output]
            self.assertGreater(len(found_terms), 0,
                             f"Subprocess status should use world terminology. Output: {result.stdout}")
    
    def test_status_reports_compliant_structure(self):
        """Test that status reports a compliant structure positively."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-compliant")
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertEqual(result.returncode, 0, f"Status should pass: {result.stderr}")
            
            # Should indicate success/compliance
            success_indicators = ["✅", "compliant", "valid", "ok"]
            has_success_indicator = any(indicator in result.stdout.lower() for indicator in success_indicators)
            self.assertTrue(has_success_indicator,
                          f"Status should indicate success/compliance. Output: {result.stdout}")
    
    def test_status_detects_paper_outside_papers_directory(self):
        """Test that status detects papers placed outside papers/ directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = create_test_repo(tmp_path, "test-misplaced-paper")
            
            # Create a paper directly under formalism (not under papers/)
            misplaced_paper = repo_path / FORMALISM_DIR / "00_misplaced"
            misplaced_paper.mkdir()
            (misplaced_paper / "00_misplaced.tex").write_text("\\documentclass{article}\n\\begin{document}\nTest\\end{document}")
            (misplaced_paper / "README.md").write_text("# Misplaced Paper\n")
            
            result = run_texrepo_direct(["status"], cwd=repo_path)
            
            self.assertNotEqual(result.returncode, 0,
                              f"Status should fail with misplaced paper: {result.stdout}")
            # Should mention the misplacement issue
            self.assertTrue("papers" in result.stdout.lower() or "misplaced" in result.stdout.lower() or "unexpected" in result.stdout.lower(),
                          f"Status should mention paper placement issue. Output: {result.stdout}")


if __name__ == "__main__":
    unittest.main()