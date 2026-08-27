# ADR-004 — Type System Organization

**Status:** Accepted

**Date:** 2026-07-31

**Supersedes:** None

**Requires:**

- ADR-001 Service Layer Architecture
- ADR-002 Query & Mutation Hook Architecture
- ADR-003 Cache & Invalidation Strategy

---

# Context

Hela360 is an enterprise-scale TypeScript application.

Without a formal type organization strategy, interfaces become duplicated across:

- services
- hooks
- components
- API clients
- utilities

This leads to:

- duplicated models
- inconsistent DTOs
- circular dependencies
- difficult maintenance

This ADR establishes the official organization of every shared type in the
frontend.

---

# Decision

All reusable TypeScript types SHALL live under

```
src/types/
```

No business entity SHALL be defined inside services or hooks.

---

# Directory Structure

```
src/types/

    entities/

    requests/

    responses/

    enums/

    api/

    common/

    index.ts
```

---

# Entities

Entities represent business objects.

Examples

```
Sale

SalesReceipt

Customer

Supplier

Product

InventoryItem

PurchaseOrder

Branch

User

Role

Permission
```

Location

```
src/types/entities/
```

Entities SHALL model business concepts only.

---

# Requests

Request DTOs represent data sent to the backend.

Examples

```
CreateSaleRequest

UpdateSaleRequest

ReceiveStockRequest

AdjustStockRequest

CreateSupplierRequest
```

Location

```
src/types/requests/
```

---

# Responses

Response DTOs represent API payloads returned by the backend.

Examples

```
SalesDashboard

InventorySummary

CashierSummary

DailySalesSummary

SupplierPerformance
```

Location

```
src/types/responses/
```

---

# Enums

Business enumerations SHALL live under

```
src/types/enums/
```

Examples

```
SaleStatus

PaymentMethod

PurchaseOrderStatus

InventoryMovementType

UserStatus
```

String unions may be used initially.

As domains mature, dedicated enums are preferred.

---

# API Types

Generic API wrappers SHALL live under

```
src/types/api/
```

Examples

```
ApiResponse

ApiError

PaginatedResponse

PaginationMeta
```

These are transport-level types and SHALL remain independent of business
domains.

---

# Common Types

Cross-cutting reusable types belong under

```
src/types/common/
```

Examples

```
Money

Address

PhoneNumber

AuditFields

DateRange

Coordinates
```

These types may be shared across multiple modules.

---

# Ownership Rules

Each type has a single owner.

Example

```
Sale

↓

entities/sale.ts
```

Hooks, services, and components SHALL import it rather than redefining it.

---

# Import Direction

Dependencies SHALL flow in one direction.

```
Components

↓

Hooks

↓

Services

↓

API

↓

Types
```

Types SHALL NOT import services, hooks, or components.

---

# Naming Rules

Entities

```
Sale

Customer

Supplier
```

Requests

```
CreateSaleRequest

UpdateCustomerRequest
```

Responses

```
SalesDashboard

InventorySummary
```

Enums

```
SaleStatus

PaymentMethod
```

Names SHALL be singular and descriptive.

---

# Service Responsibilities

Services SHALL consume shared types.

Example

Correct

```typescript
import type { Sale } from "@/types/entities";
import type { CreateSaleRequest } from "@/types/requests";
```

Incorrect

```typescript
export interface Sale {
    ...
}
```

inside a service.

---

# Benefits

This organization provides:

- single source of truth
- improved discoverability
- better IDE autocomplete
- reduced duplication
- consistent DTO ownership
- cleaner services
- easier testing
- safer refactoring

---

# Migration Strategy

Existing interfaces may temporarily remain in services while modules are under
active development.

As services are aligned with ADR-001, their types SHALL be extracted into the
shared type hierarchy.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform