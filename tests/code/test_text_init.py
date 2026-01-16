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
    result = run_texrepo(["init", str(sample_text)], cwd=tmp_path)
    if result.returncode != 0:
        raise AssertionError(
            f"tex-repo init failed: stdout={result.stdout} stderr={result.stderr}"
        )
    return tmp_path / sample_text.stem


class TextInitTests(unittest.TestCase):
    def test_init_from_text_populates_section_and_structure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = init_repo_from_text(tmp_path)

            self.assertTrue((repo_path / "SPEC" / "spec" / "main.tex").exists())

            # Ensure the imported text is present in section_1 with LaTeX-safe escaping
            section_path = (
                repo_path / "SPEC" / "spec" / "sections" / "section_1.tex"
            )
            actual_section = section_path.read_text()
            expected_section = (SAMPLE_DIR / "expected_section_1.tex").read_text()
            self.assertEqual(actual_section, expected_section)

            expected_paths = (
                SAMPLE_DIR / "expected_init_tree.txt"
            ).read_text().splitlines()
            for rel_path in expected_paths:
                if not rel_path.strip():
                    continue
                self.assertTrue(
                    (repo_path / rel_path).exists(),
                    f"Missing expected path: {rel_path}",
                )

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
