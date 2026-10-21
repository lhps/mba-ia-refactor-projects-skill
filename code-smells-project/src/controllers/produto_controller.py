import logging

from src.errors import NotFoundError, ValidationError
from src.models import produto_model
from src.models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, NOME_MAX, NOME_MIN

logger = logging.getLogger(__name__)

_OBRIGATORIOS = (("nome", "Nome"), ("preco", "Preço"), ("estoque", "Estoque"))


def _numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def validar_produto(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    for campo, rotulo in _OBRIGATORIOS:
        if campo not in dados:
            raise ValidationError(f"{rotulo} é obrigatório")

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome inválido")
    if not _numero(preco):
        raise ValidationError("Preço deve ser numérico")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser inteiro")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError("Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS)))

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def _parse_preco(valor, rotulo):
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"{rotulo} inválido")


def listar():
    produtos = produto_model.listar()
    logger.info("Listando %s produtos", len(produtos))
    return produtos


def obter(produto_id):
    produto = produto_model.buscar_por_id(produto_id)
    if produto is None:
        raise NotFoundError("Produto não encontrado")
    return produto


def buscar(termo, categoria, preco_min, preco_max):
    return produto_model.buscar(
        termo,
        categoria,
        _parse_preco(preco_min, "preco_min"),
        _parse_preco(preco_max, "preco_max"),
    )


def criar(dados):
    produto = validar_produto(dados)
    produto_id = produto_model.criar(**produto)
    logger.info("Produto criado com ID %s", produto_id)
    return produto_id


def atualizar(produto_id, dados):
    obter(produto_id)
    produto = validar_produto(dados)
    produto_model.atualizar(produto_id, **produto)


def deletar(produto_id):
    obter(produto_id)
    produto_model.deletar(produto_id)
    logger.info("Produto %s deletado", produto_id)
