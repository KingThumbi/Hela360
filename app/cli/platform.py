"""
Hela360 Platform CLI
====================

Administrative commands for the Hela360 platform domain.

These commands operate on Platform IAM and other platform-owned services.
They must not be used as tenant administration shortcuts.
"""

from __future__ import annotations

import click

from app.extensions import db
from app.services.platform.super_admin_service import (
    SuperAdminProvisioningError,
    SuperAdminService,
)


@click.group("platform")
def platform_cli() -> None:
    """Hela360 platform administration commands."""


@platform_cli.command(
    "bootstrap-super-admin"
)
@click.option(
    "--email",
    prompt="Email",
    required=True,
    help="Global Hela360 Office Super Admin email address.",
)
@click.option(
    "--username",
    prompt="Username",
    required=True,
    help="Global Hela360 Office username.",
)
@click.option(
    "--first-name",
    prompt="First name",
    required=True,
    help="Super Admin first name.",
)
@click.option(
    "--last-name",
    prompt="Last name",
    default="",
    show_default=False,
    help="Optional Super Admin last name.",
)
@click.password_option(
    "--password",
    prompt="Password",
    confirmation_prompt=True,
)
def bootstrap_super_admin(
    email: str,
    username: str,
    first_name: str,
    last_name: str,
    password: str,
) -> None:
    """
    Provision the root Hela360 Office Super Admin.

    Password input is hidden and confirmed interactively.
    """

    try:
        result = SuperAdminService(
            db.session
        ).provision(
            email=email,
            username=username,
            first_name=first_name,
            last_name=last_name or None,
            password=password,
        )

        db.session.commit()

    except SuperAdminProvisioningError as exc:
        db.session.rollback()

        raise click.ClickException(
            str(exc)
        ) from exc

    except Exception:
        db.session.rollback()
        raise

    click.echo(
        "Hela360 Super Admin provisioning completed."
    )

    click.echo(
        f"User ID: {result.platform_user_id}"
    )

    click.echo(
        f"Email: {result.email}"
    )

    click.echo(
        f"Username: {result.username}"
    )

    click.echo(
        "User created: "
        + (
            "yes"
            if result.user_created
            else "no"
        )
    )

    click.echo(
        "Super Admin role assigned: "
        + (
            "yes"
            if result.role_assigned
            else "no"
        )
    )

    click.echo(
        "Platform permissions synchronized: "
        + (
            "yes"
            if result.permissions_synchronized
            else "no"
        )
    )

    click.echo(
        "Platform roles synchronized: "
        + (
            "yes"
            if result.roles_synchronized
            else "no"
        )
    )


def register_platform_cli(
    app,
) -> None:
    """Register Hela360 platform CLI commands."""

    app.cli.add_command(
        platform_cli
    )


__all__ = [
    "platform_cli",
    "register_platform_cli",
]
