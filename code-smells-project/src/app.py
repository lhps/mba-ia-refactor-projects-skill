import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import Config
from src.controllers.pedido_controller import PedidoController
from src.middlewares.error_handler import register_error_handlers
from src.services.notification_service import NotificationService
from src.views.main_routes import main_bp
from src.views.pedido_routes import create_pedido_blueprint
from src.views.produto_routes import produto_bp
from src.views.relatorio_routes import relatorio_bp
from src.views.usuario_routes import usuario_bp


def create_app(config=Config):
    """Composition root: monta config, banco, dependências, rotas e handlers."""
    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=config.CORS_ORIGINS)

    database.init_app(app)

    pedido_controller = PedidoController(notifier=NotificationService())

    app.register_blueprint(main_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(create_pedido_blueprint(pedido_controller))
    app.register_blueprint(relatorio_bp)

    register_error_handlers(app)
    return app
