# DEVPRINT

**Developer Provenance & Portfolio Intelligence System**

Reconstructs, validates, and showcases your development history — even if you never pushed to Git.

## What It Does

1. **Catalogs** all your projects from local directories and AI chat histories
2. **Creates backdated Git repos** with commits timestamped to when work actually happened
3. **Imports AI memory** from ChatGPT, Gemini, Claude, and other providers
4. **Validates timelines** with multi-source proof (filesystem timestamps, AI export records, deployment logs)
5. **Generates a portfolio site** with contribution graphs, project pages, and proof-of-work badges
6. **Creates content** for Substack, Twitter/X, LinkedIn, TikTok/Reels (faceless video scripts)

## Quick Start

```bash
pip install -r requirements.txt

# 1. Scan your projects
python cli.py catalog scan

# 2. See what you've got
python cli.py catalog list

# 3. Preview git commits for a project
python cli.py git scan printmaxx-starter-kit

# 4. Push all projects to GitHub (backdated)
python cli.py git push-all --dry-run

# 5. Build portfolio site
python cli.py site build

# 6. Generate content for a project
python cli.py content generate printmaxx-starter-kit
```

## Architecture

```
devprint/
├── catalog/          # Project catalog (source of truth)
├── archaeologist/    # Git backdating engine
├── memory_importer/  # AI chat export processor
├── proof/            # Validation & evidence system
├── site/             # Static portfolio site generator
├── content/          # Multi-platform content engine
└── cli.py            # Main CLI entry point
```

## Git Backdating

Git supports two timestamps: author date and commit date. DEVPRINT sets both to the file's actual modification time, so GitHub's contribution graph shows activity on the days you actually did the work — not the day you pushed.

This is **reconstructing** real history, not fabricating it. The proof system provides corroborating evidence from multiple independent sources.

## AI Memory Import

Export your ChatGPT data (Settings > Data Controls > Export), and DEVPRINT will:
- Parse all conversations
- Classify them (Project / Research / Strategy / Learning / Noise)
- Merge related sessions into unified project entries
- Generate catalog entries with proper dates

For providers without export (Claude, DeepSeek, Grok, Perplexity), use the manual entry templates.

## Proof System

Each project gets a `proof.json` with evidence from:
- Filesystem timestamps (file modification dates)
- AI export timestamps (server-generated, unforgeable)
- Git commit hashes (immutable once pushed)
- Deployment records (Surge logs, DNS history)
- Cross-reference consistency (do multiple sources agree?)

Confidence levels: HIGH (3+ sources) / MEDIUM (2 sources) / LOW (1 source) / SELF-REPORTED
