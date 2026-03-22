"""Filesystem scanner that auto-generates catalog entries from Documents/."""
import json
import os
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from config import (
    CATALOG_DIR,
    CODE_EXTENSIONS,
    DOCUMENTS_DIR,
    SKIP_DIRS,
    SKIP_EXTENSIONS,
    SKIP_PROJECTS,
)


# Known project mappings (discovered from exploration)
KNOWN_PROJECTS = {
    "p/PRINTMAXX_STARTER_KITttttt": {
        "id": "printmaxx-starter-kit",
        "name": "PRINTMAXX Starter Kit",
        "tagline": "Autonomous revenue system with 33 agents and 114 deployed apps",
        "category": "project",
        "subcategory": "autonomous-system",
        "tech_stack": ["python", "node", "react-native", "expo", "fastapi", "sqlite", "remotion", "ffmpeg"],
        "ai_providers_used": ["chatgpt", "claude", "cursor", "deepseek"],
        "portfolio_priority": 1,
        "content_angles": [
            "Built an autonomous business system with 33 AI agents",
            "114 apps deployed via automated surge pipeline",
            "From zero to autonomous revenue infrastructure in 12 months",
            "Multi-venture orchestration: one system managing 8+ business verticals"
        ],
        "tags": ["autonomous", "multi-agent", "revenue", "automation", "saas", "print-on-demand", "content-generation"],
    },
    "predicting": {
        "id": "sigcraft",
        "name": "SIGCRAFT",
        "tagline": "Self-improving signal intelligence engine with 22+ data sources",
        "category": "project",
        "subcategory": "prediction-engine",
        "tech_stack": ["python", "fastapi", "sqlite", "scikit-learn", "scipy", "pymc", "aiohttp"],
        "ai_providers_used": ["claude", "cursor"],
        "portfolio_priority": 1,
        "content_angles": [
            "Built a prediction engine that scores itself against reality",
            "22+ data sources: crypto, prediction markets, news, SEC filings, social media",
            "Auto-reweighting calibration: the system learns which methods work",
            "Kelly criterion position sizing for real trading signals"
        ],
        "tags": ["prediction", "quant", "signals", "calibration", "crypto", "polymarket", "bayesian"],
    },
    "soundgrep": {
        "id": "soundgrep",
        "name": "Soundgrep",
        "tagline": "Multi-agent music production daemon with Ableton Live integration",
        "category": "project",
        "subcategory": "creative-tools",
        "tech_stack": ["python", "fastapi", "react", "vite", "sqlite", "faiss", "librosa", "essentia", "pytorch"],
        "ai_providers_used": ["claude", "cursor"],
        "portfolio_priority": 1,
        "content_angles": [
            "6 specialist AI agents that collaborate to produce music",
            "Semantic sample search: describe a sound, find it instantly via CLAP embeddings",
            "Hum a melody, get MIDI: voice-to-composition pipeline",
            "Runs as a daemon alongside Ableton Live"
        ],
        "tags": ["music", "audio", "multi-agent", "ableton", "embeddings", "creative-ai"],
    },
    "NutriAI": {
        "id": "nutriai",
        "name": "NutriAI",
        "tagline": "AI-powered mobile nutrition tracking with camera and health kit integration",
        "category": "project",
        "subcategory": "mobile-app",
        "tech_stack": ["react-native", "expo", "typescript", "redux"],
        "ai_providers_used": ["chatgpt", "cursor"],
        "portfolio_priority": 2,
        "content_angles": [
            "Mobile app that identifies food from photos and tracks nutrition",
            "Health kit integration syncs with Apple Health and Google Fit"
        ],
        "tags": ["mobile", "health", "nutrition", "react-native", "expo", "ai-vision"],
    },
    "marketingpro": {
        "id": "marketingpro",
        "name": "MarketingPro",
        "tagline": "Full-stack SaaS platform with Stripe billing and real-time analytics",
        "category": "project",
        "subcategory": "saas",
        "tech_stack": ["typescript", "express", "react", "vite", "postgresql", "drizzle", "stripe", "radix-ui"],
        "ai_providers_used": ["chatgpt", "cursor"],
        "portfolio_priority": 2,
        "content_angles": [
            "Full-stack SaaS from zero: auth, billing, dashboards, analytics",
            "Stripe integration with subscription management",
            "Modern stack: React + Express + PostgreSQL + Drizzle ORM"
        ],
        "tags": ["saas", "fullstack", "stripe", "typescript", "postgresql", "marketing"],
    },
    "cro ai": {
        "id": "cro-ai",
        "name": "CRO AI",
        "tagline": "AI-powered conversion rate optimization analytics dashboard",
        "category": "project",
        "subcategory": "analytics",
        "tech_stack": ["typescript", "vite", "tailwind"],
        "ai_providers_used": ["chatgpt", "cursor"],
        "portfolio_priority": 2,
        "content_angles": [
            "Automated A/B test analysis and conversion optimization",
            "Dashboard for tracking and improving website conversion rates"
        ],
        "tags": ["analytics", "cro", "dashboard", "optimization", "marketing"],
    },
    "ancestry-research": {
        "id": "before-you-venture",
        "name": "Before You Venture",
        "tagline": "Business idea validation framework with generator and templates",
        "category": "project",
        "subcategory": "business-tools",
        "tech_stack": ["node", "html", "css"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": [
            "Framework for validating business ideas before investing time",
            "Includes idea generator, templates, and landing page"
        ],
        "tags": ["business", "validation", "framework", "entrepreneurship"],
    },
    "autoreplyai_project": {
        "id": "autoreplyai",
        "name": "AutoReplyAI",
        "tagline": "Intelligent email auto-reply system",
        "category": "project",
        "subcategory": "automation",
        "tech_stack": ["node"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": ["AI-powered email response automation"],
        "tags": ["email", "automation", "ai", "productivity"],
    },
    "claimwatch_v2": {
        "id": "claimwatch-v2",
        "name": "ClaimWatch V2",
        "tagline": "Claims management and tracking system",
        "category": "project",
        "subcategory": "business-tools",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": ["Automated claims tracking and management"],
        "tags": ["claims", "tracking", "business", "automation"],
    },
    "memescan-bot": {
        "id": "memescan-bot",
        "name": "Memescan Bot",
        "tagline": "Meme token detection and scanning bot",
        "category": "project",
        "subcategory": "crypto-tools",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": [
            "Automated meme coin detection and analysis",
            "Early signal detection for new token launches"
        ],
        "tags": ["crypto", "meme-coins", "detection", "trading", "bot"],
    },
    "terminal agent": {
        "id": "terminal-agent",
        "name": "Terminal Agent",
        "tagline": "AI-powered terminal automation tool",
        "category": "project",
        "subcategory": "developer-tools",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": ["Autonomous terminal command execution via AI agent"],
        "tags": ["terminal", "agent", "automation", "cli", "developer-tools"],
    },
    "local_ai_stack": {
        "id": "local-ai-stack",
        "name": "Local AI Stack",
        "tagline": "On-device LLM infrastructure and inference setup",
        "category": "project",
        "subcategory": "infrastructure",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": [
            "Running LLMs locally: on-device inference infrastructure",
            "Privacy-first AI: no cloud dependency"
        ],
        "tags": ["local-ai", "llm", "inference", "privacy", "infrastructure"],
    },
    "ailab": {
        "id": "ailab",
        "name": "AI Lab",
        "tagline": "AI experimentation and model testing environment",
        "category": "project",
        "subcategory": "research",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt", "claude"],
        "portfolio_priority": 3,
        "content_angles": ["Personal AI research lab for testing models and techniques"],
        "tags": ["ai", "research", "experimentation", "ml"],
    },
    "agents": {
        "id": "agent-orchestration",
        "name": "Agent Orchestration",
        "tagline": "Multi-agent framework and orchestration toolkit",
        "category": "project",
        "subcategory": "ai-infra",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt", "claude"],
        "portfolio_priority": 3,
        "content_angles": [
            "Custom multi-agent orchestration framework",
            "Building the coordination layer for AI agent swarms"
        ],
        "tags": ["agents", "orchestration", "multi-agent", "framework"],
    },
    "vision": {
        "id": "vision-cv",
        "name": "Vision",
        "tagline": "Computer vision project",
        "category": "project",
        "subcategory": "ml",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": ["Computer vision experiments and applications"],
        "tags": ["computer-vision", "ml", "ai", "image-processing"],
    },
    "twitter bookmark": {
        "id": "twitter-bookmark-manager",
        "name": "Twitter Bookmark Manager",
        "tagline": "Twitter bookmark aggregation and management tool",
        "category": "project",
        "subcategory": "social-tools",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": ["Organizing and managing Twitter bookmarks at scale"],
        "tags": ["twitter", "bookmarks", "social-media", "automation"],
    },
    "cloud": {
        "id": "cloud-infra",
        "name": "Cloud Infrastructure",
        "tagline": "Cloud deployment and infrastructure tooling",
        "category": "project",
        "subcategory": "infrastructure",
        "tech_stack": ["python", "yaml"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 3,
        "content_angles": ["Custom cloud infrastructure and deployment automation"],
        "tags": ["cloud", "infrastructure", "deployment", "devops"],
    },
    "landing": {
        "id": "landing-page",
        "name": "Landing Page",
        "tagline": "Animated landing page with Tailwind and Framer Motion",
        "category": "project",
        "subcategory": "web",
        "tech_stack": ["node", "tailwind", "framer-motion"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 4,
        "content_angles": ["Modern animated landing page design"],
        "tags": ["web", "landing-page", "tailwind", "animation"],
    },
    "fuckedupcode": {
        "id": "backend-experiments",
        "name": "Backend Experiments",
        "tagline": "Node.js backend experimentation with MongoDB and Express",
        "category": "project",
        "subcategory": "backend",
        "tech_stack": ["node", "mongodb", "express"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 4,
        "content_angles": ["Backend API experiments and server monitoring"],
        "tags": ["backend", "node", "mongodb", "api", "experiments"],
    },
    "uaf": {
        "id": "uaf",
        "name": "UAF",
        "tagline": "Application framework project",
        "category": "project",
        "subcategory": "framework",
        "tech_stack": ["python"],
        "ai_providers_used": ["chatgpt"],
        "portfolio_priority": 4,
        "content_angles": ["Custom application framework development"],
        "tags": ["framework", "architecture"],
    },
}


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def scan_directory_timestamps(project_path: Path) -> dict:
    """Scan a project directory and return file timestamp stats."""
    earliest = None
    latest = None
    file_count = 0
    extensions = defaultdict(int)

    for root, dirs, files in os.walk(project_path):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]

        for f in files:
            fp = Path(root) / f
            ext = fp.suffix.lower()

            if ext in SKIP_EXTENSIONS:
                continue

            try:
                stat = fp.stat()
                mtime = datetime.fromtimestamp(stat.st_mtime)

                # Skip bogus timestamps (pre-2022 or future)
                if mtime.year < 2022 or mtime > datetime.now():
                    continue

                file_count += 1
                extensions[ext] += 1

                if earliest is None or mtime < earliest:
                    earliest = mtime
                if latest is None or mtime > latest:
                    latest = mtime
            except (OSError, PermissionError):
                continue

    return {
        "earliest": earliest,
        "latest": latest,
        "file_count": file_count,
        "extensions": dict(extensions),
    }


def has_git(project_path: Path) -> bool:
    """Check if directory has git initialized."""
    return (project_path / ".git").exists()


def detect_tech_stack(project_path: Path, extensions: dict) -> list:
    """Infer tech stack from files present."""
    stack = []

    if (project_path / "package.json").exists():
        stack.append("node")
        try:
            pkg = json.loads((project_path / "package.json").read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if any("react" in d for d in deps):
                stack.append("react")
            if any("expo" in d for d in deps):
                stack.append("expo")
            if any("next" in d for d in deps):
                stack.append("next")
            if any("vue" in d for d in deps):
                stack.append("vue")
            if any("express" in d for d in deps):
                stack.append("express")
            if any("stripe" in d for d in deps):
                stack.append("stripe")
            if any("tailwind" in d for d in deps):
                stack.append("tailwind")
            if "typescript" in deps:
                stack.append("typescript")
        except (json.JSONDecodeError, OSError):
            pass

    if (project_path / "requirements.txt").exists() or (project_path / "setup.py").exists():
        stack.append("python")

    if any(ext in extensions for ext in [".ts", ".tsx"]):
        if "typescript" not in stack:
            stack.append("typescript")

    if any(ext in extensions for ext in [".py"]):
        if "python" not in stack:
            stack.append("python")

    if (project_path / "Dockerfile").exists():
        stack.append("docker")

    return list(set(stack))


def scan_all_projects() -> list:
    """Scan Documents/ and generate catalog entries for all projects."""
    catalog_entries = []

    for dir_name, known_data in KNOWN_PROJECTS.items():
        project_path = DOCUMENTS_DIR / dir_name

        if not project_path.exists():
            print(f"  [SKIP] {dir_name} — path not found")
            continue

        print(f"  [SCAN] {dir_name}...")
        stats = scan_directory_timestamps(project_path)

        if stats["file_count"] == 0:
            print(f"  [SKIP] {dir_name} — no files found")
            continue

        # Build active periods from timestamps
        active_periods = []
        if stats["earliest"] and stats["latest"]:
            active_periods.append({
                "start": stats["earliest"].strftime("%Y-%m-%d"),
                "end": stats["latest"].strftime("%Y-%m-%d"),
                "intensity": "high" if stats["file_count"] > 100 else "medium" if stats["file_count"] > 20 else "low",
            })

        # Auto-detect tech if not pre-specified
        detected_tech = detect_tech_stack(project_path, stats["extensions"])
        tech_stack = known_data.get("tech_stack", detected_tech)

        entry = {
            "id": known_data["id"],
            "name": known_data["name"],
            "tagline": known_data["tagline"],
            "description": known_data.get("description", ""),
            "category": known_data.get("category", "project"),
            "subcategory": known_data.get("subcategory", ""),
            "tech_stack": tech_stack,
            "source_type": "local_code",
            "local_path": str(project_path),
            "has_existing_git": has_git(project_path),
            "github_repo": None,
            "active_periods": active_periods,
            "ai_providers_used": known_data.get("ai_providers_used", ["chatgpt"]),
            "proof": {
                "filesystem_timestamps": True,
                "ai_export_available": False,
                "surge_deploys": known_data.get("subcategory") in ["autonomous-system"],
                "confidence": "high" if stats["file_count"] > 50 else "medium",
            },
            "metrics": {
                "file_count": stats["file_count"],
                "extensions": stats["extensions"],
            },
            "portfolio_priority": known_data.get("portfolio_priority", 3),
            "content_angles": known_data.get("content_angles", []),
            "tags": known_data.get("tags", []),
        }
        catalog_entries.append(entry)

    return catalog_entries


def save_catalog(entries: list) -> None:
    """Save catalog entries to individual JSON files."""
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)

    for entry in entries:
        filepath = CATALOG_DIR / f"{entry['id']}.json"
        filepath.write_text(json.dumps(entry, indent=2, default=str))
        print(f"  [SAVED] {filepath.name}")


def load_catalog() -> list:
    """Load all catalog entries from disk."""
    entries = []
    if not CATALOG_DIR.exists():
        return entries
    for f in sorted(CATALOG_DIR.glob("*.json")):
        try:
            entries.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            print(f"  [WARN] Failed to parse {f.name}")
    return entries


if __name__ == "__main__":
    print("DEVPRINT Catalog Scanner")
    print("=" * 50)
    print(f"Scanning: {DOCUMENTS_DIR}")
    print()
    entries = scan_all_projects()
    print()
    print(f"Found {len(entries)} projects")
    save_catalog(entries)
    print()
    print("Done! Catalog entries saved to catalog/projects/")
