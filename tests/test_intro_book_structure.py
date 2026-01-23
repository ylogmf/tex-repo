import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_texrepo(args: list[str], cwd: Path, input_text: str = None, check: bool = False):
    cmd = ["python3", "-m", "texrepo"] + args
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    result = subprocess.run(
        cmd,
        cwd=cwd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=30,
        env=env,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}")
    return result


def default_metadata_input():
    return "\n".join(
        [
            "Test Project",
            "Test Author",
            "Test Org",
            "test@test.com",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    ) + "\n"


def test_init_scaffolds_book_structure(tmp_path):
    repo_path = tmp_path / "book-repo"
    result = run_texrepo(
        ["init", str(repo_path), "--layout", "new"],
        cwd=tmp_path,
        input_text=default_metadata_input(),
    )
    assert result.returncode == 0, result.stderr

    intro = repo_path / "00_introduction"
    assert (intro / "00_introduction.tex").exists()
    parts = intro / "parts"
    # New Part/Chapter structure has parts/parts/ instead of parts/sections/
    for d in ["frontmatter", "backmatter", "parts", "appendix"]:
        assert (parts / d).is_dir()
    assert (intro / "build").is_dir()
    for fname in ["title.tex", "preface.tex", "how_to_read.tex", "toc.tex"]:
        assert (parts / "frontmatter" / fname).exists()
    for fname in ["scope_limits.tex", "closing_notes.tex"]:
        assert (parts / "backmatter" / fname).exists()


def test_ns_creates_chapter_structure(tmp_path):
    repo_path = tmp_path / "ns-repo"
    run_texrepo(
        ["init", str(repo_path), "--layout", "new"],
        cwd=tmp_path,
        input_text=default_metadata_input(),
        check=True,
    )

    run_texrepo(["ns", "orientation"], cwd=repo_path, check=True)
    # New structure: parts/parts/<part>/chapters/<chapter>/
    chapter_dir = repo_path / "00_introduction" / "parts" / "parts" / "01_part-1" / "chapters" / "01_orientation"
    assert chapter_dir.is_dir()
    assert (chapter_dir / "chapter.tex").exists()
    # Section files (10 per chapter)
    for i in range(1, 11):
        assert (chapter_dir / f"1-{i}.tex").exists()

    chapter_content = (chapter_dir / "chapter.tex").read_text()
    # Chapter.tex now contains \chapter command, not \input statements
    assert "\\chapter" in chapter_content


def test_build_generates_chapter_index(tmp_path):
    repo_path = tmp_path / "build-repo"
    run_texrepo(
        ["init", str(repo_path), "--layout", "new"],
        cwd=tmp_path,
        input_text=default_metadata_input(),
        check=True,
    )
    run_texrepo(["ns", "orientation"], cwd=repo_path, check=True)

    result = run_texrepo(["b", "00_introduction"], cwd=repo_path)
    assert result.returncode == 0, result.stderr

    intro_build = repo_path / "00_introduction" / "build"
    sections_index = intro_build / "sections_index.tex"
    assert sections_index.exists()

    content = sections_index.read_text()
    # sections_index now uses parts/parts/<part>/chapters/ structure
    assert "parts/parts/01_part-1/chapters/01_orientation" in content


def test_status_accepts_book_structure(tmp_path):
    repo_path = tmp_path / "status-repo"
    run_texrepo(
        ["init", str(repo_path), "--layout", "new"],
        cwd=tmp_path,
        input_text=default_metadata_input(),
        check=True,
    )
    run_texrepo(["ns", "orientation"], cwd=repo_path, check=True)

    result = run_texrepo(["status"], cwd=repo_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_fix_adds_missing_frontmatter(tmp_path):
    repo_path = tmp_path / "fix-repo"
    repo_path.mkdir()
    intro = repo_path / "00_introduction"
    intro.mkdir()
    (repo_path / ".paperrepo").write_text("paperrepo=1\nlayout=new\n", encoding="utf-8")
    # Missing entry and front/back
    run_texrepo(
        ["fix"],
        cwd=repo_path,
        check=True,
    )

    parts = intro / "parts"
    assert (parts / "frontmatter" / "title.tex").exists()
    assert (parts / "backmatter" / "scope_limits.tex").exists()
    assert (intro / "00_introduction.tex").exists()
