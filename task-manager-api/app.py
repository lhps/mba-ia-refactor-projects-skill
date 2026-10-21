import logging
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import create_task_blueprint
from routes.user_routes import create_user_blueprint
from services.auth_service import AuthService
from services.notification_service import NotificationService


def create_app(config=Config):
    """Composition root: config, banco, dependências, rotas e error handling."""
    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(config)
    CORS(app, origins=config.CORS_ORIGINS)
    db.init_app(app)

    notifier = NotificationService.from_config(app.config)
    auth_service = AuthService(app.config['SECRET_KEY'], app.config['TOKEN_MAX_AGE_SECONDS'])

    app.register_blueprint(create_task_blueprint(TaskController(notifier)))
    app.register_blueprint(create_user_blueprint(UserController(auth_service)))
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)
    register_error_handlers(app)

    @app.get('/health')
    def health():
        return jsonify({'status': 'ok', 'timestamp': str(datetime.now())})

    @app.get('/')
    def index():
        return jsonify({'message': 'Task Manager API', 'version': app.config['APP_VERSION']})

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
