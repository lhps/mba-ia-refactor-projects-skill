import hmac
from functools import wraps

from flask import current_app, request

from src.errors import ForbiddenError


def require_admin_token(view):
    """Exige header X-Admin-Token igual ao ADMIN_TOKEN configurado; sem token configurado, nega sempre."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        esperado = current_app.config.get("ADMIN_TOKEN", "")
        recebido = request.headers.get("X-Admin-Token", "")
        if not esperado or not hmac.compare_digest(recebido, esperado):
            raise ForbiddenError("Acesso negado")
        return view(*args, **kwargs)

    return wrapper
