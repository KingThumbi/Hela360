from __future__ import annotations

from types import SimpleNamespace

from app.auth.permissions import ALL_PERMISSIONS
from app.services.platform.permission_catalogue_service import (
    CANONICAL_PERMISSION_DEFINITIONS,
    PermissionCatalogueService,
)


def test_definitions_match_canonical_registry() -> None:
    codes = tuple(
        definition.code
        for definition in CANONICAL_PERMISSION_DEFINITIONS
    )

    assert set(codes) == set(ALL_PERMISSIONS)
    assert len(codes) == len(set(codes))
    assert "*" not in codes


def test_definition_metadata_is_deterministic() -> None:
    definitions = {
        definition.code: definition
        for definition in CANONICAL_PERMISSION_DEFINITIONS
    }

    products = definitions["products.view"]

    assert products.module_code == "products"
    assert products.name == "Products View"
    assert products.description


def test_sync_result_changed_property() -> None:
    from app.services.platform.permission_catalogue_service import (
        PermissionCatalogueSyncResult,
    )

    unchanged = PermissionCatalogueSyncResult(
        created=(),
        updated=(),
        unchanged=("products.view",),
        unexpected=(),
    )

    created = PermissionCatalogueSyncResult(
        created=("products.view",),
        updated=(),
        unchanged=(),
        unexpected=(),
    )

    assert unchanged.changed is False
    assert created.changed is True
