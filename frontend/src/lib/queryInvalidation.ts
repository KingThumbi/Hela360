/**
 * ============================================================================
 * Hela360 Enterprise Query Invalidation Framework
 * ============================================================================
 *
 * Centralized TanStack Query cache invalidation.
 *
 * Responsibilities
 * ----------------
 * • Eliminate duplicated invalidateQueries() calls
 * • Standardize cache refresh behaviour
 * • Centralize cache invalidation policies
 * • Simplify mutation hooks
 * • Improve maintainability
 * • Support domain-driven cache management
 *
 * Every mutation hook should invalidate caches through this module rather than
 * interacting with QueryClient directly.
 *
 * ============================================================================
 */

import type { QueryClient } from "@tanstack/react-query";

import { QUERY_KEYS } from "./queryKeys";
import type {
  BranchQueryScope,
  TenantQueryScope,
} from "@/types/domains/query-scope";

/* ============================================================================
 * Internal Helpers
 * ============================================================================
 */

/**
 * Invalidates one or more query namespaces.
 *
 * This is the only helper that directly interacts with TanStack Query.
 * All exported invalidation functions should delegate here.
 */
async function invalidateMany(
  client: QueryClient,
  queryKeys: readonly (readonly unknown[])[],
): Promise<void> {
  await Promise.all(
    queryKeys.map((queryKey) =>
      client.invalidateQueries({
        queryKey,
      }),
    ),
  );
}

/* ============================================================================
 * Authentication
 * ============================================================================
 */

/**
 * Refreshes authentication state.
 *
 * Use after:
 *
 * • Login
 * • Logout
 * • Token Refresh
 * • Profile Update
 * • Password Change
 * • Permission Changes
 */
export async function invalidateAuthentication(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.auth.root,
    QUERY_KEYS.auth.currentUser(),
    QUERY_KEYS.auth.profile(),
    QUERY_KEYS.auth.permissions(),
  ]);
}

/* ============================================================================
 * Dashboard
 * ============================================================================
 */

/**
 * Refreshes dashboard widgets and metrics.
 */
export async function invalidateDashboard(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.dashboard.root,
  ]);
}

/* ============================================================================
 * Master Data
 * ============================================================================
 */

/**
 * Refreshes product caches.
 */
export async function invalidateProducts(
  client: QueryClient,
  scope: TenantQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.products.root(scope),
  ]);
}

/**
 * Refreshes customer caches.
 */
export async function invalidateCustomers(
  client: QueryClient,
  scope: TenantQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.customers.root(scope),
  ]);
}

/**
 * Refreshes supplier caches.
 */
export async function invalidateSuppliers(
  client: QueryClient,
  scope: TenantQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.suppliers.root(scope),
  ]);
}

/**
 * Refreshes current TillShift lifecycle state for one branch.
 */
export async function invalidateTillShifts(
  client: QueryClient,
  scope: BranchQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.tillShifts.root(scope),
  ]);
}

/* ============================================================================
 * Inventory
 * ============================================================================
 */

/**
 * Refreshes inventory caches.
 *
 * Use after:
 *
 * • Stock updates
 * • Inventory synchronization
 * • Inventory imports
 */
export async function invalidateInventory(
  client: QueryClient,
  scope?: BranchQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.inventory.root,
    ...(scope
      ? [QUERY_KEYS.inventory.branchRoot(scope)]
      : []),
  ]);
}

/**
 * Refreshes all caches affected by inventory business operations.
 *
 * Use after:
 *
 * • Goods Receipt
 * • Stock Adjustment
 * • Stock Transfer
 * • Stock Count
 * • Inventory Reconciliation
 */
export async function invalidateInventoryOperations(
  client: QueryClient,
  scope?: BranchQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.inventory.root,
    ...(scope
      ? [QUERY_KEYS.inventory.branchRoot(scope)]
      : []),
    ...(scope
      ? [QUERY_KEYS.sales.branchRoot(scope)]
      : []),
    QUERY_KEYS.dashboard.root,
  ]);
}

/**
 * Refreshes Stock Count document caches only.
 *
 * Stock Count observation/completion does not mutate StockBalance,
 * InventoryBatch, or InventoryMovement.
 */
export async function invalidateStockCounts(
  client: QueryClient,
  scope?: BranchQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    ...(scope
      ? [
          QUERY_KEYS.inventory.stockCountLists(scope),
          QUERY_KEYS.inventory.stockCountDetails(scope),
        ]
      : []),
  ]);
}

/**
 * Refreshes caches affected by posted Stock Adjustments.
 *
 * Stock Adjustment posting mutates StockBalance, InventoryBatch and
 * InventoryMovement, and may be sourced from a completed Stock Count.
 */
export async function invalidateStockAdjustments(
  client: QueryClient,
  scope?: BranchQueryScope,
  options?: {
    includeStockCounts?: boolean;
  },
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.inventory.root,
    ...(scope
      ? [
          QUERY_KEYS.inventory.branchRoot(scope),
          QUERY_KEYS.sales.branchRoot(scope),
          QUERY_KEYS.inventory.stockAdjustmentLists(scope),
          QUERY_KEYS.inventory.stockAdjustmentDetails(scope),
          ...(options?.includeStockCounts
            ? [
                QUERY_KEYS.inventory.stockCountLists(scope),
                QUERY_KEYS.inventory.stockCountDetails(scope),
              ]
            : []),
        ]
      : []),
  ]);
}

/* ============================================================================
 * Procurement
 * ============================================================================
 */

/**
 * Refreshes procurement caches.
 *
 * Use after:
 *
 * • Purchase Order updates
 * • Goods Receipt updates
 * • Procurement synchronization
 */
export async function invalidateProcurement(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.procurement.root,
  ]);
}

/**
 * Refreshes all caches affected by procurement operations.
 *
 * Procurement impacts:
 *
 * • Procurement
 * • Inventory
 * • Suppliers
 * • Finance
 * • Dashboard
 *
 * Use after:
 *
 * • Purchase Order Approval
 * • Goods Receipt
 * • Purchase Order Cancellation
 * • Supplier Delivery
 */
export async function invalidateProcurementOperations(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.procurement.root,
    QUERY_KEYS.inventory.root,
    QUERY_KEYS.finance.root,
    QUERY_KEYS.dashboard.root,
  ]);
}

/* ============================================================================
 * Sales
 * ============================================================================
 */

/**
 * Refreshes sales caches.
 *
 * Use after:
 *
 * • Sale updates
 * • Sale synchronization
 */
export async function invalidateSales(
  client: QueryClient,
  scope?: BranchQueryScope,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.sales.root,
    ...(scope
      ? [QUERY_KEYS.sales.branchRoot(scope)]
      : []),
  ]);
}

/**
 * Refreshes all caches affected by sales operations.
 *
 * Sales impacts:
 *
 * • Sales
 * • Inventory
 * • Customers
 * • Finance
 * • Reports
 * • Dashboard
 *
 * Use after:
 *
 * • Sale Creation
 * • Sale Completion
 * • Sale Suspension
 * • Sale Resume
 * • Sale Void
 * • Sale Refund
 */
export async function invalidateSalesOperations(
  client: QueryClient,
  scope?: BranchQueryScope,
  saleId?: string,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.sales.root,
    ...(scope
      ? [
          QUERY_KEYS.sales.branchRoot(scope),
          ...(saleId
            ? [
                QUERY_KEYS.sales.receipt(scope, saleId),
                QUERY_KEYS.sales.refundLookup(scope, saleId),
              ]
            : []),
        ]
      : []),
    QUERY_KEYS.inventory.root,
    ...(scope
      ? [QUERY_KEYS.inventory.branchRoot(scope)]
      : []),
    QUERY_KEYS.finance.root,
    QUERY_KEYS.reports.root,
    QUERY_KEYS.dashboard.root,
  ]);
}

/* ============================================================================
 * Finance
 * ============================================================================
 */

/**
 * Refreshes finance caches.
 *
 * Use after:
 *
 * • Financial updates
 * • Accounting synchronization
 */
export async function invalidateFinance(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.finance.root,
  ]);
}

/**
 * Refreshes all caches affected by finance operations.
 *
 * Finance impacts:
 *
 * • Finance
 * • Reports
 * • Dashboard
 *
 * Use after:
 *
 * • Journal Posting
 * • Payment Posting
 * • Invoice Posting
 * • Ledger Updates
 */
export async function invalidateFinanceOperations(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.finance.root,
    QUERY_KEYS.reports.root,
    QUERY_KEYS.dashboard.root,
  ]);
}

/* ============================================================================
 * Reports
 * ============================================================================
 */

/**
 * Refreshes reporting caches.
 */
export async function invalidateReports(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.reports.root,
  ]);
}

/* ============================================================================
 * Administration
 * ============================================================================
 */

/**
 * Refreshes administration caches.
 */
export async function invalidateAdministration(
  client: QueryClient,
): Promise<void> {
  await invalidateMany(client, [
    QUERY_KEYS.administration.root,
  ]);
}

/* ============================================================================
 * Global
 * ============================================================================
 */

/**
 * Invalidates the entire application cache.
 *
 * This should be used sparingly, for example:
 *
 * • Tenant switch
 * • User logout
 * • Full application reset
 */
export async function invalidateAll(
  client: QueryClient,
): Promise<void> {
  await client.invalidateQueries();
}
