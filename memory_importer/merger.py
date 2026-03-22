"""Merger — groups related conversations across sessions into single projects."""
import re
from collections import defaultdict
from datetime import datetime


def merge_related_conversations(classified_convs: list) -> list:
    """Group related conversations into unified project entries.

    Multiple ChatGPT sessions about the same topic → one project.

    Args:
        classified_convs: List of classified conversation dicts

    Returns:
        List of merged project groups, each containing related conversations
    """
    # Skip noise
    substantive = [c for c in classified_convs if c.get("classification", {}).get("category") != "NOISE"]

    if not substantive:
        return []

    # Build similarity graph
    groups = []
    used = set()

    for i, conv_a in enumerate(substantive):
        if i in used:
            continue

        group = [conv_a]
        used.add(i)

        for j, conv_b in enumerate(substantive):
            if j in used:
                continue
            if _are_related(conv_a, conv_b):
                group.append(conv_b)
                used.add(j)

        groups.append(group)

    # Merge each group into a single entry
    merged = []
    for group in groups:
        if len(group) == 1:
            merged.append(group[0])
        else:
            merged.append(_merge_group(group))

    return merged


def _are_related(conv_a: dict, conv_b: dict) -> bool:
    """Determine if two conversations are about the same project/topic."""
    title_a = conv_a.get("title", "").lower()
    title_b = conv_b.get("title", "").lower()

    # Same category?
    cat_a = conv_a.get("classification", {}).get("category", "")
    cat_b = conv_b.get("classification", {}).get("category", "")

    # Different categories are rarely the same project
    if cat_a != cat_b:
        return False

    # Title similarity
    words_a = set(_extract_keywords(title_a))
    words_b = set(_extract_keywords(title_b))

    if not words_a or not words_b:
        return False

    overlap = words_a & words_b
    union = words_a | words_b

    if not union:
        return False

    jaccard = len(overlap) / len(union)
    if jaccard > 0.4:
        return True

    # Check content keyword overlap
    text_a = " ".join(m.get("text", "")[:500] for m in conv_a.get("messages", [])[:3])
    text_b = " ".join(m.get("text", "")[:500] for m in conv_b.get("messages", [])[:3])

    kw_a = set(_extract_keywords(text_a.lower()))
    kw_b = set(_extract_keywords(text_b.lower()))

    if kw_a and kw_b:
        content_overlap = len(kw_a & kw_b) / max(len(kw_a), len(kw_b))
        if content_overlap > 0.3:
            return True

    # Check tech stack overlap
    tech_a = set(conv_a.get("tech_domains", []))
    tech_b = set(conv_b.get("tech_domains", []))
    if tech_a and tech_b and len(tech_a & tech_b) >= 2:
        # Shared tech + similar dates = likely related
        date_a = conv_a.get("first_message_date", "")[:10]
        date_b = conv_b.get("first_message_date", "")[:10]
        if date_a and date_b:
            try:
                da = datetime.strptime(date_a, "%Y-%m-%d")
                db = datetime.strptime(date_b, "%Y-%m-%d")
                if abs((da - db).days) < 30:
                    return True
            except ValueError:
                pass

    return False


def _merge_group(group: list) -> dict:
    """Merge a group of related conversations into one entry."""
    # Use the most descriptive title (longest non-generic)
    titles = [c.get("title", "") for c in group]
    best_title = max(titles, key=lambda t: len(t) if not _is_generic_title(t) else 0)

    # Earliest and latest dates
    first_dates = []
    last_dates = []
    for c in group:
        fd = c.get("first_message_date")
        ld = c.get("last_message_date")
        if fd:
            first_dates.append(fd)
        if ld:
            last_dates.append(ld)

    first_date = min(first_dates) if first_dates else datetime.now().isoformat()
    last_date = max(last_dates) if last_dates else first_date

    # Aggregate stats
    total_messages = sum(c.get("total_messages", 0) for c in group)
    total_words = sum(c.get("word_count", 0) for c in group)
    has_code = any(c.get("has_code", False) for c in group)

    # Merge all messages
    all_messages = []
    for c in group:
        all_messages.extend(c.get("messages", []))

    # Collect all providers
    providers = list(set(c.get("provider", "unknown") for c in group))

    # Use the most common classification
    cats = [c.get("classification", {}).get("category", "PROJECT") for c in group]
    category = max(set(cats), key=cats.count)

    # Merge tags
    all_tags = set()
    for c in group:
        all_tags.update(c.get("tags", []))

    merged = {
        "title": best_title,
        "provider": providers[0] if len(providers) == 1 else "multiple",
        "providers": providers,
        "first_message_date": first_date,
        "last_message_date": last_date,
        "total_messages": total_messages,
        "user_messages": sum(c.get("user_messages", 0) for c in group),
        "assistant_messages": sum(c.get("assistant_messages", 0) for c in group),
        "has_code": has_code,
        "messages": all_messages,
        "word_count": total_words,
        "classification": {
            "category": category,
            "confidence": max(c.get("classification", {}).get("confidence", 0) for c in group),
            "signals": [],
            "reasoning": f"Merged from {len(group)} related conversations",
        },
        "tags": list(all_tags),
        "merged_from": len(group),
        "merged_titles": titles,
    }

    return merged


def _extract_keywords(text: str) -> list:
    """Extract meaningful keywords from text."""
    # Remove stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "same", "different", "than", "too", "very",
        "just", "about", "also", "not", "no", "nor", "only", "own",
        "so", "up", "out", "if", "or", "and", "but", "how", "what",
        "when", "where", "who", "which", "that", "this", "these", "those",
        "it", "its", "i", "me", "my", "we", "our", "you", "your",
        "he", "him", "his", "she", "her", "they", "them", "their",
        "new", "chat", "untitled", "help", "make", "get", "use",
    }

    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    return [w for w in words if w not in stop_words]


def _is_generic_title(title: str) -> bool:
    """Check if a title is generic/uninformative."""
    generic = ["new chat", "untitled", "chat", "conversation", "help me", "question"]
    return title.lower().strip() in generic or len(title) < 5
