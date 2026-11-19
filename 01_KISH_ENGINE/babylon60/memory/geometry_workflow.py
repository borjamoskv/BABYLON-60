"""FL-019: governed affine-geometry evidence checked by an explicit native verifier.

Stage records declare a candidate workflow; they do not prove physical execution.
Acceptance is a snapshot over active, signed records in the configured host. Call
``get_acceptance`` to recheck it after changes. The native library path and Python
host are trusted configuration, not a boundary against code in the same process.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import importlib.util
from importlib.machinery import ExtensionFileLoader
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import struct
from threading import RLock
from types import MappingProxyType
from typing import Any, Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid5

from blake3 import blake3

from babylon60.memory.governance import (
    MemoryGovernanceEngine,
    MemoryKind,
    MemoryModality,
    MemoryRecordView,
    MemoryStatus,
    TrustLevel,
)


CHECKER_VERSION = "FL-019-AFFINE-I3-v1"
_SCHEMA = "FL-019-GEOMETRY-v1"
_U64_MAX = (1 << 64) - 1
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_KINDS = {"POLICY": MemoryKind.SOURCE_RECORD, "INPUT": MemoryKind.SOURCE_RECORD}


class GeometryWorkflowError(RuntimeError):
    """The workflow, evidence, native verifier, or current lineage is invalid."""


class _NativeVerifier(Protocol):
    def verify(self, request_json: str) -> str: ...


@dataclass(frozen=True)
class GeometryAcceptance:
    """Immutable observation; subsequent authority requires get_acceptance."""

    status: str
    record_id: str
    report: Mapping[str, Any]


@dataclass(frozen=True)
class _Lineage:
    policy: MemoryRecordView
    input: MemoryRecordView
    transform: MemoryRecordView
    execution: MemoryRecordView
    output: MemoryRecordView
    points: tuple[tuple[int, ...], ...]
    matrix: tuple[tuple[int, ...], ...]
    output_points: tuple[tuple[int, ...], ...]

    @property
    def stages(self) -> tuple[MemoryRecordView, ...]:
        return self.input, self.transform, self.execution, self.output


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _uint64(value: Any, name: str) -> int:
    if type(value) is not int or not 0 <= value <= _U64_MAX:
        raise GeometryWorkflowError(f"{name} must be a u64 integer")
    return value


def _rows(value: Any, *, width: int, bound: int, count: int | None = None) -> tuple[tuple[int, ...], ...]:
    if not isinstance(value, (list, tuple)):
        raise GeometryWorkflowError("Coordinates must be a sequence of integer rows")
    if (count is not None and len(value) != count) or (count is None and not 4 <= len(value) <= 256):
        raise GeometryWorkflowError("Geometry must contain 4..256 points or the required matrix rows")
    rows: list[tuple[int, ...]] = []
    for row in value:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            raise GeometryWorkflowError(f"Each row must have {width} coordinates")
        if any(type(item) is not int or abs(item) > bound for item in row):
            raise GeometryWorkflowError(f"Coordinates must be integers with absolute value <= {bound}")
        rows.append(tuple(row))
    return tuple(rows)


class GeometryWorkflow:
    """Store candidate stages and check their actual contents through FL-018/019.

    Revoking ``policy_record_id`` rotates this workflow policy. The governance
    engine's in-memory ``advance_policy_epoch`` is not this durable policy clock;
    the native verifier uses the root policy record's persistent Lamport tick.
    Records are valid from their commit tick until explicit revocation; externally
    supplied future validity windows or expiring leases are outside this contract.
    """

    def __init__(
        self,
        governance: MemoryGovernanceEngine,
        *,
        tenant_id: str,
        principal: str,
        native_library: Path | str,
    ) -> None:
        self._governance = governance
        self._tenant = tenant_id
        self._principal = principal
        self._lock = RLock()
        try:
            self._library = Path(native_library).absolute()
            self._library_digest = self._hash_library()
            loader = ExtensionFileLoader("_babylon60_geometry", str(self._library))
            spec = importlib.util.spec_from_file_location("_babylon60_geometry", self._library, loader=loader)
            if spec is None or spec.loader is None:
                raise GeometryWorkflowError("Cannot load the FL-019 kernel extension")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if getattr(module, "CHECKER_VERSION", None) != CHECKER_VERSION:
                raise GeometryWorkflowError("Unsupported native FL-019 checker version")
            factory = getattr(module, "GeometryVerifier", None)
            if not callable(factory):
                raise GeometryWorkflowError("Native GeometryVerifier is unavailable")
            self._factory = cast(Callable[[], _NativeVerifier], factory)
            self._native = self._factory()
            if not callable(getattr(self._native, "verify", None)):
                raise GeometryWorkflowError("Native GeometryVerifier.verify is unavailable")
            self._check_library()
        except GeometryWorkflowError:
            raise
        except Exception as error:
            raise GeometryWorkflowError(f"Cannot load the configured native verifier: {error}") from error

        policy_data = {
            "checker_version": CHECKER_VERSION,
            "native_library_digest_b3": self._library_digest,
            "contract": _SCHEMA,
        }
        self._policy_id = str(uuid5(NAMESPACE_URL, _canonical([_SCHEMA, "POLICY", tenant_id, principal, policy_data])))
        try:
            self._governance.get_record(self._policy_id, tenant_id=self._tenant, include_inactive=True)
        except KeyError:
            try:
                self._write("POLICY", policy_data, record_id=self._policy_id)
            except GeometryWorkflowError as error:
                if not isinstance(error.__cause__, sqlite3.IntegrityError):
                    raise
        except Exception as error:
            raise GeometryWorkflowError(f"Cannot inspect durable FL-019 policy: {error}") from error
        self._policy()

    @property
    def policy_record_id(self) -> str:
        return self._policy_id

    def _hash_library(self) -> str:
        digest = blake3()
        descriptor = os.open(self._library, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(descriptor, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise GeometryWorkflowError("Native library must be a regular file")
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

    def _check_library(self) -> None:
        try:
            if self._hash_library() != self._library_digest:
                raise GeometryWorkflowError("Configured native verifier bytes changed")
        except OSError as error:
            raise GeometryWorkflowError(f"Configured native verifier is unavailable: {error}") from error

    def _view(self, record_id: str) -> MemoryRecordView:
        try:
            view = self._governance.get_record(record_id, tenant_id=self._tenant)
        except Exception as error:
            raise GeometryWorkflowError(f"Record {record_id} is unavailable or invalid: {error}") from error
        if (
            view.status != MemoryStatus.ACTIVE
            or view.tenant_id != self._tenant
            or view.principal != self._principal
            or view.modality != MemoryModality.EPISTEMIC
            or view.content is None
            or view.valid_from_tick != view.tx_lamport_t
            or view.valid_to_tick is not None
        ):
            raise GeometryWorkflowError(
                f"Record {record_id} has an invalid active owner, modality, or validity interval"
            )
        return view

    @staticmethod
    def _reference(view: MemoryRecordView) -> dict[str, str]:
        return {"record_id": view.record_id, "commitment": view.commitment}

    def _read(self, record_id: str, stage: str) -> tuple[MemoryRecordView, dict[str, Any]]:
        view = self._view(record_id)
        try:
            payload = json.loads(cast(str, view.content))
        except (ValueError, TypeError) as error:
            raise GeometryWorkflowError("Workflow record is not valid JSON") from error
        if (
            not isinstance(payload, dict)
            or set(payload) != {"schema", "stage", "data", "parents", "depends_on"}
            or payload["schema"] != _SCHEMA
            or payload["stage"] != stage
            or not isinstance(payload["data"], dict)
            or view.kind != _KINDS.get(stage, MemoryKind.MEMORY_EVENT)
        ):
            raise GeometryWorkflowError(f"Invalid {stage} record contract")
        for field, actual in (("parents", view.parents), ("depends_on", view.depends_on)):
            refs = payload[field]
            if not isinstance(refs, list):
                raise GeometryWorkflowError("Signed lineage must contain explicit reference lists")
            if any(not isinstance(ref, dict) or set(ref) != {"record_id", "commitment"} for ref in refs):
                raise GeometryWorkflowError("Malformed signed lineage reference")
            ids = [ref["record_id"] for ref in refs]
            if any(not isinstance(item, str) for item in ids) or len(ids) != len(set(ids)):
                raise GeometryWorkflowError("Duplicate or invalid signed lineage identity")
            if set(ids) != set(actual) or len(ids) != len(actual):
                raise GeometryWorkflowError("Stored graph edges do not match signed lineage")
            for ref in refs:
                if self._view(ref["record_id"]).commitment != ref["commitment"]:
                    raise GeometryWorkflowError("Upstream commitment does not match signed lineage")
        return view, payload["data"]

    @staticmethod
    def _keys(data: Mapping[str, Any], keys: set[str]) -> None:
        if set(data) != keys:
            raise GeometryWorkflowError("Workflow stage fields do not match the contract")

    @staticmethod
    def _edges(view: MemoryRecordView, parents: Sequence[str], dependencies: Sequence[str]) -> None:
        if any(not isinstance(item, str) for item in (*parents, *dependencies)):
            raise GeometryWorkflowError("Workflow dependencies must be record identifiers")
        if set(view.parents) != set(parents) or set(view.depends_on) != set(dependencies):
            raise GeometryWorkflowError("Workflow stage has missing or unexpected dependencies")

    def _write(
        self,
        stage: str,
        data: dict[str, Any],
        *,
        parents: Sequence[str] = (),
        dependencies: Sequence[str] = (),
        record_id: str | None = None,
    ) -> MemoryRecordView:
        payload = {
            "schema": _SCHEMA,
            "stage": stage,
            "data": data,
            "parents": [self._reference(self._view(item)) for item in parents],
            "depends_on": [self._reference(self._view(item)) for item in dependencies],
        }
        try:
            view = self._governance.add_record(
                record_id=record_id,
                tenant_id=self._tenant,
                principal=self._principal,
                content=_canonical(payload),
                kind=_KINDS.get(stage, MemoryKind.MEMORY_EVENT),
                modality=MemoryModality.EPISTEMIC,
                trust_level=TrustLevel.RESTRICTED,
                parents=parents,
                depends_on=dependencies,
            )
        except Exception as error:
            raise GeometryWorkflowError(f"Cannot persist {stage} evidence: {error}") from error
        self._read(view.record_id, stage)
        return view

    def _policy(self) -> MemoryRecordView:
        self._check_library()
        view, data = self._read(self._policy_id, "POLICY")
        if data != {
            "checker_version": CHECKER_VERSION,
            "native_library_digest_b3": self._library_digest,
            "contract": _SCHEMA,
        }:
            raise GeometryWorkflowError("Durable checker policy does not match this verifier")
        self._edges(view, (), ())
        _uint64(view.tx_lamport_t, "policy logical tick")
        return view

    def register_input(self, points: Sequence[Sequence[int]]) -> str:
        with self._lock:
            self._policy()
            coordinates = _rows(points, width=3, bound=10000)
            return self._write("INPUT", {"points": coordinates}, dependencies=(self._policy_id,)).record_id

    def register_transform(self, input_id: str, transform: Sequence[Sequence[int]]) -> str:
        with self._lock:
            self._policy()
            source, data = self._read(input_id, "INPUT")
            self._keys(data, {"points"})
            self._edges(source, (), (self._policy_id,))
            _rows(data["points"], width=3, bound=10000)
            matrix = _rows(transform, width=4, bound=10000, count=3)
            return self._write(
                "TRANSFORM_SPEC",
                {"input_id": input_id, "transform": matrix},
                parents=(input_id,),
                dependencies=(self._policy_id,),
            ).record_id

    def register_execution(self, transform_id: str, *, method: str = "matrix") -> str:
        """Register the candidate's declared method; verification checks its output."""
        with self._lock:
            self._policy()
            specification, data = self._read(transform_id, "TRANSFORM_SPEC")
            self._keys(data, {"input_id", "transform"})
            self._edges(specification, (data["input_id"],), (self._policy_id,))
            if not isinstance(method, str) or method not in {"matrix", "decomposed"}:
                raise GeometryWorkflowError("Unknown transformation method")
            return self._write(
                "TRANSFORM",
                {"transform_id": transform_id, "method": method},
                parents=(transform_id,),
                dependencies=(self._policy_id, data["input_id"]),
            ).record_id

    def register_output(self, execution_id: str, points: Sequence[Sequence[int]]) -> str:
        with self._lock:
            self._policy()
            execution, data = self._read(execution_id, "TRANSFORM")
            self._keys(data, {"transform_id", "method"})
            specification, spec_data = self._read(data["transform_id"], "TRANSFORM_SPEC")
            self._keys(spec_data, {"input_id", "transform"})
            self._edges(execution, (specification.record_id,), (self._policy_id, spec_data["input_id"]))
            coordinates = _rows(points, width=3, bound=1000000000)
            return self._write(
                "OUTPUT",
                {"execution_id": execution_id, "points": coordinates},
                parents=(execution_id,),
                dependencies=(self._policy_id, spec_data["input_id"], specification.record_id),
            ).record_id

    def _lineage(self, output_id: str) -> _Lineage:
        policy = self._policy()
        output, out_data = self._read(output_id, "OUTPUT")
        self._keys(out_data, {"execution_id", "points"})
        execution, exec_data = self._read(out_data["execution_id"], "TRANSFORM")
        self._keys(exec_data, {"transform_id", "method"})
        specification, spec_data = self._read(exec_data["transform_id"], "TRANSFORM_SPEC")
        self._keys(spec_data, {"input_id", "transform"})
        source, in_data = self._read(spec_data["input_id"], "INPUT")
        self._keys(in_data, {"points"})
        self._edges(source, (), (policy.record_id,))
        self._edges(specification, (source.record_id,), (policy.record_id,))
        self._edges(execution, (specification.record_id,), (policy.record_id, source.record_id))
        self._edges(output, (execution.record_id,), (policy.record_id, source.record_id, specification.record_id))
        if not isinstance(exec_data["method"], str) or exec_data["method"] not in {"matrix", "decomposed"}:
            raise GeometryWorkflowError("Unknown registered transformation method")
        return _Lineage(
            policy,
            source,
            specification,
            execution,
            output,
            _rows(in_data["points"], width=3, bound=10000),
            _rows(spec_data["transform"], width=4, bound=10000, count=3),
            _rows(out_data["points"], width=3, bound=1000000000),
        )

    def _attempt_id(self, output_id: str, nonce: int) -> str:
        return str(
            uuid5(NAMESPACE_URL, _canonical([_SCHEMA, "ATTEMPT", self._tenant, self._principal, output_id, nonce]))
        )

    @staticmethod
    def _acceptance_id(attempt_id: str) -> str:
        return str(uuid5(NAMESPACE_URL, _canonical([_SCHEMA, "ACCEPTANCE", attempt_id])))

    def _request(self, lineage: _Lineage, attempt: MemoryRecordView, nonce: int) -> dict[str, Any]:
        context = {
            "schema": _SCHEMA,
            "records": [
                {"record_id": view.record_id, "commitment": view.commitment, "logical_tick": view.tx_lamport_t}
                for view in (lineage.policy, *lineage.stages, attempt)
            ],
        }
        target = blake3(b"B60:FL-019:TARGET:v1\0" + UUID(lineage.output.record_id).bytes).digest(length=8)
        return {
            "points": lineage.points,
            "transform": lineage.matrix,
            "output": lineage.output_points,
            "context_digest_b3": blake3(_canonical(context).encode("utf-8")).hexdigest(),
            "policy_epoch": lineage.policy.tx_lamport_t,
            "target_id": int.from_bytes(target, "little"),
            "nonce": nonce,
        }

    @staticmethod
    def _expected_digests(request: Mapping[str, Any]) -> tuple[str, str]:
        version = CHECKER_VERSION.encode("utf-8") + b"\0"
        source = blake3(b"B60:FL-019:INPUT:v1\0" + version)
        source.update(bytes.fromhex(request["context_digest_b3"]))
        source.update(struct.pack("<Q", len(request["points"])))
        for row in (*request["points"], *request["transform"]):
            source.update(struct.pack("<" + "q" * len(row), *row))
        source.update(struct.pack("<QQQ", request["policy_epoch"], request["target_id"], request["nonce"]))
        artifact = blake3(b"B60:FL-019:ARTIFACT:v1\0" + version)
        artifact.update(struct.pack("<Q", len(request["output"])))
        for row in request["output"]:
            artifact.update(struct.pack("<qqq", *row))
        return source.hexdigest(), artifact.hexdigest()

    def _verify(self, request: Mapping[str, Any], *, fresh: bool) -> dict[str, Any]:
        self._check_library()
        try:
            report = json.loads((self._factory() if fresh else self._native).verify(_canonical(request)))
        except Exception as error:
            raise GeometryWorkflowError(f"Native geometry verification failed: {error}") from error
        required = {
            "accepted",
            "coordinate_check",
            "oriented_volume_check",
            "input_digest_b3",
            "artifact_digest_b3",
            "joint_evidence_digest_b3",
            "checker_version",
            "reason",
        }
        if not isinstance(report, dict) or set(report) != required or report["checker_version"] != CHECKER_VERSION:
            raise GeometryWorkflowError("Malformed native geometry verification report")
        if any(type(report[key]) is not bool for key in ("accepted", "coordinate_check", "oriented_volume_check")):
            raise GeometryWorkflowError("Native geometry checks must be boolean observations")
        input_digest, artifact_digest = self._expected_digests(request)
        if report["input_digest_b3"] != input_digest or report["artifact_digest_b3"] != artifact_digest:
            raise GeometryWorkflowError("Native report is not bound to the current input and artifact bytes")
        joint = report["joint_evidence_digest_b3"]
        if joint is not None and (not isinstance(joint, str) or _DIGEST.fullmatch(joint) is None):
            raise GeometryWorkflowError("Malformed joint geometry evidence digest")
        if report["accepted"] and not (report["coordinate_check"] and report["oriented_volume_check"] and joint):
            raise GeometryWorkflowError("Native acceptance lacks both independent geometry checks")
        if report["reason"] is not None and not isinstance(report["reason"], str):
            raise GeometryWorkflowError("Invalid native rejection reason")
        return report

    def accept(self, output_id: str, nonce: int) -> GeometryAcceptance:
        """Verify a candidate once; a persisted attempt consumes output+nonce."""
        with self._lock:
            nonce = _uint64(nonce, "nonce")
            lineage = self._lineage(output_id)
            attempt_id = self._attempt_id(output_id, nonce)
            try:
                self._governance.get_record(attempt_id, tenant_id=self._tenant, include_inactive=True)
            except KeyError:
                pass
            except Exception as error:
                raise GeometryWorkflowError(f"Cannot establish replay state: {error}") from error
            else:
                raise GeometryWorkflowError("Replay rejected: this output and nonce were already attempted")
            attempt = self._write(
                "VERIFICATION_ATTEMPT",
                {"output_id": output_id, "nonce": nonce},
                parents=(output_id,),
                dependencies=(self._policy_id,),
                record_id=attempt_id,
            )
            lineage = self._lineage(output_id)
            report = self._verify(self._request(lineage, attempt, nonce), fresh=False)
            self._lineage(output_id)
            status = "SEMANTICALLY_VERIFIED" if report["accepted"] else "EXECUTED"
            acceptance = self._write(
                "ACCEPTANCE",
                {"output_id": output_id, "attempt_id": attempt_id, "nonce": nonce, "status": status, "report": report},
                parents=tuple(view.record_id for view in lineage.stages),
                dependencies=(self._policy_id, attempt_id),
                record_id=self._acceptance_id(attempt_id),
            )
            return self.get_acceptance(acceptance.record_id)

    def get_acceptance(self, record_id: str) -> GeometryAcceptance:
        """Recompute native checks and signed lineage before reporting current status."""
        with self._lock:
            acceptance, data = self._read(record_id, "ACCEPTANCE")
            self._keys(data, {"output_id", "attempt_id", "nonce", "status", "report"})
            nonce = _uint64(data["nonce"], "nonce")
            lineage = self._lineage(data["output_id"])
            attempt, attempt_data = self._read(data["attempt_id"], "VERIFICATION_ATTEMPT")
            if (
                attempt_data != {"output_id": lineage.output.record_id, "nonce": nonce}
                or attempt.record_id != self._attempt_id(lineage.output.record_id, nonce)
                or acceptance.record_id != self._acceptance_id(attempt.record_id)
            ):
                raise GeometryWorkflowError("Acceptance is not bound to its persistent verification attempt")
            self._edges(attempt, (lineage.output.record_id,), (self._policy_id,))
            self._edges(
                acceptance, tuple(view.record_id for view in lineage.stages), (self._policy_id, attempt.record_id)
            )
            report = self._verify(self._request(lineage, attempt, nonce), fresh=True)
            status = "SEMANTICALLY_VERIFIED" if report["accepted"] else "EXECUTED"
            if data["report"] != report or data["status"] != status:
                raise GeometryWorkflowError("Persisted acceptance disagrees with independent native revalidation")
            self._lineage(lineage.output.record_id)
            self._read(record_id, "ACCEPTANCE")
            return GeometryAcceptance(status, record_id, _freeze(report))
