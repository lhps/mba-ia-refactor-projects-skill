from src.errors import NotFoundError, ValidationError
from src.models import pedido_model, produto_model
from src.models.pedido_model import STATUS_CANCELADO, STATUS_VALIDOS


class PedidoController:
    def __init__(self, notifier):
        self.notifier = notifier

    @staticmethod
    def _validar_itens(itens):
        if not isinstance(itens, list) or len(itens) == 0:
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        for item in itens:
            quantidade = item.get("quantidade") if isinstance(item, dict) else None
            if not isinstance(item, dict) or "produto_id" not in item:
                raise ValidationError("Item de pedido inválido")
            if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade <= 0:
                raise ValidationError("Quantidade inválida para o produto " + str(item["produto_id"]))

    def criar(self, dados):
        if not dados:
            raise ValidationError("Dados inválidos")
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            raise ValidationError("Usuario ID é obrigatório")
        self._validar_itens(itens)

        produtos = produto_model.buscar_por_ids({i["produto_id"] for i in itens})
        total = 0
        itens_precificados = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise ValidationError("Produto " + str(item["produto_id"]) + " não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError("Estoque insuficiente para " + produto["nome"])
            total += produto["preco"] * item["quantidade"]
            itens_precificados.append({**item, "preco_unitario": produto["preco"]})

        pedido_id = pedido_model.criar(usuario_id, itens_precificados, total)
        self.notifier.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self):
        return pedido_model.listar_todos()

    def listar_por_usuario(self, usuario_id):
        return pedido_model.listar_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id, dados):
        novo_status = (dados or {}).get("status", "")
        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        pedido = pedido_model.buscar_por_id(pedido_id)
        if pedido is None:
            raise NotFoundError("Pedido não encontrado")

        cancelando = novo_status == STATUS_CANCELADO and pedido["status"] != STATUS_CANCELADO
        pedido_model.atualizar_status(pedido_id, novo_status, devolver_estoque=cancelando)

        if novo_status == "aprovado":
            self.notifier.pedido_aprovado(pedido_id)
        elif cancelando:
            self.notifier.pedido_cancelado(pedido_id)
