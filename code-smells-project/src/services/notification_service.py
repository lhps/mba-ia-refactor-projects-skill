import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Ponto único para notificações (email/SMS/push). Hoje apenas registra em log."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificando criação do pedido %s para usuário %s (email/sms/push)", pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id):
        logger.info("Pedido %s aprovado; preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("Pedido %s cancelado; estoque devolvido", pedido_id)
