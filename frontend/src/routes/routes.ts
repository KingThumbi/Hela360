/**
 * Hela360 Route Registry
 *
 * This file is the single source of truth for all application routes.
 * Do not hardcode route strings anywhere else in the application.
 */

export const PATHS = {
  ROOT: "/",
  LOGIN: "/login",
  DASHBOARD: "/dashboard",

  SALES: {
    ROOT: "/sales",
    POS: "/sales/pos",
    RECEIPT: "/sales/receipt/:saleId",
    receipt: (saleId: string) => `/sales/receipt/${saleId}`,
    HISTORY: "/sales/history",
    RETURNS: "/sales/refunds",
  },

  PRODUCTS: {
    ROOT: "/products",
  },

  CUSTOMERS: {
    ROOT: "/customers",
  },

  INVENTORY: {
    ROOT: "/inventory",
    RECEIVE: "/inventory/receive",
    RECEIPTS: "/inventory/receipts",
    RECEIPT: "/inventory/receipts/:receiptId",
    receipt: (receiptId: string) => `/inventory/receipts/${receiptId}`,
    STOCK_COUNTS: "/inventory/stock-counts",
    STOCK_COUNT_NEW: "/inventory/stock-counts/new",
    STOCK_COUNT: "/inventory/stock-counts/:countId",
    stockCount: (countId: string) => `/inventory/stock-counts/${countId}`,
    STOCK_ADJUSTMENTS: "/inventory/stock-adjustments",
    STOCK_ADJUSTMENT_NEW: "/inventory/stock-adjustments/new",
    STOCK_ADJUSTMENT: "/inventory/stock-adjustments/:adjustmentId",
    stockAdjustment: (adjustmentId: string) =>
      `/inventory/stock-adjustments/${adjustmentId}`,
  },

  WAREHOUSES: {
    ROOT: "/warehouses",
  },

  PROCUREMENT: {
    ROOT: "/procurement",
    PURCHASE_ORDERS: "/procurement/purchase-orders",
    SUPPLIERS: "/procurement/suppliers",
  },

  FINANCE: {
    ROOT: "/finance",
    EXPENSES: "/finance/expenses",
    PAYMENTS: "/finance/payments",
    CASHBOOK: "/finance/cashbook",
  },

  REPORTS: {
    ROOT: "/reports",
    ANALYTICS: "/reports/analytics",
  },

  ADMINISTRATION: {
    ROOT: "/administration",
    USERS: "/administration/users",
    ROLES: "/administration/roles",
    PERMISSIONS: "/administration/permissions",
    BRANCHES: "/administration/branches",
    WAREHOUSES: "/administration/warehouses",
    PAYMENT_METHODS: "/administration/payment-methods",
  },

  SETTINGS: {
    ROOT: "/settings",
    TENANT: "/settings/tenant",
  },
} as const;
