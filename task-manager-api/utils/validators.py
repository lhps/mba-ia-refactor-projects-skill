import re

from errors import ValidationError
from models.category import DEFAULT_COLOR
from models.task import MAX_PRIORITY, MAX_TITLE_LENGTH, MIN_PRIORITY, MIN_TITLE_LENGTH, VALID_STATUSES
from models.user import MIN_PASSWORD_LENGTH, VALID_ROLES
from utils.helpers import parse_date

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
COLOR_REGEX = re.compile(r'^#[0-9a-fA-F]{6}$')


def require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError('Dados inválidos')
    return data


def validate_task_payload(data, partial=False):
    """Valida e normaliza o payload de task. `partial=True` para updates (só campos presentes)."""
    require_payload(data)
    result = {}

    if 'title' in data or not partial:
        title = data.get('title')
        if not title or not isinstance(title, str):
            raise ValidationError('Título é obrigatório')
        title = title.strip()
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')
        result['title'] = title

    if 'description' in data or not partial:
        result['description'] = data.get('description', '')

    if 'status' in data or not partial:
        status = data.get('status', 'pending')
        if status not in VALID_STATUSES:
            raise ValidationError('Status inválido')
        result['status'] = status

    if 'priority' in data or not partial:
        priority = data.get('priority', 3)
        if not isinstance(priority, int) or isinstance(priority, bool) or not MIN_PRIORITY <= priority <= MAX_PRIORITY:
            raise ValidationError(f'Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}')
        result['priority'] = priority

    for field in ('user_id', 'category_id'):
        if field in data or not partial:
            result[field] = data.get(field)

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if parsed is None:
                raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')
            result['due_date'] = parsed
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data['tags']
        result['tags'] = ','.join(tags) if isinstance(tags, list) else tags

    return result


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_REGEX.match(email):
        raise ValidationError('Email inválido')


def validate_password(password):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres')


def validate_role(role):
    if role not in VALID_ROLES:
        raise ValidationError('Role inválido')


def validate_category_payload(data, partial=False):
    require_payload(data)
    result = {}
    if 'name' in data or not partial:
        if not data.get('name'):
            raise ValidationError('Nome é obrigatório')
        result['name'] = data['name']
    if 'description' in data or not partial:
        result['description'] = data.get('description', '')
    if 'color' in data or not partial:
        color = data.get('color', DEFAULT_COLOR)
        if not isinstance(color, str) or not COLOR_REGEX.match(color):
            raise ValidationError('Cor inválida. Use o formato #RRGGBB')
        result['color'] = color
    return result
