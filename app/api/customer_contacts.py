from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.api.utils import current_identity as _current_identity
from app.extensions import db
from app.models import Customer, CustomerContact
from app.services.common.audit_actions import AuditAction
from app.services.common.audit_modules import AuditModule
from app.services.common.audit_service import audit_service
from app.services.tenant.auth.decorators import require_permission


bp = Blueprint("customer_contacts", __name__)


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def _to_bool(value, default=False) -> bool:
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    return bool(value)


def _clean_optional(value):
    if value is None:
        return None

    return str(value).strip() or None


def _customer_for_tenant(
    customer_id: str,
    tenant_id: str,
):
    return Customer.query.filter_by(
        id=customer_id,
        tenant_id=tenant_id,
    ).first()


def _serialize_contact(contact: CustomerContact) -> dict:
    return {
        "id": contact.id,
        "tenant_id": contact.tenant_id,
        "customer_id": contact.customer_id,
        "contact_name": contact.contact_name,
        "role_title": contact.role_title,
        "phone": contact.phone,
        "alternate_phone": contact.alternate_phone,
        "email": contact.email,
        "preferred_contact_method": contact.preferred_contact_method,
        "is_primary": contact.is_primary,
        "is_billing_contact": contact.is_billing_contact,
        "is_active": contact.is_active,
        "notes": contact.notes,
        "created_at": (
            contact.created_at.isoformat()
            if contact.created_at
            else None
        ),
        "updated_at": (
            contact.updated_at.isoformat()
            if contact.updated_at
            else None
        ),
    }


def _audit_contact(
    *,
    action: AuditAction,
    identity,
    contact: CustomerContact,
    old_values: dict | None = None,
    new_values: dict | None = None,
):
    audit_service.safe_log(
        module=AuditModule.CUSTOMERS,
        action=action,
        entity_type="CustomerContact",
        tenant_id=identity.tenant_id,
        entity_id=contact.id,
        user_id=identity.user_id,
        branch_id=getattr(identity, "branch_id", None),
        old_values=old_values,
        new_values=new_values,
        details={
            "customer_id": contact.customer_id,
        },
        commit=True,
    )


@bp.get("/customers/<customer_id>/contacts")
@require_permission("customers.view")
def list_customer_contacts(customer_id: str):
    identity = _current_identity()

    customer = _customer_for_tenant(
        customer_id,
        identity.tenant_id,
    )

    if customer is None:
        return _json_error("Customer not found.", 404)

    contacts = (
        CustomerContact.query
        .filter_by(
            tenant_id=identity.tenant_id,
            customer_id=customer.id,
        )
        .order_by(
            CustomerContact.is_active.desc(),
            CustomerContact.is_primary.desc(),
            CustomerContact.contact_name.asc(),
        )
        .all()
    )

    return jsonify(
        {
            "ok": True,
            "count": len(contacts),
            "items": [
                _serialize_contact(contact)
                for contact in contacts
            ],
        }
    )


@bp.get("/customers/<customer_id>/contacts/<contact_id>")
@require_permission("customers.view")
def get_customer_contact(
    customer_id: str,
    contact_id: str,
):
    identity = _current_identity()

    customer = _customer_for_tenant(
        customer_id,
        identity.tenant_id,
    )

    if customer is None:
        return _json_error("Customer not found.", 404)

    contact = CustomerContact.query.filter_by(
        id=contact_id,
        tenant_id=identity.tenant_id,
        customer_id=customer.id,
    ).first()

    if contact is None:
        return _json_error("Customer contact not found.", 404)

    return jsonify(
        {
            "ok": True,
            "item": _serialize_contact(contact),
        }
    )


@bp.post("/customers/<customer_id>/contacts")
@require_permission("customers.create")
def create_customer_contact(customer_id: str):
    identity = _current_identity()

    customer = _customer_for_tenant(
        customer_id,
        identity.tenant_id,
    )

    if customer is None:
        return _json_error("Customer not found.", 404)

    data = request.get_json(silent=True) or {}

    contact_name = _clean_optional(data.get("contact_name"))

    if not contact_name:
        return _json_error("contact_name is required.")

    is_primary = _to_bool(
        data.get("is_primary"),
        False,
    )

    is_active = _to_bool(
        data.get("is_active"),
        True,
    )

    if not is_active:
        is_primary = False

    contact = CustomerContact(
        tenant_id=identity.tenant_id,
        customer_id=customer.id,
        contact_name=contact_name,
        role_title=_clean_optional(data.get("role_title")),
        phone=_clean_optional(data.get("phone")),
        alternate_phone=_clean_optional(
            data.get("alternate_phone")
        ),
        email=(
            _clean_optional(data.get("email"))
            .lower()
            if _clean_optional(data.get("email"))
            else None
        ),
        preferred_contact_method=_clean_optional(
            data.get("preferred_contact_method")
        ),
        is_primary=is_primary,
        is_billing_contact=_to_bool(
            data.get("is_billing_contact"),
            False,
        ),
        is_active=is_active,
        notes=_clean_optional(data.get("notes")),
    )

    try:
        if is_primary:
            (
                CustomerContact.query
                .filter_by(
                    tenant_id=identity.tenant_id,
                    customer_id=customer.id,
                    is_active=True,
                    is_primary=True,
                )
                .update(
                    {
                        CustomerContact.is_primary: False,
                    },
                    synchronize_session=False,
                )
            )

        db.session.add(contact)
        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return _json_error(
            "Unable to create customer contact because the "
            "active primary contact constraint was violated.",
            409,
        )

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to create customer contact: {exc}",
            500,
        )

    _audit_contact(
        action=AuditAction.CUSTOMER_CONTACT_CREATED,
        identity=identity,
        contact=contact,
        new_values=_serialize_contact(contact),
    )

    return (
        jsonify(
            {
                "ok": True,
                "message": "Customer contact created successfully.",
                "item": _serialize_contact(contact),
            }
        ),
        201,
    )


@bp.patch("/customers/<customer_id>/contacts/<contact_id>")
@require_permission("customers.edit")
def update_customer_contact(
    customer_id: str,
    contact_id: str,
):
    identity = _current_identity()

    customer = _customer_for_tenant(
        customer_id,
        identity.tenant_id,
    )

    if customer is None:
        return _json_error("Customer not found.", 404)

    contact = CustomerContact.query.filter_by(
        id=contact_id,
        tenant_id=identity.tenant_id,
        customer_id=customer.id,
    ).first()

    if contact is None:
        return _json_error("Customer contact not found.", 404)

    data = request.get_json(silent=True) or {}

    allowed = {
        "contact_name",
        "role_title",
        "phone",
        "alternate_phone",
        "email",
        "preferred_contact_method",
        "is_primary",
        "is_billing_contact",
        "is_active",
        "notes",
    }

    supplied = set(data).intersection(allowed)

    if not supplied:
        return _json_error(
            "At least one customer contact field is required."
        )

    old_values = _serialize_contact(contact)

    for field in (
        "role_title",
        "phone",
        "alternate_phone",
        "preferred_contact_method",
        "notes",
    ):
        if field in data:
            setattr(
                contact,
                field,
                _clean_optional(data.get(field)),
            )

    if "contact_name" in data:
        contact_name = _clean_optional(
            data.get("contact_name")
        )
        if not contact_name:
            return _json_error("contact_name cannot be empty.")
        contact.contact_name = contact_name

    if "email" in data:
        email = _clean_optional(data.get("email"))
        contact.email = email.lower() if email else None

    if "is_billing_contact" in data:
        contact.is_billing_contact = _to_bool(
            data.get("is_billing_contact"),
            False,
        )

    if "is_active" in data:
        contact.is_active = _to_bool(
            data.get("is_active"),
            contact.is_active,
        )

    if "is_primary" in data:
        contact.is_primary = _to_bool(
            data.get("is_primary"),
            contact.is_primary,
        )

    if not contact.is_active:
        contact.is_primary = False

    try:
        if contact.is_primary:
            (
                CustomerContact.query
                .filter(
                    CustomerContact.tenant_id == identity.tenant_id,
                    CustomerContact.customer_id == customer.id,
                    CustomerContact.id != contact.id,
                    CustomerContact.is_active.is_(True),
                    CustomerContact.is_primary.is_(True),
                )
                .update(
                    {
                        CustomerContact.is_primary: False,
                    },
                    synchronize_session=False,
                )
            )

        db.session.commit()

    except IntegrityError:
        db.session.rollback()
        return _json_error(
            "Unable to update customer contact because the "
            "active primary contact constraint was violated.",
            409,
        )

    except Exception as exc:
        db.session.rollback()
        return _json_error(
            f"Failed to update customer contact: {exc}",
            500,
        )

    new_values = _serialize_contact(contact)

    action = (
        AuditAction.CUSTOMER_CONTACT_DEACTIVATED
        if old_values["is_active"] and not new_values["is_active"]
        else AuditAction.CUSTOMER_CONTACT_UPDATED
    )

    _audit_contact(
        action=action,
        identity=identity,
        contact=contact,
        old_values=old_values,
        new_values=new_values,
    )

    return jsonify(
        {
            "ok": True,
            "message": "Customer contact updated successfully.",
            "item": new_values,
        }
    )


__all__ = ["bp"]
