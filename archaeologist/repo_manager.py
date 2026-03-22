"""GitHub repo creation and management via gh CLI."""
import json
import subprocess
from pathlib import Path


def check_gh_auth() -> bool:
    """Check if gh CLI is authenticated."""
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def get_github_username() -> str | None:
    """Get the authenticated GitHub username."""
    result = subprocess.run(
        ["gh", "api", "user", "--jq", ".login"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def repo_exists(repo_name: str) -> bool:
    """Check if a GitHub repo already exists."""
    username = get_github_username()
    if not username:
        return False
    result = subprocess.run(
        ["gh", "repo", "view", f"{username}/{repo_name}"],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def create_github_repo(
    repo_name: str,
    description: str,
    public: bool = True,
    dry_run: bool = False,
) -> dict:
    """Create a new GitHub repository.

    Returns:
        {"url": str, "created": bool, "already_exists": bool}
    """
    if repo_exists(repo_name):
        username = get_github_username()
        return {
            "url": f"https://github.com/{username}/{repo_name}",
            "created": False,
            "already_exists": True,
        }

    if dry_run:
        print(f"  [DRY RUN] Would create {'public' if public else 'private'} repo: {repo_name}")
        return {"url": f"https://github.com/USER/{repo_name}", "created": False, "dry_run": True}

    visibility = "--public" if public else "--private"
    result = subprocess.run(
        ["gh", "repo", "create", repo_name, visibility,
         "--description", description,
         "--source", ".",
         "--push"],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        username = get_github_username()
        return {
            "url": f"https://github.com/{username}/{repo_name}",
            "created": True,
            "already_exists": False,
        }
    else:
        return {
            "url": None,
            "created": False,
            "error": result.stderr.strip(),
        }


def push_repo(repo_path: str | Path, repo_name: str, description: str = "") -> dict:
    """Add remote and push an existing local repo to GitHub.

    This handles repos already initialized with backdated commits.
    """
    repo_path = Path(repo_path)

    # Create the remote repo first (without --source to avoid auto-push)
    username = get_github_username()
    if not username:
        return {"error": "Not authenticated with gh CLI"}

    if not repo_exists(repo_name):
        result = subprocess.run(
            ["gh", "repo", "create", f"{username}/{repo_name}",
             "--public", "--description", description],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            return {"error": f"Failed to create repo: {result.stderr.strip()}"}

    # Add remote
    remote_url = f"https://github.com/{username}/{repo_name}.git"
    subprocess.run(
        ["git", "remote", "remove", "origin"],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    subprocess.run(
        ["git", "remote", "add", "origin", remote_url],
        cwd=str(repo_path), capture_output=True, text=True,
    )

    # Push — use chunked push for large repos
    result = _chunked_push(repo_path)

    if result["success"]:
        return {"url": f"https://github.com/{username}/{repo_name}", "pushed": True}
    else:
        return {"error": f"Push failed: {result.get('error', 'unknown')}"}


def _chunked_push(repo_path: Path, chunk_size: int = 50) -> dict:
    """Push a large repo in chunks to avoid GitHub HTTP 500 errors.

    Pushes commits in batches using rev-list to avoid exceeding
    GitHub's pack size limits.
    """
    repo_path = Path(repo_path)

    # First try a normal push
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main", "--force"],
        cwd=str(repo_path), capture_output=True, text=True,
        timeout=120,
    )
    if result.returncode == 0:
        return {"success": True}

    # If normal push failed (likely too large), push in chunks
    print("    Normal push failed, trying chunked push...")

    # Get all commits in order
    rev_result = subprocess.run(
        ["git", "rev-list", "--reverse", "main"],
        cwd=str(repo_path), capture_output=True, text=True,
    )
    if rev_result.returncode != 0:
        return {"success": False, "error": rev_result.stderr.strip()}

    commits = rev_result.stdout.strip().split("\n")
    if not commits or commits == ['']:
        return {"success": False, "error": "No commits found"}

    # Push in chunks
    for i in range(0, len(commits), chunk_size):
        chunk_end = min(i + chunk_size, len(commits)) - 1
        commit_sha = commits[chunk_end]

        print(f"    Pushing commits {i+1}-{chunk_end+1} of {len(commits)}...")
        push_result = subprocess.run(
            ["git", "push", "origin", f"{commit_sha}:refs/heads/main", "--force"],
            cwd=str(repo_path), capture_output=True, text=True,
            timeout=180,
        )
        if push_result.returncode != 0:
            # Try even smaller chunks
            for j in range(i, chunk_end + 1, 10):
                mini_end = min(j + 10, chunk_end + 1) - 1
                mini_sha = commits[mini_end]
                subprocess.run(
                    ["git", "push", "origin", f"{mini_sha}:refs/heads/main", "--force"],
                    cwd=str(repo_path), capture_output=True, text=True,
                    timeout=180,
                )

    # Final push to make sure HEAD is up to date
    subprocess.run(
        ["git", "push", "-u", "origin", "main", "--force"],
        cwd=str(repo_path), capture_output=True, text=True,
        timeout=120,
    )

    return {"success": True}


def list_user_repos() -> list:
    """List all repos for the authenticated user."""
    result = subprocess.run(
        ["gh", "repo", "list", "--json", "name,description,url,isPrivate,createdAt",
         "--limit", "200"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return json.loads(result.stdout)
    return []
