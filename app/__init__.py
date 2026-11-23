from flask import Flask
from app.config import Config
from app.database.connection import init_db

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize database tables if connected
    with app.app_context():
        try:
            init_db()
        except Exception as e:
            app.logger.warning(f"Database auto-init deferred: {e}")

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.transactions import transactions_bp
    from app.routes.budgets import budgets_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.analytics import analytics_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)

    return app
