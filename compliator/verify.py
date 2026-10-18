"""Evidence record verification.

Re-computes every hash in a record's MANIFEST.json and checks that
evidence.json still binds the raw payload it claims. This is the command an
auditor (or a skeptical engineer) runs to confirm nothing was edited after
collection - the POC's whole answer to "why should I trust this?".
"""

from __future__ import annotations

import json
from pathlib import Path

from .errors import VerificationError


def verify_record(record_dir: Path) -> dict[str, object]:
    """Verify one evidence record directory. Raises VerificationError on failure."""
    record_dir = Path(record_dir)
    if not record_dir.is_dir():
        raise VerificationError(f"not a directory: {record_dir}")
    manifest_path = record_dir / "MANIFEST.json"
    evidence_path = record_dir / "evidence.json"
    if not manifest_path.is_file():
        raise VerificationError(f"{record_dir}: MANIFEST.json missing")
    if not evidence_path.is_file():
        raise VerificationError(f"{record_dir}: evidence.json missing")

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VerificationError(f"{record_dir}: unreadable JSON: {exc}") from exc

    import hashlib

    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise VerificationError(f"{record_dir}: manifest has no files to verify")

    checked: dict[str, str] = {}
    for rel, expected in files.items():
        target = record_dir / rel
        if not target.is_file():
            raise VerificationError(f"{record_dir}: manifest lists missing file '{rel}'")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != expected:
            raise VerificationError(
                f"{record_dir}: HASH MISMATCH for '{rel}' "
                f"(manifest {expected[:12]}..., actual {actual[:12]}...)"
            )
        checked[rel] = actual

    source = evidence.get("source", {})
    if source.get("raw_sha256") != checked.get(source.get("raw_file", "")):
        raise VerificationError(
            f"{record_dir}: evidence.json raw binding does not match manifest "
            f"(record was edited or assembled inconsistently)"
        )

    if manifest.get("control_id") != evidence.get("control", {}).get("id"):
        raise VerificationError(f"{record_dir}: control id mismatch between manifest and record")

    return {
        "record": str(record_dir),
        "control_id": evidence.get("control", {}).get("id"),
        "result": evidence.get("result"),
        "collection_id": evidence.get("collection", {}).get("id"),
        "files_verified": sorted(checked),
        "ok": True,
    }


def verify_all(evidence_root: Path) -> list[dict[str, object]]:
    """Verify every record directory under an evidence root."""
    results = []
    for record_dir in sorted(Path(evidence_root).glob("*/*/")):
        if (record_dir / "MANIFEST.json").is_file():
            results.append(verify_record(record_dir))
    if not results:
        raise VerificationError(f"no evidence records found under {evidence_root}")
    return results
