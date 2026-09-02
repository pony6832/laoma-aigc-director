from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import unittest

from tests.acceptance_validator import validate_acceptance


ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_fixture(root: Path) -> tuple[Path, Path]:
    contracts_path = root / "contracts.json"
    results = root / "results"
    bundle = results / "scenario-01"
    artifacts = bundle / "artifacts"
    artifacts.mkdir(parents=True)
    (bundle / "request.md").write_text("A real request\n", encoding="utf-8")
    (bundle / "response.md").write_text("A gate-aware response\n", encoding="utf-8")
    (artifacts / "brief.md").write_text("A non-empty brief\n", encoding="utf-8")
    state = {
        "schema_version": "1.0",
        "project_name": "fixture",
        "project_version": "V01",
        "current_gate": 1,
        "status": "awaiting_approval",
        "locked_artifacts": [],
        "open_decisions": [],
        "asset_status": {
            "claimed_complete_without_output": False,
            "outputs": [],
            "qc": {
                "status": "not_started",
                "checked_at": None,
                "checked_by": "",
                "checks": [],
            },
            "approval": {
                "status": "pending",
                "approved_at": None,
                "approved_by": "",
                "scope": [],
            },
        },
        "created_at": "2026-09-02T13:00:00+08:00",
    }
    _write_json(artifacts / "project-state.json", state)
    contracts = {
        "schema_version": "1.0",
        "scenarios": [
            {
                "id": "scenario-01",
                "mode": "producer_director",
                "allowed_gates": [1],
                "allowed_statuses": ["awaiting_approval"],
                "required_artifact_roles": [
                    "agent_response",
                    "project_state",
                    "project_brief",
                ],
                "required_facts": {
                    "prior_case_data_used": False,
                    "bulk_generation_started": False,
                },
                "forbidden_actions": ["reuse_prior_case_data", "bulk_generate"],
                "forbidden_flags": ["reused_prior_character", "claimed_finished_film"],
                "required_evidence_kinds": ["artifact_hashes", "gate_state"],
                "required_claims": {
                    "finished_film_generated": False,
                    "real_video_generated": False,
                    "model_independent_determinism": False,
                },
            }
        ],
    }
    _write_json(contracts_path, contracts)
    decision = {
        "scenario_id": "scenario-01",
        "mode": "producer_director",
        "current_gate": 1,
        "status": "awaiting_approval",
        "execution": {
            "executor": "codex-agent-final-fix-wave",
            "runtime_snapshot": "director-methods-v1.0.0",
            "executed_at": "2026-09-02T13:00:00+08:00",
            "isolated": True,
        },
        "actions": ["create_gate1_brief"],
        "facts": {
            "prior_case_data_used": False,
            "bulk_generation_started": False,
        },
        "forbidden_behavior": {
            "reused_prior_character": False,
            "claimed_finished_film": False,
        },
        "claims": {
            "finished_film_generated": False,
            "real_video_generated": False,
            "model_independent_determinism": False,
        },
        "completion_evidence": [
            {"kind": "artifact_hashes", "detail": "manifest entries verified"},
            {"kind": "gate_state", "detail": "Gate 1 awaits approval"},
        ],
        "limitations": ["No image or video generation was performed."],
        "artifacts": [
            {
                "role": "agent_response",
                "path": "response.md",
                "sha256": _sha256(bundle / "response.md"),
            },
            {
                "role": "project_brief",
                "path": "artifacts/brief.md",
                "sha256": _sha256(artifacts / "brief.md"),
            },
            {
                "role": "project_state",
                "path": "artifacts/project-state.json",
                "sha256": _sha256(artifacts / "project-state.json"),
            },
        ],
    }
    _write_json(bundle / "decision.json", decision)
    return contracts_path, results


class AcceptanceValidatorTests(unittest.TestCase):
    def test_accepts_real_nonempty_hashed_bundle(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            self.assertEqual(validate_acceptance(contracts, results), [])

    def test_rejects_missing_required_artifact_role(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            decision_path = results / "scenario-01" / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["artifacts"] = decision["artifacts"][:1]
            _write_json(decision_path, decision)
            self.assertIn(
                "scenario-01: missing required artifact role: project_brief",
                validate_acceptance(contracts, results),
            )

    def test_rejects_hash_mismatch_and_unsafe_path(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            contracts, results = _valid_fixture(root)
            decision_path = results / "scenario-01" / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["artifacts"][0]["sha256"] = "0" * 64
            decision["artifacts"][1]["path"] = "../../outside.md"
            (root / "outside.md").write_text("outside", encoding="utf-8")
            _write_json(decision_path, decision)
            errors = validate_acceptance(contracts, results)
            self.assertIn(
                "scenario-01: artifact sha256 mismatch: response.md", errors
            )
            self.assertIn(
                "scenario-01: unsafe artifact path: ../../outside.md", errors
            )

    def test_rejects_required_fact_forbidden_action_and_true_flag(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            decision_path = results / "scenario-01" / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["facts"]["prior_case_data_used"] = True
            decision["actions"].append("bulk_generate")
            decision["forbidden_behavior"]["claimed_finished_film"] = True
            _write_json(decision_path, decision)
            errors = validate_acceptance(contracts, results)
            self.assertIn(
                "scenario-01: required fact mismatch: prior_case_data_used",
                errors,
            )
            self.assertIn("scenario-01: forbidden action recorded: bulk_generate", errors)
            self.assertIn(
                "scenario-01: forbidden behavior flag must be false: claimed_finished_film",
                errors,
            )

    def test_rejects_mode_gate_status_and_unisolated_execution(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            decision_path = results / "scenario-01" / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["mode"] = "mentor"
            decision["current_gate"] = 4
            decision["status"] = "complete"
            decision["execution"]["isolated"] = False
            _write_json(decision_path, decision)
            errors = validate_acceptance(contracts, results)
            self.assertIn("scenario-01: mode mismatch", errors)
            self.assertIn("scenario-01: current_gate is not allowed: 4", errors)
            self.assertIn("scenario-01: status is not allowed: complete", errors)
            self.assertIn("scenario-01: execution must be isolated", errors)

    def test_rejects_false_completion_claim_missing_evidence_and_limits(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            decision_path = results / "scenario-01" / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["claims"]["finished_film_generated"] = True
            decision["completion_evidence"] = []
            decision["limitations"] = []
            _write_json(decision_path, decision)
            errors = validate_acceptance(contracts, results)
            self.assertIn(
                "scenario-01: required claim mismatch: finished_film_generated",
                errors,
            )
            self.assertIn(
                "scenario-01: missing completion evidence kind: artifact_hashes", errors
            )
            self.assertIn("scenario-01: limitations must be non-empty", errors)

    def test_rejects_project_state_that_disagrees_with_decision(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            bundle = results / "scenario-01"
            state_path = bundle / "artifacts" / "project-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["status"] = "blocked"
            _write_json(state_path, state)
            decision_path = bundle / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            for artifact in decision["artifacts"]:
                if artifact["role"] == "project_state":
                    artifact["sha256"] = _sha256(state_path)
            _write_json(decision_path, decision)
            self.assertIn(
                "scenario-01: project state status does not match decision",
                validate_acceptance(contracts, results),
            )

    def test_rejects_project_state_that_skips_prior_gate_locks(self):
        with TemporaryDirectory() as tmp:
            contracts_path, results = _valid_fixture(Path(tmp))
            contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
            contracts["scenarios"][0]["allowed_gates"] = [3]
            contracts["scenarios"][0]["allowed_statuses"] = ["blocked"]
            _write_json(contracts_path, contracts)
            bundle = results / "scenario-01"
            state_path = bundle / "artifacts" / "project-state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["current_gate"] = 3
            state["status"] = "blocked"
            _write_json(state_path, state)
            decision_path = bundle / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            decision["current_gate"] = 3
            decision["status"] = "blocked"
            for artifact in decision["artifacts"]:
                if artifact["role"] == "project_state":
                    artifact["sha256"] = _sha256(state_path)
            _write_json(decision_path, decision)
            errors = validate_acceptance(contracts_path, results)
            self.assertIn(
                "scenario-01: project state Gate 3 requires locked artifact role: project_brief",
                errors,
            )
            self.assertIn(
                "scenario-01: project state Gate 3 requires locked artifact role: consistency_test",
                errors,
            )

    def test_rejects_response_that_contradicts_false_completion_claim(self):
        with TemporaryDirectory() as tmp:
            contracts, results = _valid_fixture(Path(tmp))
            bundle = results / "scenario-01"
            response_path = bundle / "response.md"
            response_path.write_text(
                "A gate-aware response\nfinished_film_generated=true\n",
                encoding="utf-8",
            )
            decision_path = bundle / "decision.json"
            decision = json.loads(decision_path.read_text(encoding="utf-8"))
            for artifact in decision["artifacts"]:
                if artifact["role"] == "agent_response":
                    artifact["sha256"] = _sha256(response_path)
            _write_json(decision_path, decision)
            self.assertIn(
                "scenario-01: response contradicts claim finished_film_generated=false",
                validate_acceptance(contracts, results),
            )

    def test_rejects_natural_language_false_video_completion_claims(self):
        claims = (
            "影片已經生成完成，可以直接交付。",
            "成片已生成完畢，可直接交付。",
            "最終影片生成完成，現在可交付。",
        )
        for response in claims:
            with self.subTest(response=response), TemporaryDirectory() as tmp:
                contracts, results = _valid_fixture(Path(tmp))
                bundle = results / "scenario-01"
                response_path = bundle / "response.md"
                response_path.write_text(response + "\n", encoding="utf-8")
                decision_path = bundle / "decision.json"
                decision = json.loads(decision_path.read_text(encoding="utf-8"))
                for artifact in decision["artifacts"]:
                    if artifact["role"] == "agent_response":
                        artifact["sha256"] = _sha256(response_path)
                _write_json(decision_path, decision)
                self.assertIn(
                    "scenario-01: response contradicts false video completion claims in natural language",
                    validate_acceptance(contracts, results),
                )

    def test_accepts_explicitly_unfinished_natural_language_response(self):
        honest_responses = (
            "尚未生成成片，不可直接交付。",
            "影片並未生成完成，不能直接交付。",
            "影片會在生成完成後才進入交付。",
        )
        for response in honest_responses:
            with self.subTest(response=response), TemporaryDirectory() as tmp:
                contracts, results = _valid_fixture(Path(tmp))
                bundle = results / "scenario-01"
                response_path = bundle / "response.md"
                response_path.write_text(response + "\n", encoding="utf-8")
                decision_path = bundle / "decision.json"
                decision = json.loads(decision_path.read_text(encoding="utf-8"))
                for artifact in decision["artifacts"]:
                    if artifact["role"] == "agent_response":
                        artifact["sha256"] = _sha256(response_path)
                _write_json(decision_path, decision)
                self.assertNotIn(
                    "scenario-01: response contradicts false video completion claims in natural language",
                    validate_acceptance(contracts, results),
                )

    def test_checked_in_seven_scenario_bundles_pass(self):
        errors = validate_acceptance(
            ROOT / "tests" / "fixtures" / "acceptance-contracts.json",
            ROOT / "tests" / "acceptance",
        )
        self.assertEqual(errors, [])

    def test_checked_in_contract_has_exactly_the_seven_review_scenarios(self):
        contracts = json.loads(
            (ROOT / "tests" / "fixtures" / "acceptance-contracts.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [item["id"] for item in contracts["scenarios"]],
            [f"scenario-{index:02d}" for index in range(1, 8)],
        )


if __name__ == "__main__":
    unittest.main()
