from datetime import datetime, timezone

def time_ago(dt: datetime) -> str:
    """Превращает дату в строку 'X minutes ago'"""
    if dt is None:
        return ""

    # Если в базе время без таймзоны, считаем его UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - dt

    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:  # 24 часа
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 172800:  # 48 часов
        return "yesterday"
    else:
        days = int(seconds / 86400)
        return f"{days} days ago"