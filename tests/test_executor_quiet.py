from __future__ import annotations

import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "scripts" / "executor_quiet.sh"


def run_wrapper(
    *args: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(WRAPPER), *args],
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def extract_log_paths(stderr: str) -> list[Path]:
    match = re.search(r"stdout: (\S+) stderr: (\S+)", stderr)
    return [Path(match.group(1)), Path(match.group(2))] if match else []


class ExecutorQuietTest(unittest.TestCase):
    def test_rejects_missing_command(self) -> None:
        result = subprocess.run(
            [str(WRAPPER)],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_preserves_success_exit_code_and_stays_silent(self) -> None:
        result = run_wrapper("sh", "-c", "printf ok")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_success_deletes_logs(self) -> None:
        with tempfile.TemporaryDirectory() as log_dir:
            env = {**os.environ, "TMPDIR": log_dir}
            result = run_wrapper("sh", "-c", "printf ok", env=env)

            self.assertEqual(result.returncode, 0)
            leftovers = list(Path(log_dir).glob("*.log"))
            self.assertEqual(leftovers, [], f"unexpected logs left behind: {leftovers}")

    def test_preserves_failure_exit_code_and_reports_logs(self) -> None:
        with tempfile.TemporaryDirectory() as log_dir:
            env = {**os.environ, "TMPDIR": log_dir}
            result = run_wrapper("sh", "-c", "printf boom >&2; exit 7", env=env)

            self.assertEqual(result.returncode, 7)
            self.assertEqual(result.stdout, "")
            self.assertIn(f"sh failed (exit 7). stdout: {log_dir}/", result.stderr)
            self.assertIn(f" stderr: {log_dir}/", result.stderr)

    def test_failure_logs_have_restricted_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as log_dir:
            env = {**os.environ, "TMPDIR": log_dir}
            result = run_wrapper("sh", "-c", "printf boom >&2; exit 7", env=env)

            self.assertEqual(result.returncode, 7)
            stdout_logs = list(Path(log_dir).glob("*.out.log"))
            stderr_logs = list(Path(log_dir).glob("*.err.log"))
            self.assertEqual(len(stdout_logs), 1)
            self.assertEqual(len(stderr_logs), 1)
            for log_path in stdout_logs + stderr_logs:
                mode = stat.S_IMODE(log_path.stat().st_mode)
                self.assertEqual(mode, 0o600, f"{log_path} has mode {oct(mode)}")

    def test_falls_back_when_tmpdir_unwritable(self) -> None:
        if os.geteuid() == 0:
            self.skipTest("root bypasses directory write-permission checks")
        with tempfile.TemporaryDirectory() as bad_dir:
            os.chmod(bad_dir, 0o500)
            env = {**os.environ, "TMPDIR": bad_dir}
            try:
                result = run_wrapper("sh", "-c", "printf boom >&2; exit 7", env=env)
            finally:
                os.chmod(bad_dir, 0o700)

            self.assertEqual(result.returncode, 7)
            self.assertNotIn(str(bad_dir), result.stderr)
            for log_path in extract_log_paths(result.stderr):
                self.assertTrue(log_path.exists(), f"{log_path} should exist in fallback dir")
                self.assertNotEqual(log_path.parent, Path(bad_dir))
                log_path.unlink(missing_ok=True)

    def test_falls_back_when_tmpdir_missing(self) -> None:
        env = {**os.environ, "TMPDIR": "/this/does/not/exist"}
        result = run_wrapper("sh", "-c", "printf boom >&2; exit 7", env=env)

        self.assertEqual(result.returncode, 7)
        self.assertNotIn("/this/does/not/exist", result.stderr)
        self.assertIn("/tmp/", result.stderr)
        for log_path in extract_log_paths(result.stderr):
            log_path.unlink(missing_ok=True)

    def test_wrapper_runs_from_foreign_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as foreign_dir:
            result = run_wrapper("sh", "-c", "printf ok", cwd=Path(foreign_dir))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
