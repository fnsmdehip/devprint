"""Conversation classifier — categorizes AI chat exports into project types."""
import re
from datetime import datetime


# Classification categories
CATEGORIES = {
    "PROJECT": "Sustained coding/building work → individual repo",
    "RESEARCH": "Deep exploration of a topic → research repo",
    "STRATEGY": "Business planning, market analysis → project repo or standalone",
    "LEARNING": "Tutorials, skill-building → learning-log repo",
    "NOISE": "Quick lookups, factual questions → skip",
}

# Keyword patterns for each category
PROJECT_SIGNALS = [
    r'\bbuild\b', r'\bcreate\b', r'\bimplement\b', r'\bcode\b', r'\bfunction\b',
    r'\bclass\b', r'\bapi\b', r'\bapp\b', r'\bdeploy\b', r'\bserver\b',
    r'\bdatabase\b', r'\bfrontend\b', r'\bbackend\b', r'\breact\b', r'\bpython\b',
    r'\bjavascript\b', r'\btypescript\b', r'\bnode\b', r'\bfastapi\b', r'\bflask\b',
    r'\bdjango\b', r'\bnext\.?js\b', r'\bvite\b', r'\bwebsite\b', r'\bscrip[t]\b',
    r'\bautomation\b', r'\bbot\b', r'\bscraper\b', r'\bcrawler\b', r'\bagent\b',
    r'\borchestrat\b', r'\bpipeline\b', r'\bworkflow\b', r'\bintegrat\b',
    r'\bstripe\b', r'\bauth\b', r'\blogin\b', r'\bdashboard\b',
]

RESEARCH_SIGNALS = [
    r'\blongevity\b', r'\bbiohacking\b', r'\bhealth\b', r'\bsupplement\b',
    r'\bpeptide\b', r'\bnootropic\b', r'\bfasting\b', r'\bmetformin\b',
    r'\brapamycin\b', r'\btelomere\b', r'\bmitochondri\b', r'\bsenescen\b',
    r'\bphysics\b', r'\bquantum\b', r'\bcosmolog\b', r'\btheory\b',
    r'\bhypothes[ie]s\b', r'\bresearch\b', r'\bstudy\b', r'\bpaper\b',
    r'\bevidence\b', r'\bmeta-analysis\b', r'\btrial\b', r'\bexperiment\b',
    r'\bprediction market\b', r'\bpolymarket\b', r'\bmetaculus\b', r'\bmanifold\b',
    r'\bprobability\b', r'\bcalibration\b', r'\bforecast\b', r'\bbayes\b',
    r'\bpsycholog\b', r'\bneuroscien\b', r'\bcogniti\b', r'\bconsciousness\b',
    r'\bevolution\b', r'\banthropolog\b', r'\bhistor\b', r'\bphilosoph\b',
    r'\beconomic\b', r'\bmacro\b', r'\bgeopolitic\b',
]

STRATEGY_SIGNALS = [
    r'\bbusiness\b', r'\bmarket\b', r'\brevenue\b', r'\bprofit\b', r'\bmonetiz\b',
    r'\bstrategy\b', r'\bcompetitor\b', r'\btarget audience\b', r'\bcustomer\b',
    r'\bpricing\b', r'\bgrowth\b', r'\bscal\b', r'\bfundrais\b', r'\binvestor\b',
    r'\bpitch\b', r'\bbusiness model\b', r'\bvalue prop\b', r'\bgo.to.market\b',
    r'\bsaas\b', r'\barr\b', r'\bmrr\b', r'\bcac\b', r'\bltv\b',
    r'\bbrand\b', r'\bmarketing\b', r'\bcontent strategy\b', r'\bseo\b',
    r'\bsocial media\b', r'\bemail\b', r'\bfunnel\b', r'\bconversion\b',
]

LEARNING_SIGNALS = [
    r'\bhow (do|to|does)\b', r'\btutorial\b', r'\bexplain\b', r'\bwhat is\b',
    r'\blearn\b', r'\bcourse\b', r'\bguide\b', r'\bstep.by.step\b',
    r'\bexample\b', r'\bshow me\b', r'\bteach\b',
]

NOISE_SIGNALS = [
    r'\bwhat time\b', r'\bwhen does\b', r'\bhours\b', r'\bopen\b',
    r'\bweather\b', r'\bdirections\b', r'\brecipe\b', r'\bwhat.*restaurant\b',
    r'\btranslate\b', r'\bconvert\b.*\bunits?\b', r'\bdefine\b',
    r'\bwhat.*mean\b', r'\bphone number\b', r'\baddress\b',
]


def classify_conversation(conv: dict) -> dict:
    """Classify a single conversation.

    Args:
        conv: Parsed conversation dict from any parser

    Returns:
        Same dict with added 'classification' field:
        {
            "category": "PROJECT" | "RESEARCH" | "STRATEGY" | "LEARNING" | "NOISE",
            "confidence": 0.0-1.0,
            "signals": ["matched keywords..."],
            "reasoning": "explanation",
        }
    """
    # If manual entry has a category hint, use it with high confidence
    if conv.get("manual_entry") and conv.get("category_hint"):
        hint_map = {
            "project": "PROJECT",
            "research": "RESEARCH",
            "strategy": "STRATEGY",
            "learning": "LEARNING",
        }
        category = hint_map.get(conv["category_hint"].lower(), "PROJECT")
        conv["classification"] = {
            "category": category,
            "confidence": 0.95,
            "signals": ["manual_entry_hint"],
            "reasoning": f"Manual entry with category hint: {conv['category_hint']}",
        }
        return conv

    # Combine all message text for analysis
    all_text = ""
    for msg in conv.get("messages", []):
        all_text += msg.get("text", "") + " "
    all_text = all_text.lower()

    title = conv.get("title", "").lower()
    full_text = title + " " + all_text

    # Score each category
    scores = {
        "PROJECT": _score_category(full_text, PROJECT_SIGNALS),
        "RESEARCH": _score_category(full_text, RESEARCH_SIGNALS),
        "STRATEGY": _score_category(full_text, STRATEGY_SIGNALS),
        "LEARNING": _score_category(full_text, LEARNING_SIGNALS),
        "NOISE": _score_category(full_text, NOISE_SIGNALS),
    }

    # Boost PROJECT if code is present
    if conv.get("has_code"):
        scores["PROJECT"] += 3.0

    # Boost based on conversation length
    msg_count = conv.get("total_messages", 0)
    word_count = conv.get("word_count", 0)

    if msg_count <= 3:
        scores["NOISE"] += 2.0
    elif msg_count >= 10:
        # Long conversations are usually substantive
        scores["NOISE"] -= 2.0
        if not conv.get("has_code"):
            scores["RESEARCH"] += 1.0

    if word_count < 100:
        scores["NOISE"] += 3.0

    # Find winner
    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    total_score = sum(scores.values()) or 1

    # Calculate confidence (how dominant is the winner?)
    confidence = min(0.95, best_score / total_score) if total_score > 0 else 0.5

    # If it's very close between categories, lower confidence
    sorted_scores = sorted(scores.values(), reverse=True)
    if len(sorted_scores) >= 2 and sorted_scores[0] - sorted_scores[1] < 1.0:
        confidence *= 0.7

    # Collect matched signals for transparency
    matched_signals = []
    if best_category == "PROJECT":
        matched_signals = _find_matches(full_text, PROJECT_SIGNALS)
    elif best_category == "RESEARCH":
        matched_signals = _find_matches(full_text, RESEARCH_SIGNALS)
    elif best_category == "STRATEGY":
        matched_signals = _find_matches(full_text, STRATEGY_SIGNALS)
    elif best_category == "LEARNING":
        matched_signals = _find_matches(full_text, LEARNING_SIGNALS)
    elif best_category == "NOISE":
        matched_signals = _find_matches(full_text, NOISE_SIGNALS)

    conv["classification"] = {
        "category": best_category,
        "confidence": round(confidence, 3),
        "signals": matched_signals[:10],
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "reasoning": _generate_reasoning(best_category, msg_count, word_count, conv.get("has_code", False)),
    }

    return conv


def classify_batch(conversations: list) -> dict:
    """Classify a batch of conversations and return summary.

    Returns:
        {
            "classified": [conv, ...],
            "summary": {"PROJECT": N, "RESEARCH": N, ...},
            "by_category": {"PROJECT": [conv, ...], ...},
        }
    """
    classified = [classify_conversation(conv) for conv in conversations]

    summary = {"PROJECT": 0, "RESEARCH": 0, "STRATEGY": 0, "LEARNING": 0, "NOISE": 0}
    by_category = {"PROJECT": [], "RESEARCH": [], "STRATEGY": [], "LEARNING": [], "NOISE": []}

    for conv in classified:
        cat = conv["classification"]["category"]
        summary[cat] += 1
        by_category[cat].append(conv)

    return {
        "classified": classified,
        "summary": summary,
        "by_category": by_category,
    }


def _score_category(text: str, patterns: list) -> float:
    """Score text against a list of regex patterns."""
    score = 0.0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        score += len(matches) * 0.5
    return score


def _find_matches(text: str, patterns: list) -> list:
    """Find all matching keywords in text."""
    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        matches.extend(found)
    return list(set(matches))


def _generate_reasoning(category: str, msg_count: int, word_count: int, has_code: bool) -> str:
    """Generate human-readable reasoning for classification."""
    parts = [f"Classified as {category}"]

    if category == "PROJECT":
        if has_code:
            parts.append("code blocks detected")
        parts.append(f"{msg_count} messages suggest sustained work")
    elif category == "RESEARCH":
        parts.append(f"deep topic exploration ({word_count} words)")
    elif category == "STRATEGY":
        parts.append("business/market language detected")
    elif category == "LEARNING":
        parts.append("tutorial/learning pattern detected")
    elif category == "NOISE":
        if msg_count <= 3:
            parts.append(f"only {msg_count} messages")
        if word_count < 100:
            parts.append(f"only {word_count} words")

    return "; ".join(parts)
