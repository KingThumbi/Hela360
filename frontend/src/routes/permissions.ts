import { PATHS } from "@/routes/routes";

import type { PermissionCode } from "@/types/auth";

/**
 * ============================================================================
 * Hela360 Route Authorization Registry
 * ============================================================================
 *
 * Canonical frontend representation of backend route-access requirements.
 *
 * The backend remains the security boundary.
 *
 * This registry exists so routing, navigation and presentation use the same
 * permission vocabulary as the authenticated backend identity.
 *
 * Supported requirements
 * ----------------------
 * permission
 *   One specific permission is required.
 *
 * anyOf
 *   At least one of the listed permissions is required.
 *
 * Routes absent from this registry are not automatically public. They may be
 * authenticated-only, unfinished, or governed by page-level authorization.
 * ============================================================================
 */

export interface SingleRoutePermissionRequirement {
  permission: PermissionCode;
  anyOf?: never;
}

export interface AnyRoutePermissionRequirement {
  permission?: never;
  anyOf: readonly PermissionCode[];
}

export type RoutePermissionRequirement =
  | SingleRoutePermissionRequirement
  | AnyRoutePermissionRequirement;

export const ROUTE_PERMISSION_REQUIREMENTS = {
  [PATHS.PRODUCTS.ROOT]: {
    permission: "products.view",
  },

  [PATHS.PRODUCTS.CATALOGUE]: {
    permission: "products.view",
  },

  [PATHS.CUSTOMERS.ROOT]: {
    permission: "customers.view",
  },

  [PATHS.INVENTORY.ROOT]: {
    permission: "inventory.read",
  },

  [PATHS.INVENTORY.RECEIVE]: {
    permission: "inventory.receive",
  },

  [PATHS.INVENTORY.RECEIPTS]: {
    permission: "inventory.receive",
  },

  [PATHS.INVENTORY.RECEIPT]: {
    permission: "inventory.receive",
  },

  [PATHS.INVENTORY.STOCK_COUNTS]: {
    permission: "inventory.count",
  },

  [PATHS.INVENTORY.STOCK_COUNT_NEW]: {
    permission: "inventory.count",
  },

  [PATHS.INVENTORY.STOCK_COUNT]: {
    permission: "inventory.count",
  },

  [PATHS.INVENTORY.STOCK_ADJUSTMENTS]: {
    permission: "inventory.adjust",
  },

  [PATHS.INVENTORY.STOCK_ADJUSTMENT_NEW]: {
    permission: "inventory.adjust",
  },

  [PATHS.INVENTORY.STOCK_ADJUSTMENT]: {
    permission: "inventory.adjust",
  },

  [PATHS.WAREHOUSES.ROOT]: {
    anyOf: [
      "inventory.read",
      "inventory.count",
      "inventory.adjust",
    ],
  },

  [PATHS.PROCUREMENT.SUPPLIERS]: {
    permission: "suppliers.view",
  },

  [PATHS.SALES.POS]: {
    permission: "sales.create",
  },

  [PATHS.SALES.HISTORY]: {
    permission: "sales.read",
  },

  [PATHS.SALES.RECEIPT]: {
    permission: "sales.read",
  },

  [PATHS.SALES.RETURNS]: {
    permission: "sales.refund",
  },

  [PATHS.ADMINISTRATION.USERS]: {
    permission: "users.read",
  },

  [PATHS.ADMINISTRATION.ROLES]: {
    permission: "roles.read",
  },

  [PATHS.ADMINISTRATION.BRANCHES]: {
    permission: "branches.read",
  },

  [PATHS.SETTINGS.ROOT]: {
    permission: "settings.manage",
  },

  [PATHS.SETTINGS.TENANT]: {
    permission: "tenant.manage",
  },
} as const satisfies Record<
  string,
  RoutePermissionRequirement
>;

export type RoutePermissionPath =
  keyof typeof ROUTE_PERMISSION_REQUIREMENTS;

export function getRoutePermissionRequirement(
  path: string,
): RoutePermissionRequirement | undefined {
  return ROUTE_PERMISSION_REQUIREMENTS[
    path as RoutePermissionPath
  ];
}
