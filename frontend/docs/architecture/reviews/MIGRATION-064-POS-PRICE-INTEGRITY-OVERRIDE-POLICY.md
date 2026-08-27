# Migration 064 - POS Price Integrity and Override Policy

## 1. Purpose

Migration 064 makes POS checkout pricing server authoritative.

Persisted `SaleItem.unit_price` must now come from the canonical Product selling
price unless a future explicit, permissioned, and audited override contract is
introduced.

This migration does not activate POS UI, redesign Product pricing, add
batch/expiry/FEFO behavior, add receipts, add refunds, or change TillShift cash
attribution.

## 2. Migration Classification

Classification:

```text
Up to date
```

Repository migration head discovery reports:

```text
2f4a8b9c1d3e (head)
```

Local database connection checks could not verify the live database revision in
this run because PostgreSQL 16/main is down on `localhost:5432`.

## 3. Baseline

Baseline from the start of Migration 064:

```text
venv/bin/python -m compileall app: PASS
npx tsc -b --pretty false: PASS
npm run build: PASS
```

The known Vite large-chunk warning remains unchanged.

## 4. ADRs Reviewed

Reviewed:

- ADR-001 service-layer architecture
- ADR-004 type-system organization
- ADR-005 error-handling strategy
- ADR-006 multi-tenant architecture
- ADR-007 authorization architecture
- ADR-008 frontend module boundaries
- ADR-009 enterprise naming conventions
- ADR-010 domain-event architecture

## 5. Prior Migrations Reviewed

Reviewed:

- Migration 013 Product type ownership
- Migration 022 Product service facade
- Migration 054 Product operational page
- Migration 060 Sales/POS capability rebaseline
- Migration 061 Payment Method read API POS contract
- Migration 062 Till/TillShift lifecycle contract
- Migration 063 Sale TillShift attribution

## 6. Boundary

This migration is backend-contract-first.

Changed runtime source:

- `app/api/sales.py`

Changed tests:

- `app/api/tests/test_till_shift_contract.py`

Added documentation:

- `frontend/docs/architecture/reviews/MIGRATION-064-POS-PRICE-INTEGRITY-OVERRIDE-POLICY.md`

No POS frontend page was activated.

## 7. Problem

Before Migration 064, checkout totals were calculated by the server, but
`items[].unit_price` could be supplied by the client as any non-negative value.

That allowed an unaudited client-side price choice to become persisted
`SaleItem.unit_price`.

## 8. Critical Invariant

Persisted `SaleItem.unit_price` must be one of:

- canonical server Product selling price; or
- future explicit authorized and audited override.

Since no verified override contract exists, Migration 064 implements canonical
server Product price only.

## 9. Canonical Price Source

Canonical base price:

```text
Product.default_sale_price
```

The server requires this field before a Product can be sold through checkout.

## 10. Product Pricing Fields

Verified Product fields:

- `min_sale_price`
- `default_sale_price`
- `cost_price`
- `tax_code`

No `selling_price`, `sale_price`, `retail_price`, or generic `price` field is
part of the current canonical Product model.

## 11. Price Selection Decision

Chosen path:

```text
Path A - Product.default_sale_price only
```

The previous fallback list was removed from the checkout price decision. This
avoids treating non-canonical or absent model attributes as price authority.

## 12. Unit Price Request Disposition

`items[].unit_price` remains optional in the frontend DTO for compatibility.

Server behavior:

- omitted `unit_price`: accepted and calculated from `Product.default_sale_price`;
- supplied matching `unit_price`: accepted as a stale-cart guard;
- supplied differing `unit_price`: rejected.

The client cannot silently lower or raise the persisted price.

## 13. Override Inventory

Searched backend and frontend permission and request surfaces for:

- `price.override`
- `price_override`
- `override_price`
- `sales.override`
- discount/override-specific permissions

No verified price override permission or audit contract exists.

## 14. Override Policy

Price override support is classified as:

```text
Unsupported
```

Migration 064 does not add override fields, permissions, approval workflows, or
audit events.

## 15. Audit Policy

No price override audit event is emitted because no override path exists.

Future override work must define:

- permission name;
- request shape;
- approval or authorization rule;
- persisted override metadata;
- audit event shape.

## 16. Min Sale Price

`Product.min_sale_price` is now enforced as a floor for the canonical Product
price.

If `default_sale_price < min_sale_price`, checkout rejects the Product before a
Sale is persisted.

## 17. Missing Price

If `Product.default_sale_price` is null, checkout rejects the Product before a
Sale is persisted.

This makes Product activation for POS explicit.

## 18. Negative Price

Negative canonical Product price values are rejected through existing decimal
validation.

Negative client `unit_price` values remain rejected.

## 19. Client Price Mismatch

If `items[].unit_price` is supplied and does not equal the current canonical
price after two-place rounding, checkout returns HTTP 400.

This protects against stale carts and arbitrary client price selection.

## 20. Discount Policy

Positive `discount_amount` is rejected.

Reason:

- no verified discount permission exists;
- no discount audit contract exists;
- accepting client discount would allow the same practical price integrity
  failure through a different field.

Zero and omitted discount remain accepted.

## 21. Tax Policy

Positive `tax_amount` is rejected.

Reason:

- Product has `tax_code`, but no verified tax rate/configuration authority is
  wired into checkout;
- accepting client tax would make totals partly client-authored.

Zero and omitted tax remain accepted.

## 22. Active Product Enforcement

Checkout now rejects inactive Products.

The check applies to both direct `product_id` resolution and barcode resolution.

## 23. Tenant Isolation

Direct Product lookup remains tenant-scoped:

```text
Product.id == product_id
Product.tenant_id == authenticated tenant
```

Barcode ProductCode lookup also remains tenant-scoped before resolving Product.

## 24. Cross-Tenant Product Behavior

Cross-tenant Product IDs are treated as not found.

No Sale is persisted.

## 25. Branch And Warehouse Scope

Migration 064 did not change the existing branch/warehouse contract.

Warehouse must belong to the authenticated branch.

## 26. Till And TillShift Scope

Migration 064 did not change the Migration 063 TillShift attribution contract.

New checkout Sales still persist `Sale.till_shift_id` from the validated open
TillShift.

## 27. Payment Validation

Payment method validation remains server-side and active-only from Migration 061.

Payment amounts remain positive decimals.

## 28. Totals Relationship

Sale subtotal, discount total, tax total, grand total, paid amount, balance due,
and sale status remain server calculated.

Because discount and tax are zero-only in this contract, total is derived from:

```text
sum(quantity * Product.default_sale_price)
```

Partial payment remains supported; `balance_due` is calculated from the
server-derived total.

## 29. Quantity Policy

Quantity remains a required positive decimal and is quantized to four places.

Migration 064 does not change fractional quantity support.

## 30. Currency

No Product-level currency was found in the current Product model.

No currency conversion was introduced.

## 31. Prescription Products

`Product.requires_prescription` exists.

Migration 064 does not make all prescription Products unsellable because no
verified prescription capture/validation contract was part of this migration.

Prescription enforcement remains a future POS/pharmacy workflow concern.

## 32. Inventory Tracking

`Product.track_inventory` exists.

Migration 064 does not change the current stock behavior: checkout still
requires sufficient stock and records sale inventory movement.

Batch, expiry, FEFO, receiving, stock counts, adjustments, and sale-stock
integration remain future inventory migrations.

## 33. Error Contract

Checkout continues to return the existing API shape for validation errors:

```json
{"ok": false, "error": "..."}
```

Validation failures return HTTP 400.

## 34. Backward Compatibility

Backward-compatible behavior retained:

- DTO still accepts optional `unit_price`;
- exact matching client `unit_price` still succeeds;
- omitted `unit_price` now succeeds when Product has `default_sale_price`.

Intentional tightening:

- mismatched `unit_price` fails;
- positive discount fails;
- positive tax fails;
- inactive Product fails;
- missing Product price fails.

## 35. Frontend DTO

No frontend runtime source change was needed.

Current DTO remains:

```text
unit_price?: string | number
discount_amount?: string | number
tax_amount?: string | number
```

The server now owns the authoritative interpretation.

## 36. POS UI Activation

No POS route, page, navigation item, or UI workflow was activated.

## 37. Seed Infrastructure

Existing seed/bootstrap infrastructure:

```text
flask seed-initial
```

Inspected only. It can create an initial tenant, branch, administrator role/user,
and payment methods.

No seed command was executed in Migration 064.

## 38. First-Tenant Seed Readiness

From the previously verified counts:

- foundational tenant/branch/user exist;
- operational Product, Customer, Supplier, and Sales data is empty.

Product POS readiness additionally requires Products to have
`default_sale_price` before checkout can sell them.

## 39. Migration 063 DB Application State

PostgreSQL state in this run:

```text
pg_isready -h localhost -p 5432: no response
pg_lsclusters: 16/main 5432 down
```

`flask db current` and `flask db check` failed because the database connection
could not be established.

Repository head discovery:

```text
flask db heads: 2f4a8b9c1d3e (head)
```

No database upgrade was executed in Migration 064.

## 40. Tests Added

Added checkout contract coverage for:

- server `default_sale_price` when `unit_price` is omitted;
- exact matching client `unit_price`;
- lower and higher client `unit_price` rejection;
- missing `default_sale_price` rejection;
- `default_sale_price` below `min_sale_price` rejection;
- inactive Product rejection;
- cross-tenant Product rejection;
- positive discount rejection;
- positive tax rejection;
- partial payment balance from server price.

## 41. Verification

Commands run after implementation:

```text
venv/bin/python -m compileall app: PASS
venv/bin/python -m pytest app/api/tests/test_till_shift_contract.py -q: 29 passed
venv/bin/python -m pytest app/api/tests/test_sales_pos_contract.py app/api/tests/test_payment_methods_contract.py app/api/tests/test_products_list_contract.py app/api/tests/test_customers_contract.py app/services/tenant/procurement/tests/test_supplier_contract.py -q: 33 passed
venv/bin/python -m pytest app/services/tenant/auth/tests/test_current_session_service.py app/services/tenant/auth/tests/test_current_session_route.py -q: 13 passed
venv/bin/python -m pytest app/services/tenant/auth/tests -q: 129 passed
cd frontend && npx tsc -b --pretty false: PASS
cd frontend && npm run build: PASS
```

## 42. Known Warnings

Existing SQLAlchemy mapper overlap warnings remain:

- `RolePermission.role`
- `RolePermission.permission`
- `UserRole.user`
- `UserRole.role`

These were not changed in Migration 064.

## 43. Frontend Build Warning

The known Vite warning remains:

```text
Some chunks are larger than 500 kB after minification.
```

This is not part of Migration 064.

## 44. Static Search

Static search verified the new checkout price authority is isolated to
`app/api/sales.py`.

No price override permission or override field was found.

## 45. Files Changed

Migration 064 files:

- `app/api/sales.py`
- `app/api/tests/test_till_shift_contract.py`
- `frontend/docs/architecture/reviews/MIGRATION-064-POS-PRICE-INTEGRITY-OVERRIDE-POLICY.md`

## 46. Remaining Technical Debt

Remaining technical debt:

- SQLAlchemy relationship overlap warnings listed above;
- explicit POS discount authorization/audit policy;
- explicit POS tax authority;
- prescription sale validation workflow;
- inventory batch/expiry/FEFO and stock-count workflows;
- Product pricing administration hardening;
- optional future price override approval/audit workflow.

## 47. Outcome

Migration 064 closes the P0 price integrity gap for checkout.

POS checkout now persists `SaleItem.unit_price` from the server canonical Product
price or rejects the request. No fabricated override behavior was introduced.
