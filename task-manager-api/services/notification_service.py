import logging
import smtplib

from utils.helpers import utcnow

logger = logging.getLogger(__name__)


class NotificationService:
    """Envia notificações por e-mail. Desabilitado por padrão (NOTIFICATIONS_ENABLED=false) — apenas registra em log."""

    def __init__(self, enabled, host, port, user, password):
        self.enabled = enabled
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.notifications = []

    @classmethod
    def from_config(cls, config):
        return cls(
            enabled=config["NOTIFICATIONS_ENABLED"],
            host=config["SMTP_HOST"],
            port=config["SMTP_PORT"],
            user=config["SMTP_USER"],
            password=config["SMTP_PASSWORD"],
        )

    def send_email(self, to, subject, body):
        if not self.enabled:
            logger.info("Notificação (desabilitada) para usuário: %s", subject)
            return False
        try:
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.user, to, f"Subject: {subject}\n\n{body}")
            logger.info("Email enviado: %s", subject)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception("Erro ao enviar email")
            return False

    def notify_task_assigned(self, user, task):
        subject = f"Nova task atribuída: {task.title}"
        body = (f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
                f"Prioridade: {task.priority}\nStatus: {task.status}")
        self.send_email(user.email, subject, body)
        self.notifications.append({
            'type': 'task_assigned',
            'user_id': user.id,
            'task_id': task.id,
            'timestamp': utcnow(),
        })

    def notify_task_overdue(self, user, task):
        subject = f"Task atrasada: {task.title}"
        body = f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\nData limite: {task.due_date}"
        self.send_email(user.email, subject, body)

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n['user_id'] == user_id]
