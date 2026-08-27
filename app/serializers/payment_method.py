from app.models import PaymentMethod


def serialize_payment_method(
    payment_method: PaymentMethod,
) -> dict:
    return {
        "id": payment_method.id,
        "code": payment_method.code,
        "name": payment_method.name,
        "method_type": payment_method.method_type,
        "is_active": payment_method.is_active,
    }
