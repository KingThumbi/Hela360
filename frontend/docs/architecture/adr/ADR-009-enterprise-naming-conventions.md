# ADR-009 — Enterprise Naming Conventions

**Status:** Accepted

**Date:** 2026-07-31

**Supersedes:** None

**Requires:**

- ADR-001 Service Layer Architecture
- ADR-002 Query & Mutation Hook Architecture
- ADR-003 Cache & Invalidation Strategy
- ADR-004 Type System Organization
- ADR-005 Error Handling Strategy
- ADR-006 Multi-Tenant Architecture
- ADR-007 Authorization & Permission Architecture
- ADR-008 Frontend Module Boundaries

---

# Context

Hela360 is an enterprise ERP platform expected to evolve over many years and
across many contributors.

Consistent naming improves:

- readability
- discoverability
- onboarding
- refactoring
- tooling support

This ADR establishes the official naming conventions for the frontend.

---

# Decision

Names SHALL prioritize clarity over brevity.

Business terminology SHALL take precedence over technical terminology.

Names SHALL be descriptive, predictable, and consistent.

---

# General Rules

Use:

- PascalCase for types, interfaces, classes, React components, and enums.
- camelCase for variables, functions, hooks, and object properties.
- UPPER_SNAKE_CASE for constants that are intended to be immutable application
  constants.
- kebab-case for file and directory names unless framework conventions require
  otherwise.

Avoid abbreviations unless they are industry-standard (for example, API, URL,
SKU, JWT, POS).

---

# React Components

Component names SHALL use PascalCase.

Examples:

```
SalesDashboard

InventoryTable

CustomerDetails

ReceiveStockDialog
```

Component files SHALL match the component name.

```
SalesDashboard.tsx

InventoryTable.tsx
```

---

# Hooks

Hooks SHALL:

- begin with `use`
- describe a single responsibility

Examples:

```
useSales

useSale

useReceiveStock

useTransferStock

usePermissions
```

---

# Services

Services SHALL end with `Service`.

Examples:

```
salesService

inventoryService

financeService

authorizationService
```

Service classes SHALL also end with `Service`.

```
SalesService

InventoryService
```

---

# Types

Entity types SHALL be singular.

Examples:

```
Sale

Customer

Supplier

InventoryItem
```

Request DTOs SHALL end with `Request`.

```
CreateSaleRequest

ReceiveStockRequest
```

Response DTOs SHALL describe the business concept returned.

```
SalesDashboard

CashierSummary

InventorySummary
```

---

# Enums

Enum names SHALL be singular.

Examples:

```
SaleStatus

PaymentMethod

InventoryMovementType

PurchaseOrderStatus
```

Enum members SHOULD use uppercase identifiers when represented as string values.

---

# Files

Business files SHALL use kebab-case.

Examples:

```
sales-service.ts

sales-dashboard.tsx

receive-stock-dialog.tsx

query-invalidation.ts
```

When framework conventions require PascalCase (for example, React component
files), that convention takes precedence.

---

# Directories

Directories SHALL use kebab-case.

Examples:

```
sales

inventory

purchase-orders

goods-receipts
```

---

# Query Keys

Query key namespaces SHALL be singular at the root.

Examples:

```
QUERY_KEYS.sales.root

QUERY_KEYS.inventory.root

QUERY_KEYS.customer.root
```

Nested keys SHALL describe resources or views.

Examples:

```
list()

detail(id)

dashboard()

summary()
```

---

# API Endpoints

Frontend endpoint constants SHALL reflect backend resources.

Examples:

```
API_ENDPOINTS.SALES

API_ENDPOINTS.CUSTOMERS

API_ENDPOINTS.INVENTORY
```

Avoid embedding literal URLs throughout the codebase.

---

# Environment Variables

Environment variables SHALL:

- be uppercase
- begin with `VITE_` for frontend build-time variables

Examples:

```
VITE_API_BASE_URL

VITE_APP_NAME

VITE_ENABLE_ANALYTICS
```

---

# Constants

Application-wide constants SHALL use UPPER_SNAKE_CASE.

Examples:

```
DEFAULT_PAGE_SIZE

MAX_UPLOAD_SIZE_MB

SESSION_TIMEOUT_MINUTES
```

---

# Boolean Names

Boolean values SHOULD read naturally.

Examples:

```
isAuthenticated

hasPermission

canReceiveStock

isLoading

isSubmitting
```

Avoid ambiguous names such as:

```
flag

status

check
```

---

# Function Names

Functions SHALL describe actions.

Examples:

```
createSale

receiveStock

approvePurchaseOrder

invalidateSalesOperations
```

Avoid generic verbs such as:

```
process

handle

execute
```

unless additional context is provided.

---

# Imports

Prefer named imports where possible.

Group imports consistently:

1. External libraries
2. Internal shared modules
3. Feature modules
4. Relative imports

---

# Benefits

These conventions provide:

- predictable code navigation
- consistent terminology
- easier code reviews
- improved searchability
- reduced ambiguity
- better IDE support

---

# Exceptions

Framework conventions may override these rules when required.

Any intentional deviation SHALL be documented in the relevant module.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform