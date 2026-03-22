"""SHA-256 hashing for files and directories — creates tamper-proof evidence."""
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

from config import SKIP_DIRS, SKIP_EXTENSIONS


def hash_file(filepath: str | Path) -> str:
    """Compute SHA-256 hash of a single file."""
    h = hashlib.sha256()
    filepath = Path(filepath)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def hash_directory(dir_path: str | Path, include_names: bool = True) -> dict:
    """Compute a composite hash of an entire directory.

    Args:
        dir_path: Directory to hash
        include_names: If True, filenames are included in hash (detecting renames)

    Returns:
        {
            "directory_hash": "sha256:abc123...",
            "file_count": 42,
            "total_bytes": 1234567,
            "computed_at": "2026-03-22T...",
            "file_hashes": {"relative/path": "sha256:...", ...}  # top 100 files
        }
    """
    dir_path = Path(dir_path)
    composite = hashlib.sha256()
    file_hashes = {}
    total_bytes = 0
    file_count = 0

    # Walk in sorted order for deterministic hashing
    for root, dirs, files in os.walk(dir_path):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))

        for fname in sorted(files):
            fp = Path(root) / fname
            ext = fp.suffix.lower()

            if ext in SKIP_EXTENSIONS:
                continue
            if fname.startswith('.') and fname != '.gitignore':
                continue

            try:
                fhash = hash_file(fp)
                rel_path = str(fp.relative_to(dir_path))

                if include_names:
                    composite.update(rel_path.encode())
                composite.update(fhash.encode())

                file_hashes[rel_path] = f"sha256:{fhash[:16]}"
                total_bytes += fp.stat().st_size
                file_count += 1
            except (OSError, PermissionError):
                continue

    return {
        "directory_hash": f"sha256:{composite.hexdigest()}",
        "file_count": file_count,
        "total_bytes": total_bytes,
        "computed_at": datetime.now().isoformat(),
        "file_hashes": dict(list(file_hashes.items())[:100]),  # Cap at 100 for readability
    }


def hash_export_file(filepath: str | Path) -> dict:
    """Hash an AI export file for proof of authenticity.

    Returns:
        {
            "file_hash": "sha256:...",
            "file_size": 12345,
            "file_name": "conversations.json",
            "hashed_at": "2026-03-22T...",
        }
    """
    filepath = Path(filepath)
    return {
        "file_hash": f"sha256:{hash_file(filepath)}",
        "file_size": filepath.stat().st_size,
        "file_name": filepath.name,
        "hashed_at": datetime.now().isoformat(),
    }
