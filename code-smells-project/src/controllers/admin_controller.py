import logging

from src import database
from src.models import pedido_model, produto_model, usuario_model

logger = logging.getLogger(__name__)


def health(versao, ambiente):
    return {
        "status": "ok",
        "database": "connected",
        "counts": {
            "produtos": produto_model.contar(),
            "usuarios": usuario_model.contar(),
            "pedidos": pedido_model.contar(),
        },
        "versao": versao,
        "ambiente": ambiente,
    }


def reset_database():
    database.reset_db()
    logger.warning("Banco de dados resetado via endpoint administrativo")
