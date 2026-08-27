from __future__ import annotations

from decimal import Decimal

from dotenv import load_dotenv

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import TaxCode, Tenant


DIMPLES_TENANT_ID = "c99e5eb7-6d56-4024-ae1d-5782daeed340"

TAX_CODES = (
    {
        "code": "VAT16",
        "name": "Standard VAT",
        "rate": Decimal("16.0000"),
        "description": "Kenya standard VAT rate.",
    },
    {
        "code": "ZERO",
        "name": "Zero Rated",
        "rate": Decimal("0.0000"),
        "description": "Zero-rated supply.",
    },
    {
        "code": "EXEMPT",
        "name": "VAT Exempt",
        "rate": Decimal("0.0000"),
        "description": "VAT-exempt supply.",
    },
)


def main() -> None:
    app = create_app()

    with app.app_context():
        tenant = db.session.get(
            Tenant,
            DIMPLES_TENANT_ID,
        )

        if tenant is None:
            raise RuntimeError(
                "Dimples Pharmacy tenant not found."
            )

        for definition in TAX_CODES:
            tax_code = (
                TaxCode.query
                .filter_by(
                    tenant_id=str(tenant.id),
                    code=definition["code"],
                )
                .first()
            )

            if tax_code is None:
                tax_code = TaxCode(
                    tenant_id=str(tenant.id),
                    code=definition["code"],
                    name=definition["name"],
                    rate=definition["rate"],
                    description=definition["description"],
                    is_active=True,
                )

                db.session.add(tax_code)

                print("CREATED:", definition["code"])

            else:
                tax_code.name = definition["name"]
                tax_code.rate = definition["rate"]
                tax_code.description = definition["description"]
                tax_code.is_active = True

                print("UPDATED:", definition["code"])

        db.session.commit()

        print()
        print("=" * 72)
        print("DIMPLES TAX CODES")
        print("=" * 72)

        tax_codes = (
            TaxCode.query
            .filter_by(
                tenant_id=str(tenant.id),
                is_active=True,
            )
            .order_by(TaxCode.code)
            .all()
        )

        for tax_code in tax_codes:
            print(
                tax_code.code,
                "|",
                tax_code.name,
                "|",
                tax_code.rate,
            )

        print()
        print("DIMPLES TAX CODE SEED: PASS")


if __name__ == "__main__":
    main()
