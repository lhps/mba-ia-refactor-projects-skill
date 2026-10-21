from collections import defaultdict

from src.database import get_db

STATUS_PENDENTE = "pendente"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")


def _anexar_itens(pedidos):
    """Carrega os itens de todos os pedidos com uma única query (evita N+1)."""
    if not pedidos:
        return pedidos
    ids = [p["id"] for p in pedidos]
    placeholders = ",".join("?" * len(ids))
    rows = get_db().execute(
        f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
               COALESCE(p.nome, 'Desconhecido') AS produto_nome
        FROM itens_pedido i
        LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN ({placeholders})
        ORDER BY i.id
        """,
        ids,
    ).fetchall()
    itens_por_pedido = defaultdict(list)
    for r in rows:
        itens_por_pedido[r["pedido_id"]].append({
            "produto_id": r["produto_id"],
            "produto_nome": r["produto_nome"],
            "quantidade": r["quantidade"],
            "preco_unitario": r["preco_unitario"],
        })
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido[pedido["id"]]
    return pedidos


def _to_dict(row):
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }


def listar_todos():
    rows = get_db().execute("SELECT * FROM pedidos").fetchall()
    return _anexar_itens([_to_dict(r) for r in rows])


def listar_por_usuario(usuario_id):
    rows = get_db().execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    return _anexar_itens([_to_dict(r) for r in rows])


def buscar_por_id(pedido_id):
    row = get_db().execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return _to_dict(row) if row else None


def criar(usuario_id, itens, total):
    """Grava pedido, itens e baixa de estoque em uma única transação.

    `itens` é uma lista de dicts com produto_id, quantidade e preco_unitario.
    """
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        )
        pedido_id = cursor.lastrowid
        for item in itens:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
    return pedido_id


def atualizar_status(pedido_id, novo_status, devolver_estoque=False):
    db = get_db()
    with db:
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        if devolver_estoque:
            db.execute(
                """
                UPDATE produtos SET estoque = estoque + (
                    SELECT COALESCE(SUM(i.quantidade), 0) FROM itens_pedido i
                    WHERE i.pedido_id = ? AND i.produto_id = produtos.id
                )
                WHERE id IN (SELECT produto_id FROM itens_pedido WHERE pedido_id = ?)
                """,
                (pedido_id, pedido_id),
            )


def estatisticas():
    db = get_db()
    total, faturamento = db.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM pedidos").fetchone()
    por_status = dict(db.execute("SELECT status, COUNT(*) FROM pedidos GROUP BY status").fetchall())
    return {"total_pedidos": total, "faturamento": faturamento, "por_status": por_status}


def contar():
    return get_db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
