/**
 * ============================================================================
 * Hela360 Enterprise API Endpoints
 * ============================================================================
 *
 * Canonical API endpoint registry.
 *
 * Responsibilities
 * ----------------
 * • Eliminate hardcoded URLs
 * • Centralize endpoint definitions
 * • Support API versioning
 * • Provide discoverable resource endpoints
 * • Provide strongly-typed parameterized routes
 *
 * Feature modules should always consume endpoints from this registry instead
 * of constructing URL strings manually.
 *
 * Every resource owns its own endpoint namespace, making the registry
 * scalable as Hela360 grows.
 *
 * ============================================================================
 */

/**
 * Convenience helper for parameterized resource URLs.
 */
const byId = (
  resource: string,
  id: string,
) => `${resource}/${id}`;

export const API_ENDPOINTS = {
  /**
   * --------------------------------------------------------------------------
   * Health
   * --------------------------------------------------------------------------
   */

  HEALTH: "/health",

  /**
   * --------------------------------------------------------------------------
   * Authentication
   * --------------------------------------------------------------------------
   */

  AUTH: {
    LOGIN: "/auth/login",

    SESSION: "/auth/session",

    LOGOUT: "/auth/logout",

    REFRESH: "/auth/refresh",

    ME: "/auth/me",

    CHANGE_PASSWORD: "/auth/change-password",

    FORGOT_PASSWORD: "/auth/forgot-password",

    RESET_PASSWORD: "/auth/reset-password",
  },

  /**
   * --------------------------------------------------------------------------
   * Users
   * --------------------------------------------------------------------------
   */

  USERS: {
    ROOT: "/users",

    BY_ID: (id: string) => byId("/users", id),

    ACTIVATE: (id: string) =>
      `${byId("/users", id)}/activate`,

    DEACTIVATE: (id: string) =>
      `${byId("/users", id)}/deactivate`,

    RESET_PASSWORD: (id: string) =>
      `${byId("/users", id)}/reset-password`,

    UNLOCK: (id: string) =>
      `${byId("/users", id)}/unlock`,
  },

  /**
   * --------------------------------------------------------------------------
   * Roles
   * --------------------------------------------------------------------------
   */

  ROLES: {
    ROOT: "/roles",

    BY_ID: (id: string) => byId("/roles", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Permissions
   * --------------------------------------------------------------------------
   */

  PERMISSIONS: {
    ROOT: "/permissions",

    BY_ID: (id: string) =>
      byId("/permissions", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Tenants
   * --------------------------------------------------------------------------
   */

  TENANTS: {
    ROOT: "/tenants",

    BY_ID: (id: string) =>
      byId("/tenants", id),

    BRANCHES: (id: string) =>
      `${byId("/tenants", id)}/branches`,
  },

  /**
   * --------------------------------------------------------------------------
   * Branches
   * --------------------------------------------------------------------------
   */

  BRANCHES: {
    ROOT: "/branches",

    BY_ID: (id: string) =>
      byId("/branches", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Products
   * --------------------------------------------------------------------------
   */

  PRODUCTS: {
    ROOT: "/products",

    BY_ID: (id: string) =>
      byId("/products", id),

    STOCK: (id: string) =>
      `${byId("/products", id)}/stock`,

    PRICE: (id: string) =>
      `${byId("/products", id)}/price`,

    HISTORY: (id: string) =>
      `${byId("/products", id)}/history`,

    ARCHIVE: (id: string) =>
      `${byId("/products", id)}/archive`,

    RESTORE: (id: string) =>
      `${byId("/products", id)}/restore`,

    TAX_CODES: "/products/tax-codes",
  },

  /**
   * --------------------------------------------------------------------------
   * Master Catalogue
   * --------------------------------------------------------------------------
   */

  CATALOGUE: {
    ROOT: "/catalogue/items",

    BY_ID: (id: string) =>
      byId("/catalogue/items", id),

    ADOPT: (id: string) =>
      `${byId("/catalogue/items", id)}/adopt`,
  },

  /**
   * --------------------------------------------------------------------------
   * Categories
   * --------------------------------------------------------------------------
   */

  CATEGORIES: {
    ROOT: "/categories",

    BY_ID: (id: string) =>
      byId("/categories", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Inventory
   * --------------------------------------------------------------------------
   */

  INVENTORY: {
    ROOT: "/inventory",

    BY_ID: (id: string) =>
      byId("/inventory", id),

    STOCK_BATCHES: (id: string) =>
      `${byId("/inventory/stock", id)}/batches`,

    MOVEMENTS: "/inventory/movements",

    GOODS_RECEIPTS: "/inventory/goods-receipts",

    GOODS_RECEIPT: (id: string) =>
      byId("/inventory/goods-receipts", id),

    STOCK_COUNTS: "/inventory/stock-counts",

    STOCK_COUNT: (id: string) =>
      byId("/inventory/stock-counts", id),

    STOCK_COUNT_ITEM: (
      countId: string,
      itemId: string,
    ) => `${byId("/inventory/stock-counts", countId)}/items/${itemId}`,

    DISCOVERED_STOCK_COUNT_ITEM: (
      countId: string,
    ) =>
      `${byId("/inventory/stock-counts", countId)}/items/discovered`,

    CONFIRM_STOCK_COUNT_NO_STOCK: (
      countId: string,
      productId: string,
    ) =>
      `${byId("/inventory/stock-counts", countId)}/scope-products/${productId}/confirm-no-stock`,

    COMPLETE_STOCK_COUNT: (id: string) =>
      `${byId("/inventory/stock-counts", id)}/complete`,

    CANCEL_STOCK_COUNT: (id: string) =>
      `${byId("/inventory/stock-counts", id)}/cancel`,

    STOCK_ADJUSTMENTS: "/inventory/stock-adjustments",

    STOCK_ADJUSTMENT: (id: string) =>
      byId("/inventory/stock-adjustments", id),

    STOCK_ADJUSTMENT_FROM_COUNT: (id: string) =>
      `${byId("/inventory/stock-counts", id)}/adjust`,

    STOCKTAKE: "/inventory/stocktake",
  },

  /**
   * --------------------------------------------------------------------------
   * Suppliers
   * --------------------------------------------------------------------------
   */

  SUPPLIERS: {
    ROOT: "/suppliers",

    BY_ID: (id: string) =>
      byId("/suppliers", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Customers
   * --------------------------------------------------------------------------
   */

  CUSTOMERS: {
    ROOT: "/customers",

    BY_ID: (id: string) =>
      byId("/customers", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Sales
   * --------------------------------------------------------------------------
   */

  SALES: {
    ROOT: "/sales",

    BY_ID: (id: string) =>
      byId("/sales", id),

    RECEIPT: (id: string) =>
      `${byId("/sales", id)}/receipt`,

    AVAILABILITY: "/sales/availability",

    VOID: (id: string) =>
      `${byId("/sales", id)}/void`,
  },

  /**
   * --------------------------------------------------------------------------
   * Refunds
   * --------------------------------------------------------------------------
   */

  REFUNDS: {
    ROOT: "/refunds",

    BY_ID: (id: string) =>
      byId("/refunds", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Payment Methods
   * --------------------------------------------------------------------------
   */

  PAYMENT_METHODS: {
    ROOT: "/payment-methods",

    BY_ID: (id: string) =>
      byId("/payment-methods", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Tills
   * --------------------------------------------------------------------------
   */

  TILLS: {
    ROOT: "/tills",

    BY_ID: (id: string) =>
      byId("/tills", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Warehouses
   * --------------------------------------------------------------------------
   */

  WAREHOUSES: {
    ROOT: "/warehouses",

    BY_ID: (id: string) =>
      byId("/warehouses", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Till Shifts
   * --------------------------------------------------------------------------
   */

  TILL_SHIFTS: {
    ROOT: "/till-shifts",

    CURRENT: "/till-shifts/current",

    OPEN: "/till-shifts/open",

    CLOSE: (id: string) =>
      `${byId("/till-shifts", id)}/close`,
  },

  /**
   * --------------------------------------------------------------------------
   * Prescriptions
   * --------------------------------------------------------------------------
   */

  PRESCRIPTIONS: {
    ROOT: "/prescriptions",

    BY_ID: (id: string) =>
      byId("/prescriptions", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Procurement
   * --------------------------------------------------------------------------
   */

  PURCHASE_ORDERS: {
    ROOT: "/purchase-orders",

    BY_ID: (id: string) =>
      byId("/purchase-orders", id),

    APPROVE: (id: string) =>
      `${byId("/purchase-orders", id)}/approve`,

    RECEIVE: (id: string) =>
      `${byId("/purchase-orders", id)}/receive`,
  },

  /**
   * --------------------------------------------------------------------------
   * Goods Receipts
   * --------------------------------------------------------------------------
   */

  GOODS_RECEIPTS: {
    ROOT: "/goods-receipts",

    BY_ID: (id: string) =>
      byId("/goods-receipts", id),
  },

  /**
   * --------------------------------------------------------------------------
   * Finance
   * --------------------------------------------------------------------------
   */

  PAYMENTS: {
    ROOT: "/payments",

    BY_ID: (id: string) =>
      byId("/payments", id),
  },

  INVOICES: {
    ROOT: "/invoices",

    BY_ID: (id: string) =>
      byId("/invoices", id),

    PDF: (id: string) =>
      `${byId("/invoices", id)}/pdf`,
  },

  /**
   * --------------------------------------------------------------------------
   * Dashboard
   * --------------------------------------------------------------------------
   */

  DASHBOARD: {
    ROOT: "/dashboard",

    OVERVIEW: "/dashboard/overview",

    SUMMARY: "/dashboard/summary",

    METRICS: "/dashboard/metrics",

    ACTIVITY: "/dashboard/activity",
  },

  /**
   * --------------------------------------------------------------------------
   * Reports
   * --------------------------------------------------------------------------
   */

  REPORTS: {
    ROOT: "/reports",

    BY_ID: (id: string) =>
      byId("/reports", id),

    EXPORT: (id: string) =>
      `${byId("/reports", id)}/export`,
  },
} as const;

export default API_ENDPOINTS;
