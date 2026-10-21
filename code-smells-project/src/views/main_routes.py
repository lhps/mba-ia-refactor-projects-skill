from flask import Blueprint, current_app, jsonify

from src.controllers import admin_controller
from src.middlewares.admin_auth import require_admin_token

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": current_app.config["APP_VERSION"],
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


@main_bp.get("/health")
def health_check():
    config = current_app.config
    return jsonify(admin_controller.health(config["APP_VERSION"], config["APP_ENV"])), 200


@main_bp.post("/admin/reset-db")
@require_admin_token
def reset_database():
    admin_controller.reset_database()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
