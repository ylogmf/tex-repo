#!/usr/bin/env python3
"""
CLI Smoke Tests for tex-repo
Tests the CLI functionality by running commands via subprocess

NOTE: With proper installation via 'pip install -e .', the 'tex-repo' command
can be used directly without PYTHONPATH management. This test maintains 
the module approach for consistency with the test environment.
"""
import subprocess
import tempfile
import os
import shutil
from pathlib import Path


def run_texrepo_cmd(args, cwd=None, input_text=None):
    """Run tex-repo command via subprocess and return result"""
    repo_root = Path(__file__).parent.parent
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{repo_root}{os.pathsep}{env.get('PYTHONPATH', '')}"
    
    cmd = ["python", "-m", "texrepo"] + args
    
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=cwd,
            timeout=30,
            env=env
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        raise


def test_cli_smoke():
    """Comprehensive CLI smoke tests"""
    print("🧪 Running CLI smoke tests...")
    
    # Create temporary test directory under tests/
    test_dir = Path(__file__).parent
    temp_base = test_dir / "tmp_smoke"
    temp_base.mkdir(exist_ok=True)
    
    with tempfile.TemporaryDirectory(dir=temp_base) as temp_dir:
        temp_path = Path(temp_dir)
        repo_path = temp_path / "smoke_repo"
        
        # Test 1: Repository initialization
        print("🏗️  Testing repository initialization...")
        
        # First create a README to test no-overwrite behavior
        repo_path.mkdir()
        existing_readme = repo_path / "01_formalism"
        existing_readme.mkdir()
        existing_content = "EXISTING CONTENT SHOULD NOT BE OVERWRITTEN"
        (existing_readme / "README.md").write_text(existing_content)
        
        # Remove the repo directory and recreate for clean init
        shutil.rmtree(repo_path)
        
        init_input = "\n".join([
            "Smoke Test Repo",
            "Smoke Tester", 
            "Smoke Org",
            "smoke@test.com",
            "",  # default affiliation
            "",  # short affiliation  
            "",  # ORCID
            "",  # license
            "",  # date policy
            "",  # bib style
        ])
        
        result = run_texrepo_cmd(["init", str(repo_path)], input_text=init_input)
        assert result.returncode == 0, f"Init failed: {result.stderr}"
        
        # Verify required structure was created
        required_readmes = [
            "SPEC/README.md",
            "SPEC/spec/README.md", 
            "01_formalism/README.md",
            "02_processes/README.md",
            "03_applications/README.md",
            "04_testbeds/README.md",
        ]
        
        for readme_path in required_readmes:
            full_path = repo_path / readme_path
            assert full_path.exists(), f"Missing {readme_path}"
        
        print("✅ Repository initialization works")
        
        # Test 2: Domain creation
        print("📁 Testing domain creation...")
        result = run_texrepo_cmd(["nd", "01_formalism", "test_domain"], cwd=repo_path)
        assert result.returncode == 0, f"Domain creation failed: {result.stderr}"
        
        domain_readme = repo_path / "01_formalism" / "00_test_domain" / "README.md"
        assert domain_readme.exists(), "Domain README should exist"
        print("✅ Domain creation works")
        
        # Test 3: Paper creation  
        print("📄 Testing paper creation...")
        result = run_texrepo_cmd([
            "np", "01_formalism/00_test_domain", "test_paper", "Test Paper"
        ], cwd=repo_path)
        assert result.returncode == 0, f"Paper creation failed: {result.stderr}"
        
        paper_dir = repo_path / "01_formalism" / "00_test_domain" / "test_paper"
        required_files = ["README.md", "main.tex", "refs.bib"]
        required_dirs = ["sections", "build"]
        
        for file_name in required_files:
            assert (paper_dir / file_name).exists(), f"Missing {file_name}"
        
        for dir_name in required_dirs:
            assert (paper_dir / dir_name).exists(), f"Missing {dir_name}/"
        
        print("✅ Paper creation works")
        
        # Test 4: Invalid paper placement detection
        print("⚠️  Testing invalid paper placement detection...")
        bad_paper = repo_path / "01_formalism" / "bad_paper"
        bad_paper.mkdir()
        (bad_paper / "main.tex").write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        result = run_texrepo_cmd(["status"], cwd=repo_path)
        assert result.returncode != 0, "Status should fail with invalid placement"
        assert "E[INVALID_PLACEMENT]" in result.stdout, "Should detect paper under stage"
        print("✅ Invalid placement detection works")
        
        # Clean up bad paper for next tests
        shutil.rmtree(bad_paper)
        
        # Test 5: Missing README detection and fix
        print("🔧 Testing missing README detection and fix...")
        
        # Remove a README and test detection
        processes_readme = repo_path / "02_processes" / "README.md" 
        original_content = processes_readme.read_text()
        processes_readme.unlink()
        
        # Also create custom content in another README to test preservation
        formalism_readme = repo_path / "01_formalism" / "README.md"
        custom_content = "CUSTOM CONTENT THAT SHOULD BE PRESERVED"
        formalism_readme.write_text(custom_content)
        
        # Status should detect missing README
        result = run_texrepo_cmd(["status"], cwd=repo_path)
        assert result.returncode != 0, "Status should fail with missing README"
        assert "E[README_MISSING]" in result.stdout, "Should detect missing README"
        
        # Fix should recreate missing README
        result = run_texrepo_cmd(["fix"], cwd=repo_path)  
        assert result.returncode == 0, f"Fix failed: {result.stderr}"
        assert processes_readme.exists(), "Fix should recreate missing README"
        
        # Verify custom content was preserved
        assert formalism_readme.read_text() == custom_content, "Custom content should be preserved"
        
        # Status should now pass
        result = run_texrepo_cmd(["status"], cwd=repo_path)
        assert result.returncode == 0, "Status should pass after fix"
        
        print("✅ Missing README detection and fix works")
        
        # Test 6: SPEC uniqueness protection
        print("🔒 Testing SPEC uniqueness protection...")
        
        # Try to create domain under SPEC
        result = run_texrepo_cmd(["nd", "SPEC", "invalid_domain"], cwd=repo_path)
        assert result.returncode != 0, "Domain creation under SPEC should fail"
        assert "E[SPEC_IMMUTABLE]" in result.stderr, "Should reject SPEC domain"
        
        # Try to create paper under SPEC  
        result = run_texrepo_cmd(["np", "SPEC", "invalid_paper", "Invalid"], cwd=repo_path)
        assert result.returncode != 0, "Paper creation under SPEC should fail"
        assert "E[SPEC_IMMUTABLE]" in result.stderr, "Should reject SPEC paper"
        
        print("✅ SPEC uniqueness protection works")
        
    print("🎉 All CLI smoke tests passed!")
    return True


def main():
    """Run CLI smoke tests"""
    try:
        success = test_cli_smoke()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ CLI smoke tests failed: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())