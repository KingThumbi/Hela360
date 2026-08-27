# Migration 010 - Backend Supplier Domain Contract

## 1. Migration Purpose

Migration 010 establishes the canonical backend Supplier contract that Migration 009 could not verify. It defines Supplier persistence, validation, serialization, service methods, API endpoints, tenant isolation, lifecycle behavior, authorization permissions, tests, and migration metadata.

## 2. Frontend Blocker

Migration 009 stopped because no backend `Supplier` model, API route, service, serializer, or payload contract existed. This migration creates the backend evidence required for a later frontend supplier type migration.

## 3. Backend Conventions Inspected

Inspected backend models, API routes, services, auth/authorization, errors, migrations, and procurement placeholders under `app/`, plus Product, Customer, Sale, Tenant, Branch, User, Role, Permission, inventory/POS models, and ADR-001, ADR-005, ADR-006, and ADR-007.

Observed conventions:

- UUID primary keys as `String(36)` through `UUIDPrimaryKeyMixin`
- timestamps through `TimestampMixin`
- tenant ownership through non-null `tenant_id` foreign keys
- branch ownership only where the business operation is branch-local
- simple lifecycle through `is_active` where no richer workflow exists
- tenant-scoped uniqueness for business identifiers
- Flask blueprints registered in `app/__init__.py` under `/api`
- route decorators from `app.services.tenant.auth.decorators`
- JSON envelopes using `ok`, `item` or `items`, and pagination metadata

## 4. Supplier Domain Scope

Implemented:

- create supplier
- list suppliers
- get supplier
- update supplier
- deactivate supplier
- reactivate supplier

Not implemented:

- hard delete
- supplier contacts as child aggregate entities
- purchase orders
- goods receipt
- supplier payments
- supplier documents
- supplier analytics or performance summaries

## 5. Canonical Supplier Model

Model path:

```text
app/models/supplier.py
```

Table name:

```text
suppliers
```

## 6. Field Table

| Field | Type | Required | API exposed | Notes |
|---|---:|---:|---:|---|
| id | String(36) | server | yes | UUID string primary key |
| tenant_id | String(36) | server | yes | authenticated tenant ownership |
| supplier_code | String(50) | yes | yes | tenant-scoped unique business identifier |
| name | String(200) | yes | yes | display name |
| legal_name | String(200) | no | yes | optional registered/legal name |
| contact_person | String(150) | no | yes | flat contact field |
| email | String(150) | no | yes | validated email, indexed |
| phone | String(50) | no | yes | validated phone, indexed |
| alternate_phone | String(50) | no | yes | validated phone |
| address_line_1 | String(200) | no | yes | optional address |
| address_line_2 | String(200) | no | yes | optional address |
| city | String(100) | no | yes | optional address |
| county_or_region | String(100) | no | yes | optional address |
| country | String(100) | no | yes | optional address |
| postal_code | String(30) | no | yes | optional address |
| tax_number | String(80) | no | yes | tenant-scoped unique when present |
| registration_number | String(80) | no | yes | tenant-scoped unique when present |
| payment_terms_days | Integer | yes | yes | non-negative, default 0 |
| credit_limit | Numeric(18, 2) | yes | yes | non-negative, default 0 |
| currency | String(3) | yes | yes | uppercase ISO-style code, default KES |
| notes | Text | no | yes | optional operational notes |
| is_active | Boolean | yes | yes | active/inactive lifecycle |
| created_at | DateTime(timezone=True) | server | yes | `TimestampMixin` |
| updated_at | DateTime(timezone=True) | server | yes | `TimestampMixin` |

## 7. Tenant Ownership

Supplier is tenant-owned. `tenant_id` is required, derived from the authenticated identity in routes, and enforced in every `SupplierService` query.

## 8. Branch Ownership Decision

Supplier is tenant-wide with no `branch_id` in this migration. Evidence from Product and Customer showed tenant-owned master data; branch-owned tables are operational inventory/POS entities. Branch-specific supplier purchasing relationships remain future scope.

## 9. Uniqueness Constraints

Tenant-scoped uniqueness:

- `uq_suppliers_tenant_supplier_code`
- `uq_suppliers_tenant_tax_number`
- `uq_suppliers_tenant_registration_number`

No supplier business identifier is globally unique across tenants.

## 10. Status And Lifecycle

Supplier uses `is_active: bool`. No `SupplierStatus` enum was introduced because the initial lifecycle only needs active/inactive.

## 11. Request Contracts

Create request path:

```text
app/schemas/supplier.py::CreateSupplierRequest
```

Update request path:

```text
app/schemas/supplier.py::UpdateSupplierRequest
```

Client-owned fields exclude `id`, `tenant_id`, timestamps, and audit metadata. Update uses PATCH-style partial updates because the backend already uses partial mutation patterns in current APIs.

## 12. Response Contract

Serializer path:

```text
app/serializers/supplier.py::serialize_supplier
```

Single response:

```json
{
  "ok": true,
  "item": {}
}
```

Create response also includes `message`.

## 13. Pagination Contract

List response:

```json
{
  "ok": true,
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total": 0,
    "pages": 0,
    "has_next": false,
    "has_prev": false
  }
}
```

Supported filters:

- `page`
- `page_size` or `per_page`
- `search`
- `is_active`

## 14. Service Methods

Service path:

```text
app/services/tenant/procurement/supplier_service.py
```

Methods:

- `list_suppliers`
- `get_supplier`
- `create_supplier`
- `update_supplier`
- `deactivate_supplier`
- `reactivate_supplier`

## 15. API Routes

Blueprint path:

```text
app/api/suppliers.py
```

Route prefix:

```text
/api
```

Routes:

- `GET /api/suppliers`
- `POST /api/suppliers`
- `GET /api/suppliers/<supplier_id>`
- `PATCH /api/suppliers/<supplier_id>`
- `POST /api/suppliers/<supplier_id>/deactivate`
- `POST /api/suppliers/<supplier_id>/reactivate`

## 16. Authorization Permissions

Added to `app/auth/permissions.py`:

- `suppliers.view`
- `suppliers.create`
- `suppliers.update`
- `suppliers.deactivate`

Route mapping:

- list/get: `suppliers.view`
- create: `suppliers.create`
- update: `suppliers.update`
- deactivate/reactivate: `suppliers.deactivate`

## 17. Error Contracts

Added domain error base classes in `app/errors/__init__.py` and centralized API normalization in `app/api/errors.py`.

Supplier errors include:

- validation failure: `VALIDATION_ERROR`, 400
- not found/cross-tenant lookup: `NOT_FOUND`, 404
- duplicate business identifiers: `CONFLICT`, 409
- lifecycle conflict: `LIFECYCLE_CONFLICT`, 409
- authorization denial: existing `AUTHORIZATION_DENIED`, 403

## 18. Files Created

- `app/api/suppliers.py`
- `app/errors/__init__.py`
- `app/models/supplier.py`
- `app/schemas/__init__.py`
- `app/schemas/supplier.py`
- `app/serializers/__init__.py`
- `app/serializers/supplier.py`
- `app/services/tenant/auth/authorization_context.py`
- `app/services/tenant/procurement/supplier_service.py`
- `app/services/tenant/procurement/tests/__init__.py`
- `app/services/tenant/procurement/tests/test_supplier_contract.py`
- `migrations/versions/8f3b7c2a9d10_add_suppliers.py`
- `frontend/docs/architecture/reviews/MIGRATION-010-BACKEND-SUPPLIER-CONTRACT.md`

## 19. Files Modified

- `app/__init__.py`
- `app/api/customers.py`
- `app/api/errors.py`
- `app/auth/permissions.py`
- `app/models/__init__.py`
- `app/models/auth.py`
- `app/models/security.py`
- `app/services/tenant/procurement/__init__.py`

Notes:

- `app/api/customers.py` received only missing imports needed for app blueprint registration.
- `app/models/auth.py` and `app/models/security.py` received explicit relationship `foreign_keys` needed for SQLAlchemy mapper configuration.
- `app/services/tenant/auth/authorization_context.py` is a compatibility export for existing POS refund imports.

## 20. Database Migration Created

```text
migrations/versions/8f3b7c2a9d10_add_suppliers.py
```

The migration creates `suppliers`, tenant FK, indexes, tenant-scoped uniqueness constraints, and a downgrade that drops indexes and the table.

## 21. Tests Added

```text
app/services/tenant/procurement/tests/test_supplier_contract.py
```

Coverage includes create, list, get, update, deactivate, reactivate, tenant isolation, cross-tenant lookup, duplicate supplier code, validation failure, pagination envelope, active filtering, and authorization denial.

## 22. Verification Commands

```bash
python3 -m compileall app
venv/bin/python -m compileall app
venv/bin/python -m pytest app/services/tenant/procurement/tests/test_supplier_contract.py -q
venv/bin/python -m py_compile migrations/versions/8f3b7c2a9d10_add_suppliers.py
venv/bin/python -c "from app import create_app; app = create_app(); ..."
FLASK_APP='app:create_app' venv/bin/flask routes | rg suppliers
```

## 23. Test Results

Passing:

```text
6 passed
```

Warnings:

```text
4 SQLAlchemy relationship overlap warnings in existing RolePermission/UserRole mappings
```

## 24. Application Startup Result

Full application startup is still blocked by an undeclared auth dependency:

```text
ModuleNotFoundError: No module named 'argon2'
```

The missing import originates from:

```text
app/services/tenant/auth/password_service.py
```

`argon2` is not declared in `requirements.txt`, and no packages were installed in this migration.

Supplier-specific route registration was verified through the focused Flask test app in the supplier contract tests.

## 25. Unresolved Supplier Domain Questions

- Whether tax and registration identifiers should allow multiple empty strings should be confirmed before production data entry rules are finalized.
- Whether future procurement requires supplier-branch purchasing agreements remains a later procurement design decision.
- Whether supplier lifecycle needs suspended/blocked states remains future scope.

## 26. Frontend Contract Now Available

The backend now verifies canonical Supplier fields, request payloads, response shape, pagination metadata, lifecycle operations, and permissions.

## 27. Recommended Migration 011 Frontend Scope

Migration 011 should migrate frontend supplier entity and request DTO ownership from service-local assumptions to canonical types based on this backend contract only.

Suggested scope:

- `Supplier`
- `CreateSupplierRequest`
- `UpdateSupplierRequest`
- supplier list pagination response shape
- supplier service method alignment with `/api/suppliers`

Still avoid:

- `SupplierStatus` enum beyond `is_active`
- `SupplierType`
- `SupplierContact`
- `SupplierSummary`
- supplier analytics/performance types

## 28. Rollback Boundary

Rollback is limited to this migration’s new supplier table and backend contract files. No frontend source files were changed. No procurement workflows were implemented.
