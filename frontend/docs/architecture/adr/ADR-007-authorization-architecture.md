# ADR-007 — Authorization & Permission Architecture

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

---

# Context

Hela360 is a multi-tenant enterprise ERP.

Authorization determines which authenticated users may perform specific actions
within the boundaries of their tenant, branch, role, and assigned permissions.

Authorization is a business concern.

It SHALL be enforced by the backend and reflected by the frontend.

The frontend improves usability by hiding unavailable functionality, but SHALL
NOT be considered the security boundary.

---

# Decision

Hela360 SHALL implement Role-Based Access Control (RBAC) with explicit
permissions.

Authorization decisions originate from the backend.

The frontend consumes authorization information and uses it for:

- route protection
- navigation visibility
- feature availability
- action enablement
- user experience

---

# Authorization Model

Every authenticated user belongs to exactly one tenant.

A user may belong to one or more branches.

A user may hold one or more roles.

Roles grant permissions.

Permissions authorize actions.

```
Tenant

↓

User

↓

Role

↓

Permission

↓

Action
```

---

# Permission Format

Permissions SHALL use a consistent naming convention.

```
products.view

products.create

products.update

products.delete

inventory.receive

inventory.adjust

inventory.transfer

sales.create

sales.complete

sales.void

finance.postJournal

administration.manageUsers
```

Permission names SHALL be lowercase and use dot notation.

---

# Authorization Context

The frontend SHALL expose a centralized Authorization Context.

Example:

```typescript
interface AuthorizationContext {

    userId: string;

    tenantId: string;

    branchIds: string[];

    roles: string[];

    permissions: string[];

}
```

This context SHALL be immutable during a request cycle.

---

# Authorization Service

The frontend SHALL expose an Authorization Service responsible for evaluating
permissions.

Example API:

```typescript
can(permission)

canAny(permissions)

canAll(permissions)

hasRole(role)

hasAnyRole(roles)
```

Components SHALL NOT implement permission logic directly.

---

# Route Protection

Protected routes SHALL declare authorization requirements.

Example

```typescript
{
    path: "/sales",

    permission: "sales.view",
}
```

Navigation to unauthorized routes SHALL result in an access-denied experience.

---

# Navigation

Menus SHALL be permission-aware.

Example

```
Inventory

↓

Receive Stock

↓

only if

inventory.receive
```

Unavailable features SHOULD be hidden unless there is a business reason to show
them in a disabled state.

---

# Components

Components SHALL rely on authorization helpers.

Correct

```typescript
if (authorization.can("sales.complete")) {

    ...

}
```

Incorrect

```typescript
if (user.role === "Administrator") {

    ...

}
```

Role names SHALL NOT be hardcoded in components.

---

# Hooks

Hooks SHALL NOT implement authorization.

Hooks assume that authorized callers invoke them.

Permission decisions belong to the authorization layer.

---

# Services

Services SHALL NOT enforce frontend authorization.

Services communicate with the backend.

The backend remains the final authority.

---

# Backend Enforcement

Every protected backend endpoint SHALL validate authorization independently.

Frontend authorization improves usability only.

Removing UI restrictions SHALL NOT grant additional access.

---

# Cache

Authorization changes SHALL invalidate:

- current user
- permissions
- navigation
- dashboard
- feature configuration

The cache invalidation framework SHALL support authorization refresh.

---

# Testing

Authorization tests SHALL verify:

- protected routes
- menu visibility
- feature visibility
- permission helpers
- backend denial handling
- cache refresh after permission changes

---

# Benefits

This architecture provides:

- centralized authorization
- reusable permission checks
- consistent navigation
- simpler components
- backend/frontend alignment
- easier auditing

---

# Future Evolution

This architecture supports:

- Attribute-Based Access Control (ABAC)
- policy-based authorization
- delegated administration
- temporary permissions
- approval workflows
- feature licensing

without requiring changes to component code.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform