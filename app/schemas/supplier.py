from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from app.errors import ValidationError


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[0-9+().\-\s]{7,50}$")


def _clean_string(
    payload: dict[str, Any],
    field: str,
    *,
    max_length: int,
    required: bool = False,
    uppercase: bool = False,
    lowercase: bool = False,
) -> str | None:
    value = payload.get(field)
    if value in (None, ""):
        if required:
            raise ValidationError(f"{field} is required.")
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string.")
    cleaned = value.strip()
    if not cleaned:
        if required:
            raise ValidationError(f"{field} is required.")
        return None
    if len(cleaned) > max_length:
        raise ValidationError(f"{field} must be {max_length} characters or fewer.")
    if uppercase:
        return cleaned.upper()
    if lowercase:
        return cleaned.lower()
    return cleaned


def _clean_int(
    payload: dict[str, Any],
    field: str,
    *,
    default: int = 0,
) -> int:
    value = payload.get(field, default)
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be an integer.") from exc
    if parsed < 0:
        raise ValidationError(f"{field} must be non-negative.")
    return parsed


def _clean_decimal(
    payload: dict[str, Any],
    field: str,
    *,
    default: Decimal = Decimal("0"),
) -> Decimal:
    value = payload.get(field, default)
    if value in (None, ""):
        return default
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError(f"{field} must be a valid number.") from exc
    if parsed < 0:
        raise ValidationError(f"{field} must be non-negative.")
    return parsed


def _clean_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


@dataclass(slots=True)
class CreateSupplierRequest:
    supplier_code: str | None
    name: str
    legal_name: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    county_or_region: str | None = None
    country: str | None = None
    postal_code: str | None = None
    tax_number: str | None = None
    registration_number: str | None = None
    payment_terms_days: int = 0
    credit_limit: Decimal = Decimal("0")
    currency: str = "KES"
    notes: str | None = None
    is_active: bool = True

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CreateSupplierRequest":
        request = cls(
            supplier_code=_optional(
                payload,
                "supplier_code",
                max_length=50,
                uppercase=True,
            ),
            name=_clean_string(payload, "name", max_length=200, required=True),
            legal_name=_clean_string(payload, "legal_name", max_length=200),
            contact_person=_clean_string(payload, "contact_person", max_length=150),
            email=_clean_string(payload, "email", max_length=150, lowercase=True),
            phone=_clean_string(payload, "phone", max_length=50),
            alternate_phone=_clean_string(payload, "alternate_phone", max_length=50),
            address_line_1=_clean_string(payload, "address_line_1", max_length=200),
            address_line_2=_clean_string(payload, "address_line_2", max_length=200),
            city=_clean_string(payload, "city", max_length=100),
            county_or_region=_clean_string(payload, "county_or_region", max_length=100),
            country=_clean_string(payload, "country", max_length=100),
            postal_code=_clean_string(payload, "postal_code", max_length=30),
            tax_number=_clean_string(payload, "tax_number", max_length=80, uppercase=True),
            registration_number=_clean_string(
                payload,
                "registration_number",
                max_length=80,
                uppercase=True,
            ),
            payment_terms_days=_clean_int(payload, "payment_terms_days"),
            credit_limit=_clean_decimal(payload, "credit_limit"),
            currency=_clean_string(
                payload,
                "currency",
                max_length=3,
                uppercase=True,
            )
            or "KES",
            notes=_clean_string(payload, "notes", max_length=10000),
            is_active=_clean_bool(payload.get("is_active"), True),
        )
        _validate_contact_fields(request.email, request.phone, request.alternate_phone)
        if len(request.currency) != 3:
            raise ValidationError("currency must be a 3-letter ISO currency code.")
        return request


@dataclass(slots=True)
class UpdateSupplierRequest:
    name: str | None = None
    legal_name: str | None = None
    contact_person: str | None = None
    email: str | None = None
    phone: str | None = None
    alternate_phone: str | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    county_or_region: str | None = None
    country: str | None = None
    postal_code: str | None = None
    tax_number: str | None = None
    registration_number: str | None = None
    payment_terms_days: int | None = None
    credit_limit: Decimal | None = None
    currency: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "UpdateSupplierRequest":
        request = cls(
            name=_optional(payload, "name", max_length=200),
            legal_name=_optional(payload, "legal_name", max_length=200),
            contact_person=_optional(payload, "contact_person", max_length=150),
            email=_optional(payload, "email", max_length=150, lowercase=True),
            phone=_optional(payload, "phone", max_length=50),
            alternate_phone=_optional(payload, "alternate_phone", max_length=50),
            address_line_1=_optional(payload, "address_line_1", max_length=200),
            address_line_2=_optional(payload, "address_line_2", max_length=200),
            city=_optional(payload, "city", max_length=100),
            county_or_region=_optional(payload, "county_or_region", max_length=100),
            country=_optional(payload, "country", max_length=100),
            postal_code=_optional(payload, "postal_code", max_length=30),
            tax_number=_optional(payload, "tax_number", max_length=80, uppercase=True),
            registration_number=_optional(
                payload,
                "registration_number",
                max_length=80,
                uppercase=True,
            ),
            payment_terms_days=(
                _clean_int(payload, "payment_terms_days")
                if "payment_terms_days" in payload
                else None
            ),
            credit_limit=(
                _clean_decimal(payload, "credit_limit")
                if "credit_limit" in payload
                else None
            ),
            currency=_optional(payload, "currency", max_length=3, uppercase=True),
            notes=_optional(payload, "notes", max_length=10000),
            is_active=(
                _clean_bool(payload.get("is_active"), True)
                if "is_active" in payload
                else None
            ),
        )
        if "name" in payload and request.name is None:
            raise ValidationError("name cannot be blank.")
        if "currency" in payload and request.currency is None:
            raise ValidationError("currency cannot be blank.")
        _validate_contact_fields(request.email, request.phone, request.alternate_phone)
        if request.currency is not None and len(request.currency) != 3:
            raise ValidationError("currency must be a 3-letter ISO currency code.")
        return request


@dataclass(slots=True)
class SupplierListFilters:
    page: int = 1
    page_size: int = 25
    search: str | None = None
    is_active: bool | None = None

    @classmethod
    def from_query(cls, args) -> "SupplierListFilters":
        page = _positive_int(args.get("page"), "page", default=1, maximum=None)
        page_size = _positive_int(
            args.get("page_size") or args.get("per_page"),
            "page_size",
            default=25,
            maximum=100,
        )
        is_active = args.get("is_active")
        return cls(
            page=page,
            page_size=page_size,
            search=(args.get("search") or "").strip() or None,
            is_active=None if is_active is None else _clean_bool(is_active, False),
        )


def _optional(
    payload: dict[str, Any],
    field: str,
    *,
    max_length: int,
    uppercase: bool = False,
    lowercase: bool = False,
) -> str | None:
    if field not in payload:
        return None
    return _clean_string(
        payload,
        field,
        max_length=max_length,
        uppercase=uppercase,
        lowercase=lowercase,
    )


def _positive_int(
    value: Any,
    field: str,
    *,
    default: int,
    maximum: int | None,
) -> int:
    if value in (None, ""):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} must be an integer.") from exc
    if parsed < 1:
        raise ValidationError(f"{field} must be at least 1.")
    if maximum is not None and parsed > maximum:
        raise ValidationError(f"{field} must be {maximum} or less.")
    return parsed


def _validate_contact_fields(
    email: str | None,
    phone: str | None,
    alternate_phone: str | None,
) -> None:
    if email and not _EMAIL_RE.match(email):
        raise ValidationError("email must be a valid email address.")
    for field, value in (
        ("phone", phone),
        ("alternate_phone", alternate_phone),
    ):
        if value and not _PHONE_RE.match(value):
            raise ValidationError(f"{field} must be a valid phone number.")
