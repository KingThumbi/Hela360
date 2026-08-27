from __future__ import annotations

from dotenv import load_dotenv

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import PaymentMethod


DIMPLES_TENANT_ID = "c99e5eb7-6d56-4024-ae1d-5782daeed340"


PAYMENT_METHODS = (
    {
        "code": "cash",
        "name": "Cash",
        "method_type": "cash",
    },
    {
        "code": "mpesa",
        "name": "M-Pesa",
        "method_type": "mpesa",
    },
    {
        "code": "card",
        "name": "Card",
        "method_type": "card",
    },
    {
        "code": "bank",
        "name": "Bank Transfer",
        "method_type": "bank",
    },
)


def main() -> None:
    app = create_app()

    with app.app_context():
        for definition in PAYMENT_METHODS:
            row = (
                PaymentMethod.query
                .filter_by(
                    tenant_id=DIMPLES_TENANT_ID,
                    code=definition["code"],
                )
                .first()
            )

            if row is None:
                row = PaymentMethod(
                    tenant_id=DIMPLES_TENANT_ID,
                    code=definition["code"],
                    name=definition["name"],
                    method_type=definition["method_type"],
                    is_active=True,
                )

                db.session.add(row)

                print(
                    "CREATED:",
                    definition["code"],
                )

            else:
                row.name = definition["name"]
                row.method_type = definition["method_type"]
                row.is_active = True

                print(
                    "UPDATED:",
                    definition["code"],
                )

        db.session.commit()

        print()
        print("=" * 72)
        print("DIMPLES PAYMENT METHODS")
        print("=" * 72)

        rows = (
            PaymentMethod.query
            .filter_by(
                tenant_id=DIMPLES_TENANT_ID,
            )
            .order_by(
                PaymentMethod.created_at.asc(),
            )
            .all()
        )

        for row in rows:
            print(
                row.code,
                "|",
                row.name,
                "|",
                row.method_type,
                "| active:",
                row.is_active,
            )

        print()
        print("DIMPLES PAYMENT METHOD SEED: PASS")


if __name__ == "__main__":
    main()
