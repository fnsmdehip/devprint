"""Filesystem scanner for Git Archaeologist — reads file modification times."""
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from config import SKIP_DIRS, SKIP_EXTENSIONS


def scan_project_files(project_path: str | Path) -> dict:
    """Scan project directory and group files by modification date.

    Returns:
        {
            "files": [{"path": str, "mtime": datetime, "size": int, "ext": str}, ...],
            "by_date": {"2025-06-15": [file_info, ...], ...},
            "earliest": datetime,
            "latest": datetime,
            "total_files": int,
        }
    """
    project_path = Path(project_path)
    files = []
    by_date = defaultdict(list)
    earliest = None
    latest = None

    for root, dirs, filenames in os.walk(project_path):
        # Prune unwanted directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]

        for fname in filenames:
            fp = Path(root) / fname
            ext = fp.suffix.lower()

            # Skip binary and non-code files
            if ext in SKIP_EXTENSIONS:
                continue
            if fname.startswith('.') and fname != '.gitignore':
                continue

            try:
                stat = fp.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)
                size = stat.st_size

                file_info = {
                    "path": str(fp.relative_to(project_path)),
                    "abs_path": str(fp),
                    "mtime": mtime,
                    "size": size,
                    "ext": ext,
                }
                files.append(file_info)
                by_date[mtime.strftime("%Y-%m-%d")].append(file_info)

                if earliest is None or mtime < earliest:
                    earliest = mtime
                if latest is None or mtime > latest:
                    latest = mtime
            except (OSError, PermissionError):
                continue

    # Sort files within each date by time
    for date_key in by_date:
        by_date[date_key].sort(key=lambda f: f["mtime"])

    return {
        "files": sorted(files, key=lambda f: f["mtime"]),
        "by_date": dict(sorted(by_date.items())),
        "earliest": earliest,
        "latest": latest,
        "total_files": len(files),
    }


def preview_commit_plan(scan_result: dict) -> list:
    """Generate a preview of what commits would be created."""
    commits = []
    for date_str, day_files in scan_result["by_date"].items():
        # Split large days into multiple commits
        chunks = _chunk_files(day_files)
        for i, chunk in enumerate(chunks):
            # Use the median file's timestamp for commit time
            median_file = chunk[len(chunk) // 2]
            commits.append({
                "date": date_str,
                "timestamp": median_file["mtime"].isoformat(),
                "file_count": len(chunk),
                "files": [f["path"] for f in chunk],
                "message": _generate_commit_message(chunk),
            })
    return commits


def _chunk_files(files: list, max_per_commit: int = 20) -> list:
    """Split a day's files into reasonable commit-sized chunks."""
    if len(files) <= max_per_commit:
        return [files]

    chunks = []
    # Try to group by directory first
    by_dir = defaultdict(list)
    for f in files:
        top_dir = f["path"].split("/")[0] if "/" in f["path"] else "root"
        by_dir[top_dir].append(f)

    current_chunk = []
    for dir_files in by_dir.values():
        if len(current_chunk) + len(dir_files) > max_per_commit and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
        current_chunk.extend(dir_files)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks if chunks else [files]


def _generate_commit_message(files: list) -> str:
    """Generate a descriptive commit message from file paths."""
    if not files:
        return "update project files"

    # Find common directory
    dirs = set()
    extensions = set()
    for f in files:
        parts = f["path"].split("/")
        if len(parts) > 1:
            dirs.add(parts[0])
        extensions.add(f["ext"])

    # Generate message based on content
    if len(dirs) == 1:
        dir_name = list(dirs)[0].lower().replace("_", " ").replace("-", " ")
        if len(files) == 1:
            fname = Path(files[0]["path"]).stem.lower().replace("_", " ").replace("-", " ")
            return f"add {fname} to {dir_name}"
        return f"update {dir_name} ({len(files)} files)"

    ext_desc = _extension_description(extensions)
    if ext_desc:
        return f"add {ext_desc} ({len(files)} files)"

    return f"update project files ({len(files)} files)"


def _extension_description(extensions: set) -> str:
    """Human-readable description of file types."""
    ext_map = {
        ".py": "python modules",
        ".js": "javascript modules",
        ".jsx": "react components",
        ".ts": "typescript modules",
        ".tsx": "react typescript components",
        ".html": "html templates",
        ".css": "stylesheets",
        ".json": "config files",
        ".yaml": "configuration",
        ".yml": "configuration",
        ".md": "documentation",
        ".sh": "shell scripts",
        ".sql": "database schemas",
    }
    descs = []
    for ext in extensions:
        if ext in ext_map:
            descs.append(ext_map[ext])
    if len(descs) == 1:
        return descs[0]
    if len(descs) > 1:
        return f"{descs[0]} and {descs[1]}"
    return ""
