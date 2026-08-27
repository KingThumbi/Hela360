from __future__ import annotations

from dotenv import load_dotenv

load_dotenv("/home/thumbi/Hela360/.env")

from app import create_app
from app.extensions import db
from app.models import Branch, Tenant, Warehouse


DEMO_TENANT_ID = "b5a256f7-8bec-4c40-b048-91c23749390b"

DIMPLES_LEGAL_NAME = "Dimples Pharmacy Limited"
DIMPLES_DISPLAY_NAME = "Dimples Pharmacy"
DIMPLES_BUSINESS_CODE = "DPL"

BRANCH_CODE = "ROY"
BRANCH_NAME = "Roysambu"

WAREHOUSE_CODE = "ROY-MAIN"
WAREHOUSE_NAME = "Roysambu Main Warehouse"


def main() -> None:
    app = create_app()

    with app.app_context():
        # ================================================================
        # 1. Restore Demo Tenant
        # ================================================================

        demo = db.session.get(
            Tenant,
            DEMO_TENANT_ID,
        )

        if demo is None:
            raise RuntimeError(
                "Expected Hela360 Demo tenant was not found."
            )

        print("=" * 72)
        print("DEMO TENANT")
        print("=" * 72)
        print("ID:", demo.id)
        print("Legal name:", demo.legal_name)
        print("Current business code:", demo.business_code)

        if demo.legal_name != "Hela360 Demo":
            raise RuntimeError(
                "Safety check failed: the expected demo tenant "
                "does not have legal_name='Hela360 Demo'."
            )

        if demo.business_code == DIMPLES_BUSINESS_CODE:
            demo.business_code = None
            db.session.flush()

            print("Removed DPL business code from Hela360 Demo.")
        else:
            print("Demo tenant does not currently own DPL.")

        # ================================================================
        # 2. Find/Create Actual Dimples Tenant
        # ================================================================

        dimples = (
            Tenant.query
            .filter(
                Tenant.legal_name == DIMPLES_LEGAL_NAME,
            )
            .first()
        )

        if dimples is None:
            dimples = Tenant(
                legal_name=DIMPLES_LEGAL_NAME,
                display_name=DIMPLES_DISPLAY_NAME,
                business_code=DIMPLES_BUSINESS_CODE,
                business_type="pharmacy",
                phone=None,
                email=None,
                country_code="KE",
                timezone="Africa/Nairobi",
                base_currency="KES",
                status="active",
            )

            db.session.add(dimples)
            db.session.flush()

            print("CREATED DIMPLES TENANT")
        else:
            dimples.business_code = DIMPLES_BUSINESS_CODE
            dimples.display_name = DIMPLES_DISPLAY_NAME
            dimples.business_type = "pharmacy"
            dimples.country_code = "KE"
            dimples.timezone = "Africa/Nairobi"
            dimples.base_currency = "KES"
            dimples.status = "active"

            db.session.flush()

            print("UPDATED EXISTING DIMPLES TENANT")

        # ================================================================
        # 3. Dimples Roysambu Branch
        # ================================================================

        branch = (
            Branch.query
            .filter_by(
                tenant_id=str(dimples.id),
                code=BRANCH_CODE,
            )
            .first()
        )

        if branch is None:
            branch = Branch(
                tenant_id=str(dimples.id),
                code=BRANCH_CODE,
                name=BRANCH_NAME,
                phone=None,
                email=None,
                country="Kenya",
                is_head_office=True,
                is_active=True,
            )

            db.session.add(branch)
            db.session.flush()

            print("CREATED DIMPLES ROYSAMBU BRANCH")
        else:
            print("DIMPLES ROYSAMBU BRANCH ALREADY EXISTS")

        # ================================================================
        # 4. Dimples Main Warehouse
        # ================================================================

        warehouse = (
            Warehouse.query
            .filter_by(
                tenant_id=str(dimples.id),
                branch_id=str(branch.id),
                code=WAREHOUSE_CODE,
            )
            .first()
        )

        if warehouse is None:
            warehouse = Warehouse(
                tenant_id=str(dimples.id),
                branch_id=str(branch.id),
                code=WAREHOUSE_CODE,
                name=WAREHOUSE_NAME,
                is_active=True,
            )

            db.session.add(warehouse)
            db.session.flush()

            print("CREATED DIMPLES MAIN WAREHOUSE")
        else:
            print("DIMPLES MAIN WAREHOUSE ALREADY EXISTS")

        db.session.commit()

        # ================================================================
        # Result
        # ================================================================

        print()
        print("=" * 72)
        print("CORRECTED TENANT STRUCTURE")
        print("=" * 72)

        print()
        print("DEMO")
        print("-" * 72)
        print("Tenant ID:", demo.id)
        print("Legal name:", demo.legal_name)
        print("Business code:", demo.business_code)

        print()
        print("DIMPLES")
        print("-" * 72)
        print("Tenant ID:", dimples.id)
        print("Legal name:", dimples.legal_name)
        print("Display name:", dimples.display_name)
        print("Business code:", dimples.business_code)
        print("Branch ID:", branch.id)
        print("Branch:", branch.code, "-", branch.name)
        print("Warehouse ID:", warehouse.id)
        print("Warehouse:", warehouse.code, "-", warehouse.name)

        print()
        print("TENANT REPAIR: PASS")


if __name__ == "__main__":
    main()
