# ADR-008 — Frontend Module Boundaries & Module Organization

**Status:** Accepted

**Date:** 2026-08-03

**Supersedes:** None

**Requires:**

- ADR-001 Service Layer Architecture
- ADR-002 Query & Mutation Hook Architecture
- ADR-003 Cache & Invalidation Strategy
- ADR-004 Type System Organization
- ADR-005 Error Handling Strategy
- ADR-006 Multi-Tenant Architecture
- ADR-007 Authorization & Permission Architecture

---

# Context

Hela360 is a multi-tenant enterprise ERP frontend composed of multiple business
domains, shared platform infrastructure, reusable UI components, centralized
services, React Query hooks, application providers, routing, navigation, and a
shared type system.

The frontend currently includes business domains such as:

- Authentication
- Administration
- Dashboard
- Products
- Inventory
- Procurement
- Sales
- Customers
- Suppliers
- Finance
- Reports

As the application continues to grow, unrestricted dependencies between modules
introduce several architectural risks, including:

- circular dependencies
- duplicated business logic
- duplicated type definitions
- service-layer leakage
- feature coupling
- unstable public APIs
- inconsistent folder organization
- difficult refactoring
- inconsistent ownership
- unpredictable build failures

Without clearly defined module boundaries, individual domains begin to depend on
implementation details belonging to other domains rather than consuming stable
public contracts.

Over time this causes:

- increasing compilation failures
- fragile refactoring
- hidden runtime coupling
- duplicated responsibilities
- poor discoverability
- slower development
- inconsistent architectural decisions

The frontend requires explicit architectural boundaries that define:

- module ownership
- dependency direction
- public APIs
- shared infrastructure
- cross-domain communication
- reusable contracts

This ADR establishes those boundaries.

The goal is not simply to prescribe folders.

The goal is to ensure that Hela360 remains modular, maintainable, scalable and
safe to evolve as the enterprise platform expands.

---

# Decision

The Hela360 frontend SHALL be organized around clearly defined architectural
modules.

Every source file SHALL have exactly one architectural owner.

Modules SHALL communicate through stable public contracts rather than internal
implementation details.

Dependencies SHALL flow in a single direction from presentation toward
infrastructure.

Lower-level infrastructure SHALL NOT depend on higher-level presentation code.

Business domains SHALL remain independent except through explicitly documented
public interfaces.

The frontend dependency graph SHALL remain acyclic.

Every architectural layer SHALL expose only the APIs required by higher layers.

Private implementation details SHALL remain private.

---

# Architectural Principles

The frontend SHALL follow the following architectural principles.

## Single Ownership

Every source file SHALL belong to one architectural module.

Ownership SHALL be unambiguous.

Responsibilities SHALL NOT overlap between modules.

---

## Explicit Dependencies

Imports SHALL express intentional architectural dependencies.

Implicit coupling through deep imports or shared implementation details is
prohibited.

---

## Stable Public APIs

Every architectural module SHOULD expose a controlled public interface through
an `index.ts` barrel where appropriate.

Consumers SHALL depend on public contracts rather than private files.

---

## Layered Architecture

Higher layers may depend upon lower layers.

Lower layers SHALL NOT depend upon higher layers.

---

## Domain Isolation

Business domains SHALL remain independent.

Cross-domain communication SHALL occur only through approved service contracts,
shared types, backend workflows, or centralized infrastructure.

---

## Infrastructure Reuse

Cross-cutting infrastructure SHALL be shared rather than duplicated across
features.

Examples include:

- API client
- BaseService
- query keys
- cache invalidation
- authorization
- navigation
- configuration
- shared types

---

## Build Safety

Architectural scaffolding SHALL remain build-safe.

Temporary migrations SHALL preserve valid public exports and TypeScript
compilation throughout the migration process.

---

# Canonical Source Structure

The canonical frontend source structure SHALL be:

```text
src/
├── api/
├── app/
├── assets/
├── components/
├── config/
├── constants/
├── features/
├── hooks/
├── layouts/
├── lib/
├── navigation/
├── providers/
├── routes/
├── services/
├── stores/
├── types/
├── utils/
├── App.tsx
└── main.tsx
```

Each top-level directory has one primary responsibility.

No directory SHALL evolve into a miscellaneous container for unrelated code.

Directories SHALL be introduced only when they provide meaningful architectural
separation.

Empty directories SHALL NOT be created merely to preserve visual symmetry.

---

# Canonical Module Responsibilities

## api/

Owns transport infrastructure.

Examples include:

- Axios client
- interceptors
- endpoint registry
- request pipeline
- authentication headers
- tenant headers
- branch headers

---

## app/

Owns application composition.

Examples include:

- application initialization
- router composition
- provider composition
- application bootstrap

---

## assets/

Owns static frontend assets.

Examples include:

- images
- logos
- icons
- fonts

---

## components/

Owns reusable presentation components.

These components SHALL remain domain-neutral.

---

## config/

Owns runtime configuration.

Examples include:

- environment configuration
- application configuration
- feature flags

---

## constants/

Owns runtime constants.

Examples include:

- route constants
- storage keys
- application limits
- runtime identifiers

---

## features/

Owns business feature presentation.

Each business capability SHALL own its pages and feature-specific UI.

---

## hooks/

Owns reusable hooks.

This includes both:

- application hooks
- React Query hooks

---

## layouts/

Owns reusable application layouts.

---

## lib/

Owns shared platform infrastructure.

Examples include:

- query keys
- cache invalidation
- error handling
- utility helpers

---

## navigation/

Owns navigation configuration.

---

## providers/

Owns React providers.

---

## routes/

Owns route declarations.

---

## services/

Owns business service implementations.

---

## stores/

Owns client-side state.

---

## types/

Owns shared application contracts.

---

## utils/

Owns general-purpose utility functions.

Utilities SHALL remain domain-neutral.

---

# Architectural Layers

The canonical dependency hierarchy SHALL be:

```text
Application Composition

↓

Routes

↓

Layouts

↓

Feature Pages

↓

Feature Components

↓

Hooks

↓

Domain Services

↓

Base Service

↓

API Client

↓

Backend API
```

Supporting infrastructure is shared across these layers.

Supporting infrastructure includes:

```text
Types

Constants

Configuration

Authorization

Navigation

Providers

Stores

Utilities

Query Keys

Cache Invalidation
```

These supporting modules SHALL remain reusable and independent of individual
business features.

---

# Dependency Direction

Dependencies SHALL always move downward through the architectural hierarchy.

For example:

```text
Feature Component

↓

Hook

↓

Service

↓

BaseService

↓

API Client
```

This dependency direction is permitted.

The reverse dependency direction is prohibited.

For example:

```text
API Client

↓

Feature Component
```

is prohibited.

Likewise:

```text
BaseService

↓

React Hook
```

is prohibited.

Lower-level infrastructure SHALL remain unaware of presentation concerns.

---

# Application Composition

Application composition is responsible for assembling the entire frontend.

It owns:

- application bootstrap
- provider composition
- router composition
- global layouts
- authentication initialization
- theme initialization
- React Query initialization
- application shell
- global error boundaries

Canonical locations include:

```text
src/app/
src/providers/
src/routes/
src/layouts/
src/App.tsx
src/main.tsx
```

Application composition SHALL coordinate modules.

It SHALL NOT implement business logic.

Examples of prohibited responsibilities include:

- sales calculations
- inventory adjustments
- procurement workflows
- financial posting
- customer validation
- supplier approval
- product pricing

Those responsibilities belong to their respective business domains.

Application composition SHALL focus exclusively on composing the application
from reusable modules.

It SHALL remain thin, declarative and free of domain-specific behavior.

---

# Application Composition Responsibilities

Application composition SHALL:

- initialize providers
- initialize routing
- initialize authentication
- initialize application state
- initialize global infrastructure
- compose layouts
- register feature routes
- register global error handling

Application composition SHALL NOT:

- fetch business data directly
- call domain services directly
- evaluate permissions
- mutate business state
- perform calculations
- duplicate feature logic

Business behavior SHALL remain inside the appropriate feature modules and
service layers.

---

# Consequences

Adopting these module boundaries provides:

- predictable project organization
- explicit ownership
- safer refactoring
- improved discoverability
- reduced coupling
- easier onboarding
- improved testability
- consistent architectural decisions
- scalable feature growth
- improved long-term maintainability

The remaining sections of this ADR define the boundaries governing Feature
Modules, Shared Components, Hooks, Services, Shared Types, Navigation,
Providers, Cross-Domain Communication, Dependency Rules, Migration Strategy,
and Architectural Enforcement.
# Feature Modules

A feature module represents a single business capability.

Each feature owns its presentation layer while relying upon shared platform
infrastructure for cross-cutting concerns.

Feature modules SHALL remain cohesive, independently understandable and loosely
coupled to other business domains.

The canonical feature structure is:

```text
src/features/
├── administration/
├── auth/
├── customers/
├── dashboard/
├── finance/
├── inventory/
├── procurement/
├── products/
├── reports/
├── sales/
└── suppliers/
```

Each directory represents one bounded business context.

Feature modules SHALL own only the presentation concerns for that domain.

---

# Feature Responsibilities

A feature module MAY own:

- pages
- feature-specific components
- feature forms
- feature validation schemas
- feature presentation helpers
- feature-specific constants
- feature-local utilities
- feature route declarations
- feature documentation

Example:

```text
features/sales/
├── components/
├── forms/
├── pages/
├── schemas/
├── constants/
├── utils/
├── routes.tsx
└── index.ts
```

The internal organization may evolve as the feature grows.

---

# Feature Ownership

A feature SHALL own:

- user-facing pages
- feature-specific dialogs
- feature-specific tables
- feature-specific form layouts
- feature-specific UI state
- feature presentation logic
- feature routing

A feature SHALL NOT own:

- reusable entities
- reusable request DTOs
- reusable response DTOs
- reusable authorization logic
- reusable services
- reusable query keys
- reusable cache invalidation
- reusable runtime constants

These belong to shared platform infrastructure.

---

# Feature Isolation

Business domains SHALL remain isolated.

One feature SHALL NOT depend directly upon another feature's private
implementation.

Incorrect

```text
Sales

↓

Inventory Component
```

Correct

```text
Sales

↓

Inventory Service

↓

Backend

↓

Shared Types
```

Private feature implementation details SHALL remain private.

Only stable public contracts may be consumed.

---

# Feature Public APIs

Each feature SHOULD expose a stable public API.

Example:

```text
features/sales/index.ts
```

Example exports:

```typescript
export { SalesPage } from "./pages/SalesPage";

export { SalesDashboardPage } from "./pages/SalesDashboardPage";

export { SaleDetailPage } from "./pages/SaleDetailPage";
```

Consumers SHOULD import through the public feature barrel.

Correct

```typescript
import {
    SalesPage,
} from "@/features/sales";
```

Discouraged

```typescript
import {
    SalesPage,
} from "@/features/sales/pages/SalesPage";
```

The public API SHALL remain stable.

Internal refactoring SHALL NOT require changes throughout the application.

---

# Shared Components

Reusable presentation components belong under:

```text
src/components/
```

Examples include:

- buttons
- inputs
- selects
- tables
- dialogs
- cards
- badges
- alerts
- page headers
- breadcrumbs
- loading indicators
- empty states
- confirmation dialogs

Shared components SHALL remain business-neutral.

---

# Shared Component Responsibilities

Shared components SHALL:

- render UI
- expose reusable interfaces
- remain configurable
- avoid business rules
- support accessibility
- remain presentation focused

Shared components SHALL NOT:

- call backend APIs
- call business services
- implement authorization
- perform calculations
- mutate business state

---

# Domain Components

Business-specific components SHALL remain inside their feature.

Example

Correct

```text
features/sales/components/VoidSaleDialog.tsx
```

Incorrect

```text
components/VoidSaleDialog.tsx
```

Likewise

Correct

```text
features/procurement/components/PurchaseOrderTable.tsx
```

Incorrect

```text
components/PurchaseOrderTable.tsx
```

A component belongs under `src/components` only when it is reusable across
multiple business domains.

---

# Hooks

Hooks provide reusable frontend behavior.

Two categories of hooks exist.

## Application Hooks

Application hooks belong under:

```text
src/hooks/
```

Examples include:

- useApplication
- useTheme
- useNavigation
- useNotifications
- useCurrentBranch
- useUserMenu

Application hooks coordinate frontend behavior.

---

## Query Hooks

Server-state hooks belong under:

```text
src/hooks/queries/
```

Grouped by domain:

```text
src/hooks/queries/
├── administration/
├── auth/
├── customers/
├── dashboard/
├── finance/
├── inventory/
├── procurement/
├── products/
├── reports/
├── sales/
└── suppliers/
```

Every query hook SHALL belong to exactly one business domain.

---

# Query Hook Responsibilities

Query hooks SHALL:

- call domain services
- configure TanStack Query
- expose typed server state
- expose loading state
- expose error state
- expose mutation state
- consume canonical query keys
- consume centralized cache invalidation

Query hooks SHALL NOT:

- call Axios directly
- build endpoint URLs
- define reusable entities
- define reusable request DTOs
- duplicate cache invalidation
- implement authorization
- manipulate unrelated domain stores

---

# Mutation Hooks

Mutation hooks SHALL invoke centralized invalidation helpers.

Correct

```typescript
await invalidateSalesOperations(
    queryClient,
);
```

Incorrect

```typescript
await queryClient.invalidateQueries(
    ...
);

await queryClient.invalidateQueries(
    ...
);

await queryClient.invalidateQueries(
    ...
);
```

Mutation behavior SHALL remain standardized throughout the platform.

---

# Query Keys

Every query hook SHALL obtain query keys from the centralized registry.

Correct

```typescript
QUERY_KEYS.sales.list();

QUERY_KEYS.sales.detail(id);
```

Incorrect

```typescript
["sales"];

["sales", id];

["sales", "dashboard"];
```

Hardcoded query keys are prohibited.

---

# Hook Boundaries

Hooks SHALL NOT call other domain hooks to implement business workflows.

Incorrect

```text
Sales Hook

↓

Inventory Hook

↓

Finance Hook
```

Correct

```text
Sales Hook

↓

Sales Service

↓

Backend Transaction

↓

Centralized Cache Refresh
```

Backend workflows remain responsible for transactional integrity.

The frontend reflects backend state through centralized cache invalidation.

---

# Hook Ownership

Each hook SHALL have one architectural owner.

Examples:

```text
useSales

↓

Sales
```

```text
useProducts

↓

Products
```

```text
useDashboard

↓

Dashboard
```

Cross-domain hooks SHALL be exceptional and explicitly documented.

---

# Hook Naming

Hooks SHALL use consistent naming.

Examples:

Queries

```text
useSales

useSale

useProducts

useProduct
```

Mutations

```text
useCreateSale

useUpdateSale

useVoidSale

useCompleteSale
```

Names SHALL reflect business behavior rather than transport behavior.

Examples of discouraged names include:

```text
usePost

useExecute

useData

useCallApi
```

Business terminology SHALL be preferred throughout the application.

---

# Consequences

Organizing features, components and hooks in this manner provides:

- clear ownership
- isolated business domains
- reusable presentation components
- predictable query organization
- centralized cache management
- simpler testing
- easier onboarding
- reduced coupling
- scalable feature growth
- stable public APIs

The following section defines the canonical Service Layer, BaseService,
API Layer, Endpoint Registry and Shared Type System.
# Services

Services provide the frontend's business communication layer.

They encapsulate all communication with backend APIs while presenting a
business-oriented interface to hooks and higher architectural layers.

Services SHALL remain independent of React.

Services SHALL remain independent of presentation concerns.

Services SHALL communicate exclusively with the backend through the centralized
API infrastructure.

---

# Canonical Service Structure

Services belong under:

```text
src/services/
├── administration/
├── auth/
├── base/
├── customers/
├── dashboard/
├── finance/
├── procurement/
├── products/
├── reports/
├── sales/
└── suppliers/
```

Each business domain SHALL own its own service implementations.

---

# Service Responsibilities

Services SHALL own:

- backend communication
- endpoint invocation
- request construction
- response extraction
- transport orchestration
- endpoint-specific configuration
- file download
- upload operations
- business-oriented method names

Services SHALL expose a stable business API.

Example

```typescript
listSales()

getSale()

completeSale()

voidSale()

refundSale()

receiveStock()

approvePurchaseOrder()

createSupplier()
```

---

# Service Boundaries

Services SHALL NOT own:

- React components
- React hooks
- React state
- TanStack Query configuration
- cache invalidation
- notifications
- routing
- authorization logic
- reusable entities
- reusable DTOs

These responsibilities belong to other architectural layers.

---

# Service Communication

The service layer communicates only with:

- BaseService
- API Client
- Shared Types
- Endpoint Registry

It SHALL NOT communicate directly with:

- components
- providers
- stores
- routes
- navigation
- feature pages

---

# Service Method Naming

Public service methods SHALL describe business behavior.

Correct

```typescript
createSale()

completeSale()

voidSale()

getReceipt()

listProducts()

updateInventory()

approvePurchaseOrder()
```

Incorrect

```typescript
post()

put()

patch()

execute()

process()

callApi()
```

Business language SHALL remain visible throughout the public service API.

---

# Business Workflow Services

Large business domains MAY be divided into multiple services.

Example

```text
services/sales/
├── salesQueryService.ts
├── salesWorkflowService.ts
├── paymentService.ts
├── receiptService.ts
├── refundService.ts
├── prescriptionService.ts
├── salesDashboardService.ts
└── index.ts
```

Each service SHALL own one business responsibility.

Examples include:

Sales Query Service

- listing sales
- retrieving sale details
- dashboard queries

Workflow Service

- checkout
- completion
- suspension
- cancellation

Receipt Service

- receipt generation
- receipt download

Payment Service

- payment retrieval
- payment processing

This keeps service responsibilities focused and easier to maintain.

---

# Service Public API

Each domain SHOULD expose one stable public barrel.

Example

```text
services/sales/index.ts
```

Example

```typescript
export { salesQueryService };

export { salesWorkflowService };

export { paymentService };

export { receiptService };

export { refundService };

export { prescriptionService };
```

Consumers SHALL import through the public barrel rather than internal files.

---

# Legacy Services

During architectural migration a legacy service MAY temporarily remain.

Example

```text
legacySalesService.ts
```

Legacy services SHALL:

- preserve backward compatibility
- remain build-safe
- be clearly documented
- have a defined removal plan

Legacy services SHALL NOT become permanent architecture.

Every legacy implementation SHALL have a migration target.

---

# BaseService

The BaseService provides reusable transport functionality for all business
services.

Canonical location:

```text
src/services/base/
```

Every domain service MAY inherit from BaseService.

---

# BaseService Responsibilities

BaseService SHALL provide:

- GET
- POST
- PUT
- PATCH
- DELETE
- pagination
- filtering
- sorting
- uploads
- downloads
- endpoint normalization
- request configuration
- response handling

These capabilities SHALL remain generic.

---

# BaseService SHALL NOT Own

BaseService SHALL NOT contain:

- sales logic
- procurement logic
- inventory calculations
- finance rules
- customer validation
- supplier workflows
- dashboard logic

BaseService SHALL remain completely business-neutral.

---

# BaseService Public Contract

The BaseService SHALL expose protected transport primitives.

Example

```typescript
protected get()

protected post()

protected put()

protected patch()

protected delete()
```

Business services SHALL expose business terminology.

They SHALL NOT expose transport terminology.

---

# Method Collision

Business service methods SHALL NOT override transport method names.

Incorrect

```typescript
class InvoiceService {

    post()

}
```

Correct

```typescript
class InvoiceService {

    postInvoice()

}
```

Likewise

Incorrect

```typescript
patch()
```

Correct

```typescript
updateSale()

updateSupplier()

updateInventory()
```

Business terminology prevents conflicts with BaseService.

---

# API Layer

The API layer owns transport infrastructure.

Canonical location:

```text
src/api/
```

The API layer owns:

- Axios client
- interceptors
- request pipeline
- response pipeline
- authentication headers
- tenant headers
- branch headers
- retry policy
- timeout configuration

---

# API Layer Responsibilities

The API layer SHALL:

- configure Axios
- normalize requests
- normalize responses
- attach authentication
- attach tenant context
- attach branch context
- normalize backend errors

The API layer SHALL remain completely independent of business domains.

---

# API Layer SHALL NOT

The API layer SHALL NOT:

- import services
- import hooks
- import components
- import providers
- import routes
- import navigation

It remains shared transport infrastructure.

---

# Endpoint Registry

All backend endpoints SHALL originate from one centralized endpoint registry.

Canonical location:

```text
src/api/endpoints.ts
```

Literal endpoint strings SHALL NOT appear throughout service files.

Incorrect

```typescript
"/sales"

"/products"

"/inventory"
```

Correct

```typescript
API_ENDPOINTS.SALES.ROOT

API_ENDPOINTS.PRODUCTS.ROOT

API_ENDPOINTS.INVENTORY.ROOT
```

---

# Endpoint Groups

Endpoint groups SHALL expose structured APIs.

Example

```typescript
API_ENDPOINTS.SALES.ROOT

API_ENDPOINTS.SALES.BY_ID(id)

API_ENDPOINTS.SALES.RECEIPT(id)

API_ENDPOINTS.SALES.VOID(id)
```

Business services SHALL consume the appropriate endpoint member.

Constructors SHALL use:

```typescript
super(
    API_ENDPOINTS.SALES.ROOT,
);
```

rather than:

```typescript
super(
    API_ENDPOINTS.SALES,
);
```

---

# Shared Type System

Reusable application contracts belong under:

```text
src/types/
├── entities/
├── requests/
├── responses/
├── enums/
├── common/
├── domains/
└── index.ts
```

The shared type system represents the canonical contract layer for the frontend.

---

# Entity Ownership

Business entities belong under:

```text
src/types/entities/
```

Examples include:

- Sale
- Product
- Customer
- Supplier
- Invoice
- Payment
- InventoryItem

Every reusable entity SHALL have one owner.

---

# Request DTO Ownership

Request contracts belong under:

```text
src/types/requests/
```

Examples include:

- CreateSaleRequest
- UpdateSaleRequest
- LoginRequest
- CreateSupplierRequest
- UpdateProductRequest

Services SHALL consume these DTOs.

They SHALL NOT redefine them.

---

# Response DTO Ownership

Response contracts belong under:

```text
src/types/responses/
```

Examples include:

- LoginResponse
- CurrentUserResponse
- RefreshTokenResponse
- DashboardResponse
- SalesDashboardResponse

Shared response types SHALL remain centralized.

---

# Enum Ownership

Runtime-backed domain values belong under:

```text
src/types/enums/
```

Examples include:

- SaleStatus
- PaymentMethod
- ProductStatus
- InventoryStatus
- UserStatus

When runtime access is required, constant-backed values SHALL be preferred over
type-only enums.

---

# Domain Type Barrels

Domain barrels provide stable import surfaces.

Example

```text
src/types/domains/sales.ts
```

Example exports

```typescript
Sale

SaleItem

SalePayment

CreateSaleRequest

UpdateSaleRequest

SaleStatus

PaymentMethod
```

Consumers SHOULD import from the domain barrel whenever practical.

---

# Type Ownership Rules

Every reusable type SHALL have one canonical owner.

Hooks SHALL NOT redefine entities.

Services SHALL NOT redefine entities.

Components SHALL NOT redefine entities.

Duplicate business contracts are prohibited.

---

# Consequences

Separating Services, BaseService, API infrastructure and the Shared Type System
provides:

- reusable transport infrastructure
- stable business APIs
- reduced duplication
- centralized endpoint management
- clearer service responsibilities
- reusable domain contracts
- easier testing
- safer architectural evolution

The following section defines State Management, Providers, Navigation, Routes,
Query Keys, Cache Invalidation and Cross-Domain Communication.
# State Management

State management SHALL distinguish between server state and client state.

Server state represents authoritative data owned by the backend.

Client state represents frontend-only application state.

The two categories SHALL remain separate.

---

# Server State

Server state belongs to TanStack Query.

Examples include:

* sales
* products
* inventory
* customers
* suppliers
* purchase orders
* invoices
* payments
* reports
* dashboard metrics
* branch-scoped operational data

TanStack Query SHALL remain the authoritative frontend owner of server state.

---

# Server-State Responsibilities

TanStack Query SHALL manage:

* data fetching
* caching
* background refresh
* stale state
* loading state
* error state
* retry behavior
* request deduplication
* mutation lifecycle
* cache invalidation

Components SHALL consume server state through query hooks.

Components SHALL NOT duplicate authoritative server state into local stores
without an explicitly documented reason.

---

# Client State

Client-only state may belong to:

* React context
* Zustand
* local component state

Examples include:

* active theme
* application shell state
* sidebar state
* temporary filters
* active branch selection
* tenant selection
* notification state
* local preferences
* authentication session metadata
* unsaved form state

---

# Client-State Ownership

Client state SHALL have one clear owner.

Global client state SHOULD be used only when multiple unrelated parts of the
application require the same state.

Local component state SHOULD remain local where possible.

Client stores SHALL NOT become alternative caches for backend resources.

Incorrect:

```text
TanStack Query Sales Data

↓

Copied into Zustand

↓

Modified Independently
```

Correct:

```text
TanStack Query

↓

Canonical Sales Server State
```

---

# State Duplication

Authoritative server state SHALL NOT be duplicated across multiple state
systems.

Duplicating server data introduces:

* stale state
* synchronization problems
* conflicting updates
* increased complexity
* difficult debugging

Where derived state is required, it SHOULD be computed from the canonical
source rather than persisted independently.

---

# Providers

React providers belong under:

```text
src/providers/
```

Providers expose cross-cutting application context.

Examples include:

* application provider
* authentication provider
* authorization provider
* query provider
* theme provider
* notification provider
* tenant provider
* branch provider

---

# Provider Responsibilities

Providers SHALL:

* compose global context
* expose stable context hooks
* initialize client-side infrastructure
* coordinate global application lifecycle
* remain independent of feature presentation

Providers SHALL NOT:

* implement business workflows
* fetch unrelated domain data directly
* duplicate service behavior
* define feature-specific state
* import private feature internals

---

# Provider Public APIs

Providers SHALL expose stable public APIs through:

```text
src/providers/index.ts
```

A provider SHOULD export:

* the provider component
* its public context hook
* public value types where required

Example:

```typescript
export {
    ApplicationProvider,
    useApplicationContext,
} from "./ApplicationProvider";

export type {
    ApplicationContextValue,
} from "./ApplicationProvider";
```

---

# Provider Naming

The application SHALL use one canonical provider name for each responsibility.

Competing names SHALL not coexist unless one is a temporary compatibility
alias.

For example, the application SHALL standardize on either:

```typescript
AppProvider
```

or:

```typescript
ApplicationProvider
```

The same responsibility SHALL not be represented by both names indefinitely.

Compatibility aliases SHALL be documented and removed after migration.

---

# Provider Consumption

Hooks and components SHALL consume providers through their public hooks.

Correct:

```typescript
const application =
    useApplicationContext();
```

Discouraged:

```typescript
const context =
    useContext(ApplicationContext);
```

when the context itself is private to the provider module.

Public hooks allow providers to validate usage and expose stable contracts.

---

# Provider Boundaries

Providers SHALL NOT import:

* feature-specific components
* feature-specific query hooks
* private service implementations
* feature route internals

Providers MAY import:

* shared stores
* shared hooks
* shared types
* shared constants
* infrastructure utilities

---

# Navigation

Navigation configuration belongs under:

```text
src/navigation/
```

Navigation represents the application's user-facing module hierarchy.

It MAY define:

* sections
* items
* labels
* icons
* paths
* permission requirements
* feature metadata
* display order

---

# Navigation Responsibilities

Navigation SHALL:

* define menu structure
* reference route constants
* reference permission requirements
* expose typed navigation configuration
* support centralized filtering
* remain declarative

Navigation SHALL NOT:

* call services
* call APIs
* fetch business data directly
* implement business workflows
* mutate feature state
* duplicate authorization logic

---

# Navigation Authorization

Navigation visibility SHALL rely on centralized authorization helpers.

Correct:

```typescript
filterNavigation(
    navigation,
    authorization,
);
```

Incorrect:

```typescript
navigation.filter(
    (item) =>
        user.role === "Administrator",
);
```

Role names SHALL NOT be hardcoded throughout navigation.

Permission requirements SHALL remain explicit and declarative.

---

# Navigation Identifiers

Navigation identifiers SHALL be represented by runtime-safe values.

Where both runtime values and static typing are required, constant-backed unions
SHALL be used.

Example:

```typescript
export const NAVIGATION_SECTION_ID = {
    DASHBOARD: "dashboard",
    SALES: "sales",
    INVENTORY: "inventory",
    FINANCE: "finance",
} as const;

export type NavigationSectionId =
    (typeof NAVIGATION_SECTION_ID)[
        keyof typeof NAVIGATION_SECTION_ID
    ];
```

Type-only identifiers SHALL not be used as runtime values.

---

# Navigation Public API

Navigation SHALL expose a controlled public API through:

```text
src/navigation/index.ts
```

The public barrel may expose:

* navigation configuration
* navigation filtering helpers
* navigation lookup helpers
* navigation types
* navigation constants

It SHALL not export nonexistent utilities or duplicate declarations.

---

# Routes

Routes belong under:

```text
src/routes/
```

Routes define how application URLs map to feature pages.

Routes MAY declare:

* path
* page component
* layout
* authentication requirement
* permission requirement
* tenant requirement
* branch requirement
* loading boundary
* error boundary

---

# Route Responsibilities

Routes SHALL:

* connect paths to feature pages
* compose route guards
* apply layouts
* declare access requirements
* support lazy loading
* remain declarative

Routes SHALL NOT:

* implement business workflows
* call services directly
* duplicate authorization logic
* define reusable entities
* manage cache invalidation

---

# Protected Routes

Protected routes SHALL use centralized authentication and authorization
infrastructure.

Example:

```typescript
<ProtectedRoute
    permission="sales.view"
>
    <SalesPage />
</ProtectedRoute>
```

The route guard SHALL determine whether access is allowed.

Feature pages SHALL not duplicate the same route-level authorization decision.

The backend remains the final security authority.

---

# Route Constants

Route paths SHALL originate from centralized route constants.

Correct:

```typescript
APP_ROUTES.sales.root
```

Incorrect:

```typescript
"/sales"
```

repeated throughout multiple modules.

Centralized route constants reduce duplication and make navigation changes safer.

---

# Feature Route Imports

Routes SHOULD import feature pages through their public feature API.

Correct:

```typescript
import {
    SalesPage,
} from "@/features/sales";
```

Discouraged:

```typescript
import {
    SalesPage,
} from "@/features/sales/pages/internal/SalesPage";
```

Route configuration SHALL not depend unnecessarily on private feature
implementation details.

---

# Query Keys

Canonical query keys belong under:

```text
src/lib/queryKeys.ts
```

All TanStack Query keys SHALL originate from this registry.

Hardcoded query arrays are prohibited.

---

# Query-Key Hierarchy

Each domain SHALL own one root namespace.

Example:

```typescript
QUERY_KEYS.sales.root

QUERY_KEYS.inventory.root

QUERY_KEYS.customers.root
```

Nested query keys SHALL derive from the root.

Example:

```typescript
QUERY_KEYS.sales.list(params)

QUERY_KEYS.sales.detail(id)

QUERY_KEYS.sales.dashboard()
```

---

# Query Parameters

Parameters that affect a query result SHALL be represented in the query key.

For example, when pagination, filtering, sorting or search criteria change the
result:

```typescript
QUERY_KEYS.sales.list(params)
```

SHALL include those parameters.

Using the same query key for different result sets is prohibited.

---

# Query-Key Stability

Query keys SHALL remain:

* deterministic
* serializable
* hierarchical
* domain-owned
* predictable

Query keys SHALL not contain:

* functions
* mutable class instances
* DOM nodes
* non-serializable state

---

# Cache Invalidation

Canonical invalidation policies belong under:

```text
src/lib/queryInvalidation.ts
```

Cache invalidation SHALL be expressed in business terms.

Examples include:

```typescript
invalidateSalesOperations()

invalidateInventoryOperations()

invalidateProcurementOperations()

invalidateFinanceOperations()
```

---

# Invalidation Responsibilities

Centralized invalidation helpers SHALL define:

* affected domains
* affected root namespaces
* affected dashboards
* affected reports
* affected dependent read models

Mutation hooks SHALL invoke these policies.

Mutation hooks SHALL not independently duplicate the same invalidation targets.

---

# Direct Invalidation

Direct use of:

```typescript
queryClient.invalidateQueries(...)
```

outside the centralized invalidation framework is prohibited unless an explicit
architectural exception exists.

Exceptions SHALL be:

* narrow
* documented
* local to a specific cache concern
* reviewed for consistency

---

# Cross-Domain Invalidation

Business workflows may affect multiple domains.

For example:

```text
Complete Sale

↓

Sales

Inventory

Customers

Finance

Reports

Dashboard
```

The Sales invalidation policy SHALL centralize that dependency.

The mutation hook SHALL not manually invalidate each namespace.

---

# Cache Isolation

Tenant-scoped and branch-scoped data SHALL not be reused across context changes.

Changing tenant or branch SHALL invalidate or clear affected cache entries.

Cross-tenant cache reuse is prohibited.

Query-key design SHALL support tenant and branch isolation where required by the
application's request and cache strategy.

---

# Cross-Domain Communication

Business domains SHALL communicate through stable contracts.

Approved mechanisms include:

* backend workflows
* public domain services
* shared type contracts
* centralized invalidation policies
* explicit application orchestration
* approved domain events in future architecture

---

# Backend Workflow Coordination

The backend SHALL remain responsible for transactional cross-domain behavior.

Example:

```text
Complete Sale

↓

Backend Sales Transaction

↓

Inventory Reduced

↓

Finance Entry Created

↓

Customer Ledger Updated

↓

Frontend Cache Refreshed
```

The frontend SHALL not recreate this transaction by calling several unrelated
services sequentially unless the backend contract explicitly requires such
orchestration.

---

# Direct Cross-Domain Mutation

A feature SHALL not mutate another feature's private state.

Incorrect:

```text
Sales Component

↓

Inventory Zustand Store

↓

Manual Stock Reduction
```

Correct:

```text
Sales Component

↓

Complete Sale Mutation Hook

↓

Sales Service

↓

Backend Transaction

↓

Inventory Query Invalidated
```

---

# Cross-Domain Imports

A feature MAY consume:

* another domain's stable public type contract
* another domain's public page where required by composition
* shared infrastructure
* explicitly approved public services

A feature SHALL NOT consume:

* another feature's private utility
* another feature's private component
* another feature's internal store
* another feature's private hook implementation
* another feature's internal service file

---

# Application Orchestration

Cross-domain orchestration in the frontend SHALL be exceptional.

Where necessary, it SHALL live in an explicit application-level orchestration
module rather than inside an arbitrary feature component.

The orchestration SHALL:

* use stable public contracts
* preserve domain ownership
* avoid duplicating backend business rules
* remain testable
* document failure and rollback behavior

---

# Consequences

Applying these boundaries to state management, providers, navigation, routes,
query keys, cache invalidation and cross-domain communication provides:

* one authoritative owner for server state
* predictable provider contracts
* centralized navigation authorization
* declarative route protection
* stable query identities
* consistent cache refresh
* stronger tenant isolation
* reduced cross-domain coupling
* safer business workflows
* clearer frontend responsibilities

The final section of this ADR defines Dependency Rules, Circular Dependency
Prevention, Barrel Rules, Migration Policy, Testing, Enforcement, Consequences,
Alternatives, Compliance and Approval.
# Dependency Rules

All frontend dependencies SHALL follow explicit architectural direction.

Permitted dependencies include:

```text
Application Composition

↓

Routes

↓

Feature Pages

↓

Feature Components

↓

Hooks

↓

Domain Services

↓

BaseService

↓

API Client
```

Supporting modules may be consumed where their responsibilities permit.

Examples include:

```text
Feature → Shared Components

Feature → Shared Types

Hook → Query Keys

Hook → Cache Invalidation

Service → Endpoint Registry

Service → Shared Types

Provider → Shared Store

Navigation → Route Constants

Navigation → Permission Metadata
```

Dependencies SHALL remain intentional, minimal and acyclic.

---

# Permitted Dependency Directions

The following dependency directions are permitted:

```text
Application → Providers

Application → Routes

Routes → Layouts

Routes → Feature Pages

Feature Pages → Feature Components

Feature Components → Shared Components

Feature Components → Hooks

Hooks → Domain Services

Hooks → Query Keys

Hooks → Cache Invalidation

Domain Services → BaseService

Domain Services → API Endpoints

Domain Services → Shared Types

BaseService → API Client

Providers → Shared Stores

Providers → Shared Hooks

Navigation → Route Constants

Navigation → Permission Metadata

Types → Other Types
```

These dependencies preserve the canonical architectural hierarchy.

---

# Prohibited Dependency Directions

The following dependency directions are prohibited:

```text
API Client → Service

API Client → Hook

API Client → Component

BaseService → Feature

BaseService → Provider

BaseService → Navigation

Service → Hook

Service → Component

Service → Provider

Service → Route

Type → Service

Type → Hook

Type → Component

Shared Component → Domain Service

Navigation → API Client

Feature A → Feature B Private Implementation

Inventory Service → Sales Hook

Provider → Private Feature Component

Store → Feature Page
```

Lower-level infrastructure SHALL remain independent of higher-level
presentation and business composition layers.

---

# Dependency Minimality

A module SHALL import only what it requires.

Broad imports from large barrels SHOULD be avoided when they introduce:

* circular dependencies
* unnecessary coupling
* reduced tree shaking
* ambiguous ownership
* hidden runtime imports

Inside shared infrastructure, direct imports are preferred where they provide
clearer ownership and reduce circular dependency risk.

---

# Private Module Internals

Internal module files SHALL remain private unless explicitly exported through a
public API.

A consumer SHALL not rely on another module's:

* private helper
* internal store
* internal context
* internal component
* internal service implementation
* internal route fragment
* internal schema

A symbol becomes public only when intentionally exported through the owning
module's public entry point.

---

# Circular Dependencies

Circular dependencies are prohibited.

A circular dependency occurs when two or more modules depend upon each other
directly or indirectly.

Example:

```text
Sales Service

↓

Inventory Service

↓

Sales Service
```

This cycle is prohibited.

Another invalid example:

```text
Providers Barrel

↓

Application Hook

↓

Providers Barrel
```

Another invalid example:

```text
Types Barrel

↓

Service

↓

Types Barrel
```

Circular dependencies create:

* unpredictable initialization
* undefined runtime values
* fragile barrel exports
* difficult refactoring
* hidden architectural coupling
* bundling problems
* test instability

---

# Circular Dependency Prevention

To prevent cycles:

* lower layers SHALL not import higher layers
* shared types SHALL remain dependency-light
* broad wildcard barrels SHALL be used carefully
* internal code MAY import direct files
* domain services SHALL not call each other casually
* cross-domain workflows SHOULD remain backend-owned
* providers SHALL expose stable public hooks
* shared modules SHALL remain domain-neutral

Where a dependency cycle appears, ownership SHALL be reconsidered rather than
worked around with dynamic imports or duplicate types.

---

# Barrel Files

Barrel files provide controlled public module APIs.

Typical barrel files include:

```text
src/features/sales/index.ts

src/services/sales/index.ts

src/hooks/queries/sales/index.ts

src/types/entities/index.ts

src/providers/index.ts

src/navigation/index.ts
```

A barrel SHALL expose only stable, implemented and supported symbols.

---

# Barrel Export Rules

A barrel SHALL:

* export implemented symbols
* expose stable public contracts
* avoid duplicate declarations
* preserve type-only exports where appropriate
* remain free of circular dependencies
* reflect the actual module implementation

A barrel SHALL NOT:

* export nonexistent members
* export empty placeholder files
* duplicate locally declared symbols
* expose private implementation details
* preserve obsolete compatibility exports indefinitely
* re-export unrelated domains merely for convenience

---

# Type-Only Exports

Types SHOULD be exported explicitly where TypeScript module settings require
type-only semantics.

Example:

```typescript
export type {
    Sale,
    SaleItem,
    SalePayment,
} from "./entities";
```

Runtime values SHALL use normal exports.

This distinction prevents accidental runtime imports and supports strict
TypeScript compilation.

---

# Duplicate Exports

A symbol SHALL not be declared and exported more than once from the same
module.

Incorrect:

```typescript
export function useDeleteSupplier() {
    // ...
}

export {
    useDeleteSupplier,
};
```

when the second declaration causes an export conflict.

Correct:

```typescript
export {
    useDeleteSupplier,
} from "./useDeleteSupplier";
```

or:

```typescript
export function useDeleteSupplier() {
    // ...
}
```

but not both competing declarations.

---

# Placeholder Files

Empty placeholder files SHALL not be exported from production barrels.

Incorrect:

```typescript
export {
    salesQueryService,
} from "./salesQueryService";
```

when `salesQueryService.ts` exports nothing.

An unfinished module SHALL either:

1. remain unexported
2. expose a valid temporary implementation
3. be completed before the barrel is committed

Architecture scaffolding SHALL remain build-safe.

---

# Runtime and Type Export Alignment

A barrel SHALL distinguish between runtime symbols and type-only symbols.

A type alias SHALL not be exported and later used as though it were a runtime
object.

Example of an invalid pattern:

```typescript
export type ErrorCode =
    | "NETWORK"
    | "TIMEOUT";
```

followed by:

```typescript
ErrorCode.NETWORK
```

Where runtime access is required, the module SHALL export a runtime constant.

Example:

```typescript
export const ERROR_CODE = {
    NETWORK: "NETWORK",
    TIMEOUT: "TIMEOUT",
} as const;

export type ErrorCode =
    (typeof ERROR_CODE)[keyof typeof ERROR_CODE];
```

---

# Migration Policy

Architectural migrations SHALL be incremental, controlled and build-safe.

Large migrations SHALL not be performed through uncontrolled repository-wide
changes without an explicit migration sequence.

---

# Migration Sequence

A canonical migration SHALL follow this sequence:

1. Document the target architecture.
2. Identify existing consumers.
3. Create shared contracts.
4. Implement the new module beside the legacy module where required.
5. Preserve valid compatibility exports.
6. Migrate consumers in controlled groups.
7. Run TypeScript compilation after each group.
8. Remove obsolete exports.
9. Remove compatibility implementations.
10. Update documentation.

---

# Compatibility Layers

A temporary compatibility layer MAY be introduced when replacing a widely used
public contract.

Example:

```text
legacySalesService.ts
```

A compatibility layer SHALL:

* be clearly marked as temporary
* preserve existing behavior
* remain build-safe
* have a documented migration target
* avoid receiving new features
* be removed after consumer migration

Compatibility layers SHALL not become permanent architecture.

---

# Build-Safe Migration

Every committed migration stage SHOULD compile.

A migration SHALL NOT intentionally leave:

* unresolved exports
* empty exported files
* missing DTOs
* incompatible endpoint objects
* duplicate service methods
* invalid query-key calls
* broken provider names
* type-only symbols used at runtime

Where temporary compilation failures are unavoidable in a local worktree, they
SHALL be resolved before the migration is considered complete or merged.

---

# Migration Scope

Unrelated architectural migrations SHOULD not be combined unnecessarily.

For example, the following changes SHOULD be separated where practical:

* service decomposition
* type extraction
* provider renaming
* navigation normalization
* TypeScript compiler migration
* route restructuring
* query-key redesign

Separating migration concerns improves reviewability and reduces regression
risk.

---

# Legacy Removal

Legacy code SHALL be removed only after:

* all known consumers have migrated
* compatibility exports are unused
* tests pass
* TypeScript compilation succeeds
* documentation reflects the canonical implementation

Search tools SHOULD be used to verify that no imports remain.

Example:

```bash
grep -R "legacySalesService" src
```

A legacy file SHALL not be deleted solely because the replacement file exists.

---

# Testing Boundaries

Each module SHOULD own tests for its public behavior.

Canonical examples include:

```text
features/sales/__tests__/

services/sales/__tests__/

services/base/__tests__/

lib/__tests__/

providers/__tests__/
```

Tests SHOULD validate public contracts rather than private implementation
details.

---

# Feature Tests

Feature tests SHOULD verify:

* rendering behavior
* user interactions
* form validation
* permission-aware visibility
* loading states
* error states
* workflow initiation

Feature tests SHOULD mock public hooks or services rather than deep internal
implementations where practical.

---

# Service Tests

Service tests SHOULD verify:

* endpoint selection
* request payloads
* response extraction
* request configuration
* file transport behavior
* business-oriented public methods

Service tests SHALL not test React rendering.

---

# Hook Tests

Query-hook tests SHOULD verify:

* canonical query keys
* service invocation
* enabled conditions
* mutation behavior
* centralized invalidation
* error propagation

Hooks SHALL be tested independently from full page presentation where
practical.

---

# Architecture Tests

Architecture tests MAY verify:

* forbidden import directions
* circular dependencies
* invalid barrel exports
* endpoint misuse
* direct cache invalidation
* service imports from React
* type imports from services
* tenant boundary violations
* authorization boundary violations

---

# Enforcement

This ADR SHALL be enforced through engineering process and automated tooling.

Enforcement mechanisms include:

* TypeScript strict mode
* ESLint
* CI compilation
* pull request review
* architecture compliance audits
* unit tests
* integration tests
* dependency analysis
* explicit module barrels
* documentation review

---

# Recommended Tooling

Recommended tooling may include:

```text
eslint-plugin-import

eslint-plugin-boundaries

dependency-cruiser

madge

TypeScript project references

Vite build validation

CI architecture checks
```

Tooling adoption may occur incrementally.

The rules defined by this ADR apply regardless of whether every rule is already
automated.

---

# TypeScript Enforcement

The TypeScript build SHALL remain an architectural enforcement mechanism.

Compiler failures SHALL not be suppressed broadly merely to avoid completing a
migration.

Options such as:

```text
skipLibCheck

ignoreDeprecations

erasableSyntaxOnly
```

SHALL be used deliberately and SHALL not replace correction of application
architecture errors.

---

# Lint Enforcement

Lint rules SHOULD identify:

* unused imports
* duplicate exports
* forbidden dependency paths
* direct Axios usage outside the API layer
* direct invalidation outside the invalidation framework
* unsafe type imports
* circular dependencies
* deep feature imports

Lint exceptions SHALL be narrow and documented.

---

# Pull Request Review

Every pull request affecting frontend architecture SHOULD confirm:

* the changed code has one clear owner
* dependency direction remains valid
* module boundaries remain intact
* shared types are reused
* services remain React-independent
* hooks contain no transport implementation
* endpoint constants are consumed correctly
* query keys are canonical
* cache invalidation is centralized
* authorization remains centralized
* tenant isolation is preserved
* public barrels remain valid
* no circular dependency was introduced
* migration compatibility is documented
* TypeScript compilation passes

---

# Architecture Compliance Reviews

Periodic architecture reviews SHOULD inspect:

* service boundaries
* type ownership
* feature imports
* query-key consistency
* cache invalidation
* provider exports
* navigation contracts
* route protection
* endpoint usage
* circular dependencies
* compatibility layers

Architectural drift SHALL be recorded and corrected deliberately.

---

# Documentation Responsibilities

Architectural changes SHALL update:

* the relevant ADR
* architecture standards
* diagrams where applicable
* migration plans
* architecture roadmap
* public module documentation

Implementation and documentation SHALL not drift silently.

---

# Consequences

## Positive Consequences

This decision provides:

* clear architectural ownership
* predictable dependency direction
* reduced circular dependencies
* stable public module APIs
* safer migrations
* improved build reliability
* stronger type ownership
* clearer service boundaries
* consistent query behavior
* centralized authorization
* stronger tenant isolation
* easier testing
* improved developer onboarding
* future modularization readiness

---

## Trade-Offs

This decision introduces:

* additional architectural discipline
* more explicit module entry points
* more review requirements
* temporary compatibility layers during migration
* additional type and service files
* stricter dependency constraints
* migration work for existing violations

These trade-offs are accepted.

Hela360 is an enterprise platform, and long-term maintainability is more
important than minimizing the number of files or allowing unrestricted imports.

---

# Alternatives Considered

## Fully Feature-Colocated Architecture

Every feature could own its components, hooks, services, API definitions and
types within one feature directory.

This approach provides strong feature locality.

It was not selected as the canonical model because Hela360 already uses shared
service, API, query and type infrastructure across multiple domains.

Feature colocation remains appropriate for private presentation concerns.

---

## Flat Global Architecture

All components, hooks, services and types could remain in flat global
directories without domain grouping.

This approach is simple at small scale.

It was rejected because ownership and discoverability deteriorate as the
platform grows.

---

## Unrestricted Cross-Feature Imports

Features could directly consume any internal file from another feature.

This approach reduces the need for public barrels.

It was rejected because it creates hidden coupling and makes internal
refactoring unsafe.

---

## Frontend-Orchestrated Cross-Domain Transactions

The frontend could coordinate Sales, Inventory, Finance and Customer services
directly for complex workflows.

This was rejected as the default because transactional integrity belongs to the
backend.

Frontend orchestration remains possible only where explicitly required by an
approved backend contract.

---

## Immediate Micro-Frontend Architecture

Each business domain could be independently built and deployed.

This was deferred because the current platform does not require independent
frontend deployments.

The boundaries defined in this ADR preserve future extraction into packages or
micro-frontends.

---

# Current Migration Areas

The current Hela360 frontend may not yet fully comply with this ADR.

Known migration areas include:

* BaseService contract normalization
* duplicate BaseService method removal
* API endpoint registry alignment
* response type barrel normalization
* request DTO completion
* entity extraction from services
* sales service decomposition
* supplier type migration
* provider naming consistency
* query-key signature alignment
* navigation identifier normalization
* runtime constant-backed union adoption
* direct cache invalidation removal
* invalid barrel export removal
* empty service placeholder removal
* route constant normalization
* strict TypeScript compatibility

These areas represent implementation work.

They do not weaken or alter the canonical boundaries established by this ADR.

---

# Compliance Statement

From the acceptance date of this ADR:

* new modules SHALL comply immediately
* modified modules SHALL move toward compliance
* existing violations SHALL be migrated deliberately
* new circular dependencies are prohibited
* new undocumented cross-domain coupling is prohibited
* new service-owned reusable types are prohibited
* new direct Axios usage outside the API layer is prohibited
* new direct cache invalidation outside the centralized framework is prohibited
* public barrels SHALL remain explicit and build-safe
* architectural scaffolding SHALL not knowingly break compilation
* tenant and authorization boundaries SHALL remain intact

---

# Future Evolution

The architecture defined in this ADR supports future adoption of:

* workspace packages
* independently versioned domains
* plugin modules
* licensed feature modules
* generated API clients
* lazy-loaded business capabilities
* domain-specific TypeScript projects
* independent frontend teams
* extension marketplaces
* micro-frontends
* event-driven UI synchronization

Future architecture SHALL preserve stable public contracts and explicit
dependency direction.

---

# Approval

Approved.

Chief Architect

Hela360 Enterprise Platform
