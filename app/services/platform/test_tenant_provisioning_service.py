from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.platform import tenant_provisioning_service as module
from app.services.platform.tenant_provisioning_service import (
    TenantProvisioningService,
)


class FakeQuery:
    def __init__(self, result):
        self.result = result

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.result


class FakeSession:
    def __init__(self, tenant):
        self.tenant = tenant
        self.added = []

    def query(self, _model):
        return FakeQuery(self.tenant)

    def add(self, value):
        self.added.append(value)


def tenant(
    *,
    tenant_id: str = "tenant-1",
    country_code: str = "KE",
):
    return SimpleNamespace(
        id=tenant_id,
        country_code=country_code,
    )


def test_provision_defaults_synchronizes_canonical_iam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_tenant = tenant()
    session = FakeSession(fake_tenant)

    calls: list[tuple[str, str | None]] = []

    class FakePermissionCatalogueService:
        def __init__(self, supplied_session):
            assert supplied_session is session

        def synchronize(self):
            calls.append(("permissions", None))
            return SimpleNamespace()

    class FakeSystemRoleProvisioningService:
        def __init__(self, supplied_session):
            assert supplied_session is session

        def synchronize(self, *, tenant_id: str):
            calls.append(("roles", tenant_id))
            return SimpleNamespace()

    monkeypatch.setattr(
        module,
        "PermissionCatalogueService",
        FakePermissionCatalogueService,
    )

    monkeypatch.setattr(
        module,
        "SystemRoleProvisioningService",
        FakeSystemRoleProvisioningService,
    )

    service = TenantProvisioningService(session)

    monkeypatch.setattr(
        service,
        "_provision_tax_codes",
        lambda **_kwargs: calls.append(("tax", fake_tenant.id)),
    )

    result = service.provision_defaults(
        tenant_id=fake_tenant.id,
    )

    assert result is fake_tenant

    assert calls == [
        ("permissions", None),
        ("roles", "tenant-1"),
        ("tax", "tenant-1"),
    ]


def test_non_kenyan_tenant_still_receives_iam(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_tenant = tenant(
        country_code="UG",
    )

    session = FakeSession(fake_tenant)

    calls: list[tuple[str, str | None]] = []

    class FakePermissionCatalogueService:
        def __init__(self, supplied_session):
            assert supplied_session is session

        def synchronize(self):
            calls.append(("permissions", None))
            return SimpleNamespace()

    class FakeSystemRoleProvisioningService:
        def __init__(self, supplied_session):
            assert supplied_session is session

        def synchronize(self, *, tenant_id: str):
            calls.append(("roles", tenant_id))
            return SimpleNamespace()

    monkeypatch.setattr(
        module,
        "PermissionCatalogueService",
        FakePermissionCatalogueService,
    )

    monkeypatch.setattr(
        module,
        "SystemRoleProvisioningService",
        FakeSystemRoleProvisioningService,
    )

    service = TenantProvisioningService(session)

    monkeypatch.setattr(
        service,
        "_provision_tax_codes",
        lambda **_kwargs: calls.append(("tax", fake_tenant.id)),
    )

    service.provision_defaults(
        tenant_id=fake_tenant.id,
    )

    assert calls == [
        ("permissions", None),
        ("roles", "tenant-1"),
    ]
