from flask import Flask
import click
from werkzeug.security import generate_password_hash

from app.config import Config
from app.extensions import db, login_manager, migrate
from app.models import Branch, PaymentMethod, Role, Tenant, User
from app.api_sales import api_sales

def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)


def register_blueprints(app: Flask) -> None:
    from app.api.health import bp as health_bp
    from app.api.products import bp as products_bp
    from app.api.customers import bp as customers_bp
    from app.api.sales import bp as sales_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(customers_bp, url_prefix="/api")
    app.register_blueprint(sales_bp, url_prefix="/api")


def register_commands(app: Flask) -> None:
    @app.cli.command("seed-initial")
    @click.option("--tenant-name", default="Hela360 Demo", show_default=True)
    @click.option("--branch-name", default="Main Branch", show_default=True)
    @click.option("--admin-email", default="admin@hela360.local", show_default=True)
    @click.option("--admin-password", default="Admin@123", show_default=True)
    def seed_initial(
        tenant_name: str,
        branch_name: str,
        admin_email: str,
        admin_password: str,
    ) -> None:
        tenant = Tenant.query.filter_by(display_name=tenant_name).first()
        if not tenant:
            tenant = Tenant(
                legal_name=tenant_name,
                display_name=tenant_name,
                business_type="pharmacy",
                email=admin_email,
                status="active",
            )
            db.session.add(tenant)
            db.session.flush()

        branch = Branch.query.filter_by(
            tenant_id=tenant.id,
            name=branch_name,
        ).first()
        if not branch:
            branch = Branch(
                tenant_id=tenant.id,
                code="MAIN",
                name=branch_name,
                is_head_office=True,
                is_active=True,
            )
            db.session.add(branch)
            db.session.flush()

        admin_role = Role.query.filter_by(
            tenant_id=tenant.id,
            code="admin",
        ).first()
        if not admin_role:
            admin_role = Role(
                tenant_id=tenant.id,
                name="Administrator",
                code="admin",
                description="Full system access",
                is_system=True,
            )
            db.session.add(admin_role)
            db.session.flush()

        admin_user = User.query.filter_by(
            tenant_id=tenant.id,
            email=admin_email,
        ).first()
        if not admin_user:
            admin_user = User(
                tenant_id=tenant.id,
                branch_id=branch.id,
                first_name="System",
                last_name="Admin",
                email=admin_email,
                username="admin",
                password_hash=generate_password_hash(admin_password),
                is_owner=True,
                is_active=True,
            )
            db.session.add(admin_user)

        payment_methods = [
            ("cash", "Cash", "cash"),
            ("mpesa", "M-Pesa", "mpesa"),
            ("card", "Card", "card"),
            ("bank", "Bank Transfer", "bank"),
        ]

        for code, name, method_type in payment_methods:
            exists = PaymentMethod.query.filter_by(
                tenant_id=tenant.id,
                code=code,
            ).first()
            if not exists:
                db.session.add(
                    PaymentMethod(
                        tenant_id=tenant.id,
                        code=code,
                        name=name,
                        method_type=method_type,
                        is_active=True,
                    )
                )

        db.session.commit()
        click.echo("Initial seed completed successfully.")


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)
    #app.register_blueprint(api_sales)
    
    register_extensions(app)

    from app import models  # noqa: F401

    register_blueprints(app)
    register_commands(app)

    return app