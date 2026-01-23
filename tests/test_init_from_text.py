"""Test initialization from text manuscript."""

import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from texrepo.cmd_init import parse_text_manuscript, cmd_init


class Args:
    """Mock args object for testing."""
    def __init__(self, name):
        self.name = name


def test_parse_text_manuscript():
    """Test parsing a simple text manuscript."""
    fixture_path = Path(__file__).parent / 'fixtures' / 'sample_manuscript.txt'
    
    result = parse_text_manuscript(fixture_path)
    
    assert result['title'] == 'Quantum Computing and Information Theory'
    assert result['author'] == 'Alice Johnson'
    assert result['repo_name'] == 'sample_manuscript'
    assert 'Introduction' in result['body']
    assert 'quantum computing' in result['body']


def test_parse_minimal_manuscript(tmp_path):
    """Test parsing manuscript with minimal content."""
    manuscript = tmp_path / "minimal.txt"
    manuscript.write_text("My Title\nJohn Doe\n\nSome content here.")
    
    result = parse_text_manuscript(manuscript)
    
    assert result['title'] == 'My Title'
    assert result['author'] == 'John Doe'
    assert result['body'] == 'Some content here.'
    assert result['repo_name'] == 'minimal'


def test_parse_manuscript_with_blank_lines(tmp_path):
    """Test parsing manuscript with leading blank lines."""
    manuscript = tmp_path / "blanks.txt"
    manuscript.write_text("\n\nThe Title\n\nThe Author\n\n\nThe body content\nwith multiple lines.")
    
    result = parse_text_manuscript(manuscript)
    
    assert result['title'] == 'The Title'
    assert result['author'] == 'The Author'
    assert 'body content' in result['body']


def test_parse_manuscript_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        parse_text_manuscript('nonexistent.txt')


def test_parse_manuscript_insufficient_content(tmp_path):
    """Test error handling for manuscript with only title."""
    manuscript = tmp_path / "insufficient.txt"
    manuscript.write_text("Only a title\n")
    
    with pytest.raises(ValueError, match="at least a title and author"):
        parse_text_manuscript(manuscript)


def test_init_from_text_manuscript(tmp_path):
    """Test full repository initialization from text manuscript."""
    # Create test manuscript
    manuscript = tmp_path / "test_doc.txt"
    manuscript.write_text("""Research Paper Title
Dr. Jane Smith

This is the introduction to my research.

Section One

Content for section one.

Section Two

More content here.
""")
    
    # Change to tmp directory for test
    original_cwd = Path.cwd()
    try:
        # Run init command
        args = Args(str(manuscript))
        result = cmd_init(args)
        
        assert result == 0
        
        # Verify repository structure
        repo_dir = tmp_path / 'test_doc'
        assert repo_dir.exists()
        assert (repo_dir / '.paperrepo').exists()
        
        # Check shared directory
        shared_dir = repo_dir / 'shared'
        assert (shared_dir / 'packages.tex').exists()
        assert (shared_dir / 'preamble.tex').exists()
        assert (shared_dir / 'macros.tex').exists()
        assert (shared_dir / 'notation.tex').exists()
        assert (shared_dir / 'identity.tex').exists()
        
        # Check identity.tex contains manuscript metadata
        identity_content = (shared_dir / 'identity.tex').read_text()
        assert 'Research Paper Title' in identity_content
        assert 'Dr. Jane Smith' in identity_content
        
        # Check introduction document was created
        intro_dir = repo_dir / '00_introduction'
        intro_tex = intro_dir / '00_introduction.tex'
        assert intro_tex.exists()
        
        # Check content was imported
        intro_content = intro_tex.read_text()
        assert 'introduction to my research' in intro_content
        assert 'Section One' in intro_content
        assert 'Section Two' in intro_content
        
        # Check build directory exists
        assert (intro_dir / 'build').exists()
        
        # Check stage directories
        assert (repo_dir / '01_process_regime').exists()
        assert (repo_dir / '02_function_application').exists()
        assert (repo_dir / '03_hypophysis').exists()
        assert (repo_dir / 'releases').exists()
        
        # Check .gitignore
        assert (repo_dir / '.gitignore').exists()
        
    finally:
        pass


def test_init_regular_name_still_works(tmp_path):
    """Test that regular init without text file still works."""
    original_cwd = Path.cwd()
    try:
        # Run init with plain name
        args = Args('my_repo')
        result = cmd_init(args)
        
        assert result == 0
        
        # Verify basic structure
        repo_dir = Path('my_repo').resolve()
        assert repo_dir.exists()
        assert (repo_dir / '.paperrepo').exists()
        assert (repo_dir / 'shared' / 'identity.tex').exists()
        
        # Check identity has default content
        identity_content = (repo_dir / 'shared' / 'identity.tex').read_text()
        assert 'Author Name' in identity_content
        
        # Check introduction is empty (no tex file)
        intro_dir = repo_dir / '00_introduction'
        assert intro_dir.exists()
        assert not (intro_dir / '00_introduction.tex').exists()
        
        # Cleanup
        shutil.rmtree(repo_dir)
        
    finally:
        pass


def test_init_rejects_existing_directory(tmp_path):
    """Test that init fails if directory already exists."""
    # Create directory
    existing = tmp_path / 'existing_repo'
    existing.mkdir()
    
    # Try to init into it
    args = Args(str(existing))
    result = cmd_init(args)
    
    assert result == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
