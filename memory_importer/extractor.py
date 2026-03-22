"""Extractor — pulls structured project data from classified conversations."""
import re
from datetime import datetime
from pathlib import Path


def extract_project_data(conv: dict) -> dict:
    """Extract structured project/research data from a classified conversation.

    Args:
        conv: Classified conversation dict

    Returns:
        Catalog-compatible entry dict
    """
    classification = conv.get("classification", {})
    category = classification.get("category", "PROJECT")

    # Map classification to catalog category
    cat_map = {
        "PROJECT": "project",
        "RESEARCH": "research",
        "STRATEGY": "strategy",
        "LEARNING": "learning",
    }

    # Extract tech domains from conversation text
    all_text = " ".join(m.get("text", "") for m in conv.get("messages", []))
    tech_stack = _detect_tech(all_text)
    if conv.get("tech_domains"):
        tech_stack = list(set(tech_stack + conv["tech_domains"]))

    # Generate slug from title
    title = conv.get("title", "untitled")
    slug = _slugify(title)

    # Extract code snippets
    code_snippets = _extract_code_blocks(all_text)

    # Build entry
    entry = {
        "id": slug,
        "name": _titleize(title),
        "tagline": _generate_tagline(conv, category),
        "description": _generate_description(conv),
        "category": cat_map.get(category, "project"),
        "subcategory": _infer_subcategory(all_text, category),
        "tech_stack": tech_stack,
        "source_type": "ai_native",
        "local_path": conv.get("related_local_project"),
        "has_existing_git": False,
        "github_repo": None,
        "active_periods": [{
            "start": conv["first_message_date"][:10],
            "end": conv["last_message_date"][:10],
            "intensity": conv.get("intensity", _estimate_intensity(conv)),
        }],
        "ai_providers_used": [conv.get("provider", "unknown")],
        "proof": {
            "filesystem_timestamps": False,
            "ai_export_available": not conv.get("manual_entry", False),
            "surge_deploys": False,
            "confidence": "medium" if not conv.get("manual_entry") else "self-reported",
        },
        "metrics": {
            "conversation_count": 1,
            "message_count": conv.get("total_messages", 0),
            "word_count": conv.get("word_count", 0),
            "code_snippets": len(code_snippets),
        },
        "portfolio_priority": _estimate_priority(conv, category),
        "content_angles": _generate_content_angles(conv, category),
        "tags": conv.get("tags", []) + _extract_tags(all_text),
        "_code_snippets": code_snippets[:10],  # Keep for repo generation
        "_raw_conversation": conv,  # Keep reference
    }

    return entry


def _detect_tech(text: str) -> list:
    """Detect technologies mentioned in text."""
    tech_patterns = {
        "python": r'\bpython\b',
        "javascript": r'\bjavascript\b|\bjs\b',
        "typescript": r'\btypescript\b|\bts\b',
        "react": r'\breact\b',
        "node": r'\bnode\.?js\b|\bnode\b',
        "fastapi": r'\bfastapi\b',
        "flask": r'\bflask\b',
        "django": r'\bdjango\b',
        "express": r'\bexpress\b',
        "nextjs": r'\bnext\.?js\b',
        "vue": r'\bvue\b',
        "tailwind": r'\btailwind\b',
        "postgresql": r'\bpostgres\b|\bpostgresql\b',
        "mongodb": r'\bmongo\b',
        "sqlite": r'\bsqlite\b',
        "redis": r'\bredis\b',
        "docker": r'\bdocker\b',
        "aws": r'\baws\b',
        "gcp": r'\bgcp\b|\bgoogle cloud\b',
        "stripe": r'\bstripe\b',
        "openai": r'\bopenai\b|\bgpt\b',
        "langchain": r'\blangchain\b',
        "pytorch": r'\bpytorch\b|\btorch\b',
        "tensorflow": r'\btensorflow\b',
        "scikit-learn": r'\bscikit\b|\bsklearn\b',
    }

    found = []
    text_lower = text.lower()
    for tech, pattern in tech_patterns.items():
        if re.search(pattern, text_lower):
            found.append(tech)
    return found


def _extract_code_blocks(text: str) -> list:
    """Extract code blocks from conversation text."""
    pattern = r'```(?:\w+)?\n(.*?)```'
    blocks = re.findall(pattern, text, re.DOTALL)
    return [b.strip() for b in blocks if len(b.strip()) > 20]


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:60]


def _titleize(text: str) -> str:
    """Clean up a title string."""
    # Remove common ChatGPT title artifacts
    text = re.sub(r'^(New chat|Untitled)\s*[-:]?\s*', '', text, flags=re.IGNORECASE)
    if not text:
        return "Untitled Project"
    return text.strip().title()


def _generate_tagline(conv: dict, category: str) -> str:
    """Generate a one-line tagline from conversation content."""
    title = conv.get("title", "")
    provider = conv.get("provider", "AI")

    if category == "RESEARCH":
        return f"Research exploration: {title}"
    elif category == "STRATEGY":
        return f"Business strategy: {title}"
    elif category == "LEARNING":
        return f"Learning journey: {title}"

    msg_count = conv.get("total_messages", 0)
    if msg_count > 50:
        return f"In-depth {provider.title()} collaborative project: {title}"
    return f"AI-collaborative project: {title}"


def _generate_description(conv: dict) -> str:
    """Generate a description from conversation metadata."""
    parts = []
    provider = conv.get("provider", "AI").title()
    msg_count = conv.get("total_messages", 0)
    word_count = conv.get("word_count", 0)

    parts.append(f"Developed through {msg_count} messages with {provider}")
    if word_count > 5000:
        parts.append(f"spanning {word_count:,} words of collaborative dialogue")

    if conv.get("has_code"):
        parts.append("including code implementation")

    return ". ".join(parts) + "."


def _estimate_intensity(conv: dict) -> str:
    """Estimate project intensity from conversation stats."""
    msg_count = conv.get("total_messages", 0)
    word_count = conv.get("word_count", 0)

    if msg_count > 50 or word_count > 10000:
        return "high"
    elif msg_count > 15 or word_count > 3000:
        return "medium"
    return "low"


def _estimate_priority(conv: dict, category: str) -> int:
    """Estimate portfolio priority (1=highest, 5=lowest)."""
    msg_count = conv.get("total_messages", 0)
    has_code = conv.get("has_code", False)

    if has_code and msg_count > 30:
        return 2
    if category == "RESEARCH" and msg_count > 20:
        return 2
    if has_code:
        return 3
    if category in ("RESEARCH", "STRATEGY"):
        return 3
    return 4


def _infer_subcategory(text: str, category: str) -> str:
    """Infer subcategory from text content."""
    text_lower = text.lower()

    if category == "RESEARCH":
        if any(w in text_lower for w in ["longevity", "aging", "health", "biohack"]):
            return "longevity-research"
        if any(w in text_lower for w in ["physics", "quantum", "cosmolog"]):
            return "physics-research"
        if any(w in text_lower for w in ["prediction", "forecast", "polymarket"]):
            return "prediction-research"
        if any(w in text_lower for w in ["psycholog", "cogniti", "conscious"]):
            return "cognitive-science"
        return "general-research"

    if category == "PROJECT":
        if any(w in text_lower for w in ["bot", "scraper", "automation"]):
            return "automation"
        if any(w in text_lower for w in ["api", "backend", "server"]):
            return "backend"
        if any(w in text_lower for w in ["react", "frontend", "ui", "dashboard"]):
            return "frontend"
        if any(w in text_lower for w in ["mobile", "app", "expo", "react native"]):
            return "mobile-app"
        if any(w in text_lower for w in ["agent", "orchestrat", "swarm"]):
            return "ai-agents"
        return "general"

    return "general"


def _generate_content_angles(conv: dict, category: str) -> list:
    """Generate content marketing angles from the project."""
    angles = []
    title = conv.get("title", "this project")
    provider = conv.get("provider", "AI").title()

    if category == "PROJECT":
        angles.append(f"How I built {title} with {provider}")
        if conv.get("has_code"):
            angles.append(f"Code walkthrough: {title}")
    elif category == "RESEARCH":
        angles.append(f"Deep dive: what I learned researching {title}")
        angles.append(f"Key findings from {conv.get('total_messages', 'many')} sessions on {title}")
    elif category == "STRATEGY":
        angles.append(f"Business strategy breakdown: {title}")

    return angles


def _extract_tags(text: str) -> list:
    """Extract relevant tags from text."""
    tag_patterns = {
        "ai": r'\b(ai|artificial intelligence|machine learning|ml)\b',
        "crypto": r'\b(crypto|bitcoin|ethereum|defi|token)\b',
        "web3": r'\b(web3|blockchain|nft|smart contract)\b',
        "health": r'\b(health|wellness|nutrition|fitness)\b',
        "fintech": r'\b(fintech|finance|trading|investment)\b',
        "saas": r'\b(saas|subscription|recurring)\b',
        "automation": r'\b(automat|bot|scraper|pipeline)\b',
    }

    found = []
    text_lower = text.lower()
    for tag, pattern in tag_patterns.items():
        if re.search(pattern, text_lower):
            found.append(tag)
    return found
