#!/usr/bin/env python3
"""DEVPRINT CLI — Developer Provenance & Portfolio Intelligence System."""
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import CATALOG_DIR, SITE_BUILD_DIR, CONTENT_OUTPUT_DIR

console = Console()


@click.group()
def cli():
    """DEVPRINT — Developer Provenance & Portfolio Intelligence System"""
    pass


# ─── CATALOG ──────────────────────────────────────────────────────────

@cli.group()
def catalog():
    """Manage the project catalog."""
    pass


@catalog.command()
def scan():
    """Scan Documents/ and generate catalog entries."""
    console.print("\n[bold green]DEVPRINT Catalog Scanner[/]")
    console.print("=" * 50)

    from catalog.scanner import scan_all_projects, save_catalog

    entries = scan_all_projects()
    console.print(f"\n[bold]Found {len(entries)} projects[/]")
    save_catalog(entries)
    console.print("[green]Catalog saved![/]\n")


@catalog.command("list")
def catalog_list():
    """List all cataloged projects."""
    from catalog.scanner import load_catalog

    entries = load_catalog()
    if not entries:
        console.print("[yellow]No catalog entries found. Run: devprint catalog scan[/]")
        return

    table = Table(title=f"DEVPRINT Catalog ({len(entries)} projects)")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Category", style="green")
    table.add_column("Tech", style="blue")
    table.add_column("Priority", justify="center")
    table.add_column("Confidence", style="yellow")
    table.add_column("Git?", justify="center")

    for e in sorted(entries, key=lambda x: x.get("portfolio_priority", 5)):
        tech = ", ".join(e.get("tech_stack", [])[:3])
        table.add_row(
            e["id"],
            e["name"],
            e.get("category", ""),
            tech,
            str(e.get("portfolio_priority", "")),
            e.get("proof", {}).get("confidence", ""),
            "Y" if e.get("has_existing_git") else "N",
        )

    console.print(table)


@catalog.command()
@click.argument("project_id")
def show(project_id):
    """Show details for a specific project."""
    from catalog.scanner import load_catalog

    entries = load_catalog()
    entry = next((e for e in entries if e["id"] == project_id), None)

    if not entry:
        console.print(f"[red]Project '{project_id}' not found[/]")
        return

    console.print(Panel(
        json.dumps(entry, indent=2, default=str),
        title=f"[bold]{entry['name']}[/]",
        border_style="green",
    ))


# ─── GIT ARCHAEOLOGIST ──────────────────────────────────────────────

@cli.group()
def git():
    """Git Archaeologist — create backdated repos."""
    pass


@git.command("scan")
@click.argument("project_id")
def git_scan(project_id):
    """Preview what commits would be created for a project."""
    from catalog.scanner import load_catalog
    from archaeologist.scan import scan_project_files, preview_commit_plan

    entries = load_catalog()
    entry = next((e for e in entries if e["id"] == project_id), None)
    if not entry:
        console.print(f"[red]Project '{project_id}' not found[/]")
        return

    local_path = entry.get("local_path")
    if not local_path:
        console.print(f"[red]No local path for {project_id}[/]")
        return

    console.print(f"\n[bold]Scanning: {local_path}[/]")
    result = scan_project_files(local_path)

    console.print(f"  Files: {result['total_files']}")
    console.print(f"  Earliest: {result['earliest']}")
    console.print(f"  Latest: {result['latest']}")
    console.print(f"  Active days: {len(result['by_date'])}")

    commits = preview_commit_plan(result)
    console.print(f"\n  Planned commits: {len(commits)}")
    console.print()

    table = Table(title="Commit Preview (first 20)")
    table.add_column("Date", style="cyan")
    table.add_column("Time", style="green")
    table.add_column("Files", justify="right")
    table.add_column("Message")

    for c in commits[:20]:
        table.add_row(c["date"], c["timestamp"][11:19], str(c["file_count"]), c["message"])

    console.print(table)
    if len(commits) > 20:
        console.print(f"  ... and {len(commits) - 20} more commits")


@git.command("push")
@click.argument("project_id")
@click.option("--dry-run", is_flag=True, help="Preview only, don't create repo")
@click.option("--output-dir", type=click.Path(), help="Where to create the repo")
def git_push(project_id, dry_run, output_dir):
    """Create backdated repo and push to GitHub."""
    from catalog.scanner import load_catalog
    from archaeologist.scan import scan_project_files
    from archaeologist.commit_engine import create_backdated_repo
    from archaeologist.repo_manager import push_repo, check_gh_auth

    entries = load_catalog()
    entry = next((e for e in entries if e["id"] == project_id), None)
    if not entry:
        console.print(f"[red]Project '{project_id}' not found[/]")
        return

    if not dry_run and not check_gh_auth():
        console.print("[red]Not authenticated with gh CLI. Run: gh auth login[/]")
        return

    local_path = entry.get("local_path")
    if not local_path:
        console.print(f"[red]No local path for {project_id}[/]")
        return

    console.print(f"\n[bold green]Git Archaeologist: {entry['name']}[/]")
    console.print(f"  Scanning {local_path}...")

    scan_result = scan_project_files(local_path)
    console.print(f"  Found {scan_result['total_files']} files across {len(scan_result['by_date'])} days")

    result = create_backdated_repo(
        project_path=local_path,
        repo_name=project_id,
        scan_result=scan_result,
        output_dir=output_dir,
        dry_run=dry_run,
    )

    console.print(f"  Repo created: {result['repo_path']}")
    console.print(f"  Commits: {result['commit_count']}")

    if not dry_run and result.get("repo_path"):
        console.print("  Pushing to GitHub...")
        push_result = push_repo(
            result["repo_path"],
            project_id,
            entry.get("tagline", ""),
        )
        if push_result.get("url"):
            console.print(f"  [green]Pushed: {push_result['url']}[/]")
        else:
            console.print(f"  [red]Push failed: {push_result.get('error', 'unknown')}[/]")


@git.command("push-all")
@click.option("--dry-run", is_flag=True, help="Preview only")
@click.option("--output-dir", type=click.Path(), help="Where to create repos")
def git_push_all(dry_run, output_dir):
    """Process all projects — create repos and push to GitHub."""
    from catalog.scanner import load_catalog
    from archaeologist.scan import scan_project_files
    from archaeologist.commit_engine import create_backdated_repo
    from archaeologist.repo_manager import push_repo, check_gh_auth

    entries = load_catalog()
    local_entries = [e for e in entries if e.get("local_path") and e.get("source_type") == "local_code"]

    if not local_entries:
        console.print("[yellow]No local projects found in catalog[/]")
        return

    if not dry_run and not check_gh_auth():
        console.print("[red]Not authenticated with gh CLI. Run: gh auth login[/]")
        return

    console.print(f"\n[bold green]Git Archaeologist: Processing {len(local_entries)} projects[/]\n")

    for entry in sorted(local_entries, key=lambda e: e.get("portfolio_priority", 5)):
        console.print(f"[bold]→ {entry['name']}[/] ({entry['id']})")
        try:
            scan_result = scan_project_files(entry["local_path"])
            if scan_result["total_files"] == 0:
                console.print("  [yellow]No files found, skipping[/]")
                continue

            result = create_backdated_repo(
                project_path=entry["local_path"],
                repo_name=entry["id"],
                scan_result=scan_result,
                output_dir=output_dir,
                dry_run=dry_run,
            )
            console.print(f"  {result['commit_count']} commits, {scan_result['total_files']} files")

            if not dry_run and result.get("repo_path"):
                push_result = push_repo(result["repo_path"], entry["id"], entry.get("tagline", ""))
                if push_result.get("url"):
                    console.print(f"  [green]→ {push_result['url']}[/]")
                else:
                    console.print(f"  [red]Push failed: {push_result.get('error', '')}[/]")
        except Exception as e:
            console.print(f"  [red]Error: {e}[/]")

        console.print()


# ─── MEMORY IMPORT ──────────────────────────────────────────────────

@cli.group()
def memory():
    """AI Memory Importer — process chat exports."""
    pass


@memory.command("import")
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--provider", type=click.Choice(["chatgpt", "gemini"]), default="chatgpt")
def memory_import(filepath, provider):
    """Import an AI export file (ChatGPT JSON, Gemini Takeout)."""
    from memory_importer.classifier import classify_batch
    from memory_importer.merger import merge_related_conversations

    console.print(f"\n[bold green]Importing {provider} export: {filepath}[/]")

    if provider == "chatgpt":
        from memory_importer.parsers.chatgpt import parse_chatgpt_export
        conversations = parse_chatgpt_export(filepath)
    elif provider == "gemini":
        from memory_importer.parsers.gemini import parse_gemini_takeout
        conversations = parse_gemini_takeout(filepath)
    else:
        console.print(f"[red]Unknown provider: {provider}[/]")
        return

    console.print(f"  Parsed: {len(conversations)} conversations")

    # Classify
    result = classify_batch(conversations)
    console.print("\n  Classification summary:")
    for cat, count in result["summary"].items():
        console.print(f"    {cat}: {count}")

    # Merge related
    merged = merge_related_conversations(result["classified"])
    non_noise = [c for c in merged if c.get("classification", {}).get("category") != "NOISE"]
    console.print(f"\n  After merging: {len(non_noise)} unique projects/research threads")
    console.print(f"  Filtered out: {result['summary'].get('NOISE', 0)} noise conversations")

    # Extract and save to catalog
    from memory_importer.extractor import extract_project_data
    from catalog.scanner import save_catalog

    entries = [extract_project_data(c) for c in non_noise]

    # Remove internal fields before saving
    for e in entries:
        e.pop("_code_snippets", None)
        e.pop("_raw_conversation", None)

    save_catalog(entries)
    console.print(f"\n[green]Saved {len(entries)} entries to catalog[/]\n")


@memory.command("manual")
@click.option("--provider", default="claude", help="AI provider name")
@click.option("--batch", type=int, default=0, help="Generate batch template with N entries")
def memory_manual(provider, batch):
    """Generate manual entry template for non-exportable providers."""
    from memory_importer.parsers.manual import create_manual_template, generate_batch_template

    output_dir = CATALOG_DIR.parent / "manual_entries"

    if batch > 0:
        filepath = generate_batch_template(output_dir / f"batch_{provider}.json", batch, provider)
        console.print(f"\n[green]Batch template created: {filepath}[/]")
        console.print(f"  Edit the file, then run: devprint memory import-manual {filepath}")
    else:
        filepath = create_manual_template(output_dir, provider)
        console.print(f"\n[green]Template created: {filepath}[/]")
        console.print("  Edit the file with your project details, then run:")
        console.print(f"  devprint memory import-manual {filepath.parent}")


# ─── PROOF ──────────────────────────────────────────────────────────

@cli.group()
def proof():
    """Proof & Validation system."""
    pass


@proof.command("generate")
@click.argument("project_id", required=False)
def proof_generate(project_id):
    """Generate proof manifest(s). Omit ID to generate for all."""
    from catalog.scanner import load_catalog
    from proof.manifest import generate_manifest, save_manifest, generate_all_manifests

    entries = load_catalog()

    if project_id:
        entry = next((e for e in entries if e["id"] == project_id), None)
        if not entry:
            console.print(f"[red]Project '{project_id}' not found[/]")
            return
        manifest = generate_manifest(entry)
        path = save_manifest(manifest)
        console.print(f"[green]Proof manifest saved: {path}[/]")
        console.print(f"  Confidence: {manifest['confidence']}")
        console.print(f"  Evidence sources: {manifest['evidence_count']}")
    else:
        console.print(f"\n[bold green]Generating proof manifests for {len(entries)} projects[/]\n")
        manifests = generate_all_manifests(entries)
        high = sum(1 for m in manifests if m["confidence"] == "high")
        med = sum(1 for m in manifests if m["confidence"] == "medium")
        console.print(f"\n  High confidence: {high}")
        console.print(f"  Medium confidence: {med}")
        console.print(f"  Total manifests: {len(manifests)}\n")


# ─── PORTFOLIO SITE ──────────────────────────────────────────────────

@cli.group()
def site():
    """Portfolio site generator."""
    pass


@site.command("build")
def site_build():
    """Generate the static portfolio site."""
    from catalog.scanner import load_catalog
    from portfolio_site.generator import build_site

    entries = load_catalog()
    if not entries:
        console.print("[yellow]No catalog entries. Run: devprint catalog scan[/]")
        return

    console.print(f"\n[bold green]Building portfolio site ({len(entries)} projects)[/]\n")
    build_dir = build_site(entries)
    console.print(f"\n[green]Site built: {build_dir}[/]")
    console.print(f"  Preview: python -m http.server 8000 -d {build_dir}")
    console.print(f"  Deploy:  surge {build_dir} yoursite.surge.sh\n")


@site.command("preview")
def site_preview():
    """Start local preview server."""
    import subprocess
    if not SITE_BUILD_DIR.exists():
        console.print("[yellow]Site not built yet. Run: devprint site build[/]")
        return
    console.print(f"[green]Serving at http://localhost:8000[/]")
    subprocess.run(["python", "-m", "http.server", "8000", "-d", str(SITE_BUILD_DIR)])


@site.command("deploy")
@click.argument("domain")
def site_deploy(domain):
    """Deploy to Surge."""
    import subprocess
    if not SITE_BUILD_DIR.exists():
        console.print("[yellow]Site not built. Run: devprint site build[/]")
        return
    console.print(f"[bold]Deploying to {domain}...[/]")
    subprocess.run(["surge", str(SITE_BUILD_DIR), domain])


# ─── CONTENT ENGINE ──────────────────────────────────────────────────

@cli.group()
def content():
    """Content generation engine."""
    pass


@content.command("generate")
@click.argument("project_id")
def content_generate(project_id):
    """Generate all content types for a project."""
    from catalog.scanner import load_catalog
    from content.generator import generate_all_content, save_content

    entries = load_catalog()
    entry = next((e for e in entries if e["id"] == project_id), None)
    if not entry:
        console.print(f"[red]Project '{project_id}' not found[/]")
        return

    console.print(f"\n[bold green]Generating content for: {entry['name']}[/]\n")

    content_data = generate_all_content(entry)
    result = save_content(project_id, content_data)

    for ctype, path in result["files"].items():
        console.print(f"  [green]✓[/] {ctype}: {path}")

    console.print(f"\n  All content saved to: {CONTENT_OUTPUT_DIR / project_id}\n")


@content.command("calendar")
@click.option("--days", default=30, help="Number of days to plan")
def content_calendar(days):
    """Generate a content calendar."""
    from catalog.scanner import load_catalog
    from content.generator import generate_content_calendar

    entries = load_catalog()
    if not entries:
        console.print("[yellow]No catalog entries. Run: devprint catalog scan[/]")
        return

    calendar = generate_content_calendar(entries, days)

    table = Table(title=f"{days}-Day Content Calendar")
    table.add_column("Day", justify="center", style="cyan")
    table.add_column("Weekday", style="green")
    table.add_column("Platform", style="blue")
    table.add_column("Type")
    table.add_column("Project", style="bold")
    table.add_column("Angle")

    for item in calendar:
        table.add_row(
            str(item["day"]),
            item["weekday"],
            item["platform"],
            item["content_type"],
            item["project_name"],
            item["angle"][:50],
        )

    console.print(table)


# ─── DASHBOARD ──────────────────────────────────────────────────────

@cli.command()
def status():
    """Show overall DEVPRINT status."""
    from catalog.scanner import load_catalog
    from proof.timeline import generate_timeline_summary

    entries = load_catalog()

    if not entries:
        console.print("\n[yellow]No catalog entries yet.[/]")
        console.print("  Run: [bold]python cli.py catalog scan[/]\n")
        return

    summary = generate_timeline_summary(entries)

    console.print(Panel(
        f"""[bold green]DEVPRINT Status[/]

  Projects cataloged:  [bold]{len(entries)}[/]
  Earliest project:    {summary.get('earliest_project', 'N/A')}
  Latest activity:     {summary.get('latest_activity', 'N/A')}
  Total months active: [bold]{summary.get('total_months_active', 0)}[/]

  [bold]By confidence:[/]
    High:          {sum(1 for e in entries if e.get('proof', {}).get('confidence') == 'high')}
    Medium:        {sum(1 for e in entries if e.get('proof', {}).get('confidence') == 'medium')}
    Low:           {sum(1 for e in entries if e.get('proof', {}).get('confidence') == 'low')}
    Self-reported: {sum(1 for e in entries if e.get('proof', {}).get('confidence') == 'self-reported')}

  [bold]By category:[/]
    Projects:  {sum(1 for e in entries if e.get('category') == 'project')}
    Research:  {sum(1 for e in entries if e.get('category') == 'research')}
    Strategy:  {sum(1 for e in entries if e.get('category') == 'strategy')}

  Site built: {'[green]Yes[/]' if SITE_BUILD_DIR.exists() else '[yellow]No[/]  → python cli.py site build'}
""",
        border_style="green",
    ))


if __name__ == "__main__":
    cli()
