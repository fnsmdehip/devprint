"""Git Archaeologist commit engine — creates backdated commits from file timestamps."""
import os
import random
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from config import MAX_COMMITS_PER_DAY, MIN_COMMIT_GAP_MINUTES, SKIP_DIRS, SKIP_EXTENSIONS


def create_backdated_repo(
    project_path: str | Path,
    repo_name: str,
    scan_result: dict,
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a new git repo with backdated commits from file timestamps.

    Args:
        project_path: Path to the source project
        repo_name: Name for the git repo
        scan_result: Output from archaeologist.scan.scan_project_files()
        output_dir: Where to create the repo (default: temp dir)
        dry_run: If True, only print what would happen

    Returns:
        {"repo_path": str, "commit_count": int, "date_range": str}
    """
    project_path = Path(project_path)

    if output_dir:
        repo_path = Path(output_dir) / repo_name
    else:
        repo_path = Path(tempfile.mkdtemp()) / repo_name

    if dry_run:
        commits = _plan_commits(scan_result)
        print(f"\n[DRY RUN] Would create {len(commits)} commits for {repo_name}")
        for c in commits[:10]:
            print(f"  {c['timestamp']} — {c['message']} ({c['file_count']} files)")
        if len(commits) > 10:
            print(f"  ... and {len(commits) - 10} more commits")
        return {"repo_path": str(repo_path), "commit_count": len(commits), "dry_run": True}

    # Create repo directory and initialize git
    repo_path.mkdir(parents=True, exist_ok=True)
    _run_git(repo_path, ["init"])
    _run_git(repo_path, ["checkout", "-b", "main"])

    # Create .gitignore first
    _create_gitignore(repo_path)
    _run_git(repo_path, ["add", ".gitignore"])
    earliest = scan_result.get("earliest")
    if earliest:
        ignore_date = (earliest - timedelta(days=1)).strftime("%Y-%m-%dT09:00:00")
    else:
        ignore_date = "2025-01-01T09:00:00"
    _commit_with_date(repo_path, "initial project setup", ignore_date)

    # Plan and execute commits
    commits = _plan_commits(scan_result)
    commit_count = 1  # .gitignore commit

    for commit_plan in commits:
        # Copy files into repo
        files_added = []
        for file_info in commit_plan["files_data"]:
            src = Path(file_info["abs_path"])
            rel = file_info["path"]
            dst = repo_path / rel

            dst.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(str(src), str(dst))
                files_added.append(rel)
            except (OSError, PermissionError) as e:
                print(f"  [WARN] Could not copy {rel}: {e}")
                continue

        if not files_added:
            continue

        # Stage and commit
        _run_git(repo_path, ["add", "--all"])
        _commit_with_date(repo_path, commit_plan["message"], commit_plan["timestamp"])
        commit_count += 1

    date_range = ""
    if scan_result["earliest"] and scan_result["latest"]:
        date_range = f"{scan_result['earliest'].strftime('%Y-%m-%d')} to {scan_result['latest'].strftime('%Y-%m-%d')}"

    return {
        "repo_path": str(repo_path),
        "commit_count": commit_count,
        "date_range": date_range,
    }


def create_documentation_repo(
    repo_name: str,
    readme_content: str,
    extra_files: dict | None = None,
    commit_date: str = "2024-01-01T12:00:00",
    output_dir: str | Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Create a documentation-only repo (for AI-native projects).

    Args:
        repo_name: Repo name
        readme_content: README.md content
        extra_files: {"relative/path.md": "content", ...}
        commit_date: ISO date for the commit
        output_dir: Where to create repo
        dry_run: Preview only

    Returns:
        {"repo_path": str, "commit_count": int}
    """
    if output_dir:
        repo_path = Path(output_dir) / repo_name
    else:
        repo_path = Path(tempfile.mkdtemp()) / repo_name

    if dry_run:
        file_count = 1 + (len(extra_files) if extra_files else 0)
        print(f"\n[DRY RUN] Would create doc repo {repo_name} with {file_count} files at {commit_date}")
        return {"repo_path": str(repo_path), "commit_count": 1, "dry_run": True}

    repo_path.mkdir(parents=True, exist_ok=True)
    _run_git(repo_path, ["init"])
    _run_git(repo_path, ["checkout", "-b", "main"])

    # Write README
    (repo_path / "README.md").write_text(readme_content)
    _run_git(repo_path, ["add", "README.md"])

    # Write extra files
    if extra_files:
        for rel_path, content in extra_files.items():
            fp = repo_path / rel_path
            fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(content)
            _run_git(repo_path, ["add", rel_path])

    _commit_with_date(repo_path, f"initial documentation for {repo_name}", commit_date)

    return {"repo_path": str(repo_path), "commit_count": 1}


def _plan_commits(scan_result: dict) -> list:
    """Plan commits from scan data with realistic patterns."""
    commits = []

    for date_str, day_files in scan_result["by_date"].items():
        day_commits = _plan_day_commits(date_str, day_files)
        commits.extend(day_commits)

    return commits


def _plan_day_commits(date_str: str, files: list) -> list:
    """Plan commits for a single day with realistic timing."""
    if not files:
        return []

    # Cap commits per day for realism
    max_commits = min(MAX_COMMITS_PER_DAY, max(1, len(files) // 5))

    # Split files into commit groups
    if len(files) <= max_commits:
        groups = [[f] for f in files]
    else:
        # Chunk into groups
        chunk_size = max(1, len(files) // max_commits)
        groups = []
        for i in range(0, len(files), chunk_size):
            groups.append(files[i:i + chunk_size])
        # Merge any tiny trailing group
        if len(groups) > max_commits and len(groups[-1]) < 3:
            groups[-2].extend(groups[-1])
            groups = groups[:-1]

    # Cap to max
    groups = groups[:MAX_COMMITS_PER_DAY]

    commits = []
    for group in groups:
        # Use actual file mod time for commit timestamp
        median = group[len(group) // 2]
        timestamp = median["mtime"].isoformat()

        commits.append({
            "date": date_str,
            "timestamp": timestamp,
            "file_count": len(group),
            "files_data": group,
            "message": _smart_commit_message(group),
        })

    return commits


def _smart_commit_message(files: list) -> str:
    """Generate intelligent commit messages from file content/paths."""
    if not files:
        return "update project files"

    # Analyze file paths for patterns
    paths = [f["path"] for f in files]
    dirs = set()
    basenames = set()

    for p in paths:
        parts = Path(p).parts
        if len(parts) > 1:
            dirs.add(parts[0])
        basenames.add(Path(p).stem.lower())

    # Single file commit
    if len(files) == 1:
        p = Path(files[0]["path"])
        name = p.stem.lower().replace("_", " ").replace("-", " ")
        parent = p.parent.name if p.parent.name != "." else ""
        if parent:
            return f"add {name} to {parent}"
        return f"add {name}"

    # All files in one directory
    if len(dirs) == 1:
        d = list(dirs)[0].lower().replace("_", " ").replace("-", " ")
        verbs = ["update", "add", "implement", "refactor"]
        verb = random.choice(verbs[:2])  # Mostly add/update
        return f"{verb} {d} ({len(files)} files)"

    # Mixed directories
    if len(dirs) <= 3:
        dir_list = ", ".join(sorted(dirs)[:3]).lower()
        return f"update {dir_list} ({len(files)} files)"

    # Many directories — describe the scope
    return f"update project ({len(files)} files across {len(dirs)} directories)"


def _create_gitignore(repo_path: Path):
    """Create a sensible .gitignore."""
    content = """# Dependencies
node_modules/
venv/
.venv/
env/
__pycache__/
*.pyc

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Build
dist/
build/
*.egg-info/
"""
    (repo_path / ".gitignore").write_text(content)


def _commit_with_date(repo_path: Path, message: str, date_str: str):
    """Create a git commit with backdated author and committer dates."""
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    subprocess.run(
        ["git", "commit", "-m", message, "--allow-empty"],
        cwd=str(repo_path),
        env=env,
        capture_output=True,
        text=True,
    )


def _run_git(repo_path: Path, args: list) -> subprocess.CompletedProcess:
    """Run a git command in the given directory."""
    return subprocess.run(
        ["git"] + args,
        cwd=str(repo_path),
        capture_output=True,
        text=True,
    )
