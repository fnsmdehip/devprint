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

    # Push
    result = subprocess.run(
        ["git", "push", "-u", "origin", "main", "--force"],
        cwd=str(repo_path), capture_output=True, text=True,
    )

    if result.returncode == 0:
        return {"url": f"https://github.com/{username}/{repo_name}", "pushed": True}
    else:
        return {"error": f"Push failed: {result.stderr.strip()}"}


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
