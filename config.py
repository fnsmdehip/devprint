"""DEVPRINT global configuration."""
from pathlib import Path

# Paths
DEVPRINT_ROOT = Path(__file__).parent
DOCUMENTS_DIR = Path.home() / "Documents"
CATALOG_DIR = DEVPRINT_ROOT / "catalog" / "projects"
SITE_BUILD_DIR = DEVPRINT_ROOT / "portfolio_site" / "build"
CONTENT_OUTPUT_DIR = DEVPRINT_ROOT / "content" / "output"

# Git settings
GITHUB_USERNAME = None  # Set via CLI or env
DEFAULT_COMMIT_HOUR_RANGE = (9, 26)  # 9am to 2am (26 = 2am next day)
MAX_COMMITS_PER_DAY = 8
MIN_COMMIT_GAP_MINUTES = 30

# Scanner settings
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv", "env",
    ".env", ".DS_Store", ".idea", ".vscode", "dist", "build",
    ".next", ".cache", ".turbo", "coverage", ".pytest_cache",
    ".mypy_cache", "eggs", "*.egg-info", ".tox", ".nox",
}
SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".wav", ".ogg", ".mp4", ".mov", ".avi", ".mkv",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".DS_Store", ".lock",
}
# Keep these extensions (code, config, docs)
CODE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".md", ".txt", ".rst", ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".graphql", ".prisma", ".env.example",
    ".swift", ".kt", ".java", ".go", ".rs", ".rb", ".php",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".r", ".R",
    ".dockerfile", ".tf", ".hcl",
    ".gitignore", ".eslintrc", ".prettierrc",
}

# Portfolio site
SITE_TITLE = "DEVPRINT"
SITE_TAGLINE = "18+ months of AI-native development"
SURGE_DOMAIN = None  # Set via CLI

# Classification thresholds
MIN_MESSAGES_PROJECT = 5
MIN_MESSAGES_RESEARCH = 10
MIN_MESSAGES_NOISE_MAX = 3

# Proof confidence
CONFIDENCE_HIGH_MIN_SOURCES = 3
CONFIDENCE_MEDIUM_MIN_SOURCES = 2

# Tier 4 skip projects (downloaded/template)
SKIP_PROJECTS = {
    "OpenManus-main",
    "react-native-recipes-app-master",
    "coherence_commerce_bundle",
}
