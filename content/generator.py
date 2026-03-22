"""Content generator — creates multi-platform content from catalog entries."""
import json
from datetime import datetime
from pathlib import Path

from config import CONTENT_OUTPUT_DIR


def generate_all_content(entry: dict, portfolio_url: str = "") -> dict:
    """Generate all content types for a catalog entry.

    Returns:
        {
            "substack": str,
            "twitter_thread": str,
            "linkedin": str,
            "video_script": str,
            "github_readme": str,
        }
    """
    name = entry.get("name", "Project")
    tagline = entry.get("tagline", "")
    description = entry.get("description", "")
    tech_stack = entry.get("tech_stack", [])
    tags = entry.get("tags", [])
    angles = entry.get("content_angles", [])
    ai_tools = ", ".join(entry.get("ai_providers_used", []))
    metrics = entry.get("metrics", {})
    periods = entry.get("active_periods", [])

    # Calculate months active
    months = 0
    if periods:
        try:
            s = datetime.strptime(periods[0].get("start", "2025-01-01"), "%Y-%m-%d")
            e = datetime.strptime(periods[0].get("end", "2026-01-01"), "%Y-%m-%d")
            months = max(1, (e.year - s.year) * 12 + (e.month - s.month))
        except ValueError:
            months = 6

    tech_list = ", ".join(tech_stack[:5])
    file_count = metrics.get("file_count", 0)

    content = {}

    # --- Substack Article Draft ---
    content["substack"] = f"""# How I Built {name}

*{tagline}*

---

{months} months of development. {f'{file_count:,} files.' if file_count else ''} {tech_list} under the hood.

## What It Does

{description if description else tagline}

## The Tech Stack

{chr(10).join(f'- **{t}**' for t in tech_stack)}

## Key Highlights

{chr(10).join(f'- {a}' for a in angles) if angles else '- Built through AI-native pair programming'}

## The AI Collaboration

This was built through sustained pair programming with {ai_tools}. Not just asking questions — full architectural decisions, implementation, debugging, and iteration.

## What's Next

This is one of 20+ projects I've built over 18+ months of AI-native development. Follow for weekly deep dives.

*View the full portfolio with proof of work at {portfolio_url}*
"""

    # --- Twitter/X Thread ---
    content["twitter_thread"] = f"""🧵 I built {name} — {tagline}

Here's the breakdown:

---

Tweet 1:
I built {name} — {tagline}

Here's what it does and how I built it 🧵

---

Tweet 2:
{angles[0] if angles else description}

---

Tweet 3:
Tech stack:
{chr(10).join(f'• {t}' for t in tech_stack[:6])}

Built with {ai_tools}.

---

Tweet 4:
{f'By the numbers: {file_count:,} files, {months} months of development' if file_count else f'{months} months of focused development'}

---

Tweet 5:
This is one of 20+ projects I've built in 18+ months of AI-native development.

Full portfolio with proof of work: {portfolio_url}

Follow for more builds 🚀
"""

    # --- LinkedIn Post ---
    content["linkedin"] = f"""I've been building with AI for 18+ months. Not just chatting — shipping real products.

{name}: {tagline}

{description if description else tagline}

Technologies: {tech_list}

{chr(10).join(f'→ {a}' for a in angles[:3]) if angles else ''}

This is one of 20+ projects in my verified portfolio. Every project has proof of work — filesystem timestamps, AI export records, and git history that corroborates the timeline.

The future of development is human-AI collaboration. I'm living proof.

Portfolio: {portfolio_url}

#AIEngineering #BuildInPublic #AgenticCoding #SoftwareEngineering
"""

    # --- Video Script ---
    content["video_script"] = f"""60-SECOND VIDEO SCRIPT: {name}

HOOK (0-3s):
[Screen recording of {name} in action]
Text: "{tagline}"

CONTEXT (3-13s):
"I built {name} using {ai_tools} over {months} months."
[Show code editor, terminal]

DEMO (13-43s):
[Screen recording showing key features]
{chr(10).join(f'- Show: {a}' for a in angles[:3]) if angles else '- Show the project running'}

RESULTS (43-53s):
Stats on screen:
{f'- {file_count:,} files' if file_count else ''}
- {months} months of development
- Built with {ai_tools}

CTA (53-60s):
"Follow for more AI-native builds. Full portfolio in bio."
"""

    # --- GitHub README ---
    period_str = f"{periods[0].get('start', 'N/A')} to {periods[0].get('end', 'N/A')}" if periods else "N/A"
    content["github_readme"] = f"""# {name}

{tagline}

## Overview

{description if description else tagline}

## Tech Stack

{chr(10).join(f'- **{t}**' for t in tech_stack)}

## Highlights

{chr(10).join(f'- {a}' for a in angles) if angles else ''}

## Project History

- **Active Period:** {period_str}
- **Built with:** AI pair programming ({ai_tools})
- **Source:** [Verified portfolio]({portfolio_url})

---

*Part of [DEVPRINT]({portfolio_url}) — 20+ projects built through AI-native development*
"""

    return content


def save_content(entry_id: str, content: dict) -> dict:
    """Save generated content to output directory.

    Returns:
        {"files": {"substack": path, "twitter": path, ...}}
    """
    project_dir = CONTENT_OUTPUT_DIR / entry_id
    project_dir.mkdir(parents=True, exist_ok=True)

    files = {}
    for content_type, text in content.items():
        filename = f"{content_type}.md"
        filepath = project_dir / filename
        filepath.write_text(text)
        files[content_type] = str(filepath)

    return {"files": files}


def generate_content_calendar(catalog_entries: list, days: int = 30) -> list:
    """Generate a 30-day content calendar from catalog entries.

    Returns:
        List of {"day": int, "platform": str, "content_type": str, "project_id": str, "angle": str}
    """
    calendar = []

    # Sort projects by priority
    projects = sorted(catalog_entries, key=lambda e: e.get("portfolio_priority", 5))

    day = 1
    project_idx = 0

    while day <= days:
        project = projects[project_idx % len(projects)]
        angles = project.get("content_angles", ["Project overview"])
        angle = angles[(day // 7) % len(angles)] if angles else "Overview"

        # Monday: Substack article
        if day % 7 == 1:
            calendar.append({
                "day": day,
                "weekday": "Monday",
                "platform": "Substack",
                "content_type": "Long-form article",
                "project_id": project["id"],
                "project_name": project["name"],
                "angle": angle,
            })
            project_idx += 1

        # Tuesday, Thursday: Twitter threads
        elif day % 7 in (2, 4):
            calendar.append({
                "day": day,
                "weekday": "Tuesday" if day % 7 == 2 else "Thursday",
                "platform": "X / Twitter",
                "content_type": "Thread (5-8 tweets)",
                "project_id": project["id"],
                "project_name": project["name"],
                "angle": angle,
            })

        # Wednesday, Friday: Short-form video
        elif day % 7 in (3, 5):
            calendar.append({
                "day": day,
                "weekday": "Wednesday" if day % 7 == 3 else "Friday",
                "platform": "TikTok / Reels / Shorts",
                "content_type": "60-second video",
                "project_id": project["id"],
                "project_name": project["name"],
                "angle": angle,
            })

        # Saturday: LinkedIn
        elif day % 7 == 6:
            calendar.append({
                "day": day,
                "weekday": "Saturday",
                "platform": "LinkedIn",
                "content_type": "Professional post",
                "project_id": project["id"],
                "project_name": project["name"],
                "angle": angle,
            })

        day += 1

    return calendar
