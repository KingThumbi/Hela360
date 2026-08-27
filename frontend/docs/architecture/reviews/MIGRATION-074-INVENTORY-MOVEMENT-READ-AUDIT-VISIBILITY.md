# Migration 074 - Inventory Movement Read Audit Visibility

Date: 2026-08-09

Status: Complete

Migration state classification: Up to date

## Objective

Expose branch-scoped, tenant-safe, read-only inventory movement visibility for stock activity auditing.

This migration extends the verified Inventory vertical slice from Migration 073. It does not introduce stock mutation workflows.

## Scope Completed

- Added `GET /api/inventory/movements`.
- Protected the endpoint with `inventory.read`.
- Reused `InventoryQueryService`.
- Added `InventoryMovementListFilters`.
- Added pagination and newest-first movement ordering.
- Added exact filters for:
  - `date_from`
  - `date_to`
  - `product_id`
  - `warehouse_id`
  - `movement_type`
  - `reference_type`
  - `reference_id`
- Validated product filters against the authenticated tenant.
- Validated warehouse filters against the authenticated branch.
- Projected movement rows with product, warehouse, batch, reference, performer, signed quantity, and timestamp.
- Omitted `unit_cost`, `unit_price`, and `notes` from the API response.
- Added frontend request/response DTOs for inventory movement listing.
- Added `inventoryService.listMovements`.
- Added branch-scoped movement query keys.
- Added `useInventoryMovements`.
- Added an Activity tab to the Inventory page.
- Added movement activity loading, error, empty, filters, pagination, and read-only table states.
- Added sale receipt navigation only for `reference.type === "sale"` when the user has `sales.read`.
- Kept unsupported inventory mutation hooks out of the public inventory hook index.

## Explicit Non-Scope

- No goods receipt implementation.
- No receiving workflow.
- No stock adjustment workflow.
- No stock transfer workflow.
- No stock count workflow.
- No inventory reconciliation mutation.
- No deletion.
- No valuation or accounting exposure.
- No procurement activation.
- No CSV/export.
- No dashboard analytics.
- No batch mutation.
- No expiry disposal workflow.
- No cost authorization model.
- No schema migration.

## Backend API

Route:

```text
GET /api/inventory/movements
```

Permission:

```text
inventory.read
```

Response envelope:

```text
{
  ok: true,
  items: InventoryMovementSummary[],
  pagination: {...}
}
```

## Projection

Each movement contains:

- `id`
- `movement_type`
- signed `quantity`
- `product`
- `warehouse`
- nullable `batch`
- nullable `sale_item_id`
- `reference`
- nullable `performed_by`
- `created_at`

The projection intentionally excludes:

- `unit_cost`
- `unit_price`
- `notes`

## Movement Type Disposition

No enum was introduced. Current writers use raw strings, and the API preserves exact movement type values.

Verified current writer values:

- `sale`
- `sale_refund_return`
- `sale_void`

The frontend labels these known values and degrades to the raw string for future values.

## Source Matrix

POS checkout:

- Source: `sale_stock_service._add_sale_movement`
- `movement_type`: `sale`
- Quantity: negative
- `reference_type`: `sale`
- `reference_id`: sale id
- Batch: populated when batch allocation exists
- Performer: cashier/user

Refund stock restoration:

- Source: `refund_stock_service.restore_refund_stock`
- `movement_type`: `sale_refund_return`
- Quantity: positive restored quantity
- `reference_type`: `sale_refund`
- `reference_id`: refund id
- Batch: original batch when present
- Performer: refund user

Legacy void restoration:

- Source: `app/api/sales.py::restore_stock_for_void`
- `movement_type`: `sale_void`
- Quantity: positive restored quantity
- `reference_type`: `sale_void`
- `reference_id`: sale id
- Status: inspected as an existing writer path; not changed in this migration

Legacy sales module:

- Source: `app/api_sales.py`
- Status: inspected as legacy/unregistered movement-writing code; not changed in this migration

## Frontend Behavior

The Inventory page now has two views:

- Stock
- Activity

Activity supports:

- warehouse filtering
- movement type filtering
- date range filtering
- reference id filtering
- pagination
- loading state
- error state
- empty state
- read-only movement table

Direction is derived from signed quantity:

- negative: Out
- positive: In
- zero/unknown: Neutral

Reference navigation:

- `sale` references can link to the sale receipt when `sales.read` is present.
- Refund and void references are displayed as text because dedicated source detail routes are not yet verified.

## Query Boundary

Movement query keys are branch-scoped under:

```text
QUERY_KEYS.inventory.branchRoot(scope)
```

Inventory invalidation through the branch root covers both stock and movement lists.

The legacy closed `useStockMovements` hook remains disabled and is not exported from the public inventory hook index.

## Seed/Bootstrap Inspection

Existing bootstrap command inspected without execution:

```text
flask seed-initial
```

Location:

```text
app/__init__.py
```

It can create:

- initial tenant
- initial branch
- admin role
- admin user
- payment methods

It does not seed operational Product, Customer, Supplier, Sales, or Inventory movement data.

No seed command was executed in Migration 074.

## Database State

No schema migration was added.

Repository Alembic head remains:

```text
b2c3d4e5f6a7
```

Local PostgreSQL status during final verification:

```text
16/main 5432 down
localhost:5432 - no response
```

`flask db heads` passed and reported:

```text
b2c3d4e5f6a7 (head)
```

`flask db current` could not connect because local PostgreSQL was down.

`flask db check` is supported but could not connect because local PostgreSQL was down.

## First-Tenant Seed Readiness

Runtime database counts could not be re-read in this migration because local PostgreSQL was down.

Last verified state remains:

- foundational tenant exists
- foundational branch exists
- foundational user exists
- operational Product data is empty
- operational Customer data is empty
- operational Supplier data is empty
- operational Sales data is empty

Movement activity will remain empty until operational stock-affecting transactions exist.

## Verification

Backend:

```text
venv/bin/python -m compileall app
PASS
```

```text
FLASK_APP=app:create_app venv/bin/flask routes
PASS
```

Verified route:

```text
inventory.list_inventory_movements GET /api/inventory/movements
```

```text
venv/bin/python -m pytest app/api/tests/test_inventory_movement_read_contract.py -q
14 passed, 4 warnings
```

```text
venv/bin/python -m pytest app/api/tests/test_inventory_movement_read_contract.py app/api/tests/test_inventory_read_contract.py app/api/tests/test_prescription_dispensing_contract.py app/api/tests/test_sales_history_contract.py app/api/tests/test_sales_receipt_contract.py app/api/tests/test_sales_pos_contract.py app/api/tests/test_payment_methods_contract.py app/api/tests/test_products_list_contract.py app/api/tests/test_customers_contract.py app/services/tenant/procurement/tests/test_supplier_contract.py app/services/tenant/auth/tests/test_current_session_service.py app/services/tenant/auth/tests/test_current_session_route.py app/api/tests/test_till_shift_contract.py -q
170 passed, 4 warnings
```

Auth suite:

```text
venv/bin/python -m pytest app/services/tenant/auth/tests -q
129 passed
```

Frontend:

```text
cd frontend && npx tsc -b --pretty false
PASS
```

```text
cd frontend && npm run build
PASS
```

Known frontend build warning:

```text
Some chunks are larger than 500 kB after minification.
```

Static checks:

```text
rg "useInventoryMovements" frontend/src
PASS
```

```text
rg "listMovements" frontend/src
PASS
```

```text
rg "QUERY_KEYS.*movement|inventory\\.movements|movementLists" frontend/src
PASS
```

```text
rg "queryClient" frontend/src/features/inventory
PASS: no matches
```

```text
rg "localStorage|sessionStorage" frontend/src/features/inventory
PASS: no matches
```

```text
rg "useAdjustStock|useReceiveStock|useStockCount|useTransferStock" frontend/src/hooks/queries/inventory/index.ts frontend/src/features/inventory
PASS: no matches
```

## Known Warnings

The existing SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

These were not changed in Migration 074.

## Remaining Technical Debt

- SQLAlchemy relationship overlap cleanup.
- Source detail routes for refund and void movement references.
- Cost authorization model before any cost exposure.
- Inventory receiving workflow.
- Stock adjustment workflow.
- Stock transfer workflow.
- Stock count workflow.
- Inventory reconciliation workflow.
- Batch mutation APIs.
- Expiry disposal workflow.
- Procurement/goods receipt activation.
- Inventory export/reporting.
- Dashboard analytics.
- Operational seed data for product/customer/supplier/sales/inventory scenarios.

## Classification

Migration 074 is complete.

Migration state classification:

```text
Up to date
```
