#!/usr/bin/env python3
"""
End-to-end test for smart LaTeX build hints feature.
Tests tex-repo b with broken LaTeX and verifies hint output.
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


class LaTeXBuildHintsEndToEndTest(unittest.TestCase):
    """End-to-end test for smart LaTeX build hints."""
    
    def test_error_card_with_runaway_argument(self):
        """Test that _print_error_card provides smart hints for runaway argument errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            
            # Create a paper directory structure
            paper_dir = tmp_path / "broken_paper"
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            # Create entry file
            entry_file = paper_dir / "broken_paper.tex"
            entry_file.write_text("\\documentclass{article}\n\\begin{document}Test\\end{document}")
            
            # Create fake latexmk failure log
            build_dir = paper_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            log_file = build_dir / "broken_paper.log"
            fake_log_content = """This is pdfTeX, Version 3.141592653-2.6-1.40.28 (TeX Live 2025)
entering extended mode
Runaway argument?
{nameinlink,noabbrev]{cleveref} \\usepackage [numbers]{natbib} 
! Paragraph ended before \\@fileswith@ptions was complete.
<to be read again> 
                   \\par 
l.12 

!  ==> Fatal error occurred, no output PDF file produced!
Transcript written on build/broken_paper.log.
"""
            log_file.write_text(fake_log_content)
            
            # Test the error parsing logic directly
            from texrepo.build_cmd import _print_error_card
            
            # Capture print output
            import io
            import contextlib
            captured_output = io.StringIO()
            
            # Mock args for verbose check
            class MockArgs:
                verbose = False
                
            args = MockArgs()
            
            with contextlib.redirect_stdout(captured_output):
                _print_error_card(paper_dir, tmp_path, entry_file, args)
            
            output = captured_output.getvalue()
            
            # Should contain structured error output
            self.assertIn("Build failed", output, "Should indicate build failure")
            self.assertIn("Primary error:", output, "Should show primary error")
            self.assertIn("Suggested action(s):", output, "Should provide suggestions")
            
            # Should contain relevant hints for runaway argument/usepackage issues
            output_lower = output.lower()
            self.assertTrue(
                any(hint in output_lower for hint in ["usepackage", "bracket", "cleveref"]),
                f"Should contain relevant usepackage/bracket hints. Output: {output}"
            )
            
            # Should NOT contain full LaTeX logs by default
            self.assertNotIn("This is pdfTeX", output, "Should not show full LaTeX log without --verbose")
            self.assertNotIn("entering extended mode", output, "Should not show full LaTeX log without --verbose")
            
            # Now test with --verbose
            args.verbose = True
            captured_verbose = io.StringIO()
            
            with contextlib.redirect_stdout(captured_verbose):
                _print_error_card(paper_dir, tmp_path, entry_file, args)
            
            verbose_output = captured_verbose.getvalue()
            
            # Should still contain smart hints
            self.assertIn("Primary error:", verbose_output, "Verbose mode should still show primary error")
            self.assertIn("Suggested action(s):", verbose_output, "Verbose mode should still show suggestions")
            
            # Should now include LaTeX log details
            self.assertTrue(
                any(log_indicator in verbose_output for log_indicator in ["LaTeX log", "This is pdfTeX"]),
                f"Verbose mode should show LaTeX log details. Output: {verbose_output}"
            )
    
    def test_error_card_with_undefined_command(self):
        """Test that _print_error_card provides smart hints for undefined commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            
            paper_dir = tmp_path / "missing_pkg"
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            entry_file = paper_dir / "missing_pkg.tex"
            entry_file.write_text("\\documentclass{article}\n\\begin{document}Test\\end{document}")
            
            build_dir = paper_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            log_file = build_dir / "missing_pkg.log"
            fake_log_content = """! Undefined control sequence.
l.15 This paper will fail because it uses \\cref
                                              {nonexistent} without loading cleveref.
?

!  ==> Fatal error occurred, no output PDF file produced!
"""
            log_file.write_text(fake_log_content)
            
            from texrepo.build_cmd import _print_error_card
            
            import io
            import contextlib
            captured_output = io.StringIO()
            
            class MockArgs:
                verbose = False
                
            args = MockArgs()
            
            with contextlib.redirect_stdout(captured_output):
                _print_error_card(paper_dir, tmp_path, entry_file, args)
            
            output = captured_output.getvalue()
            
            # Should contain error structure
            self.assertIn("Build failed", output, "Should indicate build failure")
            self.assertIn("Primary error:", output, "Should show primary error")
            self.assertIn("Suggested action(s):", output, "Should provide suggestions")
            
            # Should suggest cleveref package
            output_lower = output.lower()
            self.assertIn("cleveref", output_lower, 
                        f"Should suggest cleveref package for \\cref command. Output: {output}")
    
    def test_error_card_with_missing_package_file(self):
        """Test that _print_error_card handles missing package files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            
            paper_dir = tmp_path / "missing_sty"
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            entry_file = paper_dir / "missing_sty.tex"
            entry_file.write_text("\\documentclass{article}\n\\begin{document}Test\\end{document}")
            
            build_dir = paper_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            log_file = build_dir / "missing_sty.log"
            fake_log_content = """! LaTeX Error: File `cleveref.sty' not found.

Type X to quit or <RETURN> to proceed,
or enter new name. (Default extension: sty)

Enter file name: 
! Emergency stop.
<read *> 

l.42 \\usepackage{cleveref}
                         
!  ==> Fatal error occurred, no output PDF file produced!
"""
            log_file.write_text(fake_log_content)
            
            from texrepo.build_cmd import _print_error_card
            
            import io
            import contextlib
            captured_output = io.StringIO()
            
            class MockArgs:
                verbose = False
                
            args = MockArgs()
            
            with contextlib.redirect_stdout(captured_output):
                _print_error_card(paper_dir, tmp_path, entry_file, args)
            
            output = captured_output.getvalue()
            
            # Should contain error structure
            self.assertIn("Build failed", output, "Should indicate build failure")
            self.assertIn("Primary error:", output, "Should show primary error")
            self.assertIn("cleveref.sty", output, "Should mention the missing package file")
            
            # Should provide suggestions
            self.assertIn("Suggested action(s):", output, "Should provide suggestions")
            output_lower = output.lower()
            self.assertIn("cleveref", output_lower, "Should suggest installing cleveref package")
    
    def test_error_card_with_no_log_file(self):
        """Test that _print_error_card handles missing log files gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            
            paper_dir = tmp_path / "no_log"
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            entry_file = paper_dir / "no_log.tex"
            entry_file.write_text("\\documentclass{article}\n\\begin{document}Test\\end{document}")
            
            # No log file created - should handle gracefully
            
            from texrepo.build_cmd import _print_error_card
            
            import io
            import contextlib
            captured_output = io.StringIO()
            
            class MockArgs:
                verbose = False
                
            args = MockArgs()
            
            with contextlib.redirect_stdout(captured_output):
                _print_error_card(paper_dir, tmp_path, entry_file, args)
            
            output = captured_output.getvalue()
            
            # Should indicate build failure but mention log file not found
            self.assertIn("Build failed", output, "Should show build failed message")
            self.assertIn("log file not found", output, "Should mention log file not found")
    
    def test_error_card_structured_output_format(self):
        """Test that error card output follows the required structured format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            
            paper_dir = tmp_path / "format_test"
            paper_dir.mkdir(parents=True, exist_ok=True)
            
            entry_file = paper_dir / "format_test.tex"
            entry_file.write_text("\\documentclass{article}\n\\begin{document}Test\\end{document}")
            
            build_dir = paper_dir / "build"
            build_dir.mkdir(exist_ok=True)
            
            log_file = build_dir / "format_test.log"
            # Use a simple error that should generate suggestions
            fake_log_content = """! Undefined control sequence.
l.10 \\cref
          {eq:test}
?
"""
            log_file.write_text(fake_log_content)
            
            from texrepo.build_cmd import _print_error_card
            
            import io
            import contextlib
            captured_output = io.StringIO()
            
            class MockArgs:
                verbose = False
                
            args = MockArgs()
            
            with contextlib.redirect_stdout(captured_output):
                _print_error_card(paper_dir, tmp_path, entry_file, args)
            
            output = captured_output.getvalue()
            lines = output.strip().split('\n')
            
            # Check required structure:
            # 1. "Build failed."
            # 2. "Primary error: ..."
            # 3. "Suggested action(s):"
            # 4. "  - ..."
            
            self.assertTrue(any("Build failed" in line for line in lines), 
                          f"Should contain 'Build failed'. Output: {output}")
            self.assertTrue(any(line.startswith("Primary error:") for line in lines),
                          f"Should contain 'Primary error:' line. Output: {output}")
            self.assertTrue(any(line.startswith("Suggested action(s):") for line in lines),
                          f"Should contain 'Suggested action(s):' line. Output: {output}")
            # Should have at least one suggestion line starting with "  - "
            suggestion_lines = [line for line in lines if line.startswith("  - ")]
            self.assertGreater(len(suggestion_lines), 0,
                             f"Should have at least one suggestion line. Output: {output}")
    

if __name__ == "__main__":
    unittest.main()