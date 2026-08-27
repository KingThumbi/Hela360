from app.models import PaymentMethod


class PaymentMethodService:
    def __init__(self, session):
        self.session = session

    def list_active(
        self,
        tenant_id: str,
    ) -> list[PaymentMethod]:
        return (
            self.session.query(PaymentMethod)
            .filter(
                PaymentMethod.tenant_id == tenant_id,
                PaymentMethod.is_active.is_(True),
            )
            .order_by(
                PaymentMethod.name.asc(),
                PaymentMethod.code.asc(),
                PaymentMethod.created_at.asc(),
            )
            .all()
        )
