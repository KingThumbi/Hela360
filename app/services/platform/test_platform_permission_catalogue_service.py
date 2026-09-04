from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import create_app
from app.extensions import db
from app.models import PlatformPermission
from app.services.platform.platform_permission_catalogue_service import (
    PlatformPermissionCatalogueService,
)
from app.services.platform.platform_permission_policy import (
    ALL_PLATFORM_PERMISSIONS,
    get_platform_permission,
)


@pytest.fixture()
def platform_session():
    app = create_app()

    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        session = Session(
            bind=connection,
            expire_on_commit=False,
        )

        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
            connection.close()


def test_synchronize_creates_canonical_permissions(
    platform_session,
):
    service = PlatformPermissionCatalogueService(
        platform_session
    )

    result = service.synchronize()

    persisted = set(
        platform_session.scalars(
            select(PlatformPermission.code)
        ).all()
    )

    assert ALL_PLATFORM_PERMISSIONS <= persisted
    assert result.changed is True


def test_synchronize_is_idempotent(
    platform_session,
):
    service = PlatformPermissionCatalogueService(
        platform_session
    )

    service.synchronize()
    second = service.synchronize()

    assert second.changed is False


def test_synchronize_repairs_metadata(
    platform_session,
):
    service = PlatformPermissionCatalogueService(
        platform_session
    )

    service.synchronize()

    permission = platform_session.scalar(
        select(PlatformPermission).where(
            PlatformPermission.code
            == "platform.catalogue.read"
        )
    )

    assert permission is not None

    permission.name = "Incorrect"
    permission.module_code = "wrong"
    permission.description = "Wrong"

    platform_session.flush()

    result = service.synchronize()

    definition = get_platform_permission(
        "platform.catalogue.read"
    )

    assert definition is not None
    assert permission.name == definition.name
    assert permission.module_code == (
        definition.module_code
    )
    assert permission.description == (
        definition.description
    )

    item = next(
        item
        for item in result.permissions
        if item.code == "platform.catalogue.read"
    )

    assert item.metadata_updated is True


def test_canonical_permissions_requires_complete_catalogue(
    platform_session,
):
    service = PlatformPermissionCatalogueService(
        platform_session
    )

    with pytest.raises(
        RuntimeError,
        match="incomplete",
    ):
        service.canonical_permissions()
