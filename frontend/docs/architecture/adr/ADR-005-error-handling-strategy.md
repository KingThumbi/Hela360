# ADR-005 — Enterprise Error Handling Strategy

**Status:** Accepted

**Date:** 2026-07-31

**Supersedes:** None

**Requires:**

- ADR-001 Service Layer Architecture
- ADR-002 Query & Mutation Hook Architecture
- ADR-003 Cache & Invalidation Strategy
- ADR-004 Type System Organization

---

# Context

Hela360 is an enterprise ERP platform.

Errors may originate from:

- backend validation
- authentication
- authorization
- network failures
- optimistic concurrency
- business rules
- third-party integrations
- infrastructure failures

Without a unified strategy, users receive inconsistent messages, developers
handle errors differently, and debugging becomes difficult.

This ADR defines the standard error handling architecture.

---

# Decision

Errors SHALL be categorized into four layers:

1. Infrastructure Errors
2. Transport Errors
3. Business Errors
4. Presentation Errors

Each layer has clearly defined responsibilities.

---

# Layer 1 — Infrastructure

Infrastructure includes:

- network failures
- DNS failures
- SSL issues
- server unavailable
- request timeout

Examples:

```
No Internet

Gateway Timeout

Connection Refused
```

These errors originate outside the business domain.

---

# Layer 2 — Transport

Transport errors are HTTP/API concerns.

Examples:

```
400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

429 Too Many Requests

500 Internal Server Error

503 Service Unavailable
```

Services SHALL normalize these errors into a consistent frontend error model.

Hooks and components SHALL NOT interpret raw HTTP status codes.

---

# Layer 3 — Business

Business errors represent domain rules.

Examples:

```
InsufficientStockError

SaleAlreadyCompletedError

SupplierInactiveError

CustomerCreditLimitExceededError

DuplicateProductError

PrescriptionExpiredError

PurchaseOrderClosedError
```

Business errors SHALL have explicit names and semantic meaning.

---

# Layer 4 — Presentation

Presentation concerns include:

- notifications
- dialogs
- banners
- form validation
- inline field errors

Components SHALL determine how errors are displayed.

Business logic SHALL NOT decide presentation.

---

# Standard Error Model

All services SHALL expose a common error shape.

```typescript
interface AppError {

    code: string;

    message: string;

    category:
        | "network"
        | "transport"
        | "business"
        | "validation"
        | "system";

    details?: unknown;

    retryable: boolean;

}
```

Services SHALL normalize backend responses into this model.

---

# Validation Errors

Validation failures SHALL preserve field-level information.

Example

```typescript
interface ValidationError {

    field: string;

    message: string;

}
```

Forms SHALL use these directly.

---

# Authentication

Authentication failures SHALL trigger:

```
logout()

clear session

redirect to login
```

without requiring individual components to implement this behavior.

---

# Authorization

Authorization failures SHALL display an appropriate access-denied experience.

Components SHALL NOT implement permission logic.

Permission decisions belong to the authorization layer.

---

# Mutation Hooks

Mutation hooks SHALL propagate normalized errors.

Example

```typescript
const mutation = useMutation(...)

mutation.error
```

The hook SHALL NOT transform the error for presentation.

---

# Retry Strategy

Automatic retries SHALL be limited to transient failures.

Retryable:

- network interruption
- timeout
- temporary server unavailable

Non-retryable:

- validation
- authorization
- business rule violations

---

# Logging

Unexpected errors SHALL be logged through a centralized logging service.

Future integrations may include:

- Sentry
- OpenTelemetry
- Azure Monitor
- Datadog

Application code SHALL NOT depend directly on any logging vendor.

---

# User Messages

User-facing messages SHALL:

- be concise
- avoid technical jargon
- avoid exposing implementation details

Incorrect:

```
AxiosError: ECONNRESET
```

Correct:

```
Unable to reach the server.
Please try again.
```

---

# Domain Ownership

Infrastructure errors belong to:

```
API Layer
```

Transport errors belong to:

```
Service Layer
```

Business errors belong to:

```
Domain Layer
```

Presentation belongs to:

```
UI Layer
```

---

# Benefits

This architecture provides:

- consistent UX
- predictable debugging
- reusable services
- centralized logging
- easier testing
- safer integrations

---

# Future Evolution

This strategy supports:

- offline mode
- background synchronization
- distributed tracing
- event sourcing
- CQRS
- microservices

without changing component code.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform