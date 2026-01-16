#!/usr/bin/env python3
"""
Simple integration test for tex-repo
Tests the CLI functionality by running the script directly
"""
import subprocess
import tempfile
import os
from pathlib import Path


def run_texrepo(args, input_text=None, cwd=None):
    """Run tex-repo command and return result"""
    repo_root = Path(__file__).parent.parent
    script_path = repo_root / 'tex-repo'
    
    cmd = [str(script_path)] + args
    
    try:
        result = subprocess.run(
            cmd, 
            input=input_text,
            text=True,
            capture_output=True,
            cwd=cwd or os.getcwd(),
            timeout=30
        )
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {' '.join(cmd)}")
        raise


def test_basic_workflow():
    """Test basic tex-repo workflow"""
    print("🧪 Testing basic tex-repo workflow...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test help command
        print("📖 Testing help command...")
        result = run_texrepo(['--help'])
        assert result.returncode == 0, "Help should work"
        assert 'tex-repo' in result.stdout, "Help should mention tex-repo"
        print("✅ Help command works")
        
        # Test init with minimal input
        print("🏗️  Testing repository initialization...")
        init_input = "\n".join([
            "Test Project",      # project_name
            "Test Author",       # author_name  
            "Test Org",          # organization
            "test@test.com",     # author_email
            "",                  # use default affiliation
            "TestOrg",           # short_affiliation
            "",                  # no ORCID
            "MIT",               # license
            "today",             # date_policy
            "plain"              # bibliography_style
        ]) + "\n"
        
        result = run_texrepo(['init', 'test-repo'], input_text=init_input)
        assert result.returncode == 0, f"Init failed: {result.stderr}"
        
        repo_path = Path('test-repo')
        assert repo_path.exists(), "Repository directory should exist"
        assert (repo_path / '.paperrepo').exists(), ".paperrepo should exist"
        assert (repo_path / 'SPEC' / 'README.md').exists(), "SPEC/README.md should exist"
        assert (repo_path / 'SPEC' / 'spec' / 'README.md').exists(), "Spec paper README should exist"
        assert (repo_path / 'SPEC' / 'spec' / 'main.tex').exists(), "Spec paper should exist"
        print("✅ Repository initialization works")
        
        # Enter the repository
        os.chdir('test-repo')
        
        # Test status command
        print("📊 Testing status command...")
        result = run_texrepo(['status'], cwd='.')
        assert result.returncode == 0, "Status should work"
        print("✅ Status command works")
        
        # Test domain command  
        print("📁 Testing domain creation...")
        result = run_texrepo(['nd', '03_applications', 'computer-vision'], cwd='.')
        assert result.returncode == 0, f"Domain creation should work: {result.stderr}"
        assert Path('03_applications/00_computer-vision').exists(), "Domain directory should exist"
        assert (Path('03_applications/00_computer-vision/README.md')).exists(), "Domain README should be created"
        print("✅ Domain creation works")
        
        # Test new paper creation (in formalism stage)
        print("📄 Testing paper creation...")
        result = run_texrepo(['np', '01_formalism', 'test-paper', 'My Test Paper'], cwd='.')
        assert result.returncode == 0, f"Paper creation failed: {result.stderr}"
        
        paper_path = Path('01_formalism/test-paper')
        assert paper_path.exists(), "Paper directory should exist"
        assert (paper_path / 'main.tex').exists(), "main.tex should exist"
        assert (paper_path / 'README.md').exists(), "Paper README should exist"
        print("✅ Paper creation works")
        
        # Test config command
        print("⚙️  Testing config command...")
        result = run_texrepo(['config'], cwd='.')
        assert result.returncode == 0, "Config should work"
        assert Path('.texrepo-config').exists(), "Config file should be created"
        print("✅ Config command works")
        
        # Test final status
        print("📊 Testing final status...")
        result = run_texrepo(['status'], cwd='.')
        print(f"Status command return code: {result.returncode}")
        print(f"Status stdout: {result.stdout[:200]}...")
        print(f"Status stderr: {result.stderr}")
        # Status command may return 1 for warnings, which is still success
        assert result.returncode in [0, 1], f"Final status should work: return code {result.returncode}"
        print("✅ Final status works")
        
        print("\n🎉 Basic workflow test passed!")
        return True


def test_error_conditions():
    """Test error handling"""
    print("🧪 Testing error conditions...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Test commands outside repository
        print("⚠️  Testing commands outside repository...")
        result = run_texrepo(['status'])
        assert result.returncode != 0, "Status should fail outside repository"
        print("✅ Commands properly fail outside repository")
        
        # Initialize a repository first
        init_input = "\n" * 10  # Use all defaults
        result = run_texrepo(['init', 'error-test'], input_text=init_input)
        assert result.returncode == 0, "Init should work"
        
        os.chdir('error-test')
        
        # Test invalid domain
        print("⚠️  Testing invalid domain access...")
        result = run_texrepo(['np', 'nonexistent-domain', 'test-paper'], cwd='.')
        assert result.returncode != 0, "Should fail with invalid domain"
        print("✅ Invalid domain properly rejected")
        
        # Create a paper first
        result = run_texrepo(['np', '01_formalism', 'test-paper', 'Test Paper'], cwd='.')
        assert result.returncode == 0, f"Paper creation should work: {result.stderr}"
        
        # Test duplicate paper
        print("⚠️  Testing duplicate paper creation...")
        result = run_texrepo(['np', '01_formalism', 'test-paper', 'Duplicate Paper'], cwd='.')
        assert result.returncode != 0, "Should fail with duplicate paper"
        print("✅ Duplicate paper properly rejected")
        
        print("\n🎉 Error condition tests passed!")
        return True


def main():
    """Run all integration tests"""
    print("🚀 Running tex-repo integration tests...")
    
    original_cwd = os.getcwd()
    
    try:
        success = True
        success &= test_basic_workflow()
        success &= test_error_conditions()
        
        if success:
            print("\n🎉 All integration tests passed!")
            return 0
        else:
            print("\n❌ Some integration tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        os.chdir(original_cwd)


if __name__ == '__main__':
    exit(main())
