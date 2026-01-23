"""Tests for new simplified commands: init, book, paper, part, chapter."""
import pytest
from pathlib import Path
import tempfile
import shutil

from texrepo.init_simple_cmd import cmd_init_simple
from texrepo.book_cmd import cmd_book
from texrepo.paper_cmd import cmd_paper
from texrepo.part_cmd import cmd_part
from texrepo.chapter_cmd import cmd_chapter
from texrepo.common import TexRepoError


class Args:
    """Mock args object."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture
def temp_workspace(monkeypatch):
    """Create a temporary workspace and clean up after."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir).resolve()
        monkeypatch.chdir(tmpdir)
        yield tmpdir


def test_init_creates_minimal_repo(temp_workspace, monkeypatch):
    """Test tex-repo init creates minimal repository structure."""
    # Mock prompt_for_metadata to avoid interactive input
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    result = cmd_init_simple(args)
    
    assert result == 0
    repo = temp_workspace / "test-repo"
    assert repo.exists()
    assert (repo / ".paperrepo").exists()
    assert (repo / ".gitignore").exists()
    assert (repo / "shared").exists()
    assert (repo / "shared" / "preamble.tex").exists()
    assert (repo / "shared" / "macros.tex").exists()
    assert (repo / "shared" / "identity.tex").exists()


def test_init_rejects_existing_directory(temp_workspace, monkeypatch):
    """Test init refuses to overwrite existing directory."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    # Create directory first
    existing = temp_workspace / "existing"
    existing.mkdir()
    
    args = Args(name="existing")
    with pytest.raises(TexRepoError, match="already exists"):
        cmd_init_simple(args)


def test_book_creates_structure_at_repo_root(temp_workspace, monkeypatch):
    """Test tex-repo book creates book structure with correct numbering."""
    # Initialize repo first
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    cmd_init_simple(args)
    
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    # Create first book
    args = Args(title="Introduction to Theory")
    result = cmd_book(args)
    
    assert result == 0
    book_dir = repo / "00_introduction_to_theory"
    assert book_dir.exists()
    assert (book_dir / "00_introduction_to_theory.tex").exists()
    assert (book_dir / "build").exists()
    assert (book_dir / "parts").exists()
    assert (book_dir / "parts" / "frontmatter").exists()
    assert (book_dir / "parts" / "backmatter").exists()
    assert (book_dir / "parts" / "parts").exists()
    assert (book_dir / "README.md").exists()
    
    # Check entry file content
    entry_tex = (book_dir / "00_introduction_to_theory.tex").read_text()
    assert r"\documentclass" in entry_tex
    assert "book" in entry_tex
    assert "Introduction to Theory" in entry_tex
    assert r"\frontmatter" in entry_tex
    assert r"\mainmatter" in entry_tex
    
    # Create second book - should get prefix 01
    args = Args(title="Advanced Topics")
    cmd_book(args)
    assert (repo / "01_advanced_topics").exists()


def test_book_enforces_repo_root(temp_workspace, monkeypatch):
    """Test book command enforces running from repo root."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    cmd_init_simple(args)
    
    repo = temp_workspace / "test-repo"
    subdir = repo / "subdir"
    subdir.mkdir()
    monkeypatch.chdir(subdir)
    
    args = Args(title="Some Book")
    with pytest.raises(TexRepoError, match="Must run.*from repository root"):
        cmd_book(args)


def test_paper_creates_article_structure(temp_workspace, monkeypatch):
    """Test tex-repo paper creates article-class paper."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    cmd_init_simple(args)
    
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    # Create first paper
    args = Args(title="Quantum Mechanics")
    result = cmd_paper(args)
    
    assert result == 0
    paper_dir = repo / "00_quantum_mechanics"
    assert paper_dir.exists()
    assert (paper_dir / "paper.tex").exists()
    assert (paper_dir / "README.md").exists()
    assert (paper_dir / "references.bib").exists()
    
    # Check entry file content
    entry_tex = (paper_dir / "paper.tex").read_text()
    assert r"\documentclass" in entry_tex
    assert "article" in entry_tex
    assert "Quantum Mechanics" in entry_tex
    assert r"\begin{abstract}" in entry_tex
    
    # Create second paper - should get prefix 01
    args = Args(title="Statistical Mechanics")
    cmd_paper(args)
    assert (repo / "01_statistical_mechanics").exists()


def test_paper_enforces_repo_root(temp_workspace, monkeypatch):
    """Test paper command enforces running from repo root."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    cmd_init_simple(args)
    
    repo = temp_workspace / "test-repo"
    subdir = repo / "subdir"
    subdir.mkdir()
    monkeypatch.chdir(subdir)
    
    args = Args(title="Some Paper")
    with pytest.raises(TexRepoError, match="Must run.*from repository root"):
        cmd_paper(args)


def test_part_creates_part_in_book(temp_workspace, monkeypatch):
    """Test tex-repo part creates part inside book."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    # Setup: init repo and create book
    args = Args(name="test-repo")
    cmd_init_simple(args)
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    args = Args(title="Introduction")
    cmd_book(args)
    
    # Change into book directory
    book_dir = repo / "00_introduction"
    monkeypatch.chdir(book_dir)
    
    # Create first part
    args = Args(title="Foundations")
    result = cmd_part(args)
    
    assert result == 0
    part_dir = book_dir / "parts" / "parts" / "01_foundations"
    assert part_dir.exists()
    assert (part_dir / "part.tex").exists()
    assert (part_dir / "chapters").exists()
    
    # Check part.tex content
    part_tex = (part_dir / "part.tex").read_text()
    assert r"\part{Foundations}" in part_tex
    
    # Create second part - should get prefix 02
    args = Args(title="Advanced Concepts")
    cmd_part(args)
    assert (book_dir / "parts" / "parts" / "02_advanced_concepts").exists()


def test_part_enforces_book_directory(temp_workspace, monkeypatch):
    """Test part command enforces running inside book directory."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    cmd_init_simple(args)
    
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    args = Args(title="Some Part")
    with pytest.raises(TexRepoError, match="Must run.*inside a book directory"):
        cmd_part(args)


def test_chapter_creates_chapter_in_part(temp_workspace, monkeypatch):
    """Test tex-repo chapter creates chapter inside part."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    # Setup: init repo, create book, create part
    args = Args(name="test-repo")
    cmd_init_simple(args)
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    args = Args(title="Introduction")
    cmd_book(args)
    
    book_dir = repo / "00_introduction"
    monkeypatch.chdir(book_dir)
    
    args = Args(title="Foundations")
    cmd_part(args)
    
    # Change into part directory
    part_dir = book_dir / "parts" / "parts" / "01_foundations"
    monkeypatch.chdir(part_dir)
    
    # Create first chapter
    args = Args(title="Basic Concepts")
    result = cmd_chapter(args)
    
    assert result == 0
    chapter_file = part_dir / "chapters" / "01_basic_concepts.tex"
    assert chapter_file.exists()
    
    # Check chapter content
    chapter_tex = chapter_file.read_text()
    assert r"\chapter{Basic Concepts}" in chapter_tex
    
    # Create second chapter - should get prefix 02
    args = Args(title="Advanced Topics")
    cmd_chapter(args)
    assert (part_dir / "chapters" / "02_advanced_topics.tex").exists()


def test_chapter_enforces_part_directory(temp_workspace, monkeypatch):
    """Test chapter command enforces running inside part directory."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    args = Args(name="test-repo")
    cmd_init_simple(args)
    
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    args = Args(title="Some Chapter")
    with pytest.raises(TexRepoError, match="Must run.*inside a part directory"):
        cmd_chapter(args)


def test_numbering_sequence(temp_workspace, monkeypatch):
    """Test that numbering increments correctly for all commands."""
    def mock_prompt(repo_name):
        return {"author": "Test Author", "org": "Test Org"}
    
    monkeypatch.setattr("texrepo.init_simple_cmd.prompt_for_metadata", mock_prompt)
    
    # Init repo
    args = Args(name="test-repo")
    cmd_init_simple(args)
    repo = temp_workspace / "test-repo"
    monkeypatch.chdir(repo)
    
    # Create multiple books and papers
    cmd_book(Args(title="Book One"))
    cmd_paper(Args(title="Paper One"))
    cmd_book(Args(title="Book Two"))
    cmd_paper(Args(title="Paper Two"))
    
    # Check numbering
    assert (repo / "00_book_one").exists()
    assert (repo / "01_paper_one").exists()
    assert (repo / "02_book_two").exists()
    assert (repo / "03_paper_two").exists()
    
    # Create parts in first book
    book1 = repo / "00_book_one"
    monkeypatch.chdir(book1)
    cmd_part(Args(title="Part A"))
    cmd_part(Args(title="Part B"))
    cmd_part(Args(title="Part C"))
    
    parts_root = book1 / "parts" / "parts"
    assert (parts_root / "01_part_a").exists()
    assert (parts_root / "02_part_b").exists()
    assert (parts_root / "03_part_c").exists()
    
    # Create chapters in first part
    part1 = parts_root / "01_part_a"
    monkeypatch.chdir(part1)
    cmd_chapter(Args(title="Chapter One"))
    cmd_chapter(Args(title="Chapter Two"))
    cmd_chapter(Args(title="Chapter Three"))
    
    chapters_dir = part1 / "chapters"
    assert (chapters_dir / "01_chapter_one.tex").exists()
    assert (chapters_dir / "02_chapter_two.tex").exists()
    assert (chapters_dir / "03_chapter_three.tex").exists()
