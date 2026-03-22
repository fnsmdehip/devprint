"""Proof manifest generator — creates verifiable evidence records per project."""
import json
from datetime import datetime
from pathlib import Path

from proof.hasher import hash_directory, hash_export_file
from proof.timeline import check_timeline_consistency
from config import CATALOG_DIR


def generate_manifest(entry: dict) -> dict:
    """Generate a proof manifest for a catalog entry.

    Returns:
        Complete proof.json structure with all available evidence.
    """
    evidence = []

    # 1. Filesystem evidence
    local_path = entry.get("local_path")
    if local_path and Path(local_path).exists():
        dir_hash = hash_directory(local_path)
        evidence.append({
            "type": "filesystem",
            "path": local_path,
            "earliest_file_mod": entry.get("active_periods", [{}])[0].get("start"),
            "file_count": dir_hash["file_count"],
            "total_bytes": dir_hash["total_bytes"],
            "directory_hash": dir_hash["directory_hash"],
            "computed_at": dir_hash["computed_at"],
        })

    # 2. AI export evidence
    if entry.get("proof", {}).get("ai_export_available"):
        evidence.append({
            "type": "ai_export",
            "provider": entry.get("ai_providers_used", ["unknown"])[0],
            "conversation_count": entry.get("metrics", {}).get("conversation_count", 0),
            "message_count": entry.get("metrics", {}).get("message_count", 0),
            "note": "Timestamps from server-side export data",
        })

    # 3. Git evidence (if already pushed)
    github_repo = entry.get("github_repo")
    if github_repo:
        evidence.append({
            "type": "git_repository",
            "url": github_repo,
            "note": "Commit hashes are immutable once pushed",
        })

    # 4. Surge deploy evidence
    if entry.get("proof", {}).get("surge_deploys"):
        evidence.append({
            "type": "surge_deployment",
            "note": "Deployment records available via surge CLI history",
        })

    # 5. Timeline consistency check
    consistency = check_timeline_consistency(entry)

    # Determine confidence
    source_count = len(evidence)
    if source_count >= 3 and consistency["consistent"]:
        confidence = "high"
    elif source_count >= 2 and consistency["consistent"]:
        confidence = "medium"
    elif source_count >= 1:
        confidence = "low"
    else:
        confidence = "self-reported"

    manifest = {
        "project_id": entry["id"],
        "project_name": entry["name"],
        "generated_at": datetime.now().isoformat(),
        "evidence": evidence,
        "evidence_count": len(evidence),
        "timeline_consistency": consistency,
        "confidence": confidence,
        "active_periods": entry.get("active_periods", []),
        "source_type": entry.get("source_type", "unknown"),
    }

    return manifest


def save_manifest(manifest: dict, output_dir: str | Path | None = None) -> Path:
    """Save proof manifest to disk."""
    if output_dir:
        out = Path(output_dir)
    else:
        out = CATALOG_DIR.parent / "proofs"

    out.mkdir(parents=True, exist_ok=True)
    filepath = out / f"{manifest['project_id']}_proof.json"
    filepath.write_text(json.dumps(manifest, indent=2, default=str))
    return filepath


def generate_all_manifests(catalog_entries: list) -> list:
    """Generate proof manifests for all catalog entries."""
    manifests = []
    for entry in catalog_entries:
        print(f"  [PROOF] Generating manifest for {entry['id']}...")
        manifest = generate_manifest(entry)
        save_manifest(manifest)
        manifests.append(manifest)
    return manifests
