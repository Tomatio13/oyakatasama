from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TODO_CLI = REPO_ROOT / "scripts" / "todo_cli.py"
EXECUTORS = REPO_ROOT / "executors.yaml"
VALIDATE_EXECUTORS = REPO_ROOT / "scripts" / "validate_executors.py"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import validate_executors  # noqa: E402  (path added above)


CONTRACT_TEXT = textwrap.dedent(
    """\
    project:
      id: "L-001"
      goal: "Example goal"
      constraints:
        - "Local only"
      success_criteria:
        - "Tests pass"
    backlog:
      - id: "T001"
        title: "First task"
        status: "pending"
        executor: "quota_selected"
        executor_history:
          - executor: "quota_selected"
            reason: "Default implementation route"
            changed_by: "lead"
        delegation:
          approval: "not_requested"
          approved_executor: null
          approved_target_files: []
        target_files:
          - "README.md"
        verification: "python -m unittest"
    learnings: []
    """
)

COMPLETED_CONTRACT_TEXT = textwrap.dedent(
    """\
    project:
      id: "L-002"
      goal: "Completed goal"
      constraints:
        - "Local only"
      success_criteria:
        - "Tests pass"
    backlog:
      - id: "T001"
        title: "Completed task"
        status: "completed"
        executor: "quota_selected"
        executor_history:
          - executor: "quota_selected"
            reason: "Default implementation route"
            changed_by: "lead"
        delegation:
          approval: "not_requested"
          approved_executor: null
          approved_target_files: []
        target_files:
          - "README.md"
        verification: "python -m unittest"
    learnings: []
    """
)


class TodoCliTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TODO_CLI), *args],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def make_contract(self) -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        contract_path = Path(temp_dir.name) / "L-001_example_goal.yaml"
        contract_path.write_text(CONTRACT_TEXT)
        return contract_path

    def test_summary_outputs_counts(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("summary", str(contract))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["project"]["id"], "L-001")
        self.assertEqual(payload["counts"]["pending"], 1)
        self.assertEqual(payload["tasks"][0]["id"], "T001")

    def test_create_generates_new_contract(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo_dir = Path(temp_dir.name)
        template_dir = repo_dir / "references"
        goal_dir = repo_dir / ".oyakatasama"
        template_dir.mkdir(parents=True)
        template_path = template_dir / ".todo.yaml"
        template_path.write_text(CONTRACT_TEXT)

        result = self.run_cli(
            "create",
            "Implement authentication flow",
            "--template",
            str(template_path),
            "--repo",
            str(repo_dir),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["project_id"], "L-001")
        created_path = Path(payload["path"])
        self.assertTrue(created_path.exists())
        created_text = created_path.read_text()
        self.assertIn('id: L-001', created_text)
        self.assertIn('goal: Implement authentication flow', created_text)
        self.assertEqual(created_path.parent, goal_dir)

    def test_set_status_updates_contract(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("set-status", str(contract), "T001", "in_progress")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["old_status"], "pending")
        self.assertEqual(payload["new_status"], "in_progress")
        updated = contract.read_text()
        self.assertIn('status: in_progress', updated)

    def test_set_status_rejects_unknown_status(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("set-status", str(contract), "T001", "done")

        self.assertEqual(result.returncode, 1)
        self.assertIn("status must be one of", result.stderr)

    def test_guard_rejects_template_edit(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        template_dir = Path(temp_dir.name) / "references"
        template_dir.mkdir(parents=True)
        template_path = template_dir / ".todo.yaml"
        template_path.write_text(CONTRACT_TEXT)

        result = self.run_cli("set-status", str(template_path), "T001", "in_progress")

        self.assertEqual(result.returncode, 1)
        self.assertIn("refusing to edit references/.todo.yaml", result.stderr)

    def test_list_active_reports_recommended_contract(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        goal_dir = Path(temp_dir.name) / ".oyakatasama"
        goal_dir.mkdir(parents=True)
        active_contract = goal_dir / "L-001_active_goal.yaml"
        completed_contract = goal_dir / "L-002_completed_goal.yaml"
        invalid_contract = goal_dir / "L-001_invalid_goal.yaml"
        active_contract.write_text(CONTRACT_TEXT)
        completed_contract.write_text(COMPLETED_CONTRACT_TEXT)
        invalid_contract.write_text(
            CONTRACT_TEXT.replace('executor: "quota_selected"', 'executor: "codex"')
        )

        result = self.run_cli("list-active", "--goal-dir", str(goal_dir), "--executors", str(EXECUTORS))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["completed_contracts_count"], 1)
        self.assertEqual(len(payload["active_contracts"]), 1)
        self.assertEqual(len(payload["invalid_contracts"]), 1)
        self.assertEqual(payload["recommended_contract"]["project"]["id"], "L-001")
        self.assertEqual(payload["active_contracts"][0]["status"], "active")
        self.assertEqual(payload["recommended_reason"], "has pending tasks and no in_progress tasks")
        self.assertEqual(payload["active_contracts"][0]["open_tasks"][0]["id"], "T001")
        self.assertEqual(payload["invalid_contracts"][0]["validation"]["rule"], "non_delegable_executor")
        self.assertEqual(payload["invalid_contracts"][0]["validation"]["category"], "legacy_schema")
        self.assertFalse(payload["invalid_contracts"][0]["validation"]["auto_migration_candidate"])

    def test_list_active_resolves_goal_dir_from_repo(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        repo_dir = Path(temp_dir.name)
        goal_dir = repo_dir / ".oyakatasama"
        goal_dir.mkdir(parents=True)
        active_contract = goal_dir / "L-001_active_goal.yaml"
        active_contract.write_text(CONTRACT_TEXT)

        result = self.run_cli("list-active", "--repo", str(repo_dir), "--executors", str(EXECUTORS))

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(len(payload["active_contracts"]), 1)
        self.assertEqual(payload["recommended_contract"]["project"]["id"], "L-001")

    def test_list_active_text_format(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        goal_dir = Path(temp_dir.name) / ".oyakatasama"
        goal_dir.mkdir(parents=True)
        active_contract = goal_dir / "L-001_active_goal.yaml"
        active_contract.write_text(CONTRACT_TEXT)

        result = self.run_cli("list-active", "--goal-dir", str(goal_dir), "--executors", str(EXECUTORS), "--format", "text")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("recommended_contract:", result.stdout)
        self.assertIn("active L-001", result.stdout)
        self.assertIn("pending T001", result.stdout)

    def test_list_active_text_format_includes_invalid_details(self) -> None:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        goal_dir = Path(temp_dir.name) / ".oyakatasama"
        goal_dir.mkdir(parents=True)
        invalid_contract = goal_dir / "L-001_invalid_goal.yaml"
        invalid_contract.write_text(
            CONTRACT_TEXT.replace('executor: "quota_selected"', 'executor: "codex"')
        )

        result = self.run_cli("list-active", "--goal-dir", str(goal_dir), "--executors", str(EXECUTORS), "--format", "text")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("category=legacy_schema", result.stdout)
        self.assertIn("rule=non_delegable_executor", result.stdout)

    def test_validate_passes_for_valid_contract(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("validate", str(EXECUTORS), str(contract))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Executor configuration is valid.", result.stdout)

    def test_validate_uses_default_executors_path(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("validate", str(contract))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Executor configuration is valid.", result.stdout)

    def test_validate_resolves_wrapper_independent_of_cwd(self) -> None:
        contract = self.make_contract()

        result = subprocess.run(
            [sys.executable, str(TODO_CLI), "validate", str(EXECUTORS), str(contract)],
            cwd=tempfile.gettempdir(),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Executor configuration is valid.", result.stdout)

    # --- {skill_dir} runtime expansion (R2-01) ---

    MINIMAL_EXECUTORS_TEMPLATE = textwrap.dedent(
        """\
        lead:
          executor: local

        reviewer:
          executor: local

        executors:
          local:
            command: current_codex_session
            model: m
            delegable: false
            data_boundary: current_session
            requires_unsandboxed_runtime: false
          wrapper:
            command: __COMMAND__
            model: m
            delegable: true
            data_boundary: external_service
            requires_unsandboxed_runtime: true
            quota_provider: p
            quota_windows: [primary]
            args:
              - "{prompt}"

        research:
          web_executor: wrapper
          x_executor: wrapper

        selection:
          quota_selected:
            candidates:
              - wrapper
            tie_breaker: wrapper
            fallback_executor: wrapper
        """
    )

    def make_skill_dir_executors(self, command_value: str) -> tuple[Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        skill_dir = Path(temp_dir.name)
        executors_path = skill_dir / "executors.yaml"
        executors_path.write_text(
            self.MINIMAL_EXECUTORS_TEMPLATE.replace("__COMMAND__", command_value)
        )
        return skill_dir, executors_path

    def run_validator(self, executors_path: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATE_EXECUTORS), str(executors_path)],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            check=False,
        )

    def test_expand_skill_dir_returns_absolute_cwd_independent_path(self) -> None:
        expanded = validate_executors.expand_skill_dir(
            "{skill_dir}/scripts/executor_quiet.sh", REPO_ROOT
        )

        self.assertEqual(expanded, f"{REPO_ROOT}/scripts/executor_quiet.sh")
        self.assertNotIn("{skill_dir}", expanded)
        self.assertTrue(Path(expanded).is_absolute(), expanded)
        self.assertIn("{skill_dir}", validate_executors.ARG_PLACEHOLDERS)
        self.assertIn("{skill_dir}", validate_executors.COMMAND_PLACEHOLDERS)

    def test_real_executors_use_skill_dir_for_wrapper_commands(self) -> None:
        import yaml

        data = yaml.safe_load(EXECUTORS.read_text())
        for executor_id in ("grok", "opencode", "agy"):
            command = data["executors"][executor_id]["command"]
            self.assertEqual(command, "{skill_dir}/scripts/executor_quiet.sh", executor_id)
            expanded = validate_executors.expand_skill_dir(command, REPO_ROOT)
            self.assertTrue(Path(expanded).is_absolute(), expanded)
            self.assertTrue(Path(expanded).exists(), expanded)

    def test_skill_dir_command_validates_from_foreign_cwd(self) -> None:
        skill_dir, executors_path = self.make_skill_dir_executors(
            '"{skill_dir}/scripts/executor_quiet.sh"'
        )
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "executor_quiet.sh").write_text("#!/bin/sh\n")

        result = self.run_validator(executors_path, cwd=Path(tempfile.gettempdir()))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Executor configuration is valid.", result.stdout)

    def test_skill_dir_command_fails_deterministically_when_missing(self) -> None:
        skill_dir, executors_path = self.make_skill_dir_executors(
            '"{skill_dir}/scripts/missing.sh"'
        )

        result = self.run_validator(executors_path, cwd=Path(tempfile.gettempdir()))

        expected_resolved = executors_path.resolve().parent / "scripts" / "missing.sh"
        self.assertEqual(result.returncode, 1)
        self.assertIn("command does not exist", result.stderr)
        self.assertIn(str(expected_resolved), result.stderr)

    def test_bare_relative_command_still_resolves_against_config_dir(self) -> None:
        skill_dir, executors_path = self.make_skill_dir_executors(
            '"./scripts/executor_quiet.sh"'
        )
        (skill_dir / "scripts").mkdir()
        (skill_dir / "scripts" / "executor_quiet.sh").write_text("#!/bin/sh\n")

        result = self.run_validator(executors_path, cwd=Path(tempfile.gettempdir()))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Executor configuration is valid.", result.stdout)

    def test_unsupported_command_placeholder_is_rejected(self) -> None:
        _skill_dir, executors_path = self.make_skill_dir_executors(
            '"{model}/scripts/executor_quiet.sh"'
        )

        result = self.run_validator(executors_path, cwd=Path(tempfile.gettempdir()))

        self.assertEqual(result.returncode, 1)
        self.assertIn("command has unsupported placeholder", result.stderr)

    def test_approve_updates_delegation(self) -> None:
        contract = self.make_contract()

        assign_result = self.run_cli("assign", str(contract), "T001", "agy", "External implementation approved")
        self.assertEqual(assign_result.returncode, 0, assign_result.stderr)

        result = self.run_cli("approve", str(contract), "T001", "agy", "README.md")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["approved_executor"], "agy")
        updated = contract.read_text()
        self.assertIn("approval: approved", updated)
        self.assertIn("approved_executor: agy", updated)

    def test_approve_rejects_mismatched_files(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("approve", str(contract), "T001", "quota_selected", "README_OTHER.md")

        self.assertEqual(result.returncode, 1)
        self.assertIn("approved_target_files must exactly match", result.stderr)

    def test_assign_updates_executor_and_history(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("assign", str(contract), "T001", "grok", "Quota selected Grok")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["old_executor"], "quota_selected")
        self.assertEqual(payload["new_executor"], "grok")
        updated = contract.read_text()
        self.assertIn("executor: grok", updated)
        self.assertIn("reason: Quota selected Grok", updated)

    def test_add_learning_appends_entry(self) -> None:
        contract = self.make_contract()

        result = self.run_cli("add-learning", str(contract), "Keep selector fallback explicit")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["learnings_count"], 1)
        updated = contract.read_text()
        self.assertIn("- Keep selector fallback explicit", updated)


if __name__ == "__main__":
    unittest.main()
