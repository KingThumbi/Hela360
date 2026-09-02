/**
 * Hela360 Office Route Registry
 *
 * Hela360 Office is the platform-management application surface.
 *
 * These routes are intentionally separate from the tenant ERP PATHS registry.
 * Tenant ERP routes represent operating a tenant business.
 * Office routes represent operating the Hela360 platform.
 */

export const OFFICE_PATHS = {
  ROOT: "/office",
  DASHBOARD: "/office/dashboard",

  CATALOGUE: {
    ROOT: "/office/catalogue",
    MASTER_ITEMS: "/office/catalogue/master-items",
    REVIEW_QUEUE: "/office/catalogue/review-queue",
    CATEGORIES: "/office/catalogue/categories",
    BRANDS: "/office/catalogue/brands",
    DATA_QUALITY: "/office/catalogue/data-quality",
  },
} as const;
