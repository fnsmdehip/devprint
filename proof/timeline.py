"""Timeline cross-reference builder — validates project timelines across sources."""
from datetime import datetime


def build_timeline(catalog_entries: list) -> list:
    """Build a unified timeline from all catalog entries.

    Returns:
        Sorted list of timeline events with source attribution.
    """
    events = []

    for entry in catalog_entries:
        project_id = entry.get("id", "unknown")
        project_name = entry.get("name", "Unknown")

        for period in entry.get("active_periods", []):
            events.append({
                "date": period["start"],
                "type": "project_start",
                "project_id": project_id,
                "project_name": project_name,
                "source": entry.get("source_type", "unknown"),
                "intensity": period.get("intensity", "medium"),
            })
            events.append({
                "date": period["end"],
                "type": "project_active",
                "project_id": project_id,
                "project_name": project_name,
                "source": entry.get("source_type", "unknown"),
                "intensity": period.get("intensity", "medium"),
            })

    events.sort(key=lambda e: e["date"])
    return events


def check_timeline_consistency(entry: dict) -> dict:
    """Check if a project's evidence sources have consistent timelines.

    Returns:
        {
            "consistent": bool,
            "issues": ["list of any inconsistencies"],
            "evidence_sources": int,
        }
    """
    issues = []
    sources = 0

    proof = entry.get("proof", {})
    periods = entry.get("active_periods", [])

    if not periods:
        return {"consistent": True, "issues": ["no active periods defined"], "evidence_sources": 0}

    start = periods[0].get("start", "")
    end = periods[-1].get("end", "")

    if proof.get("filesystem_timestamps"):
        sources += 1

    if proof.get("ai_export_available"):
        sources += 1

    if proof.get("surge_deploys"):
        sources += 1

    # Check for impossible dates
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d")
        end_dt = datetime.strptime(end, "%Y-%m-%d")

        if end_dt < start_dt:
            issues.append(f"end date ({end}) is before start date ({start})")

        if start_dt.year < 2022:
            issues.append(f"start date ({start}) seems too early for AI-native development")

        if end_dt > datetime.now():
            issues.append(f"end date ({end}) is in the future")

        # Flag suspiciously short projects with high file counts
        days = (end_dt - start_dt).days
        file_count = entry.get("metrics", {}).get("file_count", 0)
        if days < 3 and file_count > 500:
            issues.append(f"{file_count} files in {days} days seems unusually compressed")

    except ValueError:
        issues.append("could not parse date strings")

    return {
        "consistent": len(issues) == 0,
        "issues": issues,
        "evidence_sources": sources,
    }


def generate_timeline_summary(catalog_entries: list) -> dict:
    """Generate a summary of the entire development timeline.

    Returns:
        {
            "earliest_project": "2023-06-01",
            "latest_activity": "2026-03-22",
            "total_months_active": 34,
            "projects_by_year": {"2024": 5, "2025": 12, ...},
            "monthly_activity": {"2025-01": 3, "2025-02": 5, ...},
        }
    """
    all_dates = []
    monthly = {}
    yearly = {}

    for entry in catalog_entries:
        for period in entry.get("active_periods", []):
            start = period.get("start", "")
            end = period.get("end", "")

            if start:
                all_dates.append(start)
                year = start[:4]
                month = start[:7]
                yearly[year] = yearly.get(year, 0) + 1
                monthly[month] = monthly.get(month, 0) + 1

            if end:
                all_dates.append(end)

    if not all_dates:
        return {"earliest_project": None, "total_months_active": 0}

    earliest = min(all_dates)
    latest = max(all_dates)

    try:
        e = datetime.strptime(earliest, "%Y-%m-%d")
        l = datetime.strptime(latest, "%Y-%m-%d")
        total_months = (l.year - e.year) * 12 + (l.month - e.month)
    except ValueError:
        total_months = 0

    return {
        "earliest_project": earliest,
        "latest_activity": latest,
        "total_months_active": total_months,
        "total_projects": len(catalog_entries),
        "projects_by_year": dict(sorted(yearly.items())),
        "monthly_activity": dict(sorted(monthly.items())),
    }
