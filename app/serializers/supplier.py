from app.models import Supplier


def serialize_supplier(supplier: Supplier) -> dict:
    return {
        "id": supplier.id,
        "tenant_id": supplier.tenant_id,
        "supplier_code": supplier.supplier_code,
        "name": supplier.name,
        "legal_name": supplier.legal_name,
        "contact_person": supplier.contact_person,
        "email": supplier.email,
        "phone": supplier.phone,
        "alternate_phone": supplier.alternate_phone,
        "address_line_1": supplier.address_line_1,
        "address_line_2": supplier.address_line_2,
        "city": supplier.city,
        "county_or_region": supplier.county_or_region,
        "country": supplier.country,
        "postal_code": supplier.postal_code,
        "tax_number": supplier.tax_number,
        "registration_number": supplier.registration_number,
        "payment_terms_days": supplier.payment_terms_days,
        "credit_limit": (
            str(supplier.credit_limit)
            if supplier.credit_limit is not None
            else "0.00"
        ),
        "currency": supplier.currency,
        "notes": supplier.notes,
        "is_active": supplier.is_active,
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
        "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
    }
