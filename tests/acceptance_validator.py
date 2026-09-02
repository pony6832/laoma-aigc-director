"""Validate agent-produced Laoma AIGC Director acceptance bundles."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_project import (
    GATE_STATUS_MATRIX,
    GATE_THREE_LOCK_ROLES,
    GATE_TWO_LOCK_ROLES,
    SUPPORTED_SCHEMA_VERSION,
)


SCHEMA_VERSION = "1.0"
RUNTIME_SNAPSHOT = "director-methods-v1.0.0"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RESPONSE_CLAUSE_SPLIT = re.compile(r"[。！？!?；;，,\r\n]+")
_VIDEO_SUBJECT = re.compile(r"(?:影片|成片)")
_NEGATED_OR_FUTURE_VIDEO_CLAIM = re.compile(
    r"(?:尚未|還沒|仍未|並未|未曾|沒有|尚無|不可|不能|無法|尚待|待生成|待製作|"
    r"將|會|預計|若|如果|完成後|生成後)"
)
_POSITIVE_VIDEO_COMPLETION = re.compile(
    r"(?:已(?:經)?(?:生成(?:完成|完畢)?|產出|製作完成|完成)|"
    r"(?:生成|製作)(?:完成|完畢)|成片完成|可(?:以)?直接交付|可交付)"
)


def _read_json(path: Path, label: str, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}: invalid JSON ({exc})")
        return None


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _timezone_aware(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _validate_execution(scenario_id: str, execution: object, errors: list[str]) -> None:
    if not isinstance(execution, dict):
        errors.append(f"{scenario_id}: execution must be an object")
        return
    if not _nonempty_string(execution.get("executor")):
        errors.append(f"{scenario_id}: execution.executor must be non-empty")
    if execution.get("runtime_snapshot") != RUNTIME_SNAPSHOT:
        errors.append(f"{scenario_id}: runtime snapshot mismatch")
    if not _timezone_aware(execution.get("executed_at")):
        errors.append(f"{scenario_id}: execution timestamp must be timezone-aware ISO 8601")
    if execution.get("isolated") is not True:
        errors.append(f"{scenario_id}: execution must be isolated")


def _validate_artifacts(
    scenario_id: str,
    bundle: Path,
    artifacts: object,
    required_roles: object,
    errors: list[str],
) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    if not isinstance(artifacts, list):
        errors.append(f"{scenario_id}: artifacts must be a list")
        return records
    roles: set[str] = set()
    paths: set[str] = set()
    bundle_root = bundle.resolve()
    for index, artifact in enumerate(artifacts):
        label = f"{scenario_id}: artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{label} must be an object")
            continue
        role = artifact.get("role")
        path_value = artifact.get("path")
        expected_hash = artifact.get("sha256")
        if not _nonempty_string(role):
            errors.append(f"{label}.role must be non-empty")
        elif role in roles:
            errors.append(f"{scenario_id}: duplicate artifact role: {role}")
        else:
            roles.add(role)
        if not _nonempty_string(path_value):
            errors.append(f"{label}.path must be non-empty")
            continue
        if path_value in paths:
            errors.append(f"{scenario_id}: duplicate artifact path: {path_value}")
        paths.add(path_value)
        target = (bundle_root / path_value).resolve()
        try:
            target.relative_to(bundle_root)
        except ValueError:
            errors.append(f"{scenario_id}: unsafe artifact path: {path_value}")
            continue
        if not target.is_file():
            errors.append(f"{scenario_id}: artifact file does not exist: {path_value}")
            continue
        if target.stat().st_size == 0:
            errors.append(f"{scenario_id}: artifact file is empty: {path_value}")
        if not isinstance(expected_hash, str) or _SHA256.fullmatch(expected_hash) is None:
            errors.append(f"{label}.sha256 must be lowercase SHA-256")
        elif _sha256(target) != expected_hash:
            errors.append(f"{scenario_id}: artifact sha256 mismatch: {path_value}")
        if isinstance(role, str) and role not in records:
            records[role] = {
                "path": path_value,
                "sha256": expected_hash,
                "target": target,
            }

    if not isinstance(required_roles, list):
        errors.append(f"{scenario_id}: contract required_artifact_roles must be a list")
        return records
    for role in required_roles:
        if role not in roles:
            errors.append(f"{scenario_id}: missing required artifact role: {role}")
    return records


def _validate_project_state(
    scenario_id: str,
    bundle: Path,
    decision: dict,
    records: dict[str, dict[str, object]],
    errors: list[str],
) -> None:
    record = records.get("project_state")
    if record is None:
        return
    target = record.get("target")
    if not isinstance(target, Path):
        return
    state = _read_json(target, f"{scenario_id}: project state", errors)
    if not isinstance(state, dict):
        if state is not None:
            errors.append(f"{scenario_id}: project state must contain an object")
        return

    if state.get("schema_version") != SUPPORTED_SCHEMA_VERSION:
        errors.append(f"{scenario_id}: project state schema_version mismatch")
    if not _nonempty_string(state.get("project_name")):
        errors.append(f"{scenario_id}: project state project_name must be non-empty")
    version = state.get("project_version")
    if not isinstance(version, str) or re.fullmatch(r"V\d{2,}", version) is None:
        errors.append(f"{scenario_id}: project state project_version is invalid")

    gate = state.get("current_gate")
    status = state.get("status")
    if gate != decision.get("current_gate"):
        errors.append(f"{scenario_id}: project state current_gate does not match decision")
    if status != decision.get("status"):
        errors.append(f"{scenario_id}: project state status does not match decision")
    if (
        not isinstance(gate, int)
        or isinstance(gate, bool)
        or gate not in GATE_STATUS_MATRIX
    ):
        errors.append(f"{scenario_id}: project state current_gate is invalid")
        gate = None
    elif not isinstance(status, str) or status not in GATE_STATUS_MATRIX[gate]:
        errors.append(f"{scenario_id}: project state gate/status transition is invalid")

    if not _timezone_aware(state.get("created_at")):
        errors.append(f"{scenario_id}: project state created_at is invalid")

    open_decisions = state.get("open_decisions")
    if not isinstance(open_decisions, list):
        errors.append(f"{scenario_id}: project state open_decisions must be a list")
    else:
        for index, item in enumerate(open_decisions):
            if not isinstance(item, dict) or any(
                not _nonempty_string(item.get(field))
                for field in ("id", "question", "status", "opened_at")
            ):
                errors.append(
                    f"{scenario_id}: project state open_decisions[{index}] is invalid"
                )
                continue
            if item["status"] not in {"open", "resolved"} or not _timezone_aware(
                item["opened_at"]
            ):
                errors.append(
                    f"{scenario_id}: project state open_decisions[{index}] is invalid"
                )

    decision_claims = decision.get("claims")
    real_video_claim = (
        decision_claims.get("real_video_generated")
        if isinstance(decision_claims, dict)
        else None
    )
    asset_status = state.get("asset_status")
    if not isinstance(asset_status, dict) or any(
        field not in asset_status
        for field in ("claimed_complete_without_output", "outputs", "qc", "approval")
    ):
        errors.append(f"{scenario_id}: project state asset_status is invalid")
    if isinstance(asset_status, dict) and real_video_claim is False:
        if asset_status.get("outputs") != []:
            errors.append(
                f"{scenario_id}: project state outputs contradict real_video_generated=false"
            )
        if asset_status.get("claimed_complete_without_output") is not False:
            errors.append(f"{scenario_id}: project state false-completion flag is invalid")

    locked = state.get("locked_artifacts")
    lock_roles: set[str] = set()
    if not isinstance(locked, list):
        errors.append(f"{scenario_id}: project state locked_artifacts must be a list")
    else:
        bundle_root = bundle.resolve()
        for index, item in enumerate(locked):
            label = f"{scenario_id}: project state locked_artifacts[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be an object")
                continue
            if any(
                not _nonempty_string(item.get(field))
                for field in ("role", "path", "version", "sha256", "reason")
            ):
                errors.append(f"{label} requires role, path, version, sha256 and reason")
                continue
            role = item["role"]
            path_value = item["path"]
            expected_hash = item["sha256"]
            lock_roles.add(role)
            if Path(path_value).is_absolute():
                errors.append(f"{label} path is unsafe")
                continue
            lock_target = (bundle_root / path_value).resolve()
            try:
                lock_target.relative_to(bundle_root)
            except ValueError:
                errors.append(f"{label} path is unsafe")
                continue
            if not lock_target.is_file():
                errors.append(f"{label} file does not exist")
                continue
            if _SHA256.fullmatch(expected_hash) is None or _sha256(lock_target) != expected_hash:
                errors.append(f"{label} sha256 mismatch")
            record_for_role = records.get(role)
            if (
                record_for_role is None
                or record_for_role.get("path") != path_value
                or record_for_role.get("sha256") != expected_hash
            ):
                errors.append(f"{label} is not mirrored by the decision artifact manifest")

    required_lock_roles: tuple[str, ...] = ()
    if isinstance(gate, int) and gate >= 2:
        required_lock_roles = ("project_brief",)
    if isinstance(gate, int) and gate >= 3:
        required_lock_roles = GATE_TWO_LOCK_ROLES
    if isinstance(gate, int) and gate >= 4:
        required_lock_roles = GATE_TWO_LOCK_ROLES + GATE_THREE_LOCK_ROLES
    for role in required_lock_roles:
        if role not in lock_roles:
            errors.append(
                f"{scenario_id}: project state Gate {gate} requires locked artifact role: {role}"
            )


def _validate_response_claims(
    scenario_id: str,
    bundle: Path,
    decision: dict,
    records: dict[str, dict[str, object]],
    errors: list[str],
) -> None:
    try:
        response = (bundle / "response.md").read_text(encoding="utf-8").casefold()
    except OSError:
        return
    claims = decision.get("claims")
    if not isinstance(claims, dict):
        return
    markers = {
        "finished_film_generated": "finished_film_generated=true",
        "real_video_generated": "real_video_generated=true",
        "model_independent_determinism": "model_independent_determinism=true",
    }
    for claim, marker in markers.items():
        if claims.get(claim) is False and marker in response:
            errors.append(f"{scenario_id}: response contradicts claim {claim}=false")
    video_completion_is_false = any(
        claims.get(claim) is False
        for claim in ("finished_film_generated", "real_video_generated")
    )
    if video_completion_is_false:
        for clause in _RESPONSE_CLAUSE_SPLIT.split(response):
            if (
                _VIDEO_SUBJECT.search(clause)
                and not _NEGATED_OR_FUTURE_VIDEO_CLAIM.search(clause)
                and _POSITIVE_VIDEO_COMPLETION.search(clause)
            ):
                errors.append(
                    f"{scenario_id}: response contradicts false video completion "
                    "claims in natural language"
                )
                break
    if claims.get("real_video_generated") is False:
        forbidden_output_roles = {
            "finished_film",
            "generated_video",
            "video_output",
        }
        for role in forbidden_output_roles.intersection(records):
            errors.append(
                f"{scenario_id}: artifact role {role} contradicts real_video_generated=false"
            )


def _validate_required_mapping(
    scenario_id: str,
    label: str,
    required: object,
    actual: object,
    errors: list[str],
) -> None:
    if not isinstance(required, dict):
        errors.append(f"{scenario_id}: contract {label} must be an object")
        return
    if not isinstance(actual, dict):
        errors.append(f"{scenario_id}: {label} must be an object")
        return
    singular = "claim" if label == "claims" else "fact"
    for key, expected in required.items():
        if actual.get(key) != expected:
            errors.append(f"{scenario_id}: required {singular} mismatch: {key}")


def _validate_evidence(
    scenario_id: str,
    required_kinds: object,
    evidence: object,
    errors: list[str],
) -> None:
    if not isinstance(evidence, list):
        errors.append(f"{scenario_id}: completion_evidence must be a list")
        evidence_kinds: set[str] = set()
    else:
        evidence_kinds = set()
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(
                    f"{scenario_id}: completion_evidence[{index}] must be an object"
                )
                continue
            kind = item.get("kind")
            detail = item.get("detail")
            if not _nonempty_string(kind) or not _nonempty_string(detail):
                errors.append(
                    f"{scenario_id}: completion_evidence[{index}] requires kind and detail"
                )
                continue
            evidence_kinds.add(kind)
    if not isinstance(required_kinds, list):
        errors.append(f"{scenario_id}: contract required_evidence_kinds must be a list")
        return
    for kind in required_kinds:
        if kind not in evidence_kinds:
            errors.append(f"{scenario_id}: missing completion evidence kind: {kind}")


def _validate_scenario(
    contract: dict,
    results_root: Path,
    errors: list[str],
) -> None:
    scenario_id = contract.get("id")
    if not _nonempty_string(scenario_id):
        errors.append("contract scenario id must be non-empty")
        return
    bundle = results_root / scenario_id
    if not bundle.is_dir():
        errors.append(f"{scenario_id}: result bundle is missing")
        return
    for filename in ("request.md", "response.md"):
        path = bundle / filename
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"{scenario_id}: {filename} must be a non-empty file")

    decision = _read_json(bundle / "decision.json", f"{scenario_id}: decision.json", errors)
    if not isinstance(decision, dict):
        if decision is not None:
            errors.append(f"{scenario_id}: decision.json must contain an object")
        return
    if decision.get("scenario_id") != scenario_id:
        errors.append(f"{scenario_id}: scenario_id mismatch")
    if decision.get("mode") != contract.get("mode"):
        errors.append(f"{scenario_id}: mode mismatch")

    allowed_gates = contract.get("allowed_gates")
    if not isinstance(allowed_gates, list) or decision.get("current_gate") not in allowed_gates:
        errors.append(
            f"{scenario_id}: current_gate is not allowed: {decision.get('current_gate')}"
        )
    allowed_statuses = contract.get("allowed_statuses")
    if not isinstance(allowed_statuses, list) or decision.get("status") not in allowed_statuses:
        errors.append(f"{scenario_id}: status is not allowed: {decision.get('status')}")

    _validate_execution(scenario_id, decision.get("execution"), errors)

    actions = decision.get("actions")
    if not isinstance(actions, list) or not all(_nonempty_string(item) for item in actions):
        errors.append(f"{scenario_id}: actions must be a list of non-empty strings")
        action_set: set[str] = set()
    else:
        action_set = set(actions)
    forbidden_actions = contract.get("forbidden_actions")
    if not isinstance(forbidden_actions, list):
        errors.append(f"{scenario_id}: contract forbidden_actions must be a list")
    else:
        for action in forbidden_actions:
            if action in action_set:
                errors.append(f"{scenario_id}: forbidden action recorded: {action}")

    forbidden_behavior = decision.get("forbidden_behavior")
    if not isinstance(forbidden_behavior, dict):
        errors.append(f"{scenario_id}: forbidden_behavior must be an object")
    else:
        forbidden_flags = contract.get("forbidden_flags")
        if not isinstance(forbidden_flags, list):
            errors.append(f"{scenario_id}: contract forbidden_flags must be a list")
        else:
            for flag in forbidden_flags:
                if forbidden_behavior.get(flag) is not False:
                    errors.append(
                        f"{scenario_id}: forbidden behavior flag must be false: {flag}"
                    )

    _validate_required_mapping(
        scenario_id,
        "facts",
        contract.get("required_facts"),
        decision.get("facts"),
        errors,
    )
    _validate_required_mapping(
        scenario_id,
        "claims",
        contract.get("required_claims"),
        decision.get("claims"),
        errors,
    )
    _validate_evidence(
        scenario_id,
        contract.get("required_evidence_kinds"),
        decision.get("completion_evidence"),
        errors,
    )

    limitations = decision.get("limitations")
    if not isinstance(limitations, list) or not limitations or not all(
        _nonempty_string(item) for item in limitations
    ):
        errors.append(f"{scenario_id}: limitations must be non-empty")

    records = _validate_artifacts(
        scenario_id,
        bundle,
        decision.get("artifacts"),
        contract.get("required_artifact_roles"),
        errors,
    )
    _validate_project_state(scenario_id, bundle, decision, records, errors)
    _validate_response_claims(scenario_id, bundle, decision, records, errors)


def validate_acceptance(contracts_path: Path, results_root: Path) -> list[str]:
    """Return deterministic structural errors for all acceptance bundles."""
    contracts_path = Path(contracts_path)
    results_root = Path(results_root)
    errors: list[str] = []
    contracts = _read_json(contracts_path, "acceptance contracts", errors)
    if not isinstance(contracts, dict):
        if contracts is not None:
            errors.append("acceptance contracts must contain an object")
        return errors
    if contracts.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"unsupported acceptance schema_version: {contracts.get('schema_version')!r}"
        )
    scenarios = contracts.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("acceptance contracts scenarios must be a non-empty list")
        return errors
    seen: set[str] = set()
    for index, contract in enumerate(scenarios):
        if not isinstance(contract, dict):
            errors.append(f"contract scenarios[{index}] must be an object")
            continue
        scenario_id = contract.get("id")
        if isinstance(scenario_id, str) and scenario_id in seen:
            errors.append(f"duplicate contract scenario id: {scenario_id}")
            continue
        if isinstance(scenario_id, str):
            seen.add(scenario_id)
        _validate_scenario(contract, results_root, errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    args = parser.parse_args(argv)
    errors = validate_acceptance(args.contracts, args.results)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    contracts = json.loads(args.contracts.read_text(encoding="utf-8"))
    print(f"ACCEPTANCE_VALID: {len(contracts['scenarios'])} scenarios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
