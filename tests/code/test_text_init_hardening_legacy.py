import tempfile
import unittest
from pathlib import Path

from test_text_init_legacy import run_texrepo, SAMPLE_DIR


class TextInitHardeningTests(unittest.TestCase):
    def test_non_txt_source_is_rejected(self):
        # Legacy text-seed feature removed from new layout
        self.skipTest("Legacy text-seed feature removed from new layout")

    def test_missing_source_fails_without_creating_repo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = tmp_path / "repo"
            result = run_texrepo(["init", repo_path.name, "does_not_exist.txt"], cwd=tmp_path)

            self.assertNotEqual(
                result.returncode,
                0,
                f"Missing source file should fail. stdout={result.stdout} stderr={result.stderr}",
            )
            self.assertFalse(
                repo_path.exists(),
                "Repo directory should not be created when source file is missing",
            )

    def test_directory_as_source_is_rejected(self):
        # Legacy text-seed feature removed from new layout
        self.skipTest("Legacy text-seed feature removed from new layout")

    def test_too_many_arguments_fail(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_texrepo(["init", "a", "b", "c"], cwd=tmp_path, input_text="")

            self.assertNotEqual(
                result.returncode,
                0,
                f"Too many arguments should fail. stdout={result.stdout} stderr={result.stderr}",
            )

    def test_existing_directory_remains_untouched_on_failure(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            target = tmp_path / "init_notes"
            target.mkdir()
            sentinel = target / "keep.txt"
            sentinel.write_text("keep")

            result = run_texrepo(["init", target.name], cwd=tmp_path)

            self.assertNotEqual(
                result.returncode,
                0,
                f"Init should fail when target directory exists. stdout={result.stdout} stderr={result.stderr}",
            )
            self.assertTrue(sentinel.exists(), "Existing files should be preserved")
            self.assertFalse(
                (target / ".paperrepo").exists(),
                "Failure must not create .paperrepo in existing directory",
            )
            self.assertFalse(
                (target / "SPEC").exists(),
                "Failure must not create stage directories in existing directory",
            )

    def test_invalid_source_does_not_create_partial_repo(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            invalid_source = tmp_path / "not_here.txt"
            repo_path = tmp_path / "bad_repo"

            result = run_texrepo(["init", repo_path.name, str(invalid_source)], cwd=tmp_path)

            self.assertNotEqual(
                result.returncode,
                0,
                f"Init should fail with missing source. stdout={result.stdout} stderr={result.stderr}",
            )
            self.assertFalse(
                repo_path.exists(),
                "Failure with invalid source must not leave a repo directory behind",
            )

    def test_escaping_contract_preserves_content(self):
        # Legacy old-layout SPEC text-seed; not part of new layout contract
        self.skipTest("Legacy old-layout SPEC text-seed; not part of new layout contract")

    def test_init_help_available_everywhere(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_texrepo(["init", "--help"], cwd=tmp_path, input_text="")
            combined = result.stdout + result.stderr

            self.assertEqual(
                result.returncode,
                0,
                f"Help should succeed anywhere. stdout={result.stdout} stderr={result.stderr}",
            )
            self.assertIn("target", combined, "Help output should mention target argument")
            self.assertIn(
                "legacy-seed-text", combined, "Help output should mention legacy-seed-text flag"
            )


if __name__ == "__main__":
    unittest.main()
