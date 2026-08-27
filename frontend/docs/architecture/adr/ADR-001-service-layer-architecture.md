# ADR-001 — Service Layer Architecture Standard

**Status:** Accepted

**Date:** 2026-07-31

**Authors:** Hela360 Architecture Team

---

# Context

Hela360 is an enterprise-grade, multi-tenant ERP platform for pharmacies,
hospitals, wholesalers, distributors, and retail organizations.

The platform is expected to grow into dozens of business domains, including:

- Authentication
- Administration
- Products
- Inventory
- Procurement
- Sales / POS
- Finance
- CRM
- Human Resources
- Payroll
- Manufacturing
- Reporting
- Business Intelligence

Without a unified service architecture, each module risks exposing different
public APIs, naming conventions, responsibilities, and cache behaviour,
resulting in unnecessary complexity and long-term maintenance costs.

This ADR establishes the architectural contract for all frontend service
modules.

---

# Decision

Every business domain SHALL expose a single public service façade.

Examples:

```text
productService
customerService
supplierService
inventoryService
procurementService
salesService
financeService
```

The service façade represents the business domain.

It SHALL hide:

- HTTP
- Axios
- URLs
- REST semantics
- Backend implementation details

from the rest of the frontend.

---

# Service Responsibilities

A service is responsible for:

- Business operations
- Backend communication
- DTO conversion (when necessary)
- Endpoint routing
- Error propagation

A service SHALL NOT contain:

- React state
- React hooks
- Cache invalidation
- UI logic
- Component logic

---

# Public API Standard

Every service SHALL expose business-oriented methods.

## Query Operations

```typescript
listProducts()

getProduct()

listCustomers()

getCustomer()

listSales()

getSale()
```

---

## CRUD Operations

```typescript
createProduct()

updateProduct()

deleteProduct()

createCustomer()

updateCustomer()

deleteCustomer()
```

---

## Workflow Operations

Business verbs SHALL be preferred.

Examples:

```typescript
completeSale()

suspendSale()

resumeSale()

voidSale()

approvePurchaseOrder()

receiveGoods()

adjustStock()

transferStock()

postJournal()

closeShift()
```

The following names SHALL NOT be exposed publicly:

```typescript
checkout()

post()

patch()

payments()

receipt()
```

The public API represents business language rather than transport language.

---

## Supporting Operations

Examples:

```typescript
searchProducts()

inventoryValuation()

customerHistory()

listSalePayments()

getReceipt()

getDashboard()
```

---

# BaseService

All domain services SHALL inherit from BaseService.

BaseService owns generic CRUD operations.

```typescript
list()

get()

create()

update()

delete()
```

Domain services SHALL wrap these methods with business-specific names.

Example:

```typescript
class SalesService extends BaseService<...> {

    async listSales() {
        return this.list();
    }

    async getSale(id: string) {
        return this.get(id);
    }

    async createSale(payload) {
        return this.post(
            `${this.resource}/checkout`,
            payload,
        );
    }

}
```

The frontend therefore never depends on generic CRUD naming.

---

# Types

Services SHALL NOT define business entities.

Shared types SHALL live under:

```text
src/types/

    entities/

    requests/

    responses/

    enums/
```

Example:

```text
entities/
    sale.ts
    supplier.ts
    product.ts

requests/
    createSale.ts
    transferStock.ts

responses/
    salesDashboard.ts
```

---

# Query Hooks

Query hooks SHALL communicate exclusively with domain services.

Architecture:

```text
React Hook

        ↓

Domain Service

        ↓

BaseService

        ↓

Axios

        ↓

Backend API
```

Hooks SHALL NEVER communicate with Axios directly.

---

# Cache Invalidation

Services SHALL NEVER invalidate TanStack Query caches.

Mutation hooks SHALL use the centralized invalidation framework.

```typescript
invalidateSalesOperations()

invalidateInventoryOperations()

invalidateFinanceOperations()
```

located in

```text
src/lib/queryInvalidation.ts
```

This guarantees consistent cache behaviour across the application.

---

# Naming Rules

Lists:

```typescript
listProducts()

listSales()
```

Single entity:

```typescript
getProduct()

getSale()
```

Creation:

```typescript
createProduct()

createSale()
```

Update:

```typescript
updateProduct()
```

Deletion:

```typescript
deleteProduct()
```

Workflow:

```typescript
approvePurchaseOrder()

receiveGoods()

completeSale()

voidSale()
```

Dashboard:

```typescript
getDashboard()
```

---

# Module Structure

A typical module SHALL follow:

```text
services/

    sales/

        index.ts

        salesService.ts

        refundService.ts

        prescriptionService.ts
```

Future extraction into multiple services is permitted when business complexity
requires it.

Example:

```text
sales/

    salesQueryService.ts

    salesWorkflowService.ts

    receiptService.ts

    paymentService.ts

    refundService.ts
```

Such refactoring SHALL preserve the public façade.

---

# Architectural Principles

The service layer SHALL obey:

- Domain Driven Design
- Separation of Concerns
- Single Responsibility Principle
- Stable Public APIs
- Encapsulation
- Explicit Business Language

---

# Consequences

Advantages include:

- Consistent public APIs
- Easier onboarding
- Better IDE discoverability
- Easier testing
- Cleaner React hooks
- Stable module boundaries
- Reduced coupling
- Better long-term maintainability

The primary trade-off is that services may contain thin wrapper methods around
BaseService operations, which is considered acceptable in exchange for a stable
business-oriented API.

---

# Implementation Status

This ADR applies to:

- Authentication
- Products
- Customers
- Suppliers
- Inventory
- Procurement
- Sales

Future modules SHALL comply upon introduction.

---

# Supersedes

None.

This is the first architectural decision record for Hela360.

---

# Approval

Approved by:

**Chief Architect**

Hela360 Enterprise Platform

2026-07-31