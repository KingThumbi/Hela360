# ADR-002 — Query & Mutation Hook Architecture

**Status:** Accepted

**Date:** 2026-07-31

**Supersedes:** None

**Requires:** ADR-001

---

# Context

Hela360 uses TanStack Query for server state management.

Without a standardized hook architecture, query hooks become inconsistent in:

- naming
- cache invalidation
- responsibilities
- mutation behaviour
- error handling

This ADR defines the architecture for every query and mutation hook.

---

# Decision

Hooks SHALL be divided into two categories.

```
Query Hooks

Mutation Hooks
```

Queries retrieve data.

Mutations change data.

---

# Directory Structure

```
src/hooks/

    queries/

        products/

        customers/

        suppliers/

        inventory/

        procurement/

        sales/

        finance/

        administration/
```

Each domain owns its hooks.

---

# Query Hooks

Query hooks SHALL begin with

```
use
```

Examples

```
useProducts()

useProduct()

useCustomers()

useCustomer()

useSales()

useSale()
```

Query hooks SHALL NEVER perform mutations.

---

# Mutation Hooks

Mutation hooks SHALL expose one business operation.

Examples

```
useCreateProduct()

useUpdateProduct()

useDeleteProduct()

useReceiveStock()

useAdjustStock()

useTransferStock()

useCompleteSale()

useSuspendSale()

useResumeSale()

useVoidSale()
```

One hook.

One responsibility.

---

# Responsibilities

Hooks SHALL

- invoke services
- expose loading state
- expose error state
- expose success state
- invalidate cache

Hooks SHALL NOT

- call Axios
- build URLs
- contain business logic
- manipulate DTOs

---

# Services

Hooks SHALL communicate exclusively with services.

```
Hook

↓

Service

↓

BaseService

↓

Axios

↓

Backend
```

Hooks SHALL NEVER call Axios directly.

---

# Cache Invalidation

Mutation hooks SHALL use

```
queryInvalidation.ts
```

Examples

```
invalidateSalesOperations()

invalidateInventoryOperations()

invalidateProcurementOperations()
```

Direct calls to

```
queryClient.invalidateQueries()
```

inside hooks are prohibited except inside the centralized invalidation framework.

---

# Naming

Queries

```
useProducts()

useCustomers()

useSales()
```

Single entity

```
useProduct()

useCustomer()

useSale()
```

Creation

```
useCreateProduct()

useCreateSale()
```

Workflow

```
useCompleteSale()

useApprovePurchaseOrder()

useReceiveGoods()

useTransferStock()
```

---

# Domain Isolation

Hooks SHALL NOT communicate across domains.

Example

Sales hooks SHALL NOT import inventory services.

Instead

```
Sales Hook

↓

Sales Service

↓

Backend

↓

Inventory updated

↓

Cache invalidated
```

---

# Benefits

This architecture provides

- predictable hooks
- consistent naming
- reusable services
- centralized caching
- cleaner components
- easier testing

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform