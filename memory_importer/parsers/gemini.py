"""Gemini (Google Takeout) export parser."""
import json
import re
from datetime import datetime
from pathlib import Path


def parse_gemini_takeout(takeout_dir: str | Path) -> list:
    """Parse Google Takeout Gemini export.

    Export via: takeout.google.com > Select 'Gemini Apps'
    Produces a folder with conversation HTML/JSON files.

    Args:
        takeout_dir: Path to extracted Takeout directory

    Returns:
        List of parsed conversation dicts
    """
    takeout_dir = Path(takeout_dir)
    conversations = []

    # Gemini exports as individual HTML or JSON files
    # Check for JSON conversations first
    json_files = list(takeout_dir.rglob("*.json"))
    html_files = list(takeout_dir.rglob("*.html"))

    for jf in json_files:
        try:
            data = json.loads(jf.read_text())
            parsed = _parse_gemini_json(data, jf.stem)
            if parsed:
                conversations.append(parsed)
        except (json.JSONDecodeError, OSError):
            continue

    # Fall back to HTML parsing if no JSON
    if not json_files and html_files:
        for hf in html_files:
            parsed = _parse_gemini_html(hf)
            if parsed:
                conversations.append(parsed)

    conversations.sort(key=lambda c: c["first_message_date"])
    return conversations


def _parse_gemini_json(data: dict, filename: str) -> dict | None:
    """Parse a single Gemini JSON conversation."""
    messages = []

    # Gemini JSON format varies; handle common structures
    entries = data if isinstance(data, list) else data.get("messages", data.get("entries", []))

    for entry in entries:
        if isinstance(entry, dict):
            role = entry.get("role", entry.get("author", "unknown"))
            text = entry.get("text", entry.get("content", ""))
            ts = entry.get("timestamp", entry.get("create_time"))

            if isinstance(text, list):
                text = " ".join(str(t) for t in text)

            if text:
                messages.append({
                    "role": "user" if role in ("user", "human") else "assistant",
                    "text": str(text).strip(),
                    "has_code": "```" in str(text),
                    "timestamp": ts,
                })

    if not messages:
        return None

    timestamps = [m["timestamp"] for m in messages if m["timestamp"]]
    first_date = min(timestamps) if timestamps else datetime.now().isoformat()
    last_date = max(timestamps) if timestamps else first_date

    return {
        "title": filename.replace("_", " ").replace("-", " ").title(),
        "provider": "gemini",
        "first_message_date": first_date,
        "last_message_date": last_date,
        "total_messages": len(messages),
        "user_messages": len([m for m in messages if m["role"] == "user"]),
        "assistant_messages": len([m for m in messages if m["role"] == "assistant"]),
        "has_code": any(m["has_code"] for m in messages),
        "messages": messages,
        "word_count": sum(len(m["text"].split()) for m in messages),
    }


def _parse_gemini_html(html_path: Path) -> dict | None:
    """Parse a Gemini HTML conversation export (basic extraction)."""
    try:
        content = html_path.read_text(errors="replace")
    except OSError:
        return None

    # Basic HTML text extraction
    text = re.sub(r'<[^>]+>', ' ', content)
    text = re.sub(r'\s+', ' ', text).strip()

    if len(text) < 50:
        return None

    # Extract any dates from filename
    date_match = re.search(r'(\d{4}[-_]\d{2}[-_]\d{2})', html_path.stem)
    if date_match:
        date_str = date_match.group(1).replace("_", "-")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    return {
        "title": html_path.stem.replace("_", " ").replace("-", " ").title(),
        "provider": "gemini",
        "first_message_date": f"{date_str}T12:00:00",
        "last_message_date": f"{date_str}T12:00:00",
        "total_messages": 1,
        "user_messages": 1,
        "assistant_messages": 0,
        "has_code": "```" in content or "<code>" in content,
        "messages": [{"role": "user", "text": text[:2000], "has_code": False, "timestamp": None}],
        "word_count": len(text.split()),
    }
