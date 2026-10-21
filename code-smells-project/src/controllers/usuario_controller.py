import logging
import re

from werkzeug.security import check_password_hash, generate_password_hash

from src.errors import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from src.models import usuario_model

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def listar():
    return usuario_model.listar()


def obter(usuario_id):
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise NotFoundError("Usuário não encontrado")
    return usuario


def criar(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")
    if not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    if usuario_model.email_existe(email):
        raise ConflictError("Email já cadastrado")

    usuario_id = usuario_model.criar(nome, email, generate_password_hash(senha))
    logger.info("Usuário criado: %s", usuario_id)
    return usuario_id


def login(dados):
    dados = dados or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    usuario, senha_hash = usuario_model.buscar_credenciais(email)
    if usuario is None or not check_password_hash(senha_hash, senha):
        logger.info("Falha de login")
        raise UnauthorizedError("Email ou senha inválidos")

    logger.info("Login bem-sucedido do usuário %s", usuario["id"])
    return {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"], "tipo": usuario["tipo"]}
