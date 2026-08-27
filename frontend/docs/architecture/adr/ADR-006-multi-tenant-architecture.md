# ADR-006 — Multi-Tenant Architecture

**Status:** Accepted

**Date:** 2026-07-31

**Supersedes:** None

**Requires:**

- ADR-001 Service Layer Architecture
- ADR-002 Query & Mutation Hook Architecture
- ADR-003 Cache & Invalidation Strategy
- ADR-004 Type System Organization
- ADR-005 Error Handling Strategy

---

# Context

Hela360 is a Software-as-a-Service (SaaS) Enterprise Resource Planning (ERP)
platform.

A single deployment serves multiple independent organizations (tenants).

Each tenant owns its own:

- users
- branches
- inventory
- suppliers
- customers
- procurement
- finance
- reports
- configuration

Data belonging to one tenant MUST NEVER be accessible to another tenant.

Tenant isolation is therefore a security requirement rather than an application
feature.

---

# Decision

The frontend SHALL be tenant-aware at every architectural layer.

Tenant context SHALL be established immediately after authentication and remain
available throughout the application lifecycle.

---

# Tenant Context

The authenticated session SHALL expose a Tenant Context.

Example:

```typescript
interface TenantContext {

    tenantId: string;

    tenantCode: string;

    tenantName: string;

    activeBranchId?: string;

    activeBranchName?: string;

    userId: string;

    roles: string[];

    permissions: string[];

}
```

This context represents the active operating environment.

---

# Authentication

Successful authentication SHALL establish:

- authenticated user
- tenant
- active branch (if applicable)
- permissions
- roles

Authentication SHALL fail if tenant context cannot be established.

---

# Request Context

Every authenticated API request SHALL include tenant context using the backend's
approved mechanism (for example, an authorization token, tenant identifier
header, or other agreed protocol).

The frontend SHALL rely on a centralized API layer to attach this context.

Individual services and components SHALL NOT construct tenant metadata manually.

---

# Branch Context

Users may belong to multiple branches.

Only one branch is active at a time.

Changing the active branch SHALL refresh branch-scoped data.

Examples:

- inventory
- sales
- procurement
- dashboards
- reports

Branch switching SHALL NOT require re-authentication.

---

# Query Keys

Tenant-scoped data SHALL be isolated in the cache.

Conceptually:

```
tenant

↓

branch

↓

domain

↓

resource
```

Changing tenant or branch SHALL invalidate all affected caches to prevent stale
or cross-context data.

---

# Services

Domain services SHALL remain tenant-agnostic.

They SHALL NOT:

- store tenant state
- manage tenant switching
- implement authorization logic

Tenant information is supplied by the centralized request pipeline.

---

# Hooks

Hooks SHALL obtain tenant and branch context from the application's context
providers or state management layer.

Hooks SHALL NOT hardcode tenant identifiers.

---

# Authorization

Tenant membership SHALL be validated by the backend.

The frontend SHALL enforce feature visibility based on:

- roles
- permissions

The frontend SHALL NOT be relied upon as the security boundary.

---

# Cross-Tenant Isolation

The application SHALL prevent:

- cross-tenant cache reuse
- cross-tenant navigation state leakage
- cross-tenant local persistence
- cross-tenant optimistic updates

Switching tenants SHALL clear or rebuild all tenant-scoped state.

---

# Offline Storage

If offline storage is introduced, cached data SHALL be partitioned by tenant.

Example:

```
tenant-a/

tenant-b/
```

Data from different tenants SHALL NEVER share the same storage namespace.

---

# Auditability

Tenant and branch context SHALL be available for:

- diagnostics
- telemetry
- audit logging

The frontend SHALL avoid exposing sensitive identifiers unnecessarily in the UI.

---

# Testing

Multi-tenant testing SHALL verify:

- tenant isolation
- branch switching
- cache invalidation
- authorization boundaries
- session changes

Cross-tenant access attempts SHALL be treated as high-priority defects.

---

# Benefits

This architecture provides:

- strong tenant isolation
- predictable cache behavior
- safer branch switching
- scalable SaaS deployment
- simplified service design
- alignment with backend security

---

# Future Evolution

This architecture supports:

- regional deployments
- multi-region hosting
- tenant migrations
- delegated administration
- enterprise organizations with multiple legal entities

without changing the service or hook architecture.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform