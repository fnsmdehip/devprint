"""Manual entry parser for AI providers without export (Claude, DeepSeek, Grok, Perplexity)."""
import json
import os
from datetime import datetime
from pathlib import Path

# Template for manual entries
MANUAL_TEMPLATE = """{
  "provider": "claude",
  "title": "Project Name or Research Topic",
  "category_hint": "project | research | strategy | learning",
  "approximate_dates": {
    "start": "2024-06-01",
    "end": "2024-09-15"
  },
  "description": "2-3 sentences about what this was",
  "tech_domains": ["python", "trading", "data-analysis"],
  "intensity": "high | medium | low",
  "estimated_sessions": 15,
  "key_outputs": [
    "Built a backtesting framework",
    "Developed signal processing pipeline",
    "Research into prediction market mechanics"
  ],
  "related_local_project": null,
  "tags": ["prediction", "quant", "research"]
}"""


def create_manual_template(output_dir: str | Path, provider: str = "claude") -> Path:
    """Create a manual entry template file.

    Returns path to the template file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    template = MANUAL_TEMPLATE.replace('"claude"', f'"{provider}"')
    filepath = output_dir / f"manual_entry_{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath.write_text(template)
    return filepath


def parse_manual_entries(entries_dir: str | Path) -> list:
    """Parse all manual entry JSON files in a directory.

    Args:
        entries_dir: Directory containing manual entry .json files

    Returns:
        List of parsed conversation-like dicts (compatible with classifier)
    """
    entries_dir = Path(entries_dir)
    conversations = []

    for f in sorted(entries_dir.glob("manual_entry_*.json")):
        try:
            data = json.loads(f.read_text())
            parsed = _parse_manual_entry(data)
            if parsed:
                conversations.append(parsed)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [WARN] Failed to parse {f.name}: {e}")
            continue

    return conversations


def _parse_manual_entry(data: dict) -> dict | None:
    """Convert a manual entry to the standard conversation format."""
    title = data.get("title", "Untitled")
    provider = data.get("provider", "unknown")
    dates = data.get("approximate_dates", {})
    start_date = dates.get("start", datetime.now().strftime("%Y-%m-%d"))
    end_date = dates.get("end", start_date)

    description = data.get("description", "")
    key_outputs = data.get("key_outputs", [])
    estimated_sessions = data.get("estimated_sessions", 1)

    # Reconstruct a pseudo-conversation for the classifier
    text = f"{title}\n\n{description}\n\n"
    text += "Key outputs:\n"
    for output in key_outputs:
        text += f"- {output}\n"

    # Estimate word count based on sessions
    est_word_count = estimated_sessions * 500  # ~500 words per session average

    return {
        "title": title,
        "provider": provider,
        "first_message_date": f"{start_date}T12:00:00",
        "last_message_date": f"{end_date}T12:00:00",
        "total_messages": estimated_sessions * 10,  # Rough estimate
        "user_messages": estimated_sessions * 5,
        "assistant_messages": estimated_sessions * 5,
        "has_code": any(
            kw in description.lower()
            for kw in ["code", "build", "implement", "script", "api", "function", "class"]
        ),
        "messages": [{
            "role": "user",
            "text": text,
            "has_code": False,
            "timestamp": f"{start_date}T12:00:00",
        }],
        "word_count": est_word_count,
        "manual_entry": True,
        "category_hint": data.get("category_hint"),
        "tech_domains": data.get("tech_domains", []),
        "intensity": data.get("intensity", "medium"),
        "related_local_project": data.get("related_local_project"),
        "tags": data.get("tags", []),
    }


def generate_batch_template(output_path: str | Path, count: int = 5, provider: str = "claude") -> Path:
    """Generate a batch template with multiple empty entries.

    Useful for quickly entering several projects from one provider.
    """
    output_path = Path(output_path)
    entries = []

    for i in range(count):
        entries.append({
            "provider": provider,
            "title": f"Project {i + 1} — REPLACE THIS",
            "category_hint": "project",
            "approximate_dates": {"start": "2024-01-01", "end": "2024-03-01"},
            "description": "Describe what this project/research was about",
            "tech_domains": [],
            "intensity": "medium",
            "estimated_sessions": 5,
            "key_outputs": ["Output 1", "Output 2"],
            "related_local_project": None,
            "tags": [],
        })

    output_path.write_text(json.dumps(entries, indent=2))
    return output_path
