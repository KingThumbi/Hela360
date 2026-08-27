"""
Hela360 Number Sequence Service
===============================

Concurrency-safe allocator for tenant-owned human-readable identifiers.

Design
------
The sequence namespace determines the independent numeric series.

Examples
--------
Product:
    DPL-2026-000001
    DPL-2026-000002
    DPL-2027-000003

Supplier:
    DPL-SUP-000001
    DPL-SUP-000002

The product year is presentation metadata only. The underlying product
sequence remains continuous across calendar years.
"""

from __future__ import annotations

from datetime import datetime

from app.errors import ValidationError
from app.models import (
    NumberSequence,
    Tenant,
)


class NumberSequenceService:
    def __init__(self, session):
        self.session = session

    # ---------------------------------------------------------------------
    # Tenant identity
    # ---------------------------------------------------------------------

    def _business_code(
        self,
        *,
        tenant_id: str,
    ) -> str:
        tenant = (
            self.session.query(Tenant)
            .filter(
                Tenant.id == str(tenant_id)
            )
            .first()
        )

        if tenant is None:
            raise ValidationError(
                "Tenant not found."
            )

        business_code = (
            tenant.business_code or ""
        ).strip().upper()

        if not business_code:
            raise ValidationError(
                "Tenant business_code must be configured "
                "before system codes can be generated."
            )

        return business_code

    # ---------------------------------------------------------------------
    # Sequence allocation
    # ---------------------------------------------------------------------

    def _next_value(
        self,
        *,
        tenant_id: str,
        namespace: str,
    ) -> int:
        normalized_namespace = (
            namespace.strip().lower()
        )

        if not normalized_namespace:
            raise ValidationError(
                "Sequence namespace is required."
            )

        sequence = (
            self.session.query(NumberSequence)
            .filter(
                NumberSequence.tenant_id
                == str(tenant_id),
                NumberSequence.namespace
                == normalized_namespace,
            )
            .with_for_update()
            .first()
        )

        if sequence is None:
            sequence = NumberSequence(
                tenant_id=str(tenant_id),
                namespace=normalized_namespace,
                next_value=1,
            )

            self.session.add(sequence)
            self.session.flush()

        value = int(sequence.next_value)

        sequence.next_value = value + 1

        return value

    # ---------------------------------------------------------------------
    # Generic master-data codes
    # ---------------------------------------------------------------------

    def next_master_code(
        self,
        *,
        tenant_id: str,
        namespace: str,
        prefix: str,
        width: int = 6,
    ) -> str:
        business_code = self._business_code(
            tenant_id=tenant_id,
        )

        normalized_prefix = (
            prefix.strip().upper()
        )

        if not normalized_prefix:
            raise ValidationError(
                "Code prefix is required."
            )

        if width < 1:
            raise ValidationError(
                "Code width must be positive."
            )

        value = self._next_value(
            tenant_id=tenant_id,
            namespace=namespace,
        )

        return (
            f"{business_code}-"
            f"{normalized_prefix}-"
            f"{value:0{width}d}"
        )

    # ---------------------------------------------------------------------
    # Product SKU
    # ---------------------------------------------------------------------

    def next_product_sku(
        self,
        *,
        tenant_id: str,
        generated_at: datetime,
    ) -> str:
        business_code = self._business_code(
            tenant_id=tenant_id,
        )

        value = self._next_value(
            tenant_id=tenant_id,
            namespace="product",
        )

        return (
            f"{business_code}-"
            f"{generated_at.year}-"
            f"{value:06d}"
        )

    # ---------------------------------------------------------------------
    # Supplier
    # ---------------------------------------------------------------------

    def next_supplier_code(
        self,
        *,
        tenant_id: str,
    ) -> str:
        return self.next_master_code(
            tenant_id=tenant_id,
            namespace="supplier",
            prefix="SUP",
        )


number_sequence_service = NumberSequenceService
