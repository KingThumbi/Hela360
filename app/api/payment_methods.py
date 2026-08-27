from flask import Blueprint, jsonify

from app.extensions import db
from app.serializers import serialize_payment_method
from app.services.tenant.auth.decorators import (
    _current_identity,
    require_permission,
)
from app.services.tenant.pos import PaymentMethodService

bp = Blueprint("payment_methods", __name__)


@bp.get("/payment-methods")
@require_permission("sales.create")
def list_payment_methods():
    identity = _current_identity()

    payment_methods = PaymentMethodService(
        db.session,
    ).list_active(identity.tenant_id)

    return jsonify(
        {
            "ok": True,
            "items": [
                serialize_payment_method(payment_method)
                for payment_method in payment_methods
            ],
        }
    )
