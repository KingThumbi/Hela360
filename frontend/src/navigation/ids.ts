/**
 * ============================================================================
 * Hela360 Navigation Identifiers
 * ============================================================================
 *
 * Runtime constants and derived types for navigation identity.
 *
 * ============================================================================
 */

export const NAVIGATION_SECTION_IDS = {
  DASHBOARD: "dashboard",
  SALES: "sales",
  INVENTORY: "inventory",
  CUSTOMERS: "customers",
  PROCUREMENT: "procurement",
  FINANCE: "finance",
  REPORTS: "reports",
  ADMINISTRATION: "administration",
  SETTINGS: "settings",
} as const;

export type NavigationSectionId =
  (typeof NAVIGATION_SECTION_IDS)[keyof typeof NAVIGATION_SECTION_IDS];

export const NAVIGATION_ITEM_IDS = {
  DASHBOARD: "dashboard",
  POS: "pos",
  SALES_HISTORY: "sales-history",
  REFUNDS: "refunds",
  PRODUCTS: "products",
  PRODUCT_CATALOGUE: "product-catalogue",
  INVENTORY: "inventory",
  INVENTORY_WAREHOUSES: "inventory-warehouses",
  STOCK_ADJUSTMENTS: "stock-adjustments",
  CUSTOMERS: "customers",
  PURCHASE_ORDERS: "purchase-orders",
  SUPPLIERS: "suppliers",
  EXPENSES: "expenses",
  PAYMENTS: "payments",
  CASHBOOK: "cashbook",
  REPORTS: "reports",
  ANALYTICS: "analytics",
  USERS: "users",
  ROLES: "roles",
  PERMISSIONS: "permissions",
  BRANCHES: "branches",
  ADMINISTRATION_WAREHOUSES: "administration-warehouses",
  PAYMENT_METHODS: "payment-methods",
  SETTINGS: "settings",
  TENANT: "tenant",
} as const;

export type NavigationItemId =
  (typeof NAVIGATION_ITEM_IDS)[keyof typeof NAVIGATION_ITEM_IDS];
