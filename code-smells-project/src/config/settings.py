import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _env_bool(name, default="false"):
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


class Config:
    APP_ENV = os.environ.get("APP_ENV", "development")
    APP_VERSION = "1.0.0"
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    DEBUG = _env_bool("FLASK_DEBUG")
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
    # Token exigido por rotas administrativas; sem valor definido elas ficam desabilitadas.
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")


if not os.environ.get("SECRET_KEY"):
    logger.warning("SECRET_KEY não definida; usando chave efêmera gerada no boot.")
