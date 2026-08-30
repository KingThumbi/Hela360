from __future__ import annotations

import json

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    CatalogueSupplier,
    MasterItem,
    MasterItemSupplierMapping,
    SupplierItemPrice,
)


SUPPORTED_SCHEMA_VERSION = 1


class MasterCatalogueSeedError(ValueError):
    """
    Raised when a catalogue seed cannot be safely imported.
    """


@dataclass(frozen=True)
class SeedEntityResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0

    @property
    def processed(self) -> int:
        return (
            self.created
            + self.updated
            + self.unchanged
        )


@dataclass(frozen=True)
class MasterCatalogueSeedResult:
    master_items: SeedEntityResult
    suppliers: SeedEntityResult
    mappings: SeedEntityResult
    prices: SeedEntityResult

    @property
    def changed(self) -> bool:
        return any(
            result.created > 0
            or result.updated > 0
            for result in (
                self.master_items,
                self.suppliers,
                self.mappings,
                self.prices,
            )
        )


def _text(
    value: Any,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()

    return normalized or None


def _required_text(
    value: Any,
    *,
    field: str,
) -> str:
    normalized = _text(value)

    if normalized is None:
        raise MasterCatalogueSeedError(
            f"{field} is required."
        )

    return normalized


def _decimal(
    value: Any,
    *,
    field: str,
) -> Decimal | None:
    if value is None or value == "":
        return None

    try:
        return Decimal(str(value))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise MasterCatalogueSeedError(
            f"{field} must be numeric."
        ) from exc


def _date(
    value: Any,
    *,
    field: str,
) -> date | None:
    normalized = _text(value)

    if normalized is None:
        return None

    try:
        return date.fromisoformat(
            normalized
        )
    except ValueError as exc:
        raise MasterCatalogueSeedError(
            f"{field} must use YYYY-MM-DD."
        ) from exc


def _boolean_or_none(
    value: Any,
    *,
    field: str,
) -> bool | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    raise MasterCatalogueSeedError(
        f"{field} must be true, false, or null."
    )


def _normalize_supplier_name(
    value: str,
) -> str:
    return " ".join(
        value.casefold().split()
    )


class MasterCatalogueSeedService:
    """
    Import a versioned Hela360 Master Catalogue seed.

    Architectural rules
    -------------------
    * Master catalogue records are platform-owned.
    * No tenant Products are created.
    * Master codes are never tenant SKUs.
    * Supplier prices remain source evidence.
    * Unknown values remain null.
    * The importer is idempotent.
    * Transaction ownership belongs to the caller.
    """

    MASTER_ITEM_FIELDS = (
        "canonical_name",
        "brand_name",
        "generic_name",
        "strength",
        "dosage_form",
        "pack_quantity",
        "pack_unit",
        "pack_type",
        "item_class",
        "category_name",
        "subcategory_name",
        "manufacturer",
        "country_of_origin",
        "cold_chain",
        "restricted_item",
        "requires_prescription",
        "tax_classification",
        "review_status",
        "is_active",
    )

    PRICE_FIELDS = (
        "price_type",
        "amount",
        "currency",
        "discount_percent",
        "vat_source",
        "effective_date",
        "source_document",
        "source_location",
        "is_comparable_procurement",
    )

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def import_file(
        self,
        path: str | Path,
    ) -> MasterCatalogueSeedResult:
        seed_path = Path(path)

        if not seed_path.exists():
            raise MasterCatalogueSeedError(
                f"Seed file not found: {seed_path}"
            )

        try:
            payload = json.loads(
                seed_path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise MasterCatalogueSeedError(
                "Catalogue seed is not valid JSON."
            ) from exc

        return self.import_payload(
            payload
        )

    def import_payload(
        self,
        payload: dict[str, Any],
    ) -> MasterCatalogueSeedResult:
        self._validate_payload(payload)

        master_result = (
            self._sync_master_items(
                payload["master_items"]
            )
        )

        self.session.flush()

        supplier_result, suppliers = (
            self._sync_suppliers(
                payload["supplier_offers"]
            )
        )

        self.session.flush()

        mapping_result, mappings = (
            self._sync_mappings(
                payload["supplier_offers"],
                suppliers=suppliers,
            )
        )

        self.session.flush()

        price_result = (
            self._sync_prices(
                payload["supplier_offers"],
                mappings=mappings,
            )
        )

        self.session.flush()

        return MasterCatalogueSeedResult(
            master_items=master_result,
            suppliers=supplier_result,
            mappings=mapping_result,
            prices=price_result,
        )

    def _validate_payload(
        self,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(
            payload,
            dict,
        ):
            raise MasterCatalogueSeedError(
                "Catalogue seed root must be an object."
            )

        schema_version = payload.get(
            "schema_version"
        )

        if (
            schema_version
            != SUPPORTED_SCHEMA_VERSION
        ):
            raise MasterCatalogueSeedError(
                "Unsupported catalogue seed "
                f"schema version: {schema_version!r}."
            )

        master_items = payload.get(
            "master_items"
        )

        supplier_offers = payload.get(
            "supplier_offers"
        )

        if not isinstance(
            master_items,
            list,
        ):
            raise MasterCatalogueSeedError(
                "master_items must be a list."
            )

        if not isinstance(
            supplier_offers,
            list,
        ):
            raise MasterCatalogueSeedError(
                "supplier_offers must be a list."
            )

        master_codes: set[str] = set()

        for index, raw in enumerate(
            master_items,
            start=1,
        ):
            if not isinstance(raw, dict):
                raise MasterCatalogueSeedError(
                    "Each master_items entry "
                    "must be an object."
                )

            master_code = _required_text(
                raw.get("master_code"),
                field=(
                    "master_items"
                    f"[{index}].master_code"
                ),
            )

            if master_code in master_codes:
                raise MasterCatalogueSeedError(
                    "Duplicate master_code in seed: "
                    f"{master_code}."
                )

            master_codes.add(
                master_code
            )

            _required_text(
                raw.get(
                    "canonical_name"
                ),
                field=(
                    "master_items"
                    f"[{index}].canonical_name"
                ),
            )

        offer_keys: set[str] = set()

        for index, raw in enumerate(
            supplier_offers,
            start=1,
        ):
            if not isinstance(raw, dict):
                raise MasterCatalogueSeedError(
                    "Each supplier_offers entry "
                    "must be an object."
                )

            source_key = _required_text(
                raw.get(
                    "source_mapping_id"
                ),
                field=(
                    "supplier_offers"
                    f"[{index}].source_mapping_id"
                ),
            )

            if source_key in offer_keys:
                raise MasterCatalogueSeedError(
                    "Duplicate source offer key "
                    f"in seed: {source_key}."
                )

            offer_keys.add(
                source_key
            )

            master_code = _required_text(
                raw.get("master_code"),
                field=(
                    "supplier_offers"
                    f"[{index}].master_code"
                ),
            )

            if master_code not in master_codes:
                raise MasterCatalogueSeedError(
                    "Supplier offer references "
                    "unknown master_code: "
                    f"{master_code}."
                )

            _required_text(
                raw.get(
                    "supplier_name"
                ),
                field=(
                    "supplier_offers"
                    f"[{index}].supplier_name"
                ),
            )

            _required_text(
                raw.get(
                    "supplier_item_name"
                ),
                field=(
                    "supplier_offers"
                    f"[{index}].supplier_item_name"
                ),
            )

            _required_text(
                raw.get("price_type"),
                field=(
                    "supplier_offers"
                    f"[{index}].price_type"
                ),
            )

            amount = _decimal(
                raw.get("amount"),
                field=(
                    "supplier_offers"
                    f"[{index}].amount"
                ),
            )

            if amount is None:
                raise MasterCatalogueSeedError(
                    "supplier_offers"
                    f"[{index}].amount "
                    "is required."
                )

    def _sync_master_items(
        self,
        rows: list[dict[str, Any]],
    ) -> SeedEntityResult:
        created = 0
        updated = 0
        unchanged = 0

        existing = {
            item.master_code: item
            for item in (
                self.session.query(
                    MasterItem
                )
                .filter(
                    MasterItem.master_code.in_(
                        [
                            _required_text(
                                row.get(
                                    "master_code"
                                ),
                                field="master_code",
                            )
                            for row in rows
                        ]
                    )
                )
                .all()
            )
        }

        for row in rows:
            master_code = _required_text(
                row.get("master_code"),
                field="master_code",
            )

            values = (
                self._master_item_values(
                    row
                )
            )

            item = existing.get(
                master_code
            )

            if item is None:
                item = MasterItem(
                    master_code=master_code,
                    **values,
                )

                self.session.add(item)

                existing[
                    master_code
                ] = item

                created += 1
                continue

            if self._apply_changes(
                item,
                values,
            ):
                updated += 1
            else:
                unchanged += 1

        return SeedEntityResult(
            created=created,
            updated=updated,
            unchanged=unchanged,
        )

    def _master_item_values(
        self,
        row: dict[str, Any],
    ) -> dict[str, Any]:
        review_status = _required_text(
            row.get("review_status"),
            field="review_status",
        )

        if review_status not in {
            "draft",
            "approved",
        }:
            raise MasterCatalogueSeedError(
                "review_status must be "
                "'draft' or 'approved'."
            )

        is_active = _boolean_or_none(
            row.get("is_active"),
            field="is_active",
        )

        if is_active is None:
            raise MasterCatalogueSeedError(
                "is_active must not be null."
            )

        return {
            "canonical_name":
                _required_text(
                    row.get(
                        "canonical_name"
                    ),
                    field="canonical_name",
                ),

            "brand_name":
                _text(
                    row.get(
                        "brand_name"
                    )
                ),

            "generic_name":
                _text(
                    row.get(
                        "generic_name"
                    )
                ),

            "strength":
                _text(
                    row.get(
                        "strength"
                    )
                ),

            "dosage_form":
                _text(
                    row.get(
                        "dosage_form"
                    )
                ),

            "pack_quantity":
                _decimal(
                    row.get(
                        "pack_quantity"
                    ),
                    field="pack_quantity",
                ),

            "pack_unit":
                _text(
                    row.get(
                        "pack_unit"
                    )
                ),

            "pack_type":
                _text(
                    row.get(
                        "pack_type"
                    )
                ),

            "item_class":
                _text(
                    row.get(
                        "item_class"
                    )
                ),

            "category_name":
                _text(
                    row.get(
                        "category_name"
                    )
                ),

            "subcategory_name":
                _text(
                    row.get(
                        "subcategory_name"
                    )
                ),

            "manufacturer":
                _text(
                    row.get(
                        "manufacturer"
                    )
                ),

            "country_of_origin":
                _text(
                    row.get(
                        "country_of_origin"
                    )
                ),

            "cold_chain":
                _boolean_or_none(
                    row.get(
                        "cold_chain"
                    ),
                    field="cold_chain",
                ),

            "restricted_item":
                _boolean_or_none(
                    row.get(
                        "restricted_item"
                    ),
                    field=(
                        "restricted_item"
                    ),
                ),

            "requires_prescription":
                _boolean_or_none(
                    row.get(
                        "requires_prescription"
                    ),
                    field=(
                        "requires_prescription"
                    ),
                ),

            "tax_classification":
                _text(
                    row.get(
                        "tax_classification"
                    )
                ),

            "review_status":
                review_status,

            "is_active":
                is_active,
        }

    def _sync_suppliers(
        self,
        rows: list[dict[str, Any]],
    ) -> tuple[
        SeedEntityResult,
        dict[str, CatalogueSupplier],
    ]:
        requested: dict[
            str,
            tuple[str, str | None],
        ] = {}

        for row in rows:
            name = _required_text(
                row.get("supplier_name"),
                field="supplier_name",
            )

            normalized = (
                _normalize_supplier_name(
                    name
                )
            )

            country = _text(
                row.get(
                    "supplier_country"
                )
            )

            requested[normalized] = (
                name,
                country,
            )

        existing = {
            supplier.normalized_name:
                supplier
            for supplier in (
                self.session.query(
                    CatalogueSupplier
                )
                .filter(
                    CatalogueSupplier
                    .normalized_name.in_(
                        list(
                            requested.keys()
                        )
                    )
                )
                .all()
            )
        }

        created = 0
        updated = 0
        unchanged = 0

        for normalized, (
            name,
            country,
        ) in requested.items():
            supplier = existing.get(
                normalized
            )

            values = {
                "name": name,
                "normalized_name":
                    normalized,
                "country": country,
                "is_active": True,
            }

            if supplier is None:
                supplier = (
                    CatalogueSupplier(
                        **values
                    )
                )

                self.session.add(
                    supplier
                )

                existing[
                    normalized
                ] = supplier

                created += 1
                continue

            if self._apply_changes(
                supplier,
                values,
            ):
                updated += 1
            else:
                unchanged += 1

        return (
            SeedEntityResult(
                created=created,
                updated=updated,
                unchanged=unchanged,
            ),
            existing,
        )

    def _sync_mappings(
        self,
        rows: list[dict[str, Any]],
        *,
        suppliers: dict[
            str,
            CatalogueSupplier,
        ],
    ) -> tuple[
        SeedEntityResult,
        dict[str, MasterItemSupplierMapping],
    ]:
        master_items = {
            item.master_code: item
            for item in (
                self.session.query(
                    MasterItem
                )
                .filter(
                    MasterItem.master_code.in_(
                        list({
                            _required_text(
                                row.get(
                                    "master_code"
                                ),
                                field="master_code",
                            )
                            for row in rows
                        })
                    )
                )
                .all()
            )
        }

        listing_rows: dict[
            tuple[str, ...],
            dict[str, Any],
        ] = {}

        offer_listing_keys: dict[
            str,
            tuple[str, ...],
        ] = {}

        for row in rows:
            source_key = _required_text(
                row.get(
                    "source_mapping_id"
                ),
                field="source_mapping_id",
            )

            supplier_name = _required_text(
                row.get(
                    "supplier_name"
                ),
                field="supplier_name",
            )

            normalized_supplier = (
                _normalize_supplier_name(
                    supplier_name
                )
            )

            master_code = _required_text(
                row.get(
                    "master_code"
                ),
                field="master_code",
            )

            supplier_item_code = _text(
                row.get(
                    "supplier_item_code"
                )
            )

            supplier_item_name = (
                _required_text(
                    row.get(
                        "supplier_item_name"
                    ),
                    field="supplier_item_name",
                )
            )

            if supplier_item_code:
                listing_key = (
                    "code",
                    normalized_supplier,
                    supplier_item_code,
                )
            else:
                listing_key = (
                    "no-code",
                    normalized_supplier,
                    master_code,
                    supplier_item_name,
                )

            previous = listing_rows.get(
                listing_key
            )

            if previous is not None:
                previous_description = _text(
                    previous.get(
                        "source_description"
                    )
                )

                current_description = _text(
                    row.get(
                        "source_description"
                    )
                )

                if (
                    previous_description
                    != current_description
                ):
                    raise MasterCatalogueSeedError(
                        "Conflicting supplier listing "
                        "descriptions for identity "
                        f"{listing_key!r}."
                    )
            else:
                listing_rows[
                    listing_key
                ] = row

            offer_listing_keys[
                source_key
            ] = listing_key

        created = 0
        updated = 0
        unchanged = 0

        mappings_by_listing: dict[
            tuple[str, ...],
            MasterItemSupplierMapping,
        ] = {}

        for listing_key, row in (
            listing_rows.items()
        ):
            supplier_name = _required_text(
                row.get(
                    "supplier_name"
                ),
                field="supplier_name",
            )

            supplier = suppliers[
                _normalize_supplier_name(
                    supplier_name
                )
            ]

            master_code = _required_text(
                row.get(
                    "master_code"
                ),
                field="master_code",
            )

            master_item = master_items[
                master_code
            ]

            supplier_item_code = _text(
                row.get(
                    "supplier_item_code"
                )
            )

            supplier_item_name = (
                _required_text(
                    row.get(
                        "supplier_item_name"
                    ),
                    field="supplier_item_name",
                )
            )

            query = (
                self.session.query(
                    MasterItemSupplierMapping
                )
                .filter(
                    MasterItemSupplierMapping
                    .catalogue_supplier_id
                    == supplier.id
                )
            )

            if supplier_item_code:
                mapping = (
                    query.filter(
                        MasterItemSupplierMapping
                        .supplier_item_code
                        == supplier_item_code
                    )
                    .first()
                )
            else:
                mapping = (
                    query.filter(
                        MasterItemSupplierMapping
                        .master_item_id
                        == master_item.id,
                        MasterItemSupplierMapping
                        .supplier_item_code
                        .is_(None),
                        MasterItemSupplierMapping
                        .supplier_item_name
                        == supplier_item_name,
                    )
                    .first()
                )

            values = {
                "master_item_id":
                    master_item.id,

                "catalogue_supplier_id":
                    supplier.id,

                "supplier_item_code":
                    supplier_item_code,

                "supplier_item_name":
                    supplier_item_name,

                "source_description":
                    _text(
                        row.get(
                            "source_description"
                        )
                    ),

                "is_active":
                    True,
            }

            if mapping is None:
                mapping = (
                    MasterItemSupplierMapping(
                        **values
                    )
                )

                self.session.add(
                    mapping
                )

                self.session.flush()

                created += 1

            elif self._apply_changes(
                mapping,
                values,
            ):
                updated += 1

            else:
                unchanged += 1

            mappings_by_listing[
                listing_key
            ] = mapping

        mappings_by_offer = {
            source_key:
                mappings_by_listing[
                    listing_key
                ]
            for source_key, listing_key
            in offer_listing_keys.items()
        }

        return (
            SeedEntityResult(
                created=created,
                updated=updated,
                unchanged=unchanged,
            ),
            mappings_by_offer,
        )

    def _sync_prices(
        self,
        rows: list[dict[str, Any]],
        *,
        mappings: dict[
            str,
            MasterItemSupplierMapping,
        ],
    ) -> SeedEntityResult:
        source_keys = [
            _required_text(
                row.get(
                    "source_mapping_id"
                ),
                field="source_mapping_id",
            )
            for row in rows
        ]

        existing = {
            price.source_offer_key: price
            for price in (
                self.session.query(
                    SupplierItemPrice
                )
                .filter(
                    SupplierItemPrice
                    .source_offer_key.in_(
                        source_keys
                    )
                )
                .all()
            )
        }

        created = 0
        updated = 0
        unchanged = 0

        for row in rows:
            source_key = _required_text(
                row.get(
                    "source_mapping_id"
                ),
                field="source_mapping_id",
            )

            mapping = mappings[
                source_key
            ]

            values = {
                "supplier_mapping_id":
                    mapping.id,

                "source_offer_key":
                    source_key,

                "price_type":
                    _required_text(
                        row.get(
                            "price_type"
                        ),
                        field="price_type",
                    ),

                "amount":
                    _decimal(
                        row.get(
                            "amount"
                        ),
                        field="amount",
                    ),

                "currency":
                    (
                        _text(
                            row.get(
                                "currency"
                            )
                        )
                        or "KES"
                    ),

                "discount_percent":
                    _decimal(
                        row.get(
                            "discount_percent"
                        ),
                        field=(
                            "discount_percent"
                        ),
                    ),

                "vat_source":
                    _text(
                        row.get(
                            "vat_source"
                        )
                    ),

                "effective_date":
                    _date(
                        row.get(
                            "effective_date"
                        ),
                        field=(
                            "effective_date"
                        ),
                    ),

                "source_document":
                    _text(
                        row.get(
                            "source_document"
                        )
                    ),

                "source_location":
                    _text(
                        row.get(
                            "source_location"
                        )
                    ),

                "is_comparable_procurement":
                    _boolean_or_none(
                        row.get(
                            "is_comparable_procurement"
                        ),
                        field=(
                            "is_comparable_procurement"
                        ),
                    ),
            }

            if (
                values[
                    "is_comparable_procurement"
                ]
                is None
            ):
                values[
                    "is_comparable_procurement"
                ] = True

            if values["amount"] is None:
                raise MasterCatalogueSeedError(
                    "Supplier price amount "
                    "must not be null."
                )

            price = existing.get(
                source_key
            )

            if price is None:
                price = SupplierItemPrice(
                    **values
                )

                self.session.add(price)

                existing[
                    source_key
                ] = price

                created += 1
                continue

            if self._apply_changes(
                price,
                values,
            ):
                updated += 1
            else:
                unchanged += 1

        return SeedEntityResult(
            created=created,
            updated=updated,
            unchanged=unchanged,
        )

    @staticmethod
    def _apply_changes(
        entity: Any,
        values: dict[str, Any],
    ) -> bool:
        changed = False

        for field, value in values.items():
            if getattr(
                entity,
                field,
            ) != value:
                setattr(
                    entity,
                    field,
                    value,
                )

                changed = True

        return changed
