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
} as const;
