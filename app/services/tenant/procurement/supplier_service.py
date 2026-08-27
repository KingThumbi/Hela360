from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.errors import ConflictError, LifecycleError, NotFoundError
from app.extensions import db
from app.models import Supplier
from app.schemas import CreateSupplierRequest, SupplierListFilters, UpdateSupplierRequest
from app.services.common.number_sequence_service import (
    NumberSequenceService,
)


class SupplierService:
    def list_suppliers(
        self,
        tenant_id: str,
        filters: SupplierListFilters,
    ) -> tuple[list[Supplier], dict[str, int | bool]]:
        query = Supplier.query.filter_by(tenant_id=tenant_id)

        if filters.search:
            like = f"%{filters.search}%"
            query = query.filter(
                db.or_(
                    Supplier.supplier_code.ilike(like),
                    Supplier.name.ilike(like),
                    Supplier.legal_name.ilike(like),
                    Supplier.contact_person.ilike(like),
                    Supplier.email.ilike(like),
                    Supplier.phone.ilike(like),
                    Supplier.tax_number.ilike(like),
                    Supplier.registration_number.ilike(like),
                )
            )

        if filters.is_active is not None:
            query = query.filter(Supplier.is_active == filters.is_active)

        total = query.count()
        items = (
            query.order_by(Supplier.name.asc(), Supplier.supplier_code.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
            .all()
        )

        pages = (total + filters.page_size - 1) // filters.page_size
        return items, {
            "page": filters.page,
            "page_size": filters.page_size,
            "total": total,
            "pages": pages,
            "has_next": filters.page < pages,
            "has_prev": filters.page > 1,
        }

    def get_supplier(self, tenant_id: str, supplier_id: str) -> Supplier:
        supplier = Supplier.query.filter_by(
            id=supplier_id,
            tenant_id=tenant_id,
        ).first()

        if supplier is None:
            raise NotFoundError("Supplier not found.")

        return supplier

    def create_supplier(
        self,
        tenant_id: str,
        request: CreateSupplierRequest,
    ) -> Supplier:
        """
        Create a tenant-owned supplier.

        Supplier codes may be supplied explicitly. When omitted, Hela360
        generates the next tenant-scoped supplier code.

        The persisted Supplier model always retains a non-null supplier_code.
        """

        try:
            supplier_code = (
                request.supplier_code
                or NumberSequenceService(
                    db.session
                ).next_supplier_code(
                    tenant_id=tenant_id,
                )
            )

            self._ensure_unique(
                tenant_id,
                supplier_code=supplier_code,
                tax_number=request.tax_number,
                registration_number=request.registration_number,
            )

            payload = asdict(request)
            payload["supplier_code"] = supplier_code

            supplier = Supplier(
                tenant_id=tenant_id,
                **payload,
            )

            db.session.add(supplier)
            db.session.commit()

        except Exception:
            # Number allocation and Supplier persistence belong to the same
            # transaction. Any failure must roll back both operations.
            db.session.rollback()
            raise

        return supplier

    def update_supplier(
        self,
        tenant_id: str,
        supplier_id: str,
        request: UpdateSupplierRequest,
    ) -> Supplier:
        supplier = self.get_supplier(tenant_id, supplier_id)

        updates = {
            key: value
            for key, value in asdict(request).items()
            if value is not None
        }

        self._ensure_unique(
            tenant_id,
            tax_number=updates.get("tax_number"),
            registration_number=updates.get(
                "registration_number"
            ),
            exclude_supplier_id=supplier.id,
        )

        for field, value in updates.items():
            setattr(supplier, field, value)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise

        return supplier

    def deactivate_supplier(
        self,
        tenant_id: str,
        supplier_id: str,
    ) -> Supplier:
        supplier = self.get_supplier(tenant_id, supplier_id)

        if not supplier.is_active:
            raise LifecycleError("Supplier is already inactive.")

        supplier.is_active = False
        db.session.commit()
        return supplier

    def reactivate_supplier(
        self,
        tenant_id: str,
        supplier_id: str,
    ) -> Supplier:
        supplier = self.get_supplier(tenant_id, supplier_id)

        if supplier.is_active:
            raise LifecycleError("Supplier is already active.")

        supplier.is_active = True
        db.session.commit()
        return supplier

    def _ensure_unique(
        self,
        tenant_id: str,
        *,
        supplier_code: Any = None,
        tax_number: Any = None,
        registration_number: Any = None,
        exclude_supplier_id: str | None = None,
    ) -> None:
        checks = (
            ("supplier_code", supplier_code, "supplier_code already exists."),
            ("tax_number", tax_number, "tax_number already exists."),
            (
                "registration_number",
                registration_number,
                "registration_number already exists.",
            ),
        )

        for field, value, message in checks:
            if value in (None, ""):
                continue

            query = Supplier.query.filter_by(
                tenant_id=tenant_id,
                **{field: value},
            )

            if exclude_supplier_id is not None:
                query = query.filter(Supplier.id != exclude_supplier_id)

            if query.first() is not None:
                raise ConflictError(message)


supplier_service = SupplierService()


__all__ = ["SupplierService", "supplier_service"]
