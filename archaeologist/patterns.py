"""Realistic commit pattern generation for AI-native projects without file timestamps."""
import random
from datetime import datetime, timedelta


def generate_activity_pattern(
    start_date: str,
    end_date: str,
    intensity: str = "medium",
    style: str = "autodidact",
) -> list:
    """Generate a realistic pattern of commit dates for a project period.

    Args:
        start_date: ISO date string "YYYY-MM-DD"
        end_date: ISO date string "YYYY-MM-DD"
        intensity: "high", "medium", "low"
        style: "autodidact" (late nights, variable schedule),
               "professional" (9-5 weekdays),
               "weekend-warrior" (bursts on weekends)

    Returns:
        List of datetime objects representing commit timestamps.
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days

    if total_days <= 0:
        return [start.replace(hour=14, minute=30)]

    # Activity probability per day based on intensity
    daily_prob = {
        "high": 0.7,
        "medium": 0.4,
        "low": 0.15,
    }[intensity]

    # Commits per active day
    commits_range = {
        "high": (2, 6),
        "medium": (1, 3),
        "low": (1, 2),
    }[intensity]

    # Hour distributions by style
    hour_weights = _get_hour_weights(style)

    timestamps = []
    current = start

    while current <= end:
        is_weekend = current.weekday() >= 5

        # Adjust probability for weekends
        if style == "autodidact":
            day_prob = daily_prob * (0.6 if is_weekend else 1.0)
        elif style == "professional":
            day_prob = daily_prob * (0.1 if is_weekend else 1.0)
        elif style == "weekend-warrior":
            day_prob = daily_prob * (2.0 if is_weekend else 0.3)
        else:
            day_prob = daily_prob

        day_prob = min(day_prob, 0.95)

        if random.random() < day_prob:
            # This is an active day
            n_commits = random.randint(*commits_range)

            for _ in range(n_commits):
                hour = random.choices(range(24), weights=hour_weights, k=1)[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)

                ts = current.replace(hour=hour, minute=minute, second=second)
                timestamps.append(ts)

        # Occasionally add burst days (deep focus sessions)
        if random.random() < 0.05 and intensity in ("high", "medium"):
            n_burst = random.randint(4, 8)
            base_hour = random.choice([10, 14, 20])
            for i in range(n_burst):
                ts = current.replace(
                    hour=min(23, base_hour + i // 2),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )
                timestamps.append(ts)

        current += timedelta(days=1)

    timestamps.sort()
    return timestamps


def _get_hour_weights(style: str) -> list:
    """Get hour-of-day probability weights for different work styles."""
    if style == "autodidact":
        # Active 10am-2am, peaks at 2pm and 11pm
        weights = [
            2, 2, 1, 0, 0, 0, 0, 0,   # 0-7: late night taper
            1, 3, 5, 7, 8, 9, 10, 9,   # 8-15: morning ramp to afternoon peak
            8, 7, 6, 7, 8, 9, 10, 8,   # 16-23: evening second wind
        ]
    elif style == "professional":
        # 9-5 with lunch dip
        weights = [
            0, 0, 0, 0, 0, 0, 0, 0,
            1, 5, 8, 9, 4, 7, 9, 8,
            5, 2, 0, 0, 0, 0, 0, 0,
        ]
    elif style == "weekend-warrior":
        # Afternoon/evening focused
        weights = [
            1, 0, 0, 0, 0, 0, 0, 0,
            0, 1, 3, 5, 6, 8, 9, 10,
            10, 9, 8, 7, 6, 5, 3, 2,
        ]
    else:
        weights = [1] * 24

    return weights


def spread_commits_over_period(
    file_list: list,
    timestamps: list,
) -> list:
    """Assign files to commit timestamps.

    Args:
        file_list: List of file info dicts
        timestamps: List of datetime commit timestamps

    Returns:
        List of {"timestamp": datetime, "files": [file_info, ...], "message": str}
    """
    if not timestamps:
        return []
    if not file_list:
        return []

    # Distribute files across timestamps roughly evenly
    commits = []
    files_per_commit = max(1, len(file_list) // len(timestamps))

    file_idx = 0
    for ts in timestamps:
        chunk = file_list[file_idx:file_idx + files_per_commit]
        if not chunk and file_idx < len(file_list):
            chunk = [file_list[file_idx]]
        if chunk:
            commits.append({
                "timestamp": ts,
                "files": chunk,
                "message": _auto_message(chunk),
            })
            file_idx += len(chunk)

    # Assign any remaining files to the last commit
    if file_idx < len(file_list):
        remaining = file_list[file_idx:]
        if commits:
            commits[-1]["files"].extend(remaining)
        else:
            commits.append({
                "timestamp": timestamps[-1],
                "files": remaining,
                "message": _auto_message(remaining),
            })

    return commits


def _auto_message(files: list) -> str:
    """Generate commit message from file list."""
    if len(files) == 1:
        name = files[0].get("path", "file").replace("/", " > ")
        return f"add {name}"
    return f"update project ({len(files)} files)"
