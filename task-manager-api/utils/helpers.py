from datetime import datetime, timezone

DATE_FORMAT = "%Y-%m-%d"


def utcnow():
    """UTC naive: substitui datetime.utcnow() (deprecated) mantendo compatibilidade com colunas DateTime do SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value):
    """Converte 'YYYY-MM-DD' em datetime; retorna None se inválido."""
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (TypeError, ValueError):
        return None


def format_date(value):
    return str(value) if value else None


def calculate_percentage(part, total):
    return round((part / total) * 100, 2) if total > 0 else 0
