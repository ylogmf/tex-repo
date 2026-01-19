#!/usr/bin/env python3
"""
Tests for world-first structure initialization with tex-repo init.
Tests the new canonical structure and naming rules.
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
    check_world_first_structure,
    check_entry_file_naming,
    check_required_readmes,
    EXPECTED_TOP_LEVEL_DIRS,
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


def run_texrepo_subprocess(args, cwd, input_text=DEFAULT_INPUT):
    """Run tex-repo via subprocess (matches real usage)."""
    # Use python -m texrepo instead of the bash wrapper to avoid shell issues
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


def run_texrepo_direct(args, cwd, input_text=DEFAULT_INPUT):
    """Run tex-repo by importing CLI directly."""
    # Import and call main function directly
    from texrepo.cli import main
    
    # Change to the specified directory 
    old_cwd = os.getcwd()
    old_argv = sys.argv
    old_stdin = sys.stdin
    
    try:
        os.chdir(cwd)
        sys.argv = ['tex-repo'] + args
        
        # Mock stdin for input
        if input_text:
            from io import StringIO
            sys.stdin = StringIO(input_text)
        
        # Capture stdout/stderr
        from io import StringIO
        import contextlib
        
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            try:
                result_code = main()
            except SystemExit as e:
                result_code = e.code or 0
        
        # Create a result object similar to subprocess.run
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


class WorldFirstInitTests(unittest.TestCase):
    """Test tex-repo init creates proper world-first structure."""
    
    def test_init_creates_world_first_structure(self):
        """Test that init creates the complete world-first structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_name = "test-world-repo"
            
            # Run init
            result = run_texrepo_direct(["init", repo_name], cwd=tmp_path)
            
            if result.returncode != 0:
                self.fail(f"tex-repo init failed: stdout={result.stdout} stderr={result.stderr}")
            
            repo_path = tmp_path / repo_name
            self.assertTrue(repo_path.exists(), "Repository directory should be created")
            
            # Check basic metadata files
            self.assertTrue((repo_path / ".paperrepo").exists(), "Missing .paperrepo")
            self.assertTrue((repo_path / ".gitignore").exists(), "Missing .gitignore")
            # Note: .texrepo-config is created by 'tex-repo config' command, not init
            
            # Check top-level directories
            for dir_name in EXPECTED_TOP_LEVEL_DIRS:
                dir_path = repo_path / dir_name
                self.assertTrue(dir_path.is_dir(), f"Missing top-level directory: {dir_name}")
            
            # Check world-first structure
            is_valid, errors = check_world_first_structure(repo_path)
            if not is_valid:
                self.fail(f"World-first structure validation failed: {errors}")
            
            # Check required READMEs
            all_readmes_exist, missing_readmes = check_required_readmes(repo_path)
            if not all_readmes_exist:
                self.fail(f"Missing required READMEs: {missing_readmes}")
    
    def test_foundation_paper_structure(self):
        """Test foundation paper has correct structure and entry file naming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_name = "test-foundation"
            
            result = run_texrepo_direct(["init", repo_name], cwd=tmp_path)
            self.assertEqual(result.returncode, 0, f"Init failed: {result.stderr}")
            
            repo_path = tmp_path / repo_name
            foundation_dir = repo_path / FOUNDATION_REL
            
            # Check entry file naming rule
            is_valid, message = check_entry_file_naming(foundation_dir)
            self.assertTrue(is_valid, f"Foundation entry file naming failed: {message}")
            
            # Check foundation-specific files
            self.assertTrue((foundation_dir / "refs.bib").exists(), "Missing foundation refs.bib")
            self.assertTrue((foundation_dir / "sections" / "00_definitions.tex").exists(), 
                          "Missing definitions section")
            self.assertTrue((foundation_dir / "sections" / "01_axioms.tex").exists(),
                          "Missing axioms section") 
            self.assertTrue((foundation_dir / "README.md").exists(), "Missing foundation README")
            
            # Check content
            entry_file = foundation_dir / f"{FOUNDATION_DIRNAME}.tex"
            content = entry_file.read_text()
            self.assertIn("Foundation", content, "Entry file should reference Foundation title")
            self.assertIn("00_definitions", content, "Entry file should include definitions section")
            self.assertIn("01_axioms", content, "Entry file should include axioms section")
    
    def test_spec_paper_structure(self):
        """Test spec paper has correct structure and entry file naming."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_name = "test-spec"
            
            result = run_texrepo_direct(["init", repo_name], cwd=tmp_path)
            self.assertEqual(result.returncode, 0, f"Init failed: {result.stderr}")
            
            repo_path = tmp_path / repo_name
            spec_dir = repo_path / SPEC_REL
            
            # Check entry file naming rule
            is_valid, message = check_entry_file_naming(spec_dir)
            self.assertTrue(is_valid, f"Spec entry file naming failed: {message}")
            
            # Check spec-specific files
            self.assertTrue((spec_dir / "refs.bib").exists(), "Missing spec refs.bib")
            self.assertTrue((spec_dir / "README.md").exists(), "Missing spec README")
            
            # Check entry file exists and has proper content
            entry_file = spec_dir / f"{SPEC_DIRNAME}.tex"
            self.assertTrue(entry_file.exists(), "Missing spec entry file")
            content = entry_file.read_text()
            self.assertIn("Spec", content, "Entry file should reference Spec title")
    
    def test_papers_directory_structure(self):
        """Test that all required papers/ directories are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_name = "test-papers"
            
            result = run_texrepo_direct(["init", repo_name], cwd=tmp_path)
            self.assertEqual(result.returncode, 0, f"Init failed: {result.stderr}")
            
            repo_path = tmp_path / repo_name
            
            # Check all papers directories
            expected_papers_dirs = [
                f"{FORMALISM_DIR}/{PAPERS_DIRNAME}",
                f"{PROCESS_REGIME_DIR}/process/{PAPERS_DIRNAME}",
                f"{PROCESS_REGIME_DIR}/regime/{PAPERS_DIRNAME}",
                f"{FUNCTION_APPLICATION_DIR}/function/{PAPERS_DIRNAME}",
                f"{FUNCTION_APPLICATION_DIR}/application/{PAPERS_DIRNAME}"
            ]
            
            for papers_dir in expected_papers_dirs:
                papers_path = repo_path / papers_dir
                self.assertTrue(papers_path.is_dir(), f"Missing papers directory: {papers_dir}")
    
    def test_init_from_text_file(self):
        """Test init from text file populates spec properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            
            # Create a text file with content
            text_file = tmp_path / "init_content.txt"
            test_content = "This is test content.\nIt has multiple lines.\nAnd should be LaTeX-escaped."
            text_file.write_text(test_content)
            
            result = run_texrepo_direct(["init", str(text_file)], cwd=tmp_path)
            self.assertEqual(result.returncode, 0, f"Init from text failed: {result.stderr}")
            
            repo_path = tmp_path / "init_content"  # repo name is text file stem
            
            # Check that content was imported into spec section_1.tex
            section_path = repo_path / SPEC_REL / "sections" / "section_1.tex"
            self.assertTrue(section_path.exists(), "Missing section_1.tex after text import")
            
            section_content = section_path.read_text()
            self.assertIn("Section 1", section_content, "Section should have proper heading")
            self.assertIn("This is test content", section_content, "Content should be imported")
    
    def test_init_refuses_existing_directory(self):
        """Test that init refuses to overwrite existing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            existing_dir = tmp_path / "existing"
            existing_dir.mkdir()
            
            result = run_texrepo_direct(["init", "existing"], cwd=tmp_path)
            
            self.assertNotEqual(result.returncode, 0, "Init should refuse existing directories")
            self.assertFalse((existing_dir / ".paperrepo").exists(),
                           "Existing directory should remain untouched")
    
    def test_init_subprocess_execution(self):
        """Test init via subprocess to match real usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_name = "test-subprocess"
            
            # Run via subprocess (as specified in requirements)
            result = run_texrepo_subprocess(["init", repo_name], cwd=tmp_path)
            
            if result.returncode != 0:
                self.fail(f"Subprocess init failed: stdout={result.stdout} stderr={result.stderr}")
            
            repo_path = tmp_path / repo_name
            
            # Verify basic structure was created
            self.assertTrue((repo_path / ".paperrepo").exists(), "Missing .paperrepo")
            self.assertTrue((repo_path / FOUNDATION_REL / f"{FOUNDATION_DIRNAME}.tex").exists(), 
                          "Missing foundation entry file")
            self.assertTrue((repo_path / SPEC_REL / f"{SPEC_DIRNAME}.tex").exists(),
                          "Missing spec entry file")


if __name__ == "__main__":
    unittest.main()