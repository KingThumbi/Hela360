# ADR-010 — Domain Event & Workflow Architecture

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
- ADR-009 Enterprise Naming Conventions

---

# Context

Hela360 is an enterprise ERP platform.

Most business operations affect multiple domains.

Examples:

- completing a sale
- receiving stock
- approving a purchase order
- posting a journal
- completing stock counting
- issuing a refund

These are business workflows rather than isolated CRUD operations.

This ADR defines how workflows are represented in the frontend.

---

# Decision

The frontend SHALL model business operations as workflows.

A workflow represents a complete business action.

Workflows coordinate services but SHALL NOT contain business rules that belong
to the backend.

---

# Workflow Principles

A workflow SHALL:

- represent one business outcome
- invoke one or more services
- trigger appropriate cache invalidation
- expose progress and error states
- remain idempotent where practical

---

# Domain Events

A domain event represents something that has already occurred.

Examples:

```
SaleCompleted

StockReceived

StockAdjusted

PurchaseOrderApproved

JournalPosted

GoodsIssued

ShiftClosed
```

Events are business facts.

They are named in the past tense.

---

# Business Commands

Commands represent requested actions.

Examples:

```
CompleteSale

ReceiveStock

TransferStock

ApprovePurchaseOrder

PostJournal
```

Commands express intent.

The backend validates and executes them.

---

# Workflow Lifecycle

Every workflow follows a common lifecycle.

```
User Action

↓

Validation

↓

Service Call

↓

Backend Processing

↓

Success or Failure

↓

Cache Invalidation

↓

UI Refresh
```

---

# Service Coordination

A workflow may involve multiple domains.

Example:

```
Complete Sale

↓

Sales Service

↓

Backend

↓

Inventory Updated

↓

Finance Updated

↓

Customer Ledger Updated

↓

Cache Invalidation

↓

Dashboard Refresh
```

The frontend coordinates the sequence but does not implement business rules.

---

# Cache Refresh

Workflow completion SHALL invoke the centralized invalidation framework.

Examples:

```
invalidateSalesOperations()

invalidateInventoryOperations()

invalidateFinanceOperations()
```

Workflow code SHALL NOT duplicate invalidation logic.

---

# Long-Running Workflows

Some operations may be asynchronous.

Examples:

- report generation
- inventory reconciliation
- data import
- background synchronization

These workflows SHALL expose progress to the user and support polling or future
push-based updates.

---

# Error Handling

Workflow errors SHALL use the standardized error model defined in ADR-005.

Business failures SHALL be presented with clear, actionable messages.

Infrastructure failures SHALL be handled consistently across workflows.

---

# UI Responsibilities

The UI SHALL:

- initiate workflows
- display progress
- display results
- present errors

The UI SHALL NOT implement business rules.

---

# Workflow Naming

Workflow hooks SHALL use business terminology.

Examples:

```
useCompleteSale

useReceiveStock

useApprovePurchaseOrder

usePostJournal
```

Workflow services SHALL expose matching business methods.

---

# Backend Authority

The backend remains the source of truth.

The frontend SHALL assume that:

- validation
- authorization
- business rules
- transaction integrity

are enforced server-side.

---

# Future Evolution

This architecture supports future adoption of:

- event-driven architecture
- message queues
- workflow engines
- sagas
- CQRS
- event sourcing
- real-time notifications

without changing the public workflow APIs.

---

# Benefits

This architecture provides:

- business-oriented APIs
- clear workflow boundaries
- reusable orchestration
- consistent cache refresh
- simpler UI components
- alignment with backend domain logic

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform