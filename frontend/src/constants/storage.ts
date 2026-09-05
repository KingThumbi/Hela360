/**
 * ============================================================================
 * Hela360 Enterprise Storage Keys
 * ============================================================================
 */

export const STORAGE = {
  ACCESS_TOKEN: "hela360.access_token",

  REFRESH_TOKEN: "hela360.refresh_token",

  PLATFORM_ACCESS_TOKEN:
    "hela360.platform.access_token",

  PLATFORM_REFRESH_TOKEN:
    "hela360.platform.refresh_token",

  THEME: "hela360.theme",

  SIDEBAR_COLLAPSED:
    "hela360.sidebar.collapsed",

  TENANT_ID: "hela360.tenant.id",

  BRANCH_ID: "hela360.branch.id",

  REMEMBER_ME: "hela360.remember_me",
} as const;

export default STORAGE;
