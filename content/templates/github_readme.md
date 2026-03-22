# {{ project_name }}

{{ tagline }}

{% if badges %}
{{ badges }}
{% endif %}

## Overview

{{ description }}

## Features

{% for feature in features %}
- {{ feature }}
{% endfor %}

## Tech Stack

| Technology | Purpose |
|-----------|---------|
{% for tech, purpose in tech_details %}
| {{ tech }} | {{ purpose }} |
{% endfor %}

{% if architecture %}
## Architecture

```
{{ architecture }}
```
{% endif %}

## Getting Started

```bash
{{ setup_commands }}
```

{% if screenshots %}
## Screenshots

{{ screenshots }}
{% endif %}

## Project History

- **Active Period:** {{ active_period }}
- **Built with:** AI pair programming ({{ ai_tools }})
- **Proof of work:** [Verified portfolio]({{ portfolio_url }})

## License

MIT

---

*Part of [DEVPRINT]({{ portfolio_url }}) — {{ total_projects }}+ projects built through AI-native development*
