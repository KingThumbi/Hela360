from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import or_
from sqlalchemy.orm import noload

from app.errors import ValidationError
from app.models import Branch, Customer, Sale, Till, User


ALLOWED_SALE_STATUSES = {
    "completed",
    "paid",
    "partially_paid",
    "voided",
    "partially_refunded",
    "refunded",
}


@dataclass(frozen=True)
class SalesListFilters:
    page: int = 1
    per_page: int = 25
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    status: str | None = None
    customer_id: str | None = None

    @classmethod
    def from_query(cls, args) -> "SalesListFilters":
        page = _positive_int(args.get("page"), "page", 1)
        per_page = _positive_int(args.get("per_page"), "per_page", 25)
        search = _optional_text(args.get("search") or args.get("q"))
        status = _optional_text(args.get("status"))
        customer_id = _optional_text(args.get("customer_id"))

        if status and status not in ALLOWED_SALE_STATUSES:
            raise ValidationError("status is not supported.")

        return cls(
            page=page,
            per_page=per_page,
            search=search,
            date_from=_date_start(args.get("date_from"), "date_from"),
            date_to=_date_end(args.get("date_to"), "date_to"),
            status=status,
            customer_id=customer_id,
        )


def _positive_int(value, field_name: str, default: int) -> int:
    if value in (None, ""):
        return default

    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"{field_name} must be a positive integer."
        ) from exc

    if parsed < 1:
        raise ValidationError(f"{field_name} must be a positive integer.")

    return parsed


def _optional_text(value) -> str | None:
    if value in (None, ""):
        return None

    normalized = str(value).strip()
    return normalized or None


def _parse_date(value, field_name: str):
    normalized = _optional_text(value)
    if normalized is None:
        return None

    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError as exc:
        raise ValidationError(
            f"{field_name} must be a valid date in YYYY-MM-DD format."
        ) from exc


def _date_start(value, field_name: str) -> datetime | None:
    parsed = _parse_date(value, field_name)
    if parsed is None:
        return None
    return datetime.combine(parsed, datetime.min.time()).replace(
        tzinfo=timezone.utc
    )


def _date_end(value, field_name: str) -> datetime | None:
    parsed = _parse_date(value, field_name)
    if parsed is None:
        return None
    return datetime.combine(parsed, datetime.max.time()).replace(
        tzinfo=timezone.utc
    )


def _decimal(value, default: str = "0.00") -> str:
    if value is None:
        return default
    if isinstance(value, Decimal):
        return str(value)
    return str(value)


def _timestamp(value) -> str | None:
    return value.isoformat() if value else None


def _full_name(record) -> str | None:
    parts = [
        getattr(record, "first_name", None),
        getattr(record, "other_names", None),
        getattr(record, "last_name", None),
    ]
    name = " ".join(part.strip() for part in parts if part and part.strip())
    return name or getattr(record, "username", None)


def _pagination(page: int, per_page: int, total: int) -> dict:
    pages = (total + per_page - 1) // per_page if per_page else 1
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
        "has_prev": page > 1,
        "has_next": page < pages,
    }


class SalesQueryService:
    def __init__(self, session):
        self.session = session

    def list_sales(
        self,
        *,
        tenant_id: str,
        branch_id: str | None,
        filters: SalesListFilters,
    ) -> tuple[list[dict], dict]:
        if not branch_id:
            raise ValidationError(
                "Authenticated user is not assigned to a branch."
            )

        branch = (
            self.session.query(Branch)
            .filter(
                Branch.id == branch_id,
                Branch.tenant_id == tenant_id,
                Branch.is_active.is_(True),
            )
            .first()
        )
        if not branch:
            raise ValidationError("Authenticated branch is not active.")

        query = (
            self.session.query(Sale)
            .outerjoin(
                Customer,
                (Customer.id == Sale.customer_id)
                & (Customer.tenant_id == Sale.tenant_id),
            )
            .filter(
                Sale.tenant_id == tenant_id,
                Sale.branch_id == branch_id,
            )
        )

        if filters.search:
            like = f"%{filters.search}%"
            query = query.filter(
                or_(
                    Sale.sale_number.ilike(like),
                    Customer.customer_number.ilike(like),
                    Customer.first_name.ilike(like),
                    Customer.last_name.ilike(like),
                    Customer.other_names.ilike(like),
                    Customer.phone.ilike(like),
                )
            )

        if filters.date_from:
            query = query.filter(Sale.sale_date >= filters.date_from)

        if filters.date_to:
            query = query.filter(Sale.sale_date <= filters.date_to)

        if filters.status:
            query = query.filter(Sale.status == filters.status)

        if filters.customer_id:
            customer = (
                self.session.query(Customer.id)
                .filter(
                    Customer.id == filters.customer_id,
                    Customer.tenant_id == tenant_id,
                )
                .first()
            )
            if not customer:
                raise ValidationError("customer_id is not valid.")
            query = query.filter(Sale.customer_id == filters.customer_id)

        total = query.count()
        sales = (
            query.order_by(Sale.sale_date.desc(), Sale.id.desc())
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
            .all()
        )

        return (
            self._serialize_sales(sales),
            _pagination(filters.page, filters.per_page, total),
        )

    def _serialize_sales(self, sales: list[Sale]) -> list[dict]:
        customer_ids = {
            str(sale.customer_id)
            for sale in sales
            if sale.customer_id
        }
        cashier_ids = {
            str(sale.cashier_id)
            for sale in sales
            if sale.cashier_id
        }
        till_ids = {
            str(sale.till_id)
            for sale in sales
            if sale.till_id
        }

        customers = self._records_by_id(Customer, customer_ids)
        cashiers = self._records_by_id(User, cashier_ids)
        tills = self._records_by_id(Till, till_ids)

        return [
            self._serialize_sale(
                sale,
                customers.get(str(sale.customer_id)),
                cashiers.get(str(sale.cashier_id)),
                tills.get(str(sale.till_id)),
            )
            for sale in sales
        ]

    def _records_by_id(self, model, ids: set[str]) -> dict[str, object]:
        if not ids:
            return {}

        records = (
            self.session.query(model)
            .options(noload("*"))
            .filter(model.id.in_(ids))
            .all()
        )
        return {str(record.id): record for record in records}

    def _serialize_sale(
        self,
        sale: Sale,
        customer: Customer | None,
        cashier: User | None,
        till: Till | None,
    ) -> dict:
        return {
            "id": str(sale.id),
            "sale_number": sale.sale_number,
            "status": sale.status,
            "sold_at": _timestamp(sale.sale_date),
            "created_at": _timestamp(sale.created_at),
            "customer": self._serialize_customer(customer),
            "cashier": self._serialize_cashier(cashier),
            "till": self._serialize_till(till),
            "till_shift_id": str(sale.till_shift_id)
            if sale.till_shift_id
            else None,
            "subtotal": _decimal(sale.subtotal),
            "discount_amount": _decimal(sale.discount_amount),
            "tax_amount": _decimal(sale.tax_amount),
            "total_amount": _decimal(sale.total_amount),
            "paid_amount": _decimal(sale.paid_amount),
            "balance_due": _decimal(sale.balance_due),
            "refund_status": getattr(sale, "refund_status", None),
            "refunded_amount": _decimal(
                getattr(sale, "refunded_amount", None)
            ),
        }

    def _serialize_customer(self, customer: Customer | None) -> dict | None:
        if not customer:
            return None

        return {
            "id": str(customer.id),
            "customer_number": customer.customer_number,
            "full_name": _full_name(customer),
            "phone": customer.phone,
        }

    def _serialize_cashier(self, cashier: User | None) -> dict | None:
        if not cashier:
            return None

        return {
            "id": str(cashier.id),
            "name": _full_name(cashier),
            "username": cashier.username,
        }

    def _serialize_till(self, till: Till | None) -> dict | None:
        if not till:
            return None

        return {
            "id": str(till.id),
            "code": till.code,
            "name": till.name,
        }
