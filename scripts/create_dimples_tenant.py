from __future__ import annotations

from dotenv import load_dotenv

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import (
    Branch,
    Tenant,
    Warehouse,
)


LEGAL_NAME = "Dimples Pharmacy Limited"
DISPLAY_NAME = "Dimples Pharmacy"
BUSINESS_CODE = "DPL"

BUSINESS_TYPE = "pharmacy"

PHONE = None
EMAIL = None

COUNTRY_CODE = "KE"
TIMEZONE = "Africa/Nairobi"
BASE_CURRENCY = "KES"

BRANCH_CODE = "ROY"
BRANCH_NAME = "Roysambu"

WAREHOUSE_CODE = "ROY-MAIN"
WAREHOUSE_NAME = "Roysambu Main Warehouse"


def main() -> None:
    app = create_app()

    with app.app_context():
        tenant = (
            Tenant.query
            .filter_by(
                business_code=BUSINESS_CODE,
            )
            .first()
        )

        if tenant is None:
            tenant = Tenant(
                legal_name=LEGAL_NAME,
                display_name=DISPLAY_NAME,
                business_code=BUSINESS_CODE,
                business_type=BUSINESS_TYPE,
                phone=PHONE,
                email=EMAIL,
                country_code=COUNTRY_CODE,
                timezone=TIMEZONE,
                base_currency=BASE_CURRENCY,
                status="active",
            )

            db.session.add(tenant)
            db.session.flush()

            print("CREATED TENANT")
        else:
            print("TENANT ALREADY EXISTS")

        branch = (
            Branch.query
            .filter_by(
                tenant_id=str(tenant.id),
                code=BRANCH_CODE,
            )
            .first()
        )

        if branch is None:
            branch = Branch(
                tenant_id=str(tenant.id),
                code=BRANCH_CODE,
                name=BRANCH_NAME,
                phone=PHONE,
                email=EMAIL,
                country="Kenya",
                is_head_office=True,
                is_active=True,
            )

            db.session.add(branch)
            db.session.flush()

            print("CREATED BRANCH")
        else:
            print("BRANCH ALREADY EXISTS")

        warehouse = (
            Warehouse.query
            .filter_by(
                tenant_id=str(tenant.id),
                branch_id=str(branch.id),
                code=WAREHOUSE_CODE,
            )
            .first()
        )

        if warehouse is None:
            warehouse = Warehouse(
                tenant_id=str(tenant.id),
                branch_id=str(branch.id),
                code=WAREHOUSE_CODE,
                name=WAREHOUSE_NAME,
                is_active=True,
            )

            db.session.add(warehouse)
            db.session.flush()

            print("CREATED WAREHOUSE")
        else:
            print("WAREHOUSE ALREADY EXISTS")

        db.session.commit()

        print()
        print("=" * 72)
        print("DIMPLES PHARMACY TENANT")
        print("=" * 72)

        print("Tenant ID:      ", tenant.id)
        print("Legal name:     ", tenant.legal_name)
        print("Display name:   ", tenant.display_name)
        print("Business code:  ", tenant.business_code)
        print("Currency:       ", tenant.base_currency)
        print("Timezone:       ", tenant.timezone)

        print()
        print("Branch ID:      ", branch.id)
        print("Branch code:    ", branch.code)
        print("Branch name:    ", branch.name)

        print()
        print("Warehouse ID:   ", warehouse.id)
        print("Warehouse code: ", warehouse.code)
        print("Warehouse name: ", warehouse.name)

        print()
        print("DIMPLES TENANT BOOTSTRAP: PASS")


if __name__ == "__main__":
    main()
