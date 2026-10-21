from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from errors import UnauthorizedError

_SALT = "task-manager-auth"


class AuthService:
    """Emite e valida tokens assinados (substitui o antigo 'fake-jwt-token-<id>')."""

    def __init__(self, secret_key, max_age_seconds):
        self.serializer = URLSafeTimedSerializer(secret_key, salt=_SALT)
        self.max_age_seconds = max_age_seconds

    def issue_token(self, user):
        return self.serializer.dumps({"user_id": user.id, "role": user.role})

    def verify_token(self, token):
        try:
            return self.serializer.loads(token, max_age=self.max_age_seconds)
        except (BadSignature, SignatureExpired):
            raise UnauthorizedError("Token inválido")
