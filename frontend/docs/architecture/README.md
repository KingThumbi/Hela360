# Hela360 Architecture Handbook

**Version:** 1.0

**Last Updated:** 2026-07-31

---

# Purpose

This directory contains the official architectural documentation for the
Hela360 Enterprise Platform.

Its purpose is to ensure the system evolves through deliberate architectural
decisions rather than ad hoc implementation.

All developers should consult this handbook before introducing new modules,
patterns, or significant changes.

---

# Architecture Principles

Hela360 follows these guiding principles:

- Domain-Driven Design (DDD)
- Modular Architecture
- Service-Oriented Frontend
- Multi-Tenant SaaS
- Enterprise RBAC
- Centralized State Management
- Predictable Data Flow
- Strong Type Safety
- Business Workflow Orientation
- API-First Development

---

# Architecture Decision Records (ADRs)

The `adr/` directory contains Architecture Decision Records documenting
significant technical decisions.

## Foundational ADRs

| ADR | Title |
|-----|-------|
| ADR-001 | Service Layer Architecture |
| ADR-002 | Query & Mutation Hook Architecture |
| ADR-003 | Cache & Invalidation Strategy |
| ADR-004 | Type System Organization |
| ADR-005 | Error Handling Strategy |
| ADR-006 | Multi-Tenant Architecture |
| ADR-007 | Authorization & Permission Architecture |
| ADR-008 | Frontend Module Boundaries |
| ADR-009 | Enterprise Naming Conventions |
| ADR-010 | Domain Event & Workflow Architecture |

ADRs are immutable historical records.

When an architectural decision changes, a new ADR supersedes the previous one.

---

# Standards

The `standards/` directory contains coding standards and implementation
guidelines.

Examples include:

- Coding Standards
- React Standards
- TypeScript Standards
- API Design
- Folder Organization
- UI Standards
- Testing Standards

Unlike ADRs, standards may evolve over time.

---

# Diagrams

The `diagrams/` directory contains architecture diagrams describing:

- Frontend Architecture
- Backend Architecture
- Authentication Flow
- Inventory Workflow
- Procurement Workflow
- Sales Workflow
- Finance Workflow
- Deployment Architecture

These diagrams complement the ADRs.

---

# Decision Registry

The `decisions/` directory tracks the lifecycle of architectural decisions.

- Proposed
- Accepted
- Deprecated
- Superseded

---

# Repository Architecture

The frontend is organized around business capabilities.

```
src/

    api/

    components/

    contexts/

    features/

    hooks/

    layouts/

    lib/

    routes/

    services/

    types/

    utils/
```

Each feature remains independently maintainable while sharing common platform
infrastructure.

---

# Architectural Layers

```
React Pages

↓

Components

↓

Hooks

↓

Services

↓

API Client

↓

Backend
```

Supporting layers include:

- Query Keys
- Cache Invalidation
- Authorization
- Tenant Context
- Shared Types

---

# Core Principles

## Single Responsibility

Every module, service, hook, and component should have one clearly defined
responsibility.

---

## Separation of Concerns

Business logic belongs in backend domain services.

Frontend services orchestrate communication.

Hooks manage server state.

Components render the user interface.

---

## Predictability

All modules should follow consistent naming, folder structure, and architectural
patterns.

Developers should be able to predict where new functionality belongs.

---

## Consistency

The architecture values consistency over cleverness.

When multiple approaches are possible, the established ADRs take precedence.

---

# Contributing

Before introducing new architecture:

1. Review existing ADRs.
2. Verify alignment with architectural principles.
3. Document significant new decisions using a new ADR.
4. Update relevant standards where necessary.

---

# Governance

The architecture handbook is the authoritative reference for frontend
architecture.

Implementation should follow these documents unless a newer ADR explicitly
supersedes an earlier decision.