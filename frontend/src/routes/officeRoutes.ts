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

  SUPPLIER_INTELLIGENCE: {
    ROOT: "/office/supplier-intelligence",
    CATALOGUE_SUPPLIERS:
      "/office/supplier-intelligence/catalogue-suppliers",
    CATALOGUE_SUPPLIER_DETAIL:
      "/office/supplier-intelligence/catalogue-suppliers/:supplierId",
    catalogueSupplierDetail: (
      supplierId: string,
    ) =>
      `/office/supplier-intelligence/catalogue-suppliers/${supplierId}`,
  },

  CATALOGUE: {
    ROOT: "/office/catalogue",
    MASTER_ITEMS: "/office/catalogue/master-items",
    MASTER_ITEM_DETAIL:
      "/office/catalogue/master-items/:masterItemId",
    masterItemDetail: (
      masterItemId: string,
    ) =>
      `/office/catalogue/master-items/${masterItemId}`,
    REVIEW_QUEUE: "/office/catalogue/review-queue",
    CATEGORIES: "/office/catalogue/categories",
    BRANDS: "/office/catalogue/brands",
    DATA_QUALITY: "/office/catalogue/data-quality",
  },
} as const;
