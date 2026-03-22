# DEVPRINT — Developer Provenance & Portfolio Intelligence System

## Spec v1.0 | 2026-03-22

---

## 1. Purpose

DEVPRINT is a system that reconstructs, validates, and showcases 18+ months of AI-native
development work across 25+ projects, 6+ AI providers, and multiple tech stacks — producing
a GitHub contribution history, portfolio website, proof-of-work validation layer, and
multi-platform content engine.

**Goals:** Get hired. Build tech credibility. Establish entrepreneur brand. Create content flywheel.

---

## 2. System Components

```
devprint/
├── SPEC.md                          # This document
├── catalog/                         # Project catalog (source of truth)
│   ├── schema.json                  # Catalog entry schema
│   └── projects/                    # One .json per project
├── archaeologist/                   # Git backdating engine
│   ├── scan.py                      # Filesystem scanner (reads mod times)
│   ├── commit_engine.py             # Creates backdated git commits
│   ├── repo_manager.py              # Creates/manages GitHub repos via gh CLI
│   └── patterns.py                  # Realistic commit pattern generator
├── memory_importer/                 # AI chat export processor
│   ├── parsers/                     # Per-provider export parsers
│   │   ├── chatgpt.py               # ChatGPT JSON conversations.json
│   │   ├── gemini.py                # Google Takeout format
│   │   └── manual.py                # Manual entry template processor
│   ├── classifier.py                # LLM-powered conversation classifier
│   ├── extractor.py                 # Pulls structured data from conversations
│   └── merger.py                    # Groups related conversations into projects
├── proof/                           # Validation & evidence system
│   ├── hasher.py                    # SHA-256 file/directory hashing
│   ├── timeline.py                  # Cross-reference timeline builder
│   └── manifest.py                  # Generates proof.json per project
├── site/                            # Static portfolio site generator
│   ├── generator.py                 # Builds HTML from catalog data
│   ├── templates/                   # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html               # Hero + contribution graph + stats
│   │   ├── projects.html            # Filterable project grid
│   │   ├── project_detail.html      # Individual project deep-dive
│   │   ├── research.html            # Research journal entries
│   │   ├── timeline.html            # Interactive chronological view
│   │   ├── proof.html               # Validation methodology
│   │   └── about.html               # Story, skills, philosophy
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── build/                       # Generated output (surge deploy from here)
├── content/                         # Content generation engine
│   ├── templates/                   # Per-platform content templates
│   │   ├── substack_article.md
│   │   ├── twitter_thread.md
│   │   ├── linkedin_post.md
│   │   ├── short_video_script.md
│   │   └── github_readme.md
│   ├── generator.py                 # Generates content drafts from catalog
│   └── output/                      # Generated content drafts
├── cli.py                           # Main CLI entry point
├── config.py                        # Global configuration
├── requirements.txt
└── README.md
```

---

## 3. Project Catalog Schema

Each project gets a JSON entry in `catalog/projects/`:

```json
{
  "id": "printmaxx-starter-kit",
  "name": "PRINTMAXX Starter Kit",
  "tagline": "Autonomous revenue system with 33 agents and 114 deployed apps",
  "description": "Full-stack autonomous business system...",
  "category": "project",
  "subcategory": "autonomous-system",
  "tech_stack": ["python", "node", "react-native", "expo", "fastapi", "sqlite"],
  "source_type": "local_code",
  "local_path": "/Users/macbookpro/Documents/p/PRINTMAXX_STARTER_KITttttt/",
  "has_existing_git": true,
  "github_repo": null,
  "active_periods": [
    {"start": "2025-03-01", "end": "2026-03-22", "intensity": "high"}
  ],
  "ai_providers_used": ["chatgpt", "claude", "cursor", "deepseek"],
  "proof": {
    "filesystem_timestamps": true,
    "ai_export_available": false,
    "surge_deploys": true,
    "confidence": "high"
  },
  "metrics": {
    "file_count": 141000,
    "deployed_apps": 114,
    "agent_count": 33,
    "script_count": 392
  },
  "portfolio_priority": 1,
  "content_angles": [
    "Built an autonomous business system with 33 AI agents",
    "114 apps deployed via automated pipeline",
    "From zero to autonomous revenue infrastructure"
  ],
  "tags": ["autonomous", "multi-agent", "revenue", "automation", "saas"]
}
```

---

## 4. Git Archaeologist

### 4.1 Scanning

For each project with `source_type: "local_code"`:
1. Walk directory tree, skip: node_modules, .git, __pycache__, .env, venv, .DS_Store, binaries
2. For each file, record: path, modification time, size, extension
3. Group files by modification date
4. Identify active periods (clusters of file modifications)

### 4.2 Commit Strategy

**Type A — Local Code Projects:**
- Group files modified on same date into one commit
- If >20 files on one day, split into 2-3 commits with logical groupings
- Commit message generated from file paths: "add batch automation scripts" not "update files"
- Set GIT_AUTHOR_DATE and GIT_COMMITTER_DATE to file mod time
- Vary commit times within the day (don't stamp everything at midnight)

**Type B — AI-Native Projects (from memory imports):**
- Create README.md + research notes + code snippets extracted from conversations
- Spread commits across the conversation date range
- 1-3 commits per active day, matching conversation timestamps

**Type C — Research Threads:**
- Create structured markdown: README + topic files
- Commit per research session/conversation
- Research journal style

### 4.3 Commit Patterns (Realism)

```python
# Not this (suspicious):
# 50 commits all at 2025-06-15T00:00:00

# This (realistic):
# 2025-06-15T09:23:00 — 3 files (morning session)
# 2025-06-15T14:47:00 — 7 files (afternoon push)
# 2025-06-15T22:11:00 — 2 files (late night fix)
# 2025-06-16 — no commits (day off)
# 2025-06-17T10:05:00 — 5 files
```

Rules:
- Max 8 commits per day (realistic for active development)
- Include gaps (weekends, breaks) matching real patterns
- Commit times based on actual file mod timestamps when available
- For AI-native projects, spread across 10am-2am window (realistic for autodidact)
- Commit messages are descriptive, derived from file content/paths

### 4.4 GitHub Repo Creation

Via `gh` CLI:
```bash
gh repo create <name> --public --description "<tagline>"
git remote add origin <url>
git push -u origin main
```

Each project = individual repo. No umbrella repos.

---

## 5. AI Memory Importer

### 5.1 Supported Providers

| Provider | Export Method | Format |
|----------|-------------|--------|
| ChatGPT | Settings > Export data | JSON (conversations.json) |
| Gemini | Google Takeout | HTML/JSON |
| Claude | No native export | Manual entry via template |
| DeepSeek | No native export | Manual entry via template |
| Grok | No native export | Manual entry via template |
| Perplexity | No native export | Manual entry via template |

### 5.2 Classification Pipeline

```
NOISE (skip): < 4 messages, factual lookups, store hours, tweet explanations
PROJECT: code blocks present, "build/create/make" language, 5+ messages
RESEARCH: 10+ messages, no code, deep topic exploration, sustained Q&A
STRATEGY: business planning, market analysis, ideation sessions
LEARNING: tutorials, skill-building, how-to sessions
```

Classifier uses keyword heuristics first (fast), then LLM for ambiguous cases.

### 5.3 Conversation Merging

Multiple conversations on the same topic across sessions → single project entry.
Merge criteria:
- Same topic keywords appearing in title/content
- Overlapping date ranges
- Referenced technologies match

---

## 6. Proof & Validation

### 6.1 Evidence Types

1. **AI Export Timestamps** — server-generated, unforgeable
2. **Filesystem Timestamps** — file stat() data, can be overwritten but typically accurate
3. **Git Commit Hashes** — immutable SHA chain post-push
4. **Surge Deploy Records** — deployment logs, DNS history
5. **Cross-Reference Consistency** — multiple independent sources agreeing

### 6.2 Proof Manifest

Each project gets `proof.json` with:
- All evidence sources and their timestamps
- SHA-256 hash of directory state at time of cataloging
- Confidence rating: high / medium / low / self-reported
- Timeline consistency check (do sources agree?)

### 6.3 Confidence Levels

- **HIGH**: 3+ independent evidence sources, timestamps consistent
- **MEDIUM**: 2 evidence sources, timestamps consistent
- **LOW**: 1 evidence source
- **SELF-REPORTED**: Manual entry only, no corroborating evidence

---

## 7. Portfolio Site

### 7.1 Static Site Generation

Built with Jinja2 templates + vanilla JS. No framework dependency.
Generates to `site/build/`. Deploys via `surge site/build/ yoursite.surge.sh`.

### 7.2 Pages

**Index (/):**
- Hero with name, one-liner, key stats
- GitHub-style contribution heatmap (generated from catalog data, not just GitHub)
- Tech stack icons
- Featured projects (top 3-5 by priority)
- Call-to-action links

**Projects (/projects):**
- Filterable grid: by category, tech stack, date range
- Cards: title, tagline, tech tags, timeline bar, proof badge, links

**Project Detail (/projects/:slug):**
- Full description
- Tech stack breakdown
- Timeline with key milestones
- Screenshots / demos
- Proof summary
- Links to GitHub, live site

**Research (/research):**
- Research journal entries from AI conversations
- Topics: longevity, biohacking, prediction markets, physics, health
- Shows depth of intellectual curiosity

**Timeline (/timeline):**
- Full chronological view of all projects
- Colored bars showing project lifespans
- AI provider icons per project
- Commit activity heatmap underneath

**Proof (/proof):**
- Explains validation methodology
- Links to evidence for each project
- Builds trust with skeptical viewers

**About (/about):**
- Personal story
- Skills matrix
- Philosophy on AI-native development
- Contact / links

### 7.3 Design

- Dark theme (developer aesthetic)
- Monospace headings, clean sans-serif body
- GitHub green contribution graph colors
- Responsive (mobile-friendly for recruiters on phones)
- Fast (static HTML, minimal JS)

---

## 8. Content Engine

### 8.1 Template System

Each catalog entry can generate content for:

**Substack Article:**
- Hook → Project story → Technical breakdown → Lessons → CTA
- 800-1500 words
- Include code snippets, architecture diagrams

**Twitter/X Thread:**
- Hook tweet → 5-8 detail tweets → CTA tweet
- Include screenshots, contribution graph
- Use proven formats: "I built X in Y months. Here's what happened 🧵"

**LinkedIn Post:**
- Professional framing, 200-400 words
- Focus on skills, outcomes, growth narrative
- Hashtags: #AIEngineering #BuildInPublic #AgenticCoding

**Short-form Video Script (TikTok/Reels/Shorts):**
- 60-second format
- Hook (3 sec) → Context (10 sec) → Show the thing (30 sec) → Results (10 sec) → CTA (7 sec)
- Screen recording directions
- Text overlay suggestions
- Faceless: screen recordings + AI voiceover

**GitHub README:**
- Project name + badges
- One-liner description
- Features list
- Tech stack
- Architecture diagram (mermaid)
- Getting started
- Screenshots

### 8.2 Content Calendar

Auto-generates a 30-day content calendar from catalog:
- 1 Substack article / week (deep dive on a project)
- 3-5 X threads / week (project highlights, hot takes, journey updates)
- 2 LinkedIn posts / week (professional narrative)
- 2-3 short videos / week (screen recordings with scripts)

---

## 9. CLI Interface

```bash
# Catalog management
python cli.py catalog scan          # Scan Documents/ and generate catalog entries
python cli.py catalog list          # List all cataloged projects
python cli.py catalog show <id>     # Show project details

# Git archaeology
python cli.py git scan <id>         # Preview what commits would be created
python cli.py git push <id>         # Create repo + backdated commits + push
python cli.py git push-all          # Process all projects

# Memory import
python cli.py memory import <file>  # Import AI export file
python cli.py memory classify       # Run classifier on imported conversations
python cli.py memory manual         # Interactive manual entry

# Proof generation
python cli.py proof generate <id>   # Generate proof manifest for project
python cli.py proof generate-all    # All projects
python cli.py proof verify <id>     # Verify timeline consistency

# Portfolio site
python cli.py site build            # Generate static site
python cli.py site preview          # Local preview server
python cli.py site deploy           # Deploy to surge

# Content engine
python cli.py content generate <id> # Generate all content types for project
python cli.py content calendar      # Generate 30-day content calendar
python cli.py content list          # List generated content
```

---

## 10. Implementation Priority

**Phase 1 — Foundation (NOW):**
1. Project scaffolding + config
2. Catalog schema + scanner (auto-populate from Documents/)
3. Git archaeologist (scan + commit engine + GitHub push)
4. Run on all 25+ projects → GitHub graph populated

**Phase 2 — Intelligence:**
5. AI memory importer (ChatGPT parser + classifier)
6. Manual entry templates for non-exportable providers
7. Proof system (hasher + timeline + manifests)

**Phase 3 — Visibility:**
8. Portfolio site generator (all pages)
9. Content engine (all templates)
10. Deploy site + generate initial content batch

---

## 11. Discovered Projects (from scan)

### Tier 1 — Flagship (individual showcase repos)
1. **PRINTMAXX Starter Kit** — 33-agent autonomous revenue system, 114 deployed apps
2. **SIGCRAFT** — Self-improving signal intelligence, 22+ data sources, prediction calibration
3. **Soundgrep** — Multi-agent music production, Ableton integration, CLAP embeddings

### Tier 2 — Substantial (individual repos)
4. **NutriAI** — React Native nutrition tracking, Expo, camera/health integrations
5. **MarketingPro** — Full-stack SaaS, Express+React, Stripe, PostgreSQL
6. **CRO AI** — Conversion rate optimization analytics dashboard
7. **Ancestry Research / Before You Venture** — Business idea framework + generator

### Tier 3 — Notable (individual repos)
8. **AutoReplyAI** — Email auto-reply system
9. **ClaimWatch V2** — Claims management/tracking
10. **Memescan Bot** — Meme token detection
11. **Terminal Agent** — Terminal automation tool
12. **Local AI Stack** — On-device LLM infrastructure
13. **AILab** — AI experimentation environment
14. **Agents** — Multi-agent orchestration toolkit
15. **Vision** — Computer vision project
16. **Twitter Bookmark Manager** — Twitter tool
17. **Cloud** — Cloud infrastructure tooling
18. **Landing Page** — Tailwind + Framer Motion landing

### Tier 4 — Skip (downloaded/template projects)
- OpenManus (open source download)
- React Native Recipes (template)
- Coherence Commerce Bundle (template)
- Pocket Alexandria variants (starter packs)

### Tier 5 — AI Memory Projects (to be extracted)
- Research threads from ChatGPT, Claude, Gemini, DeepSeek, Grok, Perplexity
- Categories: longevity, biohacking, health, physics, prediction markets, trading, business strategy

---

## 12. Tech Stack (DEVPRINT itself)

- **Python 3.11+** — core engine
- **Jinja2** — HTML templating
- **Click** — CLI framework
- **gh CLI** — GitHub repo management
- **git** — version control operations (subprocess)
- **hashlib** — SHA-256 proof hashing
- **json/pathlib/os** — filesystem operations
- **surge** — portfolio deployment
