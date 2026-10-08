from __future__ import annotations

import click

from app.extensions import db
from app.services.platform.permission_catalogue_service import PermissionCatalogueService
from app.services.tenant.finance import ChartOfAccountsError, ChartOfAccountsService


@click.group("finance")
def finance_cli() -> None:
    """Hela360 tenant Finance administration commands."""


@finance_cli.command("sync-permissions")
def sync_permissions() -> None:
    """Synchronize the canonical tenant Finance permissions."""
    try:
        result = PermissionCatalogueService(db.session).synchronize()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    click.echo("Finance permission catalogue synchronized.")
    click.echo(f"Created: {len(result.created)}")
    click.echo(f"Updated: {len(result.updated)}")
    click.echo(f"Unchanged: {len(result.unchanged)}")
    if result.unexpected:
        click.echo(
            "Unexpected persisted permissions preserved: "
            + ", ".join(result.unexpected)
        )


@finance_cli.command("seed-default-chart")
@click.option("--tenant-id", required=True)
def seed_default_chart(tenant_id: str) -> None:
    """Provision the controlled default Kenyan retail/pharmacy chart."""
    try:
        result = ChartOfAccountsService(db.session).seed_default_chart(
            tenant_id=tenant_id,
        )
        db.session.commit()
    except ChartOfAccountsError as exc:
        db.session.rollback()
        raise click.ClickException(str(exc)) from exc
    except Exception:
        db.session.rollback()
        raise

    click.echo("Default Chart of Accounts synchronized.")
    click.echo(f"Created: {len(result.created)}")
    click.echo(f"Unchanged: {len(result.unchanged)}")


def register_finance_cli(app) -> None:
    app.cli.add_command(finance_cli)


__all__ = ["finance_cli", "register_finance_cli"]
