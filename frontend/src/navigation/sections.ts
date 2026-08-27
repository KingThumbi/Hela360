/**
 * Hela360 Navigation Section Registry
 *
 * Defines the canonical identifiers for all navigation sections.
 * These identifiers are used throughout the frontend for:
 *
 * - Navigation configuration
 * - Sidebar rendering
 * - Breadcrumb generation
 * - Permission filtering
 * - Analytics
 * - UI state persistence
 *
 * Do not use string literals elsewhere in the application.
 */

import {
  NAVIGATION_SECTION_IDS,
  type NavigationSectionId,
} from "./ids";

/**
 * Ordered list of navigation sections.
 *
 * Used by:
 * - Sidebar rendering
 * - Navigation ordering
 * - Future customization features
 */
export const NAVIGATION_SECTION_ORDER: readonly NavigationSectionId[] = [
  NAVIGATION_SECTION_IDS.DASHBOARD,
  NAVIGATION_SECTION_IDS.SALES,
  NAVIGATION_SECTION_IDS.INVENTORY,
  NAVIGATION_SECTION_IDS.CUSTOMERS,
  NAVIGATION_SECTION_IDS.PROCUREMENT,
  NAVIGATION_SECTION_IDS.FINANCE,
  NAVIGATION_SECTION_IDS.REPORTS,
  NAVIGATION_SECTION_IDS.ADMINISTRATION,
  NAVIGATION_SECTION_IDS.SETTINGS,
] as const;

/**
 * Human-readable labels for navigation sections.
 *
 * Keeping labels centralized makes localization
 * and future branding changes straightforward.
 */
export const NAVIGATION_SECTION_LABELS: Readonly<
  Record<NavigationSectionId, string>
> = {
  [NAVIGATION_SECTION_IDS.DASHBOARD]: "Dashboard",
  [NAVIGATION_SECTION_IDS.SALES]: "Sales",
  [NAVIGATION_SECTION_IDS.INVENTORY]: "Inventory",
  [NAVIGATION_SECTION_IDS.CUSTOMERS]: "Customers",
  [NAVIGATION_SECTION_IDS.PROCUREMENT]: "Procurement",
  [NAVIGATION_SECTION_IDS.FINANCE]: "Finance",
  [NAVIGATION_SECTION_IDS.REPORTS]: "Reports",
  [NAVIGATION_SECTION_IDS.ADMINISTRATION]: "Administration",
  [NAVIGATION_SECTION_IDS.SETTINGS]: "Settings",
} as const;

export {
  NAVIGATION_SECTION_IDS,
};

export type {
  NavigationSectionId,
};
