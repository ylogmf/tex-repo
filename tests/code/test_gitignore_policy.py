import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "tex-repo"
DEFAULT_INPUT = "\n" * 10  # Accept defaults for metadata prompts


def run_texrepo(args, cwd, input_text=DEFAULT_INPUT):
    return subprocess.run(
        [str(CLI_PATH)] + args,
        input=input_text,
        text=True,
        capture_output=True,
        cwd=cwd,
    )


POLICY_MARKER_START = "# >>> tex-repo policy"
POLICY_MARKER_END = "# <<< tex-repo policy"


def assert_policy_lines(testcase: unittest.TestCase, content: str):
    testcase.assertIn("**/build/", content)
    testcase.assertIn("!releases/", content)
    testcase.assertIn("!releases/**", content)
    testcase.assertIn(POLICY_MARKER_START, content)
    testcase.assertIn(POLICY_MARKER_END, content)


class GitignorePolicyTests(unittest.TestCase):
    def test_init_creates_gitignore_when_absent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            result = run_texrepo(["init", "repo"], cwd=tmp_path)
            self.assertEqual(
                result.returncode,
                0,
                f"Init should succeed. stdout={result.stdout} stderr={result.stderr}",
            )
            gitignore = tmp_path / "repo" / ".gitignore"
            self.assertTrue(gitignore.exists(), ".gitignore should be created by init")
            content = gitignore.read_text()
            assert_policy_lines(self, content)

    def test_init_does_not_overwrite_existing_gitignore(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            repo_path = tmp_path / "myrepo"
            repo_path.mkdir()
            sentinel = "# USER_SENTINEL_DO_NOT_TOUCH\n"
            gitignore = repo_path / ".gitignore"
            gitignore.write_text(sentinel)

            result = run_texrepo(["init", repo_path.name], cwd=tmp_path)
            self.assertNotEqual(
                result.returncode,
                0,
                f"Init should refuse existing directory. stdout={result.stdout} stderr={result.stderr}",
            )
            self.assertEqual(
                gitignore.read_text(),
                sentinel,
                ".gitignore content should remain unchanged",
            )

    def test_fix_creates_gitignore_when_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_texrepo(["init", "repo"], cwd=tmp_path)
            repo_path = tmp_path / "repo"
            gitignore = repo_path / ".gitignore"
            gitignore.unlink()

            result = run_texrepo(["fix"], cwd=repo_path)
            self.assertEqual(
                result.returncode,
                0,
                f"Fix should succeed. stdout={result.stdout} stderr={result.stderr}",
            )
            content = gitignore.read_text()
            assert_policy_lines(self, content)

    def test_fix_patches_existing_gitignore_preserving_user_rules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_texrepo(["init", "repo"], cwd=tmp_path)
            repo_path = tmp_path / "repo"
            gitignore = repo_path / ".gitignore"

            custom_content = "\n".join(
                [
                    "# TOP_SENTINEL",
                    "*.custom",
                    "# BOTTOM_SENTINEL",
                    "",
                ]
            )
            gitignore.write_text(custom_content)

            result = run_texrepo(["fix"], cwd=repo_path)
            self.assertEqual(
                result.returncode,
                0,
                f"Fix should succeed. stdout={result.stdout} stderr={result.stderr}",
            )
            content = gitignore.read_text()
            assert_policy_lines(self, content)
            self.assertEqual(content.count("# TOP_SENTINEL"), 1)
            self.assertEqual(content.count("# BOTTOM_SENTINEL"), 1)
            self.assertEqual(content.count(POLICY_MARKER_START), 1)
            self.assertEqual(content.count(POLICY_MARKER_END), 1)

    def test_fix_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            tmp_path = Path(temp_dir)
            run_texrepo(["init", "repo"], cwd=tmp_path)
            repo_path = tmp_path / "repo"

            first = run_texrepo(["fix"], cwd=repo_path)
            self.assertEqual(
                first.returncode,
                0,
                f"First fix should succeed. stdout={first.stdout} stderr={first.stderr}",
            )
            gitignore = repo_path / ".gitignore"
            content_first = gitignore.read_text()

            second = run_texrepo(["fix"], cwd=repo_path)
            self.assertEqual(
                second.returncode,
                0,
                f"Second fix should succeed. stdout={second.stdout} stderr={second.stderr}",
            )
            content_second = gitignore.read_text()

            self.assertEqual(
                content_first,
                content_second,
                "Fix should be idempotent; .gitignore content must not change",
            )


if __name__ == "__main__":
    unittest.main()
