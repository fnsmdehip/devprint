"""ChatGPT export parser — processes conversations.json from data export."""
import json
from datetime import datetime
from pathlib import Path


def parse_chatgpt_export(export_path: str | Path) -> list:
    """Parse ChatGPT data export (conversations.json).

    To export: ChatGPT Settings > Data Controls > Export data
    You'll receive an email with a zip containing conversations.json.

    Args:
        export_path: Path to conversations.json

    Returns:
        List of parsed conversation dicts
    """
    export_path = Path(export_path)

    if export_path.suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(export_path) as zf:
            with zf.open("conversations.json") as f:
                raw = json.loads(f.read())
    else:
        raw = json.loads(export_path.read_text())

    conversations = []
    for conv in raw:
        parsed = _parse_conversation(conv)
        if parsed:
            conversations.append(parsed)

    # Sort by earliest message
    conversations.sort(key=lambda c: c["first_message_date"])
    return conversations


def _parse_conversation(conv: dict) -> dict | None:
    """Parse a single ChatGPT conversation."""
    title = conv.get("title", "Untitled")
    create_time = conv.get("create_time")
    update_time = conv.get("update_time")

    # Extract messages
    messages = []
    mapping = conv.get("mapping", {})

    for node_id, node in mapping.items():
        msg = node.get("message")
        if not msg:
            continue

        role = msg.get("author", {}).get("role", "unknown")
        content_parts = msg.get("content", {}).get("parts", [])
        create_ts = msg.get("create_time")

        # Flatten content parts to text
        text = ""
        has_code = False
        for part in content_parts:
            if isinstance(part, str):
                text += part + "\n"
                if "```" in part:
                    has_code = True
            elif isinstance(part, dict):
                # Image or other content type
                text += f"[{part.get('content_type', 'attachment')}]\n"

        if not text.strip():
            continue

        messages.append({
            "role": role,
            "text": text.strip(),
            "has_code": has_code,
            "timestamp": datetime.fromtimestamp(create_ts).isoformat() if create_ts else None,
        })

    if not messages:
        return None

    # Filter to meaningful messages (skip system)
    user_messages = [m for m in messages if m["role"] == "user"]
    assistant_messages = [m for m in messages if m["role"] == "assistant"]

    # Calculate dates
    timestamps = [m["timestamp"] for m in messages if m["timestamp"]]
    first_date = min(timestamps) if timestamps else None
    last_date = max(timestamps) if timestamps else None

    if not first_date:
        if create_time:
            first_date = datetime.fromtimestamp(create_time).isoformat()
        else:
            return None

    if not last_date:
        if update_time:
            last_date = datetime.fromtimestamp(update_time).isoformat()
        else:
            last_date = first_date

    return {
        "title": title,
        "provider": "chatgpt",
        "first_message_date": first_date,
        "last_message_date": last_date,
        "total_messages": len(messages),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "has_code": any(m["has_code"] for m in messages),
        "messages": messages,
        "word_count": sum(len(m["text"].split()) for m in messages),
    }
