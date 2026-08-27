# Migration 072 - Prescription and Dispensing Contract

## 1. Migration Purpose
Migration 072 establishes the minimum backend-owned prescription enforcement and SaleItem-linked dispensing audit contract for pharmacy POS checkout.

## 2. ADR Rules
The migration follows ADR-001, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, and ADR-010: backend services own domain validation, frontend types live under canonical request owners, route authorization remains verified, tenant/branch isolation is server-enforced, and no unsupported clinical workflow is invented.

## 3. Starting Baseline
Baseline passed before changes: `venv/bin/python -m compileall app`, `npx tsc -b --pretty false`, and `npm run build`. The known Vite large chunk warning remained.

## 4. Product Prescription Fields
Canonical field: `Product.requires_prescription`, a non-null Boolean with default `False`. It is serialized by `app/api/products.py`, exposed by `frontend/src/types/entities/product.ts`, supported by `CreateProductRequest`, validated in Product forms, and displayed in Product/POS UI.

## 5. Current Enforcement Gap
Before this migration, checkout resolved Product and price but did not enforce `requires_prescription`.

## 6. Existing Prescription/Dispensing Model Inventory
Backend Prescription model: absent. Backend Dispensing model: absent. Backend Patient model: absent. Prescriber model: absent. Existing frontend `prescriptionService.ts` is unsupported scaffolding/placeholder because there is no verified backend API behind it.

## 7. Customer/Patient Decision
No separate Patient model exists. The MVP uses the existing Customer as the explicit person receiving prescription-required items. This does not redefine all Customers as clinical patients outside POS dispensing.

## 8. Walk-In Prescription Disposition
Prescription-required checkout with `customer_id = null` is rejected. Ordinary retail checkout may remain walk-in.

## 9. Minimum Prescription Data
Minimum required documentary data is `prescriber_name`. Optional documentary fields are `prescription_reference`, `prescriber_registration_number`, `prescription_date`, and `notes`.

## 10. Prescriber Identity Decision
Prescriber identity is stored as an immutable free-text snapshot. No prescriber directory or external license verification was introduced.

## 11. Prescription Entity Decision
No separate Prescription entity was created. The current contract does not need lifecycle, refills, or cross-sale reuse.

## 12. Dispensing Entity Decision
Created a narrow `DispensingRecord` persistence entity for SaleItem-level audit.

## 13. SaleItem Relationship
`DispensingRecord.sale_item_id` is unique, giving each prescription-required SaleItem at most one dispensing audit record.

## 14. Batch Trace Disposition
Batch trace remains through `SaleItem -> InventoryMovement.sale_item_id -> InventoryBatch`. Batch allocation is not duplicated into the dispensing table.

## 15. Quantity Behavior
`dispensed_quantity` is derived from persisted `SaleItem.quantity`, so it cannot exceed the sold line quantity.

## 16. Multi-Item Behavior
Multiple SaleItems in the same checkout may use the same documentary prescription reference by repeating the same snapshot on each required line.

## 17. Prescription Reuse/Refill Disposition
Cross-sale reuse, repeats, refill balances, and validity periods are unsupported and deferred.

## 18. Controlled-Drug Disposition
No controlled-drug register exists. `requires_prescription` is not treated as controlled-drug compliance.

## 19. Authorization
No new permission was added. Prescription enforcement runs inside POS checkout, which is already guarded by `sales.create`.

## 20. Checkout Request Shape
`CreateSaleItemRequest` now supports an optional line-level `prescription` object with `prescription_reference`, `prescriber_name`, `prescriber_registration_number`, `prescription_date`, and `notes`.

## 21. Server Enforcement
`DispensingService` checks the Product flag after Product/price validation and before stock allocation. Frontend cannot bypass enforcement by omitting UI fields.

## 22. Errors
Validation uses current checkout error behavior with concise messages for missing prescription context, missing Customer, missing prescriber name, malformed prescription date, and overlong documentary text.

## 23. Date Validation
`prescription_date` parses ISO `YYYY-MM-DD`. No future-date rule or prescription validity period was invented.

## 24. Prescriber Registration Disposition
`prescriber_registration_number` is stored as documentary text only. No licensing verification is claimed.

## 25. Transaction Boundary
Sale, SaleItems, SalePayments, inventory movements, stock deductions, and DispensingRecord rows are added in the same SQLAlchemy transaction. Any dispensing persistence failure rolls back Sale, payments, stock, movements, and dispensing data.

## 26. Refund Behavior
Refunds do not delete dispensing history. Commercial reversal and stock restoration remain handled by the existing refund/stock services.

## 27. Receipt Behavior
Receipt projection remains unchanged and does not expose prescription reference, prescriber fields, or dispensing details.

## 28. Sales History Behavior
Sales History remains commercial/read-only and does not expose prescription details.

## 29. Product UI Changes
No Product form redesign was needed. Product already exposes `requires_prescription`.

## 30. POS UI Changes
POS already marks prescription-required Products in search results. Cart lines now show prescription fields only for prescription-required Products.

## 31. Customer Requirement UX
POS blocks checkout before submit when prescription-required items are present and no Customer is selected. The backend enforces the same rule.

## 32. Frontend Types
Created `CreateSalePrescriptionContext` under `frontend/src/types/requests` and referenced it from `CreateSaleItemRequest`.

## 33. Service/Read API Disposition
No Prescription list/read/admin API was created. Dispensing data is created only inside checkout.

## 34. Audit Trail
`DispensingRecord` captures tenant, branch, Customer, Sale, SaleItem, Product, dispensed quantity, prescriber snapshot, prescription date/reference, dispenser user, and timestamps.

## 35. Tenant/Branch Isolation
Dispensing rows copy tenant and branch from the authenticated checkout/Sale context. Tests verify customer/product tenant consistency and branch-scoped checkout behavior through the existing POS stack.

## 36. Tests
Added focused tests for ordinary checkout, missing prescription context, missing Customer, valid prescription checkout, stock deduction, mixed cart behavior, multi-line shared prescription reference, malformed prescription date, atomic rollback, refund retention, and receipt non-disclosure.

## 37. Alembic Revision
Added revision `b2c3d4e5f6a7_add_dispensing_records.py` after `9a1b2c3d4e5f`. The migration is additive and creates `dispensing_records`.

## 38. Historical Sale Disposition
Existing Sales have no dispensing rows and are classified as legacy/unattributed dispensing history. No backfill was added.

## 39. Local DB State
PostgreSQL `16/main` is down on `localhost:5432`; `pg_isready` reports no response. `flask db heads` reads source head `b2c3d4e5f6a7`; `flask db current` cannot connect.

## 40. Backend Compile
`venv/bin/python -m compileall app` passed.

## 41. Regression Totals
Auth suite passed: 129 tests. Targeted backend regression including Prescription/Dispensing, Sales History, Receipt, POS, payment methods, Product list, Customer, Supplier, current session, and TillShift passed: 141 tests.

## 42. Frontend TypeScript
`npx tsc -b --pretty false` passed.

## 43. Frontend Build
`npm run build` passed. The known Vite large chunk warning remains.

## 44. Warnings
The known SQLAlchemy relationship overlap warnings remain unchanged: `RolePermission.role`, `RolePermission.permission`, `UserRole.user`, and `UserRole.role`.

## 45. Files Inspected
Inspected ADR-001, ADR-004 through ADR-010, Product/Inventory/Customer/Sales/POS/Receipt/History migration reviews, Product model/API/types/forms, Customer model, POS Sale/SaleItem models, checkout route, stock allocation service, refund service, receipt service, Sales DTOs, and POS page.

## 46. Files Created
Created `app/services/tenant/pos/dispensing_service.py`, `app/api/tests/test_prescription_dispensing_contract.py`, `migrations/versions/b2c3d4e5f6a7_add_dispensing_records.py`, `frontend/src/types/requests/create-sale-prescription-context.ts`, and this review document.

## 47. Files Modified
Modified `app/models/pos.py`, `app/models/__init__.py`, `app/api/sales.py`, `app/services/tenant/pos/__init__.py`, `frontend/src/types/requests/create-sale-item-request.ts`, `frontend/src/types/requests/index.ts`, and `frontend/src/features/sales/pages/PosPage.tsx`.

## 48. Remaining Pharmacy Blockers
Remaining pharmacy work includes Prescription read/audit views, refills/repeats, controlled-drug register, prescriber administration, prescription validity policy, e-prescription integration, pharmacy inventory receiving/counts/adjustments, and broader clinical workflows if ever required.

## 49. Invariants Verified
Backend Product flag determines prescription requirement, frontend cannot bypass enforcement, ordinary Products remain unaffected, prescription Products require Customer plus documentary context, dispenser is server-derived, persistence is atomic, refunds retain dispensing history, no EMR fields were introduced, no controlled-drug claim is made, receipt/Sales History remain unchanged, TypeScript is clean, and production build succeeds.

## 50. Rollback Boundary
Rollback removes the dispensing model/table/service/tests, checkout enforcement, POS prescription form wiring, and frontend request type addition. Existing historical Sales require no rollback data migration.

## 51. Recommended Next Migration
Recommended next migration: Inventory backend/API layer for pharmacy receiving, batch/expiry operations, stock counts, adjustments, and operational stock APIs.
