from app.services.platform.platform_permission_policy import (
    ALL_PLATFORM_PERMISSIONS,
    PLATFORM_PERMISSION_DEFINITIONS,
    SYSTEM_PERMISSION,
    get_platform_permission,
    is_valid_platform_permission,
    list_platform_permissions,
)


def test_platform_permission_catalogue_has_unique_codes():
    codes = [
        definition.code
        for definition in PLATFORM_PERMISSION_DEFINITIONS
    ]

    assert len(codes) == len(set(codes))


def test_system_permission_is_canonical():
    assert SYSTEM_PERMISSION == "*"
    assert SYSTEM_PERMISSION in ALL_PLATFORM_PERMISSIONS


def test_office_access_is_canonical():
    assert (
        "platform.office.access"
        in ALL_PLATFORM_PERMISSIONS
    )


def test_permission_lookup():
    definition = get_platform_permission(
        "platform.catalogue.approve"
    )

    assert definition is not None
    assert definition.module_code == "catalogue"


def test_permission_validation():
    assert is_valid_platform_permission(
        "platform.users.read"
    )

    assert not is_valid_platform_permission(
        "products.read"
    )


def test_permission_listing_is_deterministic():
    assert list_platform_permissions() == sorted(
        ALL_PLATFORM_PERMISSIONS
    )
