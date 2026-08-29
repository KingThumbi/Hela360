"""
Product Identity Service
========================

Centralized tenant-scoped Product identity allocation.

Responsibilities
----------------
* Normalize manually supplied internal SKUs.
* Enforce tenant-scoped internal SKU uniqueness.
* Allocate automatic Product SKUs through NumberSequenceService.
* Detect generated SKU collisions.
* Retry automatic allocation safely.
* Keep Product identity rules out of API routes.
* Provide one canonical SKU path for normal Product creation and
  future master-catalogue adoption.

The service does not create or persist Product records.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import Product
from app.services.common.number_sequence_service import NumberSequenceService
from app.errors import ValidationError


class ProductSkuConflictError(ValidationError):
    """
    Raised when a requested internal SKU already belongs to another Product
    within the same tenant.
    """


class ProductIdentityService:
    """
    Resolve tenant-scoped Product identity values.

    Product internal SKUs are unique within a tenant.

    A manually supplied SKU is preserved after whitespace normalization and
    uniqueness validation.

    When no SKU is supplied, a tenant-wide sequence-backed SKU is allocated
    through NumberSequenceService.

    Generated candidates are checked against existing Products because legacy
    or manually created Product records may already use a sequence-shaped SKU.
    """

    MAX_SKU_ALLOCATION_ATTEMPTS = 100

    def __init__(self, session: Session):
        self.session = session
        self.sequence_service = NumberSequenceService(session)

    def resolve_internal_sku(
        self,
        *,
        tenant_id: str,
        supplied_sku: str | None = None,
        generated_at: datetime | None = None,
    ) -> str:
        """
        Return a valid tenant-scoped internal Product SKU.

        Parameters
        ----------
        tenant_id:
            Tenant that will own the Product.

        supplied_sku:
            Optional manually supplied SKU. Leading and trailing whitespace
            is removed. A non-empty supplied SKU is preserved.

        generated_at:
            Optional timestamp used when formatting an automatically generated
            SKU. Primarily useful for deterministic tests. Defaults to the
            current UTC timestamp.

        Returns
        -------
        str
            Resolved unique internal SKU.

        Raises
        ------
        ValidationError
            If a supplied SKU already exists for the tenant or if a unique
            generated SKU cannot be allocated within the retry limit.
        """

        normalized_sku = (supplied_sku or "").strip()

        if normalized_sku:
            self._ensure_internal_sku_available(
                tenant_id=tenant_id,
                internal_sku=normalized_sku,
            )
            return normalized_sku

        allocation_time = generated_at or datetime.now(UTC)

        for _ in range(self.MAX_SKU_ALLOCATION_ATTEMPTS):
            candidate = self.sequence_service.next_product_sku(
                tenant_id=tenant_id,
                generated_at=allocation_time,
            )

            if not self._internal_sku_exists(
                tenant_id=tenant_id,
                internal_sku=candidate,
            ):
                return candidate

        raise ValidationError(
            "Unable to allocate a unique product SKU."
        )

    def _ensure_internal_sku_available(
        self,
        *,
        tenant_id: str,
        internal_sku: str,
    ) -> None:
        if self._internal_sku_exists(
            tenant_id=tenant_id,
            internal_sku=internal_sku,
        ):
            raise ProductSkuConflictError(
                "A product with that internal_sku already exists."
            )

    def _internal_sku_exists(
        self,
        *,
        tenant_id: str,
        internal_sku: str,
    ) -> bool:
        return (
            self.session.query(Product.id)
            .filter(
                Product.tenant_id == tenant_id,
                Product.internal_sku == internal_sku,
            )
            .first()
            is not None
        )
