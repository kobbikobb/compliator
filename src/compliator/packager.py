"""=====================================================================
TRUST BOUNDARY - the one component in this POC written to be reviewed
like production code.
=====================================================================

An auditor is being asked to trust the evidence this module emits. So the
rules here are deliberately boring and explicit:

  1. RAW COPY IS KEPT. Every record ships the exact bytes the plugin pulled
     (canonicalised JSON only - no field is added, removed or interpreted).
     A pass/fail summary is worthless without the population underneath it.
  2. EVERYTHING IS HASHED. The record's MANIFEST.json lists a SHA-256 for
     every file, and evidence.json binds the raw payload hash. Anyone can
     re-verify with ``PYTHONPATH=src python3 -m compliator verify <record-dir>``
     - trust comes from re-computation, not from trusting this code's output.
  3. PROVENANCE IS EXPLICIT. Source, plugin, file, file hash, collection
     time, config hash. An auditor can tell where each fact came from and
     whether the control definition changed since.
  4. THE OUTPUT IS DETERMINISTIC. Same raw facts + same config + same
     as-of date => byte-identical evidence.json except ``collected_at``.
     Determinism is what makes independent re-run verification meaningful.
  5. NO CONTROL LOGIC. Assertions were evaluated in evaluate.py and handed
     in already-resolved, with observed values recorded. This module judges
     nothing; it records, hashes and packages.

Review checklist for a human: canonicalisation, hash coverage, the
LATEST-pointer update rule (only on success), and the absence of any
try/except that could turn a failure into an empty record.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .config import Control
from .evaluate import CheckResult

EVIDENCE_SCHEMA = "compliator/evidence-record/v1"
MANIFEST_SCHEMA = "compliator/evidence-manifest/v1"


def canonical_json(obj: Any) -> str:
    """Canonical serialisation: sorted keys, fixed indent, trailing newline.

    Deterministic bytes are a precondition for meaningful hashing: any
    reordering or whitespace drift would make the hash useless as an
    integrity check.
    """
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def collection_id(collected_at: datetime, config_sha256: str) -> str:
    stamp = collected_at.strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{config_sha256[:8]}"


def _utc_iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def write_record(
    evidence_root: Path,
    control: Control,
    source_name: str,
    plugin_name: str,
    provenance: dict[str, Any],
    raw: dict[str, Any],
    check_results: list[CheckResult],
    as_of: str,
    collected_at: datetime | None = None,
) -> tuple[Path, str]:
    """Write one evidence record for one control. Returns (record_dir, result).

    Only called on success: the runner does not invoke this when collection
    or evaluation failed. There is intentionally no "empty record" path.
    """
    collected_at = collected_at or datetime.now(timezone.utc)
    cid = collection_id(collected_at, control.config_sha256)
    control_dir = evidence_root / control.id
    record_dir = control_dir / cid
    raw_dir = record_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    raw_rel = f"raw/{source_name}.json"
    raw_path = record_dir / raw_rel
    raw_text = canonical_json(raw)
    raw_path.write_text(raw_text, encoding="utf-8")
    raw_sha = sha256_bytes(raw_text.encode("utf-8"))

    checks = [result.as_dict() for result in check_results]
    passed = all(result.passed for result in check_results)
    result = "pass" if passed else "fail"

    record = {
        "schema": EVIDENCE_SCHEMA,
        "control": {
            "id": control.id,
            "title": control.title,
            "statement": control.statement,
            "owner": control.owner,
            "frequency": f"{control.frequency_days}d",
            "frameworks": control.frameworks,
        },
        "collection": {
            "id": cid,
            "collected_at": _utc_iso(collected_at),
            "as_of": as_of,
            "config_sha256": control.config_sha256,
            "engine_version": __version__,
        },
        "source": {
            "name": source_name,
            "plugin": plugin_name,
            "provenance": provenance,
            "raw_file": raw_rel,
            "raw_sha256": raw_sha,
        },
        "checks": checks,
        "result": result,
    }
    evidence_path = record_dir / "evidence.json"
    evidence_path.write_text(canonical_json(record), encoding="utf-8")

    # No "how to verify" command string is stored. It would be a command line
    # tied to one checkout layout, sitting inside a hashed artifact, going stale
    # the moment the CLI changes - and nothing verifies it. The stable pins are
    # permanent and enforced: `schema` below, and engine_version in the record.
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "collection_id": cid,
        "control_id": control.id,
        "files": {
            "evidence.json": sha256_file(evidence_path),
            raw_rel: sha256_file(raw_path),
        },
    }
    manifest_path = record_dir / "MANIFEST.json"
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8")

    latest = {
        "collection_id": cid,
        "collected_at": record["collection"]["collected_at"],
        "result": result,
        "evidence_sha256": manifest["files"]["evidence.json"],
        "manifest_sha256": sha256_file(manifest_path),
    }
    (control_dir / "LATEST.json").write_text(canonical_json(latest), encoding="utf-8")
    return record_dir, result
