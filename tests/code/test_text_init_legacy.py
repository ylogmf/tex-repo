import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tex-repo"
SAMPLE_DIR = REPO_ROOT / "tests" / "sample"
DEFAULT_INPUT = "\n" * 10  # Accept defaults for metadata prompts


def run_texrepo(args, cwd, input_text=DEFAULT_INPUT):
    result = subprocess.run(
        [str(CLI_PATH)] + args,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=cwd,
    )
    return result


def init_repo_from_text(tmp_path: Path) -> Path:
    sample_text = SAMPLE_DIR / "init_notes.txt"
    repo_name = sample_text.stem
    result = run_texrepo(
        ["init", repo_name, "--legacy-seed-text", str(sample_text), "--layout", "old"],
        cwd=tmp_path
    )
    if result.returncode != 0:
        raise AssertionError(
            f"tex-repo init failed: stdout={result.stdout} stderr={result.stderr}"
        )
    return tmp_path / repo_name


class TextInitTests(unittest.TestCase):
    def test_init_from_text_populates_section_and_structure(self):
        # Legacy old-layout SPEC text-seed; not part of new layout contract
        self.skipTest("Legacy old-layout SPEC text-seed; not part of new layout contract")

    def test_status_succeeds_after_text_init(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = init_repo_from_text(tmp_path)

            result = run_texrepo(["status"], cwd=repo_path)
            self.assertEqual(
                result.returncode,
                0,
                f"Status failed: stdout={result.stdout} stderr={result.stderr}",
            )

    def test_init_refuses_existing_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            target = tmp_path / "init_notes"
            target.mkdir()

            result = run_texrepo(["init", target.name], cwd=tmp_path)

            self.assertNotEqual(
                result.returncode, 0, "Init should refuse existing directories"
            )
            self.assertFalse(
                (target / ".paperrepo").exists(),
                "Existing directory should remain untouched",
            )


if __name__ == "__main__":
    unittest.main()
