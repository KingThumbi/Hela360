from flask import Flask
import click
from werkzeug.security import generate_password_hash
from flask_cors import CORS
from app.config import Config
from app.extensions import db, login_manager, migrate

# Ensure SQLAlchemy models are registered
from app import models  # noqa: F401

from app.models import (
    Branch,
    PaymentMethod,
    Role,
    Tenant,
    User,
)

from app.auth import init_app as init_auth


# =============================================================================
# Extensions
# =============================================================================

def register_extensions(app: Flask) -> None:
    """
    Register Flask extensions.
    """

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config[
                    "CORS_ALLOWED_ORIGINS"
                ],
            },
        },
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Tenant-ID",
            "X-Branch-ID",
            "X-Request-ID",
        ],
        methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
        ],
    )

# =============================================================================
# Blueprints
# =============================================================================

def register_blueprints(app: Flask) -> None:
    """
    Register every API blueprint.

    Authentication is registered first because every protected endpoint
    depends on the IAM subsystem.
    """

    from app.api.health import bp as health_bp
    from app.api.products import bp as products_bp
    from app.api.catalogue import bp as catalogue_bp
    from app.api.office_catalogue import bp as office_catalogue_bp
    from app.api.payment_methods import bp as payment_methods_bp
    from app.api.inventory import bp as inventory_bp
    from app.api.tills import bp as tills_bp
    from app.api.warehouses import bp as warehouses_bp
    from app.api.customers import bp as customers_bp
    from app.api.sales import bp as sales_bp
    from app.api.suppliers import bp as suppliers_bp
    from app.api.dashboard import bp as dashboard_bp

    # Enterprise IAM
    init_auth(app)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(catalogue_bp, url_prefix="/api")
    app.register_blueprint(office_catalogue_bp, url_prefix="/api")
    app.register_blueprint(payment_methods_bp, url_prefix="/api")
    app.register_blueprint(inventory_bp, url_prefix="/api")
    app.register_blueprint(tills_bp, url_prefix="/api")
    app.register_blueprint(warehouses_bp, url_prefix="/api")
    app.register_blueprint(customers_bp, url_prefix="/api")
    app.register_blueprint(sales_bp, url_prefix="/api")
    app.register_blueprint(suppliers_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api")


# =============================================================================
# CLI Commands
# =============================================================================

def register_commands(app: Flask) -> None:
    """
    Register Flask CLI commands.
    """

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
        """
        Seed an initial tenant, branch, administrator and payment methods.
        """

        tenant = Tenant.query.filter_by(display_name=tenant_name).first()

        if tenant is None:
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

        if branch is None:
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

        if admin_role is None:
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

        if admin_user is None:
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

        payment_methods = (
            ("cash", "Cash", "cash"),
            ("mpesa", "M-Pesa", "mpesa"),
            ("card", "Card", "card"),
            ("bank", "Bank Transfer", "bank"),
        )

        for code, name, method_type in payment_methods:
            exists = PaymentMethod.query.filter_by(
                tenant_id=tenant.id,
                code=code,
            ).first()

            if exists is None:
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

    @app.cli.command(
        "seed-master-catalogue"
    )
    @click.option(
        "--file",
        "seed_file",
        required=True,
        type=click.Path(
            exists=True,
            dir_okay=False,
            path_type=str,
        ),
        help=(
            "Path to a versioned Hela360 "
            "Master Catalogue JSON seed."
        ),
    )
    def seed_master_catalogue(
        seed_file: str,
    ) -> None:
        """
        Synchronize the platform-owned Master Catalogue.
        """

        from app.services.platform import (
            MasterCatalogueSeedError,
            MasterCatalogueSeedService,
        )

        try:
            result = (
                MasterCatalogueSeedService(
                    db.session
                )
                .import_file(
                    seed_file
                )
            )

            db.session.commit()

        except MasterCatalogueSeedError as exc:
            db.session.rollback()

            raise click.ClickException(
                str(exc)
            ) from exc

        except Exception:
            db.session.rollback()
            raise

        click.echo(
            "Master Catalogue synchronized."
        )

        click.echo(
            "Master items: "
            f"{result.master_items.created} created, "
            f"{result.master_items.updated} updated, "
            f"{result.master_items.unchanged} unchanged."
        )

        click.echo(
            "Suppliers: "
            f"{result.suppliers.created} created, "
            f"{result.suppliers.updated} updated, "
            f"{result.suppliers.unchanged} unchanged."
        )

        click.echo(
            "Mappings: "
            f"{result.mappings.created} created, "
            f"{result.mappings.updated} updated, "
            f"{result.mappings.unchanged} unchanged."
        )

        click.echo(
            "Prices: "
            f"{result.prices.created} created, "
            f"{result.prices.updated} updated, "
            f"{result.prices.unchanged} unchanged."
        )


# =============================================================================
# Application Factory
# =============================================================================

def create_app(
    config_class: type[Config] = Config,
) -> Flask:
    """
    Create and configure the Hela360 application.

    The application factory is responsible for:

    1. Creating the Flask application instance.
    2. Loading application configuration.
    3. Initializing extensions.
    4. Registering API blueprints.
    5. Registering global API error handlers.
    6. Registering CLI commands.

    Returns
    -------
    Flask
        A fully configured Flask application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions.
    register_extensions(app)

    # Import database models for SQLAlchemy metadata discovery.
    from app import models  # noqa: F401

    # Register REST API blueprints.
    register_blueprints(app)

    # Register centralized API exception handlers.
    from app.api.errors import register_error_handlers

    register_error_handlers(app)

    # Register custom Flask CLI commands.
    register_commands(app)

    return app
