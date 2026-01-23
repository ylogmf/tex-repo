"""Integration tests for tex-repo commands."""

import pytest
import tempfile
import shutil
from pathlib import Path
import subprocess
import sys


@pytest.fixture
def temp_repo():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def run_texrepo(args, cwd=None):
    """Run tex-repo command and return result."""
    cmd = [sys.executable, '-m', 'texrepo'] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    return result


class TestInit:
    """Test init command."""
    
    def test_init_creates_structure(self, temp_repo):
        """Test that init creates all required files and directories."""
        repo_name = 'test-repo'
        result = run_texrepo(['init', repo_name], cwd=temp_repo)
        
        assert result.returncode == 0, f"init failed: {result.stderr}"
        
        repo_dir = temp_repo / repo_name
        assert repo_dir.exists()
        assert (repo_dir / '.paperrepo').exists()
        assert (repo_dir / 'shared').is_dir()
        assert (repo_dir / 'shared' / 'preamble.tex').exists()
        assert (repo_dir / 'shared' / 'macros.tex').exists()
        assert (repo_dir / 'shared' / 'notation.tex').exists()
        assert (repo_dir / 'shared' / 'identity.tex').exists()
        # Stage directories (not including 00_introduction which is created by book command)
        assert (repo_dir / '01_process_regime').is_dir()
        assert (repo_dir / '02_function_application').is_dir()
        assert (repo_dir / '03_hypophysis').is_dir()
        assert (repo_dir / 'releases').is_dir()
        assert (repo_dir / '.gitignore').exists()
    
    def test_init_rejects_existing_directory(self, temp_repo):
        """Test that init fails if directory already exists."""
        repo_name = 'test-repo'
        (temp_repo / repo_name).mkdir()
        
        result = run_texrepo(['init', repo_name], cwd=temp_repo)
        assert result.returncode != 0


class TestBook:
    """Test book command."""
    
    def test_book_creates_structure(self, temp_repo):
        """Test that book creates complete book structure."""
        # Initialize repo first
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        
        # Create book
        result = run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        assert result.returncode == 0, f"book failed: {result.stderr}"
        
        book_dir = repo_dir / '00_introduction'
        assert book_dir.exists()
        assert (book_dir / '00_introduction.tex').exists()
        assert (book_dir / 'build').is_dir()
        assert (book_dir / 'parts' / 'frontmatter').is_dir()
        assert (book_dir / 'parts' / 'parts').is_dir()
        assert (book_dir / 'parts' / 'backmatter').is_dir()
        assert (book_dir / 'build' / 'sections_index.tex').exists()
        assert (book_dir / 'build' / 'chapters_index.tex').exists()
    
    def test_book_auto_numbering(self, temp_repo):
        """Test that books are auto-numbered."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        
        # First book (not Introduction) should be 04_ (after stage dirs 01,02,03)
        run_texrepo(['book', 'First'], cwd=repo_dir)
        assert (repo_dir / '04_first').exists()
        
        # Second book should be 05_
        run_texrepo(['book', 'Second'], cwd=repo_dir)
        assert (repo_dir / '05_second').exists()


class TestPaper:
    """Test paper command."""
    
    def test_paper_creates_structure(self, temp_repo):
        """Test that paper creates complete paper structure."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        
        result = run_texrepo(['paper', 'Test Paper'], cwd=repo_dir)
        assert result.returncode == 0, f"paper failed: {result.stderr}"
        
        # Papers numbered after stage dirs (01,02,03), so first paper is 04
        paper_dir = repo_dir / '04_test_paper'
        assert paper_dir.exists()
        # Entry file matches directory name
        assert (paper_dir / '04_test_paper.tex').exists()
        assert (paper_dir / 'sections').is_dir()
        assert (paper_dir / 'build').is_dir()
        assert (paper_dir / 'refs.bib').exists()


class TestPart:
    """Test part command."""
    
    def test_part_creates_structure(self, temp_repo):
        """Test that part creates complete part structure."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        
        book_dir = repo_dir / '00_introduction'
        result = run_texrepo(['part', 'Foundations'], cwd=book_dir)
        assert result.returncode == 0, f"part failed: {result.stderr}"
        
        part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
        assert part_dir.exists()
        assert (part_dir / 'part.tex').exists()
        assert (part_dir / 'chapters').is_dir()
    
    def test_part_requires_book_context(self, temp_repo):
        """Test that part fails outside a book."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        
        result = run_texrepo(['part', 'Foundations'], cwd=repo_dir)
        assert result.returncode != 0


class TestChapter:
    """Test chapter command."""
    
    def test_chapter_creates_structure(self, temp_repo):
        """Test that chapter creates complete chapter structure."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        
        book_dir = repo_dir / '00_introduction'
        run_texrepo(['part', 'Foundations'], cwd=book_dir)
        
        part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
        result = run_texrepo(['chapter', 'Overview'], cwd=part_dir)
        assert result.returncode == 0, f"chapter failed: {result.stderr}"
        
        # Chapter is a directory with chapter.tex and section placeholders
        chapter_dir = part_dir / 'chapters' / '01_overview'
        assert chapter_dir.is_dir()
        assert (chapter_dir / 'chapter.tex').is_file()
        # Check section placeholders 1-1.tex through 1-10.tex
        for i in range(1, 11):
            assert (chapter_dir / f'1-{i}.tex').is_file()

    
    def test_chapter_requires_part_context(self, temp_repo):
        """Test that chapter fails outside a part."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        
        book_dir = repo_dir / '00_introduction'
        result = run_texrepo(['chapter', 'Overview'], cwd=book_dir)
        assert result.returncode != 0


class TestValidation:
    """Test validation commands."""
    
    def test_status_on_valid_repo(self, temp_repo):
        """Test that status passes on a valid repository."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        
        book_dir = repo_dir / '00_introduction'
        result = run_texrepo(['status'], cwd=book_dir)
        assert result.returncode == 0
        assert 'no violations' in result.stdout.lower()
    
    def test_guard_fails_on_violations(self, temp_repo):
        """Test that guard exits non-zero on violations."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        
        # Remove required directory to create violation
        book_dir = repo_dir / '00_introduction'
        shutil.rmtree(book_dir / 'parts' / 'frontmatter')
        
        result = run_texrepo(['guard'], cwd=book_dir)
        assert result.returncode != 0
        assert 'BOOK_FRONTMATTER_DIR_MISSING' in result.stdout
    
    def test_fix_creates_missing_files(self, temp_repo):
        """Test that fix creates missing required files."""
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        
        book_dir = repo_dir / '00_introduction'
        # Remove spine file
        (book_dir / 'build' / 'sections_index.tex').unlink()
        
        result = run_texrepo(['fix'], cwd=book_dir)
        assert result.returncode == 0
        assert (book_dir / 'build' / 'sections_index.tex').exists()


class TestWorkflow:
    """Test complete workflows."""
    
    def test_full_book_workflow(self, temp_repo):
        """Test complete book creation workflow."""
        # Init
        run_texrepo(['init', 'test-repo'], cwd=temp_repo)
        repo_dir = temp_repo / 'test-repo'
        
        # Create book
        run_texrepo(['book', 'Introduction'], cwd=repo_dir)
        book_dir = repo_dir / '00_introduction'
        
        # Create part
        run_texrepo(['part', 'Foundations'], cwd=book_dir)
        part_dir = book_dir / 'parts' / 'parts' / '01_foundations'
        
        # Create chapter
        run_texrepo(['chapter', 'Overview'], cwd=part_dir)
        # Chapter is a directory with chapter.tex and section placeholders
        chapter_dir = part_dir / 'chapters' / '01_overview'
        
        # Verify structure
        assert chapter_dir.is_dir()
        assert (chapter_dir / 'chapter.tex').is_file()
        for i in range(1, 11):
            assert (chapter_dir / f'1-{i}.tex').is_file()
        
        # Validate
        result = run_texrepo(['status'], cwd=book_dir)
        assert result.returncode == 0
