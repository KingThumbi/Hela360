from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from app import create_app
from app.services.platform.super_admin_service import (
    SuperAdminProvisioningError,
    SuperAdminProvisioningResult,
)


@pytest.fixture()
def app():
    return create_app()


def test_platform_group_is_registered(
    app,
):
    runner = app.test_cli_runner()

    result = runner.invoke(
        args=[
            "platform",
            "--help",
        ]
    )

    assert result.exit_code == 0

    assert (
        "bootstrap-super-admin"
        in result.output
    )


def test_bootstrap_super_admin_commits_success(
    app,
):
    result_value = SuperAdminProvisioningResult(
        platform_user_id="platform-user-1",
        email="root@hela360.invalid",
        username="root",
        user_created=True,
        role_assigned=True,
        permissions_synchronized=True,
        roles_synchronized=True,
    )

    service = Mock()
    service.provision.return_value = result_value

    runner = app.test_cli_runner()

    with (
        patch(
            "app.cli.platform.SuperAdminService",
            return_value=service,
        ),
        patch(
            "app.cli.platform.db.session.commit"
        ) as commit,
        patch(
            "app.cli.platform.db.session.rollback"
        ) as rollback,
    ):
        result = runner.invoke(
            args=[
                "platform",
                "bootstrap-super-admin",
            ],
            input=(
                "root@hela360.invalid\n"
                "root\n"
                "Hela360\n"
                "Administrator\n"
                "PlatformRoot@12345\n"
                "PlatformRoot@12345\n"
            ),
        )

    assert result.exit_code == 0

    commit.assert_called_once()
    rollback.assert_not_called()

    service.provision.assert_called_once_with(
        email="root@hela360.invalid",
        username="root",
        first_name="Hela360",
        last_name="Administrator",
        password="PlatformRoot@12345",
    )

    assert (
        "Super Admin provisioning completed"
        in result.output
    )


def test_bootstrap_super_admin_rolls_back_known_error(
    app,
):
    service = Mock()

    service.provision.side_effect = (
        SuperAdminProvisioningError(
            "Provisioning rejected."
        )
    )

    runner = app.test_cli_runner()

    with (
        patch(
            "app.cli.platform.SuperAdminService",
            return_value=service,
        ),
        patch(
            "app.cli.platform.db.session.commit"
        ) as commit,
        patch(
            "app.cli.platform.db.session.rollback"
        ) as rollback,
    ):
        result = runner.invoke(
            args=[
                "platform",
                "bootstrap-super-admin",
            ],
            input=(
                "root@hela360.invalid\n"
                "root\n"
                "Hela360\n"
                "\n"
                "PlatformRoot@12345\n"
                "PlatformRoot@12345\n"
            ),
        )

    assert result.exit_code != 0

    commit.assert_not_called()
    rollback.assert_called_once()

    assert (
        "Provisioning rejected."
        in result.output
    )
