from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "SKILL.md"
RUNNER_POLICY = REPO_ROOT / "references" / "executor_runner.md"
CONTRACT_POLICY = REPO_ROOT / "references" / "executor_contract_update_policy.md"


class ExecutorRunnerPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = SKILL.read_text(encoding="utf-8")
        cls.runner = RUNNER_POLICY.read_text(encoding="utf-8")
        cls.contract = CONTRACT_POLICY.read_text(encoding="utf-8")

    def test_runner_policy_file_exists(self) -> None:
        self.assertTrue(RUNNER_POLICY.is_file(), f"missing {RUNNER_POLICY}")

    def test_skill_requires_direct_child_runner_and_wait(self) -> None:
        self.assertIn("executor-runner", self.skill)
        self.assertIn("direct-child", self.skill)
        self.assertRegex(
            self.skill,
            re.compile(r"MUST NOT invoke a task executor `command` directly", re.I),
        )
        self.assertIn("Wait** for the executor-runner", self.skill)
        self.assertIn("references/executor_runner.md", self.skill)

    def test_skill_step5_does_not_invoke_executor_in_lead_session(self) -> None:
        step5 = self._section(self.skill, "### Step 5 — Delegate and verify", "### Step 6")
        self.assertIn("do not run that command in the Lead session", step5)
        self.assertIn("Spawn a direct-child **executor-runner** Subagent", step5)
        self.assertNotRegex(
            step5,
            re.compile(
                r"(?m)^\d+\.\s+Invoke the configured `command`",
            ),
        )

    def test_runner_policy_forbids_approvals_routing_target_files_and_review(self) -> None:
        forbidden = self._section(
            self.runner,
            "## What the runner must not do",
            "## Runner return package",
        )
        for needle in (
            "new external-delegation approvals",
            "Re-run CodexBar",
            "Edit any task `target_files`",
            "Decide that verification has passed",
            "Launch the Reviewer",
        ):
            self.assertIn(needle, forbidden)

    def test_runner_return_package_fields(self) -> None:
        for field in (
            "exit_code:",
            "changed_files:",
            "executor_self_reported_verification:",
            "unresolved_issues:",
        ):
            self.assertIn(field, self.runner)
            self.assertIn(field, self.skill)

    def test_lead_keeps_verification_approval_and_review(self) -> None:
        lead_section = self._section(
            self.runner,
            "## What the Lead must do",
            "## What the runner may do",
        )
        self.assertIn("independently run each task's `verification`", lead_section)
        self.assertIn("Keep Reviewer launch", lead_section)
        self.assertIn("external", lead_section.lower())
        self.assertIn(
            "run independent verification and `validate` after the runner returns",
            self.contract,
        )
        self.assertIn(
            "keep Reviewer launch in the Lead session",
            self.contract,
        )

    def test_contract_policy_includes_runner_column(self) -> None:
        self.assertIn("Executor-runner responsibility", self.contract)
        self.assertIn("Fields the executor-runner may edit", self.contract)
        self.assertIn("None.", self.contract)
        self.assertIn("executor_runner.md", self.contract)

    def test_runner_is_not_an_executors_yaml_id(self) -> None:
        self.assertIn("not an `executors.yaml` executor ID", self.runner)
        self.assertIn("not an `executors.yaml` ID", self.contract)

    def test_happy_path_architecture_documented(self) -> None:
        self.assertIn("Lead (parent session)", self.runner)
        self.assertIn("executor-runner Subagent", self.runner)
        self.assertIn("task executor command", self.runner)
        self.assertIn(
            "spawn a direct-child executor-runner Subagent and wait for its completion",
            self.contract,
        )

    @staticmethod
    def _section(text: str, start: str, end: str) -> str:
        start_idx = text.index(start)
        end_idx = text.index(end, start_idx + len(start))
        return text[start_idx:end_idx]


if __name__ == "__main__":
    unittest.main()
