"""
Hela360 Tenant Provisioning Service
===================================

Creates and maintains baseline configuration required by every tenant.

Responsibilities
----------------
- Ensure tenant business code exists
- Synchronize Hela360's canonical permission catalogue
- Provision canonical built-in tenant roles
- Provision jurisdiction-specific tax classifications
- Keep tenant bootstrap logic outside feature routes
- Support existing-tenant backfills
- Support future tenant onboarding workflows

Architectural boundaries
------------------------
- This service provisions tenant-level defaults only.
- Hela360 platform/back-office administration is a separate domain.
- Tenant authorization policy originates from canonical Hela360 IAM policy.
- Authorization policy MUST NOT be copied from another tenant.
- Human administrator onboarding and role assignment remain separate concerns.
- Transaction ownership remains with the caller.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.errors import ValidationError
from app.models import TaxCode, Tenant
from app.services.platform.permission_catalogue_service import (
    PermissionCatalogueService,
)
from app.services.platform.system_role_provisioning_service import (
    SystemRoleProvisioningService,
)


@dataclass(frozen=True, slots=True)
class TaxCodeDefinition:
    code: str
    name: str
    rate: Decimal
    description: str


KENYA_TAX_CODES = (
    TaxCodeDefinition(
        code="VAT16",
        name="Standard VAT",
        rate=Decimal("16.0000"),
        description="Kenya standard VAT classification.",
    ),
    TaxCodeDefinition(
        code="ZERO",
        name="Zero Rated",
        rate=Decimal("0.0000"),
        description="Kenya zero-rated supply classification.",
    ),
    TaxCodeDefinition(
        code="EXEMPT",
        name="VAT Exempt",
        rate=Decimal("0.0000"),
        description="Kenya VAT-exempt supply classification.",
    ),
)


class TenantProvisioningService:
    def __init__(self, session):
        self.session = session

    def provision_defaults(
        self,
        *,
        tenant_id: str,
    ) -> Tenant:
        tenant = (
            self.session.query(Tenant)
            .filter(
                Tenant.id == str(tenant_id),
            )
            .first()
        )

        if tenant is None:
            raise ValidationError(
                "Tenant not found."
            )

        # --------------------------------------------------------------
        # Canonical tenant IAM
        # --------------------------------------------------------------
        #
        # The permission catalogue is global, while built-in roles are
        # tenant-scoped. Both operations are idempotent and leave transaction
        # ownership with the caller.

        PermissionCatalogueService(
            self.session
        ).synchronize()

        SystemRoleProvisioningService(
            self.session
        ).synchronize(
            tenant_id=str(tenant.id),
        )

        # --------------------------------------------------------------
        # Jurisdiction-specific defaults
        # --------------------------------------------------------------

        country_code = (
            tenant.country_code or ""
        ).strip().upper()

        if country_code == "KE":
            self._provision_tax_codes(
                tenant=tenant,
                definitions=KENYA_TAX_CODES,
            )

        return tenant

    def _provision_tax_codes(
        self,
        *,
        tenant: Tenant,
        definitions: tuple[TaxCodeDefinition, ...],
    ) -> None:
        for definition in definitions:
            tax_code = (
                self.session.query(TaxCode)
                .filter(
                    TaxCode.tenant_id
                    == str(tenant.id),
                    TaxCode.code
                    == definition.code,
                )
                .first()
            )

            if tax_code is None:
                tax_code = TaxCode(
                    tenant_id=str(tenant.id),
                    code=definition.code,
                    name=definition.name,
                    rate=definition.rate,
                    description=definition.description,
                    is_active=True,
                )

                self.session.add(tax_code)

            else:
                tax_code.name = definition.name
                tax_code.rate = definition.rate
                tax_code.description = definition.description
                tax_code.is_active = True
