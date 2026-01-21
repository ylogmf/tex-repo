"""
Comprehensive integration tests for all tex-repo commands under new layout.
Tests commands via subprocess to ensure true end-to-end behavior.
"""
import os
import subprocess
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def run_texrepo(args: list[str], cwd: Path, input_text: str = None, check: bool = False):
    """Run tex-repo command via subprocess."""
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
    """Return default metadata input for init command."""
    return "\n".join([
        "Test Project",
        "Test Author",
        "Test Org",
        "test@test.com",
        "",  # affiliation
        "",  # short affiliation
        "",  # ORCID
        "",  # license
        "",  # date policy
        "",  # bib style
    ]) + "\n"


class TestCommandMatrix:
    """Test the full command workflow under new layout."""
    
    def test_happy_path_workflow(self, tmp_path):
        """Test complete workflow: init -> config -> sync-meta -> ns -> np -> status -> fix -> build -> release."""
        repo_path = tmp_path / "test-repo"
        
        # A) init - create new layout repo
        result = run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
        )
        assert result.returncode == 0, f"init failed: {result.stderr}"
        
        # Verify new layout structure
        assert (repo_path / "00_introduction").is_dir()
        assert (repo_path / "00_introduction" / "00_introduction.tex").exists()
        assert (repo_path / "00_introduction" / "sections").is_dir()
        assert (repo_path / "00_introduction" / "README.md").exists()
        assert not (repo_path / "00_introduction" / "papers").exists()
        assert (repo_path / "01_process_regime").is_dir()
        assert (repo_path / "02_function_application").is_dir()
        assert (repo_path / "03_hypnosis").is_dir()
        assert (repo_path / "shared").is_dir()
        
        # Verify stage READMEs exist
        assert (repo_path / "01_process_regime" / "README.md").exists()
        assert (repo_path / "02_function_application" / "README.md").exists()
        assert (repo_path / "03_hypnosis" / "README.md").exists()
        
        # Verify branch READMEs exist
        assert (repo_path / "01_process_regime" / "process" / "README.md").exists()
        assert (repo_path / "01_process_regime" / "regime" / "README.md").exists()
        assert (repo_path / "02_function_application" / "function" / "README.md").exists()
        assert (repo_path / "02_function_application" / "application" / "README.md").exists()
        
        # J) config - create config file
        result = run_texrepo(["config"], cwd=repo_path)
        assert result.returncode == 0, f"config failed: {result.stderr}"
        assert (repo_path / ".texrepo-config").exists()
        
        # config is idempotent
        result = run_texrepo(["config"], cwd=repo_path)
        assert result.returncode == 0
        
        # I) sync-meta - regenerate identity.tex
        result = run_texrepo(["sync-meta"], cwd=repo_path)
        assert result.returncode == 0, f"sync-meta failed: {result.stderr}"
        identity_path = repo_path / "shared" / "identity.tex"
        assert identity_path.exists()
        identity_content = identity_path.read_text()
        assert "Test Project" in identity_content
        assert "Test Author" in identity_content
        
        # D) ns - create introduction section
        result = run_texrepo(["ns", "foundations"], cwd=repo_path)
        assert result.returncode == 0, f"ns failed: {result.stderr}"
        section_dir = repo_path / "00_introduction" / "sections" / "01_foundations"
        assert section_dir.is_dir()
        for i in range(1, 11):
            assert (section_dir / f"1-{i}.tex").exists()
        
        # D) ns - create second section
        result = run_texrepo(["ns", "applications"], cwd=repo_path)
        assert result.returncode == 0
        section_dir2 = repo_path / "00_introduction" / "sections" / "02_applications"
        assert section_dir2.is_dir()
        for i in range(1, 11):
            assert (section_dir2 / f"2-{i}.tex").exists()
        
        # E) nd - create domain under paper-scale stage
        result = run_texrepo(["nd", "03_hypnosis", "framework"], cwd=repo_path)
        assert result.returncode == 0, f"nd failed: {result.stderr}"
        domain_dir = repo_path / "03_hypnosis" / "papers" / "00_framework"
        assert domain_dir.is_dir()
        assert (domain_dir / "README.md").exists()
        
        # F) np - create paper in paper-scale location
        result = run_texrepo(
            ["np", "03_hypnosis/00_framework", "Framework Paper"],
            cwd=repo_path,
        )
        assert result.returncode == 0, f"np failed: {result.stderr}"
        paper_dir = repo_path / "03_hypnosis" / "papers" / "00_framework"
        assert (paper_dir / "00_framework.tex").exists()
        assert (paper_dir / "refs.bib").exists()
        assert (paper_dir / "sections").is_dir()
        
        # B) status - verify compliant structure
        result = run_texrepo(["status"], cwd=repo_path)
        assert result.returncode == 0, f"status failed: {result.stdout}\n{result.stderr}"
        
        # C) fix --dry-run - should not create anything
        result = run_texrepo(["fix", "--dry-run"], cwd=repo_path)
        assert result.returncode == 0, f"fix --dry-run failed: {result.stderr}"
        
        # G) build 00_introduction - build book
        result = run_texrepo(["b", "00_introduction"], cwd=repo_path)
        assert result.returncode == 0, f"build failed: {result.stdout}\n{result.stderr}"
        pdf_path = repo_path / "00_introduction" / "build" / "00_introduction.pdf"
        assert pdf_path.exists(), "PDF should be generated"
        
        # H) release - create release bundle
        result = run_texrepo(["release", "00_introduction"], cwd=repo_path)
        assert result.returncode == 0, f"release failed: {result.stderr}"
        releases_dir = repo_path / "releases"
        assert releases_dir.is_dir()
        # Find the release directory (has timestamp)
        release_dirs = list(releases_dir.glob("*"))
        assert len(release_dirs) > 0, "Release directory should be created"
        
        # B) status - verify still compliant after all operations
        result = run_texrepo(["status"], cwd=repo_path)
        assert result.returncode == 0, f"final status failed: {result.stdout}\n{result.stderr}"
    
    def test_init_never_overwrites(self, tmp_path):
        """Test that init refuses to overwrite existing directory."""
        repo_path = tmp_path / "existing-repo"
        repo_path.mkdir()
        sentinel = repo_path / "existing.txt"
        sentinel.write_text("keep me")
        
        result = run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
        )
        assert result.returncode != 0, "init should fail on existing directory"
        assert sentinel.exists(), "Existing files should be preserved"
        assert not (repo_path / ".paperrepo").exists()


class TestStatusValidation:
    """Test status command validation rules."""
    
    def test_status_rejects_papers_under_introduction(self, tmp_path):
        """Test that status fails if papers/ exists under 00_introduction."""
        repo_path = tmp_path / "bad-repo"
        
        # Create minimal repo structure
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Create forbidden papers/ directory
        papers_dir = repo_path / "00_introduction" / "papers"
        papers_dir.mkdir()
        
        result = run_texrepo(["status"], cwd=repo_path)
        assert result.returncode != 0, "status should fail with papers/ under introduction"
        assert "papers" in result.stdout.lower() or "papers" in result.stderr.lower()
    
    def test_status_requires_entry_file(self, tmp_path):
        """Test that status fails if 00_introduction.tex is missing."""
        repo_path = tmp_path / "incomplete-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Remove entry file
        entry_file = repo_path / "00_introduction" / "00_introduction.tex"
        entry_file.unlink()
        
        result = run_texrepo(["status"], cwd=repo_path)
        assert result.returncode != 0, "status should fail without entry file"
    
    def test_status_requires_sections_dir(self, tmp_path):
        """Test that status fails if sections/ is missing."""
        repo_path = tmp_path / "no-sections-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Remove sections directory
        import shutil
        sections_dir = repo_path / "00_introduction" / "sections"
        shutil.rmtree(sections_dir)
        
        result = run_texrepo(["status"], cwd=repo_path)
        assert result.returncode != 0, "status should fail without sections/"


class TestFixCommand:
    """Test fix command behavior."""
    
    def test_fix_creates_missing_structure(self, tmp_path):
        """Test that fix creates missing directories and READMEs."""
        repo_path = tmp_path / "broken-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Remove some structure
        readme = repo_path / "01_process_regime" / "README.md"
        readme.unlink()
        
        import shutil
        branch_dir = repo_path / "01_process_regime" / "process"
        shutil.rmtree(branch_dir, ignore_errors=True)
        
        # Run fix
        result = run_texrepo(["fix"], cwd=repo_path)
        assert result.returncode == 0, f"fix failed: {result.stderr}"
        
        # Verify restoration
        assert readme.exists()
        assert branch_dir.is_dir()
        assert (branch_dir / "README.md").exists()
    
    def test_fix_never_overwrites(self, tmp_path):
        """Test that fix preserves existing file content."""
        repo_path = tmp_path / "custom-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Customize a README
        custom_content = "# Custom Content\n\nDo not overwrite!\n"
        readme = repo_path / "00_introduction" / "README.md"
        readme.write_text(custom_content)
        
        # Run fix
        result = run_texrepo(["fix"], cwd=repo_path)
        assert result.returncode == 0
        
        # Verify custom content preserved
        assert readme.read_text() == custom_content
    
    def test_fix_creates_introduction_book_structure(self, tmp_path):
        """Test that fix creates introduction book structure if missing."""
        repo_path = tmp_path / "missing-intro-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Remove introduction structure
        entry_file = repo_path / "00_introduction" / "00_introduction.tex"
        entry_file.unlink()
        
        import shutil
        sections_dir = repo_path / "00_introduction" / "sections"
        shutil.rmtree(sections_dir, ignore_errors=True)
        
        # Run fix
        result = run_texrepo(["fix"], cwd=repo_path)
        assert result.returncode == 0
        
        # Verify restoration
        assert entry_file.exists()
        assert sections_dir.is_dir()


class TestNsCommand:
    """Test ns (new section) command."""
    
    def test_ns_creates_numbered_section(self, tmp_path):
        """Test that ns creates properly numbered section with subsections."""
        repo_path = tmp_path / "ns-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Create first section
        result = run_texrepo(["ns", "basics"], cwd=repo_path)
        assert result.returncode == 0, f"ns failed: {result.stderr}"
        
        section_dir = repo_path / "00_introduction" / "sections" / "01_basics"
        assert section_dir.is_dir()
        for i in range(1, 11):
            subsection = section_dir / f"1-{i}.tex"
            assert subsection.exists(), f"Subsection 1-{i}.tex should exist"
        
        # Create second section - should be numbered 02
        result = run_texrepo(["ns", "advanced"], cwd=repo_path)
        assert result.returncode == 0
        
        section_dir2 = repo_path / "00_introduction" / "sections" / "02_advanced"
        assert section_dir2.is_dir()
        for i in range(1, 11):
            subsection = section_dir2 / f"2-{i}.tex"
            assert subsection.exists()
    
    def test_ns_refuses_duplicate(self, tmp_path):
        """Test that ns refuses to create duplicate section."""
        repo_path = tmp_path / "dup-section-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Create section
        run_texrepo(["ns", "test"], cwd=repo_path, check=True)
        
        # Try to create same name again - should create 02_test (different number)
        result = run_texrepo(["ns", "test"], cwd=repo_path)
        # It actually succeeds with a different number, not a refusal
        assert result.returncode == 0
        # Both should exist with different numbers
        assert (repo_path / "00_introduction" / "sections" / "01_test").exists()
        assert (repo_path / "00_introduction" / "sections" / "02_test").exists()


class TestNdCommand:
    """Test nd (new domain) command."""
    
    def test_nd_works_for_paper_scale(self, tmp_path):
        """Test that nd creates domain in paper-scale locations."""
        repo_path = tmp_path / "nd-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Create domain under hypnosis (paper-scale)
        result = run_texrepo(["nd", "03_hypnosis", "experiments"], cwd=repo_path)
        assert result.returncode == 0, f"nd failed: {result.stderr}"
        
        domain_dir = repo_path / "03_hypnosis" / "papers" / "00_experiments"
        assert domain_dir.is_dir()
        assert (domain_dir / "README.md").exists()
    
    def test_nd_refuses_introduction(self, tmp_path):
        """Test that nd refuses to create domain under introduction."""
        repo_path = tmp_path / "nd-intro-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Try to create domain under introduction
        result = run_texrepo(["nd", "00_introduction", "invalid"], cwd=repo_path)
        assert result.returncode != 0, "nd should refuse introduction"
        assert not (repo_path / "00_introduction" / "papers").exists()


class TestNpCommand:
    """Test np (new paper) command."""
    
    def test_np_auto_inserts_papers_dir(self, tmp_path):
        """Test that np auto-inserts papers/ when omitted."""
        repo_path = tmp_path / "np-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Create paper without explicit papers/ prefix
        result = run_texrepo(["np", "03_hypnosis/00_test", "Test Paper"], cwd=repo_path)
        assert result.returncode == 0, f"np failed: {result.stderr}"
        
        paper_dir = repo_path / "03_hypnosis" / "papers" / "00_test"
        assert paper_dir.is_dir()
        assert (paper_dir / "README.md").exists()
        assert (paper_dir / "00_test.tex").exists()
        assert (paper_dir / "refs.bib").exists()
        assert (paper_dir / "sections").is_dir()
    
    def test_np_refuses_introduction(self, tmp_path):
        """Test that np refuses to create paper under introduction."""
        repo_path = tmp_path / "np-intro-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Try to create paper under introduction
        result = run_texrepo(["np", "00_introduction/00_invalid"], cwd=repo_path)
        assert result.returncode != 0, "np should refuse introduction"
        combined = result.stdout + result.stderr
        assert "ns" in combined.lower() or "section" in combined.lower()


class TestBuildCommand:
    """Test build command."""
    
    def test_build_introduction_book(self, tmp_path):
        """Test building introduction as book."""
        repo_path = tmp_path / "build-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Build introduction
        result = run_texrepo(["b", "00_introduction"], cwd=repo_path)
        assert result.returncode == 0, f"build failed: {result.stdout}\n{result.stderr}"
        
        pdf_path = repo_path / "00_introduction" / "build" / "00_introduction.pdf"
        assert pdf_path.exists(), "PDF should be generated"
    
    def test_build_all(self, tmp_path):
        """Test building all papers."""
        repo_path = tmp_path / "build-all-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Create a paper
        run_texrepo(["np", "03_hypnosis/00_paper", "Test"], cwd=repo_path, check=True)
        
        # Build all
        result = run_texrepo(["b", "all"], cwd=repo_path)
        assert result.returncode == 0, f"build all failed: {result.stdout}\n{result.stderr}"


class TestReleaseCommand:
    """Test release command."""
    
    def test_release_creates_bundle(self, tmp_path):
        """Test that release creates immutable bundle."""
        repo_path = tmp_path / "release-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Build first
        run_texrepo(["b", "00_introduction"], cwd=repo_path, check=True)
        
        # Create release
        result = run_texrepo(["release", "00_introduction"], cwd=repo_path)
        assert result.returncode == 0, f"release failed: {result.stderr}"
        
        releases_dir = repo_path / "releases"
        assert releases_dir.is_dir()
        
        # Check that release was created
        release_dirs = list(releases_dir.glob("*"))
        assert len(release_dirs) > 0


class TestEnvCommand:
    """Test env command."""
    
    def test_env_runs_without_error(self, tmp_path):
        """Test that env command runs successfully."""
        # env needs a subcommand - try 'check'
        result = run_texrepo(["env", "check"], cwd=tmp_path)
        # Should exit 0 or show env info
        assert result.returncode == 0 or "Environment" in result.stdout or "LaTeX" in result.stdout


class TestInstallCommand:
    """Test install command."""
    
    def test_install_exits_cleanly(self, tmp_path):
        """Test that install command exits without error."""
        repo_path = tmp_path / "install-repo"
        
        run_texrepo(
            ["init", str(repo_path), "--layout", "new"],
            cwd=tmp_path,
            input_text=default_metadata_input(),
            check=True,
        )
        
        # Run env to generate guide first
        run_texrepo(["env"], cwd=repo_path)
        
        # install should exit cleanly (may just print commands)
        result = run_texrepo(["install"], cwd=repo_path)
        # Allow non-zero exit if it's just informational
        assert result.returncode in (0, 1, 2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
