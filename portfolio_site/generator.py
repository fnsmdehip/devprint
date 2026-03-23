"""Static site generator — builds portfolio HTML from catalog data."""
import json
import shutil
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from config import CATALOG_DIR, SITE_BUILD_DIR


def build_site(catalog_entries: list, site_config: dict | None = None) -> Path:
    """Generate the complete static portfolio site.

    Args:
        catalog_entries: List of project catalog entries
        site_config: Optional overrides for site configuration

    Returns:
        Path to the build directory
    """
    config = {
        "site_title": "DEVPRINT",
        "site_tagline": "18+ months of AI-native development — autonomous agents, prediction engines, SaaS, mobile apps, and deep research",
        "github_url": "",
        "twitter_url": "",
        "linkedin_url": "",
        "email": "",
    }
    if site_config:
        config.update(site_config)

    # Setup Jinja2
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=False)

    # Prepare build directory
    SITE_BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Copy static assets
    static_src = Path(__file__).parent / "static"
    static_dst = SITE_BUILD_DIR / "static"
    if static_dst.exists():
        shutil.rmtree(static_dst)
    shutil.copytree(str(static_src), str(static_dst))

    # Compute global stats
    all_tech = set()
    all_ai_tools = set()
    for entry in catalog_entries:
        all_tech.update(entry.get("tech_stack", []))
        all_ai_tools.update(entry.get("ai_providers_used", []))

    # Sort projects by priority then date
    sorted_projects = sorted(
        catalog_entries,
        key=lambda e: (e.get("portfolio_priority", 5), e.get("active_periods", [{}])[0].get("start", "9999")),
    )

    featured = [p for p in sorted_projects if p.get("portfolio_priority", 5) <= 2][:6]
    research_projects = [p for p in sorted_projects if p.get("category") == "research"]

    # Group by category
    categories = defaultdict(list)
    for p in sorted_projects:
        cat = p.get("category", "uncategorized")
        categories[cat].append(p)

    category_meta = {
        "software": {"icon": "💻", "label": "Software", "desc": "Applications, agents, platforms, tools, and infrastructure"},
        "hardware": {"icon": "🔧", "label": "Hardware", "desc": "Physical devices, IoT, sensing systems, and embedded projects"},
        "research": {"icon": "🔬", "label": "Research", "desc": "Deep explorations in physics, longevity, finance, and more"},
        "business-strategy": {"icon": "📊", "label": "Business Strategy", "desc": "Revenue methods, market research, growth systems, and playbooks"},
        "content-system": {"icon": "📹", "label": "Content Systems", "desc": "Video automation, social media engines, newsletters, and content factories"},
        "data-system": {"icon": "🗄️", "label": "Data Systems", "desc": "Scraping fleets, data pipelines, digital libraries, and intelligence gathering"},
    }

    categories_with_meta = []
    for cat_id in ["software", "hardware", "research", "business-strategy", "content-system", "data-system"]:
        if cat_id in categories:
            meta = category_meta.get(cat_id, {"icon": "📁", "label": cat_id, "desc": ""})
            categories_with_meta.append({
                "id": cat_id,
                "count": len(categories[cat_id]),
                "projects": categories[cat_id],
                **meta,
            })

    # Compute timeline summary
    earliest = "2024-01"
    all_dates = []
    for entry in catalog_entries:
        for period in entry.get("active_periods", []):
            if period.get("start"):
                all_dates.append(period["start"])
    if all_dates:
        earliest = min(all_dates)[:7]

    try:
        e_date = datetime.strptime(min(all_dates)[:10], "%Y-%m-%d") if all_dates else datetime(2024, 1, 1)
        total_months = (datetime.now().year - e_date.year) * 12 + (datetime.now().month - e_date.month)
    except ValueError:
        total_months = 18

    # Generate contribution graph data
    contribution_cells, month_labels = _generate_contribution_graph(catalog_entries)

    # Group projects by year for timeline
    projects_by_year = defaultdict(list)
    for p in sorted_projects:
        if p.get("active_periods"):
            year = p["active_periods"][0].get("start", "2025")[:4]
            projects_by_year[year].append(p)

    # Shared template context
    shared_ctx = {
        "total_projects": len(catalog_entries),
        "total_months": total_months,
        "tech_count": len(all_tech),
        "ai_provider_count": len(all_ai_tools),
        "all_tech": sorted(all_tech),
        "ai_tools": sorted(all_ai_tools),
    }

    # Build index
    print("  [BUILD] index.html")
    # Find PRINTMAXX github URL
    printmaxx_entry = next((p for p in catalog_entries if p.get("id") == "printmaxx-starter-kit"), {})
    printmaxx_github = printmaxx_entry.get("github_repo", "")

    _render(env, "index.html", SITE_BUILD_DIR / "index.html", {
        **shared_ctx,
        **config,
        "featured_projects": featured,
        "contribution_cells": contribution_cells,
        "month_labels": month_labels,
        "categories": categories_with_meta,
        "printmaxx_github": printmaxx_github,
    })

    # Build projects listing with category filter
    print("  [BUILD] projects.html")
    _render(env, "projects.html", SITE_BUILD_DIR / "projects.html", {
        **shared_ctx,
        "all_projects": sorted_projects,
        "categories": categories_with_meta,
    })

    # Build category directory pages
    cat_dir = SITE_BUILD_DIR / "categories"
    cat_dir.mkdir(exist_ok=True)
    print("  [BUILD] categories/index.html")
    _render(env, "categories_index.html", cat_dir / "index.html", {
        **shared_ctx,
        "categories": categories_with_meta,
    })
    for cat_data in categories_with_meta:
        print(f"  [BUILD] categories/{cat_data['id']}.html")
        _render(env, "category_detail.html", cat_dir / f"{cat_data['id']}.html", {
            **shared_ctx,
            "category": cat_data,
        })

    # Build individual project pages
    projects_dir = SITE_BUILD_DIR / "projects"
    projects_dir.mkdir(exist_ok=True)
    for project in sorted_projects:
        print(f"  [BUILD] projects/{project['id']}.html")
        _render(env, "project_detail.html", projects_dir / f"{project['id']}.html", {
            **shared_ctx,
            "project": project,
        })

    # Build research page
    print("  [BUILD] research.html")
    _render(env, "research.html", SITE_BUILD_DIR / "research.html", {
        **shared_ctx,
        "research_projects": research_projects,
    })

    # Build timeline page
    print("  [BUILD] timeline.html")
    _render(env, "timeline.html", SITE_BUILD_DIR / "timeline.html", {
        **shared_ctx,
        "projects_by_year": dict(sorted(projects_by_year.items(), reverse=True)),
        "earliest": earliest,
    })

    # Build proof page
    print("  [BUILD] proof.html")
    _render(env, "proof.html", SITE_BUILD_DIR / "proof.html", {
        **shared_ctx,
        "all_projects": sorted_projects,
    })

    # Build about page
    print("  [BUILD] about.html")
    _render(env, "about.html", SITE_BUILD_DIR / "about.html", {
        **shared_ctx,
        **config,
    })

    print(f"\n  Site built: {SITE_BUILD_DIR}")
    print(f"  Pages: {2 + len(sorted_projects) + 4} total")
    return SITE_BUILD_DIR


def _render(env: Environment, template_name: str, output_path: Path, context: dict):
    """Render a template to an HTML file."""
    template = env.get_template(template_name)
    html = template.render(**context)
    output_path.write_text(html)


def _generate_contribution_graph(catalog_entries: list) -> list:
    """Generate GitHub-style contribution graph data from catalog.

    Returns list of {"date": str, "count": int, "level": str} for 52 weeks.
    """
    # Count activity per day from BLENDED data:
    # - verified_filesystem: real file modification timestamps (103K files scanned)
    # - estimated_ai_native: days within active project periods where AI chat/research
    #   likely happened but no local files were modified
    # Source: proof/blended_activity_data.json
    daily_activity = {}
    daily_source = {}  # date -> "verified" | "estimated"
    blended_path = Path(__file__).parent.parent / "proof" / "blended_activity_data.json"
    real_data_path = Path(__file__).parent.parent / "proof" / "real_activity_data.json"

    if blended_path.exists():
        import json as _json
        blended_data = _json.loads(blended_path.read_text())

        for date_str, info in blended_data.items():
            commits = info.get("commits", 0)
            if commits > 0:
                daily_activity[date_str] = min(commits, 12)
                daily_source[date_str] = info.get("source", "unknown")
    elif real_data_path.exists():
        import json as _json
        real_data = _json.loads(real_data_path.read_text())
        for date_str, info in real_data.items():
            file_mods = info.get("total_file_modifications", 0)
            if file_mods > 0:
                if file_mods <= 10: commits = 1
                elif file_mods <= 50: commits = 2
                elif file_mods <= 200: commits = 3
                else: commits = min(5 + info.get("project_count", 1), 12)
                daily_activity[date_str] = commits
                daily_source[date_str] = "verified_filesystem"

    # Generate cells for last 52 weeks
    cells = []
    month_labels = []
    today = datetime.now()
    start_date = today - timedelta(weeks=52)

    # Align to Sunday (GitHub convention: columns = weeks, rows = days Sun-Sat)
    start_date -= timedelta(days=(start_date.weekday() + 1) % 7)

    current = start_date
    week_idx = 0
    last_month = None
    while current <= today:
        date_str = current.strftime("%Y-%m-%d")
        day_of_week = (current.weekday() + 1) % 7  # 0=Sun, 1=Mon, ..., 6=Sat
        count = daily_activity.get(date_str, 0)

        # Track month labels (first Sunday of each new month)
        current_month = current.strftime("%b")
        if day_of_week == 0:
            if current_month != last_month:
                month_labels.append({"label": current_month, "week": week_idx})
                last_month = current_month

        if count == 0:
            level = ""
        elif count <= 2:
            level = "l1"
        elif count <= 4:
            level = "l2"
        elif count <= 7:
            level = "l3"
        else:
            level = "l4"

        # Get project info from blended data
        active_projects = []
        source = daily_source.get(date_str, "")
        if blended_path.exists():
            day_info = blended_data.get(date_str, {})
            active_projects = day_info.get("projects", [])
        elif real_data_path.exists():
            day_info = real_data.get(date_str, {})
            day_projects = day_info.get("projects", {})
            for proj_name, fcount in sorted(day_projects.items(), key=lambda x: -x[1]):
                active_projects.append(f"{proj_name} ({fcount} files)")

        cells.append({
            "date": date_str,
            "display_date": current.strftime("%b %d, %Y"),
            "count": count,
            "level": level,
            "source": source,
            "day_of_week": day_of_week,
            "week": week_idx,
            "projects": active_projects[:5],
        })

        if day_of_week == 6:  # Saturday = end of week column
            week_idx += 1

        current += timedelta(days=1)

    return cells, month_labels
