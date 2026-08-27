/**
 * ============================================================================
 * Hela360 Tenant Permission Registry
 * ============================================================================
 *
 * Frontend representation of Hela360's canonical tenant-scoped permissions.
 *
 * IMPORTANT
 * ---------
 * The backend is the authorization authority.
 *
 * Permission codes defined here MUST correspond to canonical permission codes
 * in:
 *
 *     app/auth/permissions.py
 *
 * The frontend MUST NOT invent permissions merely for navigation, routes,
 * pages, widgets or presentation concerns.
 *
 * Frontend permission checks improve usability by hiding unavailable
 * functionality. They are not a security boundary.
 * ============================================================================
 */

export const PERMISSIONS = {
  /* ------------------------------------------------------------------
   * Products
   * ------------------------------------------------------------------ */

  PRODUCTS_VIEW: "products.view",
  PRODUCTS_CREATE: "products.create",
  PRODUCTS_EDIT: "products.edit",
  PRODUCTS_DELETE: "products.delete",

  /* ------------------------------------------------------------------
   * Inventory
   * ------------------------------------------------------------------ */

  INVENTORY_READ: "inventory.read",
  INVENTORY_RECEIVE: "inventory.receive",
  INVENTORY_COUNT: "inventory.count",
  INVENTORY_ADJUST: "inventory.adjust",
  INVENTORY_TRANSFER: "inventory.transfer",

  /* ------------------------------------------------------------------
   * Sales / POS
   * ------------------------------------------------------------------ */

  SALES_READ: "sales.read",
  SALES_CREATE: "sales.create",
  SALES_REFUND: "sales.refund",
  SALES_CANCEL: "sales.cancel",

  /**
   * POS access currently corresponds to the ability to create sales.
   */
  POS_ACCESS: "sales.create",

  /* ------------------------------------------------------------------
   * Customers
   * ------------------------------------------------------------------ */

  CUSTOMERS_VIEW: "customers.view",
  CUSTOMERS_CREATE: "customers.create",
  CUSTOMERS_EDIT: "customers.edit",

  /* ------------------------------------------------------------------
   * Suppliers / Procurement
   * ------------------------------------------------------------------ */

  SUPPLIERS_VIEW: "suppliers.view",
  SUPPLIERS_CREATE: "suppliers.create",
  SUPPLIERS_UPDATE: "suppliers.update",
  SUPPLIERS_DEACTIVATE: "suppliers.deactivate",

  /* ------------------------------------------------------------------
   * Reports
   * ------------------------------------------------------------------ */

  REPORTS_VIEW: "reports.view",
  REPORTS_EXPORT: "reports.export",

  /* ------------------------------------------------------------------
   * User & Role Administration
   * ------------------------------------------------------------------ */

  USERS_READ: "users.read",
  USERS_MANAGE: "users.manage",

  ROLES_READ: "roles.read",
  ROLES_MANAGE: "roles.manage",

  /* ------------------------------------------------------------------
   * Tenant Settings
   * ------------------------------------------------------------------ */

  SETTINGS_MANAGE: "settings.manage",

  /* ------------------------------------------------------------------
   * Branches
   * ------------------------------------------------------------------ */

  BRANCHES_READ: "branches.read",
  BRANCHES_MANAGE: "branches.manage",

  /* ------------------------------------------------------------------
   * Audit
   * ------------------------------------------------------------------ */

  AUDIT_VIEW: "audit.view",

  /* ------------------------------------------------------------------
   * Tenant Administration
   * ------------------------------------------------------------------ */

  TENANT_MANAGE: "tenant.manage",
} as const;

/**
 * Canonical tenant permission value.
 */
export type Permission =
  (typeof PERMISSIONS)[keyof typeof PERMISSIONS];

/**
 * Compatibility name used by the authentication and authorization layers.
 */
export type PermissionCode = Permission;
