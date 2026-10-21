from src.database import get_db

TIPO_PADRAO = "cliente"

_CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def _to_dict(row):
    """Serialização pública: nunca inclui a senha."""
    return {campo: row[campo] for campo in _CAMPOS_PUBLICOS}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(r) for r in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def buscar_credenciais(email):
    """Retorna (usuario_publico, hash_da_senha) ou (None, None)."""
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None, None
    return _to_dict(row), row["senha"]


def email_existe(email):
    return get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone() is not None


def criar(nome, email, senha_hash, tipo=TIPO_PADRAO):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def contar():
    return get_db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
