from __future__ import annotations

import shutil
from types import SimpleNamespace
from pathlib import Path

import texrepo.init_cmd as init_cmd
from texrepo.fix_cmd import cmd_fix
from texrepo.layouts import get_layout, required_dirs
from texrepo.status_cmd import check_repo_status
from texrepo.section_cmd import cmd_ns
from texrepo.paper_cmd import cmd_np
from texrepo.common import write_text, TexRepoError


SAMPLE_METADATA = {
    "project_name": "Layout Test Repo",
    "author_name": "Tester",
    "organization": "Test Org",
    "author_email": "tester@example.com",
    "default_author_affil": "Test Org",
    "short_affiliation": "TO",
    "author_orcid": "0000-0000-0000-0000",
    "license": "MIT",
    "date_policy": "today",
    "default_bibliography_style": "plainnat",
}


def _init_repo(tmp_path: Path, monkeypatch, layout: str = "new") -> Path:
    """Initialize a test repository with the specified layout."""
    monkeypatch.setattr(init_cmd, "prompt_for_metadata", lambda repo_name: SAMPLE_METADATA.copy())
    repo_path = tmp_path / f"{layout}-layout-repo"
    args = SimpleNamespace(target=repo_path, legacy_seed_text=None, layout=layout)
    rc = init_cmd.cmd_init(args)
    assert rc == 0, "Initialization should succeed"
    return repo_path


def _create_minimal_repo(tmp_path: Path, layout: str = "new") -> Path:
    """Create a minimal repository structure without using init."""
    repo_path = tmp_path / "minimal-repo"
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Write .paperrepo
    write_text(repo_path / ".paperrepo", f"paperrepo=1\nversion=3\nlayout={layout}\n")
    
    # Create required top-level directories
    for dirname in required_dirs(layout):
        (repo_path / dirname).mkdir(parents=True, exist_ok=True)
    
    # Create extras
    for extra in ["shared", "scripts", "98_context", "99_legacy", "releases"]:
        (repo_path / extra).mkdir(parents=True, exist_ok=True)
    
    return repo_path


# Test 1: status accepts new layout with book-structured introduction
def test_status_accepts_new_layout_with_book_intro(tmp_path, monkeypatch):
    """Verify status accepts a properly structured new layout repo with book-scale introduction."""
    repo_path = _create_minimal_repo(tmp_path, "new")
    
    # Create required READMEs
    write_text(repo_path / "00_introduction" / "README.md", "# Introduction\n")
    write_text(repo_path / "01_process_regime" / "README.md", "# Process Regime\n")
    write_text(repo_path / "02_function_application" / "README.md", "# Function Application\n")
    write_text(repo_path / "03_hypnosis" / "README.md", "# Hypnosis\n")
    
    # Create introduction book structure with entry file and sections/
    intro_path = repo_path / "00_introduction"
    write_text(intro_path / "00_introduction.tex", "\\documentclass{article}\n\\begin{document}\nIntro\n\\end{document}\n")
    (intro_path / "sections").mkdir(parents=True, exist_ok=True)
    
    # Create a section in introduction under sections/
    section_dir = intro_path / "sections" / "01_foundations"
    section_dir.mkdir(parents=True, exist_ok=True)
    for i in range(1, 11):
        write_text(section_dir / f"1-{i}.tex", f"% Section 1, subsection {i}\n")
    
    # Create branch directories for process_regime and function_application
    for branch in ["process", "regime"]:
        branch_dir = repo_path / "01_process_regime" / branch
        branch_dir.mkdir(parents=True, exist_ok=True)
        write_text(branch_dir / "README.md", f"# {branch.capitalize()}\n")
        (branch_dir / "papers").mkdir(parents=True, exist_ok=True)
    
    for branch in ["function", "application"]:
        branch_dir = repo_path / "02_function_application" / branch
        branch_dir.mkdir(parents=True, exist_ok=True)
        write_text(branch_dir / "README.md", f"# {branch.capitalize()}\n")
        (branch_dir / "papers").mkdir(parents=True, exist_ok=True)
    
    # Create a valid paper in paper-scale location (03_hypnosis)
    (repo_path / "03_hypnosis" / "papers").mkdir(parents=True, exist_ok=True)
    paper_dir = repo_path / "03_hypnosis" / "papers" / "00_test"
    paper_dir.mkdir(parents=True, exist_ok=True)
    write_text(paper_dir / "README.md", "# Test Paper\n")
    write_text(paper_dir / "00_test.tex", "\\documentclass{article}\n\\begin{document}\nTest\n\\end{document}\n")
    write_text(paper_dir / "refs.bib", "% Bibliography\n")
    (paper_dir / "sections").mkdir(parents=True, exist_ok=True)
    
    # Run status
    result = check_repo_status(repo_path)
    assert result.is_compliant, f"Status should succeed. Messages: {result.messages}"


# Test 2: status rejects papers/ under introduction
def test_status_rejects_intro_papers_dir(tmp_path):
    """Verify status rejects introduction with papers/ directory."""
    repo_path = _create_minimal_repo(tmp_path, "new")
    
    # Create required READMEs
    write_text(repo_path / "00_introduction" / "README.md", "# Introduction\n")
    
    # Create papers/ under introduction (INVALID)
    papers_dir = repo_path / "00_introduction" / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)
    
    # Run status
    result = check_repo_status(repo_path)
    assert not result.is_compliant, "Status should fail when papers/ exists under introduction"
    
    # Check error message mentions papers not allowed
    messages_str = " ".join(result.messages)
    assert "papers" in messages_str.lower() or "introduction" in messages_str.lower()


# Test 3: fix creates missing READMEs and directories without overwriting
def test_fix_creates_missing_readmes_and_dirs_without_overwrite(tmp_path, monkeypatch):
    """Verify fix creates missing structure without overwriting existing files."""
    repo_path = _create_minimal_repo(tmp_path, "new")
    
    # Create one README with custom content
    custom_content = "# Custom Introduction Content\n\nDo not overwrite me!\n"
    write_text(repo_path / "00_introduction" / "README.md", custom_content)
    
    # Remove other READMEs (fix should create them)
    (repo_path / "01_process_regime" / "README.md").unlink(missing_ok=True)
    (repo_path / "03_hypnosis" / "README.md").unlink(missing_ok=True)
    
    # Remove process/regime branch directories
    shutil.rmtree(repo_path / "01_process_regime", ignore_errors=True)
    (repo_path / "01_process_regime").mkdir(parents=True, exist_ok=True)
    
    # Run fix with absolute path (avoid monkeypatch.chdir which fails if cwd was deleted)
    import sys
    sys.path.insert(0, str(repo_path.parent.parent.parent))  # Add texrepo to path
    from texrepo.common import find_repo_root
    original_find = find_repo_root
    
    def mock_find_repo_root():
        return repo_path
    
    monkeypatch.setattr('texrepo.common.find_repo_root', mock_find_repo_root)
    monkeypatch.setattr('texrepo.fix_cmd.find_repo_root', mock_find_repo_root)
    
    rc = cmd_fix(SimpleNamespace(dry_run=False))
    assert rc == 0, "Fix should succeed"
    
    # Verify custom content was NOT overwritten
    intro_readme = (repo_path / "00_introduction" / "README.md").read_text()
    assert intro_readme == custom_content, "Fix should not overwrite existing READMEs"
    
    # Verify missing READMEs were created
    assert (repo_path / "01_process_regime" / "README.md").exists(), "Fix should create missing README"
    assert (repo_path / "03_hypnosis" / "README.md").exists(), "Fix should create missing README"
    
    # Verify branch structure was created
    assert (repo_path / "01_process_regime" / "process" / "README.md").exists()
    assert (repo_path / "01_process_regime" / "regime" / "README.md").exists()
    assert (repo_path / "01_process_regime" / "process" / "papers").is_dir()


# Test 4: ns creates section with 10 subsections
def test_ns_creates_section_with_10_subsections(tmp_path, monkeypatch):
    """Verify ns command creates numbered section with 10 subsection files."""
    repo_path = _init_repo(tmp_path, monkeypatch, "new")
    
    # Mock find_repo_root to return our test repo
    def mock_find_repo_root():
        return repo_path
    
    monkeypatch.setattr('texrepo.section_cmd.find_repo_root', mock_find_repo_root)
    
    args = SimpleNamespace(section_name="foundations")
    rc = cmd_ns(args)
    assert rc == 0, "ns command should succeed"
    
    # Verify section directory was created with correct numbering under sections/
    section_dir = repo_path / "00_introduction" / "sections" / "01_foundations"
    assert section_dir.is_dir(), "Section directory should be created under sections/"
    
    # Verify all 10 subsection files exist
    for i in range(1, 11):
        subsection_file = section_dir / f"1-{i}.tex"
        assert subsection_file.exists(), f"Subsection file 1-{i}.tex should exist"
    
    # Verify status passes after creating section
    result = check_repo_status(repo_path)
    # Note: status may have warnings about missing papers, but should not have errors about intro structure
    messages_str = " ".join(result.messages)
    assert "papers" not in messages_str or "not allowed" not in messages_str


# Test 5: np creates paper skeleton in paper-scale only, refuses introduction
def test_np_creates_paper_skeleton_in_paper_scale_only(tmp_path, monkeypatch, capsys):
    """Verify np creates papers in paper-scale locations but refuses introduction."""
    repo_path = _init_repo(tmp_path, monkeypatch, "new")
    
    # Mock find_repo_root to return our test repo
    def mock_find_repo_root():
        return repo_path
    
    monkeypatch.setattr('texrepo.paper_cmd.find_repo_root', mock_find_repo_root)
    
    # Test 1: np should work for paper-scale location (03_hypnosis)
    args = SimpleNamespace(path_or_domain="03_hypnosis/00_framework", maybe_slug=None, title="Framework Paper")
    rc = cmd_np(args)
    assert rc == 0, "np should succeed for paper-scale location"
    
    # Verify paper skeleton was created
    paper_dir = repo_path / "03_hypnosis" / "papers" / "00_framework"
    assert paper_dir.is_dir(), "Paper directory should be created"
    assert (paper_dir / "README.md").exists(), "Paper README should exist"
    assert (paper_dir / "00_framework.tex").exists(), "Paper entry file should exist with correct name"
    assert (paper_dir / "refs.bib").exists(), "Paper refs.bib should exist"
    assert (paper_dir / "sections").is_dir(), "Paper sections/ should exist"
    
    # Test 2: np should REFUSE introduction path
    args2 = SimpleNamespace(path_or_domain="00_introduction/00_context", maybe_slug=None, title="Context Paper")
    try:
        rc2 = cmd_np(args2)
        # If it returns an error code, that's expected
        assert rc2 != 0, "np should fail for introduction path"
    except (TexRepoError, SystemExit):
        # If it raises an error or exits, that's also expected
        pass
    
    # Verify no paper skeleton was created under introduction
    assert not (repo_path / "00_introduction" / "papers").exists(), "papers/ should not be created under introduction"
    assert not (repo_path / "00_introduction" / "00_context").exists(), "Paper dir should not be created under introduction"


# Additional tests to maintain compatibility
def test_status_new_layout_ok(tmp_path, monkeypatch):
    """Verify basic new layout initialization passes status."""
    repo_path = _init_repo(tmp_path, monkeypatch, "new")

    result = check_repo_status(repo_path)
    assert result.is_compliant
    assert get_layout(repo_path) == "new"
    for name in required_dirs("new"):
        assert (repo_path / name).is_dir()


def test_fix_respects_new_layout(tmp_path, monkeypatch):
    """Verify fix recreates new layout directories correctly."""
    repo_path = _init_repo(tmp_path, monkeypatch, "new")

    intro_dir = repo_path / "00_introduction"
    if intro_dir.exists():
        shutil.rmtree(intro_dir)

    # Mock find_repo_root to return our test repo
    def mock_find_repo_root():
        return repo_path
    
    monkeypatch.setattr('texrepo.fix_cmd.find_repo_root', mock_find_repo_root)
    
    rc = cmd_fix(SimpleNamespace(dry_run=False))
    assert rc == 0

    assert (repo_path / "00_introduction").is_dir(), "Fix should recreate new-layout roots"
    assert not (repo_path / "00_world").exists(), "Fix must not introduce old-layout directories"


def test_init_scaffolds_new_layout(tmp_path, monkeypatch):
    """Verify init scaffolds new layout correctly and excludes old layout directories."""
    repo_path = _init_repo(tmp_path, monkeypatch, "new")
    top_level = {p.name for p in repo_path.iterdir()}

    for expected in required_dirs("new"):
        assert expected in top_level
    assert "00_world" not in top_level
    assert "01_formalism" not in top_level
