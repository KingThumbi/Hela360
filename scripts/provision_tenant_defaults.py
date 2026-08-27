from __future__ import annotations

import argparse

from dotenv import load_dotenv

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import TaxCode, Tenant
from app.services.platform.tenant_provisioning_service import (
    TenantProvisioningService,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--tenant-id",
        required=True,
    )

    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        service = TenantProvisioningService(
            db.session,
        )

        tenant = service.provision_defaults(
            tenant_id=args.tenant_id,
        )

        db.session.commit()

        print("=" * 72)
        print("TENANT DEFAULTS")
        print("=" * 72)
        print("Tenant ID:", tenant.id)
        print("Legal name:", tenant.legal_name)
        print("Business code:", tenant.business_code)
        print("Country:", tenant.country_code)

        print()
        print("TAX CODES")
        print("-" * 72)

        for tax_code in (
            TaxCode.query
            .filter_by(
                tenant_id=str(tenant.id),
                is_active=True,
            )
            .order_by(TaxCode.code)
            .all()
        ):
            print(
                tax_code.code,
                "|",
                tax_code.name,
                "|",
                tax_code.rate,
            )

        print()
        print("TENANT DEFAULT PROVISIONING: PASS")


if __name__ == "__main__":
    main()
