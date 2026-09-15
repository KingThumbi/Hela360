from __future__ import annotations

from sqlalchemy import inspect

from app import create_app
from app.extensions import db
from app.models import (
    TenantUOMRemediationProductDecision,
    TenantUOMRemediationReview,
)


def _app():
    app = create_app()
    app.config.update(TESTING=True)
    return app


def test_uom_remediation_model_exports_and_table_names():
    assert (
        TenantUOMRemediationReview.__tablename__
        == "tenant_uom_remediation_reviews"
    )
    assert (
        TenantUOMRemediationProductDecision.__tablename__
        == "tenant_uom_remediation_product_decisions"
    )


def test_review_table_contract():
    app = _app()

    with app.app_context():
        inspector = inspect(db.engine)

        columns = {
            column["name"]: column
            for column in inspector.get_columns(
                "tenant_uom_remediation_reviews"
            )
        }

        assert columns["tenant_id"]["nullable"] is False
        assert columns["source_uom_id"]["nullable"] is False
        assert columns["status"]["nullable"] is False
        assert columns["audit_classification"]["nullable"] is False
        assert columns["recommended_action"]["nullable"] is False
        assert columns["planner_version"]["nullable"] is False
        assert columns["planner_fingerprint"]["nullable"] is False
        assert columns["planner_snapshot"]["nullable"] is False
        assert columns["created_by"]["nullable"] is False

        indexes = {
            index["name"]: index
            for index in inspector.get_indexes(
                "tenant_uom_remediation_reviews"
            )
        }

        active = indexes[
            "ix_tenant_uom_remediation_reviews_one_active"
        ]

        assert active["unique"] is True
        assert active["column_names"] == [
            "tenant_id",
            "source_uom_id",
        ]

        where = (
            active.get("dialect_options", {})
            .get("postgresql_where")
        )

        assert where is not None
        where_text = str(where).lower()

        assert "pending" in where_text
        assert "approved" in where_text

        checks = {
            constraint["name"]: constraint["sqltext"]
            for constraint
            in inspector.get_check_constraints(
                "tenant_uom_remediation_reviews"
            )
        }

        status_check = str(
            checks[
                "ck_tenant_uom_remediation_reviews_status"
            ]
        ).lower()

        for value in (
            "pending",
            "approved",
            "rejected",
            "superseded",
            "executed",
        ):
            assert value in status_check


def test_review_foreign_keys_do_not_cascade_operational_records():
    app = _app()

    with app.app_context():
        inspector = inspect(db.engine)

        foreign_keys = inspector.get_foreign_keys(
            "tenant_uom_remediation_reviews"
        )

        by_column = {
            fk["constrained_columns"][0]: fk
            for fk in foreign_keys
        }

        assert (
            by_column["tenant_id"]["referred_table"]
            == "tenants"
        )
        assert (
            by_column["source_uom_id"]["referred_table"]
            == "units_of_measure"
        )
        assert (
            by_column["selected_canonical_uom_id"][
                "referred_table"
            ]
            == "canonical_units_of_measure"
        )
        assert (
            by_column["created_by"]["referred_table"]
            == "users"
        )
        assert (
            by_column["reviewed_by"]["referred_table"]
            == "users"
        )

        for fk in foreign_keys:
            assert (
                fk.get("options", {}).get("ondelete")
                is None
            )


def test_product_decision_table_contract():
    app = _app()

    with app.app_context():
        inspector = inspect(db.engine)

        uniques = {
            constraint["name"]:
            constraint["column_names"]
            for constraint
            in inspector.get_unique_constraints(
                "tenant_uom_remediation_product_decisions"
            )
        }

        assert (
            uniques[
                "uq_tenant_uom_remediation_decisions_"
                "review_product"
            ]
            == ["review_id", "product_id"]
        )

        foreign_keys = inspector.get_foreign_keys(
            "tenant_uom_remediation_product_decisions"
        )

        by_column = {
            fk["constrained_columns"][0]: fk
            for fk in foreign_keys
        }

        assert (
            by_column["review_id"]["referred_table"]
            == "tenant_uom_remediation_reviews"
        )
        assert (
            by_column["review_id"]
            .get("options", {})
            .get("ondelete")
            == "CASCADE"
        )

        expected = {
            "tenant_id": "tenants",
            "product_id": "products",
            "source_product_unit_id": "product_units",
            "target_canonical_uom_id":
                "canonical_units_of_measure",
            "target_tenant_uom_id": "units_of_measure",
        }

        for column, table in expected.items():
            fk = by_column[column]

            assert fk["referred_table"] == table
            assert (
                fk.get("options", {}).get("ondelete")
                is None
            )


def test_uom_remediation_model_defaults():
    review_table = (
        TenantUOMRemediationReview.__table__
    )
    decision_table = (
        TenantUOMRemediationProductDecision.__table__
    )

    status_default = (
        review_table.c.status.default
    )
    preserve_default = (
        decision_table.c.preserve_historical_unit.default
    )

    assert status_default is not None
    assert status_default.arg == "pending"

    assert preserve_default is not None
    assert preserve_default.arg is True
