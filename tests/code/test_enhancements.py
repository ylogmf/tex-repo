#!/usr/bin/env python3
"""
Test script for tex-repo enhancements
Tests the improved error messages, configuration system, and build caching
"""
import sys
import os
import tempfile
import shutil
import subprocess
from pathlib import Path

def run_texrepo_command(args, input_text=None):
    """Run tex-repo command via the main script"""
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / 'tex-repo'
    
    cmd = [str(script_path)] + args
    result = subprocess.run(cmd, input=input_text, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        raise SystemExit(result.returncode)
    
    return result.returncode
from texrepo.cli import main
from texrepo.config import get_paper_config, create_default_config
from texrepo.build_cmd import needs_rebuild
from texrepo.meta_cmd import parse_paperrepo_metadata
from texrepo.common import TexRepoError
import time


def test_enhanced_init():
    """Test enhanced initialization with metadata"""
    print("🔧 Testing enhanced init with metadata...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        responses = [
            "Test Project",          # project_name
            "Test Author",           # author_name
            "Test University",       # organization
            "test@example.com",      # author_email
            "",                      # default_author_affil (use org)
            "TestU",                 # short_affiliation
            "0000-0000-0000-0000",   # author_orcid
            "MIT License",           # license
            "today",                 # date_policy
            "unsrtnat"               # bibliography_style
        ]
        
        input_text = "\n".join(responses) + "\n"
        exit_code = run_texrepo_command(['init', 'test-repo'], input_text=input_text)
        
        assert exit_code == 0, "Init should succeed"
        
        # Check metadata was created
        repo_path = Path('test-repo')
        assert (repo_path / '.paperrepo').exists(), ".paperrepo should exist"
        assert (repo_path / 'shared' / 'identity.tex').exists(), "identity.tex should exist"
        
        # Check metadata content
        metadata = parse_paperrepo_metadata(repo_path)
        assert metadata['author_name'] == 'Test Author', "Author name should be saved"
        assert metadata['project_name'] == 'Test Project', "Project name should be saved"
        
        # Check identity.tex content
        identity_content = (repo_path / 'shared' / 'identity.tex').read_text()
        assert 'Test Author' in identity_content, "Identity should contain author name"
        assert 'TestU' in identity_content, "Identity should contain short affiliation"
        
        print("✅ Enhanced init test passed")


def test_configuration_system():
    """Test configuration system"""
    print("🔧 Testing configuration system...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Create a test repo
        run_texrepo_command(['init', 'config-test'], input_text="\n"*10)
        
        os.chdir('config-test')
        
        # Create custom config
        config_content = """[paper]
section_count = 5
document_class = report
document_options = 12pt
include_abstract = false

[build]
default_engine = pdflatex
"""
        with open('.texrepo-config', 'w') as f:
            f.write(config_content)
        
        # Test config loading
        config = get_paper_config()
        assert config['section_count'] == 5, "Should use custom section count"
        assert config['document_class'] == 'report', "Should use custom document class"
        assert config['include_abstract'] == False, "Should disable abstract"
        
        # Create a paper and check it uses config
        main(['np', '01_formalism', 'test-paper', 'Test Paper'])
        
        main_tex_content = Path('01_formalism/test-paper/main.tex').read_text()
        assert 'report' in main_tex_content, "Should use report document class"
        assert '12pt' in main_tex_content, "Should use 12pt option"
        
        # Check section count (should be 5 sections)
        sections_dir = Path('01_formalism/test-paper/sections')
        section_files = list(sections_dir.glob('section_*.tex'))
        # Should have section_1.tex through section_5.tex (no section_0.tex due to include_abstract=false)
        assert len(section_files) == 5, f"Should have 5 section files, got {len(section_files)}"
        
        print("✅ Configuration system test passed")


def test_build_caching():
    """Test build caching system"""
    print("🔧 Testing build caching...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Create a test repo
        run_texrepo_command(['init', 'cache-test'], input_text="\n"*10)
        
        os.chdir('cache-test')
        
        # Create test paper
        main(['np', '01_formalism', 'test-cache', 'Test Caching'])
        
        paper_dir = Path('01_formalism/test-cache')
        
        # Initially should need rebuild (no PDF)
        assert needs_rebuild(paper_dir), "Should need rebuild when PDF doesn't exist"
        
        # Create a fake PDF to test caching
        build_dir = paper_dir / 'build'
        build_dir.mkdir(exist_ok=True)
        pdf_file = build_dir / 'main.pdf'
        pdf_file.write_text("fake pdf")
        
        # Set PDF timestamp to now
        current_time = time.time()
        os.utime(pdf_file, (current_time, current_time))
        
        # Should not need rebuild now
        assert not needs_rebuild(paper_dir), "Should not need rebuild when PDF is newer"
        
        # Touch a source file to make it newer
        time.sleep(0.1)  # Ensure different timestamp
        main_tex = paper_dir / 'main.tex'
        main_tex.touch()
        
        # Should need rebuild now
        assert needs_rebuild(paper_dir), "Should need rebuild when source is newer than PDF"
        
        print("✅ Build caching test passed")


def test_improved_error_messages():
    """Test improved error messages"""
    print("🔧 Testing improved error messages...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Create a test repo
        run_texrepo_command(['init', 'error-test'], input_text="\n"*10)
        
        os.chdir('error-test')
        
        # Test error when domain doesn't exist
        try:
            main(['np', 'nonexistent-domain', 'test-paper'])
            assert False, "Should have failed with error"
        except (SystemExit, TexRepoError):
            # Expected - the die() function calls sys.exit()
            pass
        
        # Test error when paper already exists
        main(['np', '01_formalism', 'duplicate-test'])
        
        try:
            main(['np', '01_formalism', 'duplicate-test'])
            assert False, "Should have failed with duplicate paper error"
        except (SystemExit, TexRepoError):
            # Expected
            pass
        
        print("✅ Improved error messages test passed")


def test_config_command():
    """Test config command"""
    print("🔧 Testing config command...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        
        # Create a test repo
        run_texrepo_command(['init', 'config-cmd-test'], input_text="\n"*10)
        
        os.chdir('config-cmd-test')
        
        # Remove default config if it exists
        config_file = Path('.texrepo-config')
        if config_file.exists():
            config_file.unlink()
        
        # Run config command
        exit_code = main(['config'])
        assert exit_code == 0, "Config command should succeed"
        
        # Check config file was created
        assert config_file.exists(), "Config file should be created"
        
        content = config_file.read_text()
        assert '[paper]' in content, "Config should contain paper section"
        assert 'section_count' in content, "Config should contain section_count"
        
        print("✅ Config command test passed")


def run_all_tests():
    """Run all enhancement tests"""
    print("🧪 Running tex-repo enhancement tests...")
    
    original_cwd = os.getcwd()
    
    try:
        test_enhanced_init()
        test_configuration_system()
        test_build_caching()
        test_improved_error_messages()
        test_config_command()
        
        print("\n🎉 All enhancement tests passed!")
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        os.chdir(original_cwd)


if __name__ == '__main__':
    sys.exit(run_all_tests())
