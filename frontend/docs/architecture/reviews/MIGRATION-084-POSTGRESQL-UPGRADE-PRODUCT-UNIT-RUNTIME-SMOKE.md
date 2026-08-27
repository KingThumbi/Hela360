# Migration 084 - PostgreSQL Upgrade Verification and Product Unit Runtime Smoke

## 1. Migration Purpose

Migration 084 attempted to bring the real local Hela360 PostgreSQL database to Alembic head `f6a7b8c9d0e1` and verify the Migration 083 ProductUnit/base-quantity runtime contract against PostgreSQL.

The runtime database phase was blocked because PostgreSQL 16/main is down and could not be started from this session.

## 2. Starting Source Head

Source Alembic head before runtime verification:

```text
f6a7b8c9d0e1
```

## 3. PostgreSQL Cluster Status

`pg_lsclusters`:

```text
16 main 5432 down nobody /var/lib/postgresql/16/main /var/log/postgresql/postgresql-16-main.log
```

`pg_isready -h localhost -p 5432`:

```text
localhost:5432 - no response
```

Two approval-reviewed attempts to run `sudo pg_ctlcluster 16 main start` timed out before approval. No PostgreSQL configuration was modified.

## 4. Effective DB Config Without Secrets

Explicit dotenv loading produced:

```text
scheme: postgresql
host: localhost
port: 5432
database: hela360
username: thumbi
password_present: True
```

The password was not printed.

## 5. Connectivity Result

Application connectivity failed because PostgreSQL is offline.

`SELECT 1`, `current_database()`, and `current_user` could not be executed.

## 6. Pre-Upgrade Alembic Revision

Blocked.

`flask db current` requires a live database connection and failed with `sqlalchemy.exc.OperationalError`.

`psql -d hela360 -c "SELECT version_num FROM alembic_version;"` also failed because the server/socket is unavailable.

## 7. Pending Chain

Source history is linear:

```text
19b1ccd035ac -> 8f3b7c2a9d10
8f3b7c2a9d10 -> 2f4a8b9c1d3e
2f4a8b9c1d3e -> 6c2f9d8a1b4e
6c2f9d8a1b4e -> 7d9e2f4a6c8b
7d9e2f4a6c8b -> 9a1b2c3d4e5f
9a1b2c3d4e5f -> b2c3d4e5f6a7
b2c3d4e5f6a7 -> c3d4e5f6a7b8
c3d4e5f6a7b8 -> d4e5f6a7b8c9
d4e5f6a7b8c9 -> e5f6a7b8c9d0
e5f6a7b8c9d0 -> f6a7b8c9d0e1
```

`flask db heads` reports:

```text
f6a7b8c9d0e1 (head)
```

## 8. Migration Review

The pending source chain was inspected for revision/down-revision continuity and expected upgrade/downgrade operations.

Key operations reviewed:

- sale till-shift attribution
- till warehouse attribution
- inventory movement sale item trace
- refund till-shift attribution
- dispensing records
- goods receipts/items
- stock counts/items
- stock adjustments/items
- product units
- ProductCode `product_unit_id`
- sale/goods-receipt/refund base quantity snapshot fields

No source-chain branching was found.

## 9. Pre-Upgrade Row Counts

Blocked.

The requested read-only row count script requires PostgreSQL connectivity.

## 10. Backup Disposition

No `pg_dump` backup was taken because PostgreSQL is offline.

No database mutation was attempted.

## 11. Upgrade Command / Result

`flask db upgrade` was not run.

Reason: critical invariant requires verifying DB identity/current revision before upgrade, and that verification is blocked by offline PostgreSQL.

## 12. Final Current / Head / Version

Source head:

```text
f6a7b8c9d0e1 (head)
```

Database current/version:

```text
Blocked: PostgreSQL offline
```

## 13. db Check

Blocked.

`flask db check` requires the database connection and was not meaningful while PostgreSQL is down.

## 14. New Tables

Runtime table inspection via `psql \dt` was blocked.

Expected newer tables from source migrations include:

- `dispensing_records`
- `goods_receipts`
- `goods_receipt_items`
- `stock_counts`
- `stock_count_items`
- `stock_adjustments`
- `stock_adjustment_items`
- `product_units`

## 15. ProductUnit Schema

Runtime `\d+ product_units` inspection was blocked.

Source migration defines:

- primary key `id`
- `tenant_id`
- `product_id`
- `unit_id`
- `conversion_factor_to_base Numeric(18,6)`
- `is_base`
- `can_sell`
- `can_receive`
- `sale_price`
- `minimum_sale_price`
- `is_active`
- timestamps
- tenant/product/unit uniqueness
- one-base-per-product partial unique index for PostgreSQL

## 16. ProductCode Schema

Runtime inspection was blocked.

Source migration adds nullable `product_unit_id` with FK/index to `product_units`.

## 17. SaleItem Unit Snapshot Schema

Runtime inspection was blocked.

Source migration adds:

- `product_unit_id`
- `base_quantity`
- `unit_code_snapshot`
- `unit_name_snapshot`
- `conversion_factor_to_base`

## 18. GoodsReceiptItem Unit Snapshot Schema

Runtime inspection was blocked.

Source migration adds:

- `product_unit_id`
- `base_quantity`
- `unit_code_snapshot`
- `unit_name_snapshot`
- `conversion_factor_to_base`
- `base_unit_cost`

## 19. Historical Row Compatibility

Runtime verification was blocked.

Source migration uses factor-1 compatibility backfills for historical sale, refund, and goods receipt rows, without guessed pack conversions.

## 20. Existing Product Compatibility Strategy

Runtime verification was blocked.

Source migration creates factor-1 base ProductUnit rows for existing Products with `unit_id`, and runtime service compatibility falls back to Product.unit_id/factor 1 when no ProductUnit exists.

## 21. Fixture Strategy

No Migration 084 runtime fixture was created because PostgreSQL is offline.

No test data was inserted.

## 22. ProductUnit Conversion Smoke

Blocked for real PostgreSQL runtime.

Source-level targeted tests from Migration 083 remain passing.

## 23. Product Unit API Smoke

Blocked for real PostgreSQL runtime.

The route exists in source:

```text
GET /api/products/<product_id>/units
```

## 24. Receiving Conversion

Blocked for real PostgreSQL runtime.

Source regression verifies receiving conversion in isolated tests.

## 25. Receiving Cost Conversion

Blocked for real PostgreSQL runtime.

Source regression verifies base-unit cost conversion in isolated tests.

## 26. POS Conversion

Blocked for real PostgreSQL runtime.

No runtime sale fixture was created.

## 27. FEFO

Blocked for real PostgreSQL runtime.

Existing source regression continues to pass.

## 28. Refund

Blocked for real PostgreSQL runtime.

No runtime converted SaleItem/refund fixture was created.

## 29. Partial Refund Precision

Blocked for real PostgreSQL runtime.

Source implementation prorates:

```text
sale_item.base_quantity * refund_quantity / sale_item.quantity
```

using Decimal helpers.

## 30. Receipt Commercial-Unit Truth

Blocked for real PostgreSQL runtime.

Source SaleItem serializer preserves commercial quantity and unit snapshot fields.

## 31. Goods Receipt Commercial-Unit Truth

Blocked for real PostgreSQL runtime.

Source GoodsReceipt serializer preserves commercial quantity/unit/cost and base quantity/base cost.

## 32. Inventory Base-Unit Truth

Blocked for real PostgreSQL runtime.

Source services post converted base quantity to stock balance, batch, and inventory movement.

## 33. POS Availability Quantity Semantics

Runtime verification blocked.

Source behavior remains base inventory quantity; no selected-unit availability projection was added in Migration 084.

## 34. Stock Count Compatibility

Runtime verification blocked.

Source regression for Stock Count continues to pass.

## 35. Stock Adjustment Compatibility

Runtime verification blocked.

Source regression for Stock Adjustment continues to pass.

## 36. ProductCode Compatibility

Runtime verification blocked.

Source compatibility keeps existing product-level codes valid with nullable `product_unit_id`.

## 37. Snapshot Immutability

Runtime verification blocked.

Source schema persists transaction conversion snapshots on sale and goods receipt lines.

## 38. Legacy Endpoint Compatibility

Source regression passed:

```text
188 passed, 4 warnings
```

No old endpoint requires `product_unit_id`.

## 39. Integrity SQL Checks

Blocked.

Negative quantity and batch/stock-balance consistency SQL checks require PostgreSQL connectivity.

## 40. Batch / StockBalance Consistency

Blocked.

No runtime inventory aggregate comparison was possible.

## 41. Schema Constraint Verification

Runtime PostgreSQL verification blocked.

Isolated source tests remain passing.

## 42. Backend Regression

Compile:

```text
venv/bin/python -m compileall app
PASS
```

Targeted backend:

```text
188 passed, 4 warnings
```

Auth suite:

```text
129 passed
```

## 43. Frontend TypeScript

```text
npx tsc -b --pretty false
PASS
```

TypeScript errors: 0.

## 44. Frontend Build

```text
npm run build
PASS
```

The known large chunk warning remains.

## 45. Warnings

Known SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

They were not changed in Migration 084.

## 46. Fixture Cleanup Disposition

No fixture records were created.

No cleanup was required.

## 47. Files Created

- `frontend/docs/architecture/reviews/MIGRATION-084-POSTGRESQL-UPGRADE-PRODUCT-UNIT-RUNTIME-SMOKE.md`

## 48. Files Modified

No runtime source files were modified in Migration 084.

Only this review document was added.

## 49. Remaining Runtime Blockers

PostgreSQL 16/main is down and must be started by the operator before database upgrade verification can proceed.

Required next runtime steps:

```bash
sudo pg_ctlcluster 16 main start
pg_isready -h localhost -p 5432
```

Then rerun Migration 084 from Phase 2.

## 50. Migration-State Classification

Blocked before upgrade.

Do not classify as `Up to date` because the required checks are blocked:

- `flask db current`
- `alembic_version`
- `flask db upgrade`
- `flask db check`

## 51. ProductUnit Runtime Classification

- ProductUnit ORM: Blocked for real PostgreSQL runtime
- Conversion service: Blocked for real PostgreSQL runtime
- Goods Receipt conversion: Blocked for real PostgreSQL runtime
- POS conversion: Blocked for real PostgreSQL runtime
- Refund conversion: Blocked for real PostgreSQL runtime
- FEFO conversion: Blocked for real PostgreSQL runtime
- Receipt commercial-unit truth: Blocked for real PostgreSQL runtime
- Inventory base-unit truth: Blocked for real PostgreSQL runtime

Source-level regression remains verified.

## 52. Rollback / Recovery Notes

No database upgrade was run, no fixtures were inserted, and no cleanup or rollback was needed.

Once PostgreSQL is started, take a logical backup before upgrade if tooling permits:

```bash
pg_dump -d hela360 -Fc -f /tmp/hela360-pre-migration-084.dump
```

Do not stamp the database to head.

## 53. Recommended Next Migration

Resume Migration 084 after PostgreSQL is online, beginning with effective DB config and connectivity verification.

Only after the database reaches `f6a7b8c9d0e1` and runtime ProductUnit smoke passes should the project move to pack/unit operational UI work.
