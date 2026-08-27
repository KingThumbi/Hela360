# ADR-003 — TanStack Query Cache & Invalidation Strategy

**Status:** Accepted

**Date:** 2026-07-31

**Supersedes:** None

**Requires:**

- ADR-001 Service Layer Architecture
- ADR-002 Query & Mutation Hook Architecture

---

# Context

Hela360 is a multi-tenant enterprise ERP.

A single business operation often affects multiple business domains.

Example

Sale Completion

↓

Inventory

↓

Finance

↓

Customer Ledger

↓

Dashboard

↓

Reports

↓

Analytics

Without centralized cache invalidation:

- duplicate invalidation logic appears everywhere
- developers invalidate different caches
- stale data becomes common
- maintenance becomes difficult

This ADR establishes the cache strategy for the platform.

---

# Decision

Cache invalidation SHALL be centralized.

Mutation hooks SHALL NEVER decide which query keys to invalidate.

Instead they SHALL invoke centralized invalidation helpers.

```
invalidateSalesOperations()

invalidateInventoryOperations()

invalidateFinanceOperations()

invalidateProcurementOperations()
```

---

# Query Keys

Every cache key SHALL originate from

```
src/lib/queryKeys.ts
```

Hardcoded query keys are prohibited.

Incorrect

```typescript
["products"]
```

Correct

```typescript
QUERY_KEYS.products.root
```

---

# Cache Invalidation

All invalidation SHALL occur through

```
src/lib/queryInvalidation.ts
```

Mutation hooks SHALL NOT call

```typescript
queryClient.invalidateQueries(...)
```

directly except inside the invalidation framework.

---

# Business Operations

Business operations invalidate multiple domains.

Example

Sale Completion

```
Sales

Inventory

Finance

Customers

Reports

Dashboard
```

Therefore

```typescript
invalidateSalesOperations()
```

refreshes all affected domains.

---

Goods Receipt

```
Procurement

Inventory

Suppliers

Finance

Dashboard
```

Therefore

```typescript
invalidateProcurementOperations()
```

refreshes those domains.

---

Stock Adjustment

```
Inventory

Dashboard
```

Therefore

```typescript
invalidateInventoryOperations()
```

is sufficient.

---

# Cache Hierarchy

Each domain owns a root namespace.

Example

```
products.root

customers.root

inventory.root

sales.root

finance.root
```

Nested keys derive from the root.

Example

```
products.list()

products.detail(id)

products.categories()
```

This allows efficient invalidation.

---

# Rules

Services SHALL NOT invalidate cache.

Hooks SHALL NOT determine invalidation policy.

Components SHALL NEVER invalidate cache.

Only

```
queryInvalidation.ts
```

defines invalidation policy.

---

# Benefits

Centralization provides

- predictable refresh behaviour
- easier maintenance
- fewer stale views
- reusable mutation hooks
- simpler testing
- easier onboarding

---

# Future Evolution

The invalidation framework may later support

- optimistic updates

- event-driven invalidation

- websocket synchronization

- CQRS read-model refresh

without changing hook implementations.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform