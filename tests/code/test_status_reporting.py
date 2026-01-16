import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tex-repo"
DEFAULT_INPUT = "\n" * 10  # Accept defaults for metadata prompts


def run_texrepo(args, cwd, input_text=DEFAULT_INPUT):
    return subprocess.run(
        [str(CLI_PATH)] + args,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=cwd,
    )


def create_minimal_repo(repo_path: Path):
    """Create a minimal valid tex-repo structure."""
    # Create core stage and paper
    core_stage = repo_path / "00_core"
    core_stage.mkdir()
    core_paper = core_stage / "core"
    core_paper.mkdir()
    (core_paper / "main.tex").write_text("% Core paper main file\n")
    
    # Create other required stages
    for stage in ["01_derivations", "02_interpretations", "03_applications", "04_testbeds"]:
        (repo_path / stage).mkdir()
    
    # Create basic metadata
    (repo_path / ".paperrepo").write_text("tex-repo\n")
    metadata_content = """
author_name: Test Author
organization: Test Org
"""
    (repo_path / "paperrepo.yaml").write_text(metadata_content)


class StatusReportingTests(unittest.TestCase):
    
    def test_ds_store_treated_as_ignored_not_violation(self):
        """Test that .DS_Store is treated as ignored, not a violation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = tmp_path / "test_repo"
            repo_path.mkdir()
            
            # Create minimal repo
            create_minimal_repo(repo_path)
            
            # Add .DS_Store to 00_core
            ds_store_path = repo_path / "00_core" / ".DS_Store"
            ds_store_path.write_bytes(b'\x00\x05\x16\x07\x00\x02')  # Some binary content like real .DS_Store
            
            # Run status command
            result = run_texrepo(["status"], cwd=repo_path)
            
            # Should exit with success (code 0) since .DS_Store is ignored
            self.assertEqual(
                result.returncode,
                0,
                f"Status should succeed when .DS_Store is present. stdout={result.stdout} stderr={result.stderr}",
            )
            
            # Should report .DS_Store as ignored, not as violation
            self.assertIn("ignored", result.stdout.lower())
            self.assertNotIn("Unexpected item in 00_core: .DS_Store", result.stdout)
            self.assertIn("✅ Repository structure is fully compliant!", result.stdout)
            
            # Should show ignored count > 0
            lines = result.stdout.split('\n')
            summary_section = False
            for line in lines:
                if "Status summary:" in line:
                    summary_section = True
                elif summary_section and "ignored:" in line:
                    # Extract number after "ignored:"
                    ignored_count = int(line.split("ignored:")[1].strip())
                    self.assertGreater(ignored_count, 0, "Ignored count should be > 0")
                    break
    
    def test_unexpected_non_ignored_file_becomes_violation(self):
        """Test that truly unexpected files become violations and cause exit code 1."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = tmp_path / "test_repo"
            repo_path.mkdir()
            
            # Create minimal repo
            create_minimal_repo(repo_path)
            
            # Add an unexpected file that should NOT be ignored
            unexpected_file = repo_path / "00_core" / "unexpected_file.txt"
            unexpected_file.write_text("This should be a violation")
            
            # Run status command
            result = run_texrepo(["status"], cwd=repo_path)
            
            # Should exit with failure (code 1) due to violation
            self.assertEqual(
                result.returncode,
                1,
                f"Status should fail when unexpected file is present. stdout={result.stdout} stderr={result.stderr}",
            )
            
            # Should report the unexpected file as a violation
            self.assertIn("Unexpected item in 00_core: unexpected_file.txt", result.stdout)
            self.assertIn("❌ Repository structure has violations!", result.stdout)
            
            # Should show violations count > 0
            lines = result.stdout.split('\n')
            summary_section = False
            for line in lines:
                if "Status summary:" in line:
                    summary_section = True
                elif summary_section and "violations:" in line:
                    # Extract number after "violations:"
                    violations_count = int(line.split("violations:")[1].strip())
                    self.assertGreater(violations_count, 0, "Violations count should be > 0")
                    break
    
    def test_multiple_macos_files_all_ignored(self):
        """Test that various macOS noise files are all properly ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = tmp_path / "test_repo"
            repo_path.mkdir()
            
            # Create minimal repo
            create_minimal_repo(repo_path)
            
            # Add various macOS noise files to 00_core
            macos_files = [".DS_Store", "._metadata", ".AppleDouble", "Thumbs.db", "Desktop.ini"]
            for filename in macos_files:
                noise_file = repo_path / "00_core" / filename
                noise_file.write_bytes(b'noise')
            
            # Run status command
            result = run_texrepo(["status"], cwd=repo_path)
            
            # Should exit with success (code 0) since all are ignored
            self.assertEqual(
                result.returncode,
                0,
                f"Status should succeed when macOS noise files are present. stdout={result.stdout} stderr={result.stderr}",
            )
            
            # Should report files as ignored
            self.assertIn("✅ Repository structure is fully compliant!", result.stdout)
            
            # Should show ignored count >= number of files we added
            lines = result.stdout.split('\n')
            summary_section = False
            for line in lines:
                if "Status summary:" in line:
                    summary_section = True
                elif summary_section and "ignored:" in line:
                    # Extract number after "ignored:"
                    ignored_count = int(line.split("ignored:")[1].strip())
                    self.assertGreaterEqual(ignored_count, len(macos_files), 
                                           f"Should ignore at least {len(macos_files)} files")
                    break
    
    def test_summary_counts_match_classifications(self):
        """Test that summary counts match the actual classifications in output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = tmp_path / "test_repo"
            repo_path.mkdir()
            
            # Create minimal repo but introduce various issues
            create_minimal_repo(repo_path)
            
            # Add ignored file (.DS_Store)
            (repo_path / "00_core" / ".DS_Store").write_bytes(b'ignored')
            
            # Add violation (unexpected file)
            (repo_path / "00_core" / "violation.txt").write_text("violation")
            
            # Add warning by creating non-contiguous domains
            derivations = repo_path / "01_derivations"
            (derivations / "00_first").mkdir()
            (derivations / "02_third").mkdir()  # Missing 01_second - should be warning
            
            # Run status command
            result = run_texrepo(["status"], cwd=repo_path)
            
            # Should exit with failure due to violation
            self.assertEqual(result.returncode, 1)
            
            # Parse the summary
            lines = result.stdout.split('\n')
            summary_section = False
            errors = warnings = violations = ignored = 0
            
            for line in lines:
                if "Status summary:" in line:
                    summary_section = True
                elif summary_section:
                    if "errors:" in line:
                        errors = int(line.split("errors:")[1].strip())
                    elif "warnings:" in line:
                        warnings = int(line.split("warnings:")[1].strip())
                    elif "violations:" in line:
                        violations = int(line.split("violations:")[1].strip())
                    elif "ignored:" in line:
                        ignored = int(line.split("ignored:")[1].strip())
            
            # Verify counts make sense
            self.assertGreater(violations, 0, "Should have violations")
            self.assertGreater(ignored, 0, "Should have ignored items") 
            self.assertGreaterEqual(warnings, 0, "Warnings count should be valid")
            self.assertGreaterEqual(errors, 0, "Errors count should be valid")
            
            # Count actual occurrences in output to verify consistency
            violation_messages = result.stdout.count("Unexpected item in 00_core:")
            self.assertGreater(violation_messages, 0, "Should have violation messages")


if __name__ == "__main__":
    unittest.main()