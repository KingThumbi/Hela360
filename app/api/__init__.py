from flask import Flask

from app.config import Config
from app.extensions import db, login_manager, migrate


def register_blueprints(app: Flask) -> None:
    from app.api.health import bp as health_bp

    app.register_blueprint(health_bp, url_prefix="/api")


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    register_extensions(app)

    # Import models so SQLAlchemy metadata is loaded for migrations.
    import app.models  # noqa: F401

    register_blueprints(app)
    return app