/**
 * Hela360 Navigation Module
 *
 * Public exports for the application's navigation infrastructure.
 *
 * Import from "@/navigation" rather than individual files.
 *
 * Example:
 *
 * import {
 *   navigation,
 *   PERMISSIONS,
 *   NavigationSectionId,
 *   flattenNavigation,
 *   filterNavigationByPermissions,
 * } from "@/navigation";
 */

export { navigation } from "./navigation";

export { PERMISSIONS } from "./permissions";

export {
  NAVIGATION_ITEM_IDS,
  NAVIGATION_SECTION_IDS,
} from "./ids";

export type {
  NavigationItemId,
  NavigationSectionId,
} from "./ids";

export {
  NAVIGATION_SECTION_LABELS,
  NAVIGATION_SECTION_ORDER,
} from "./sections";

export {
  flattenNavigation,
  findNavigationItemById,
  findNavigationItemByPath,
  findNavigationSection,
  isNavigationItemActive,
  getProtectedNavigationItems,
  filterNavigation,
  filterNavigationSection,
  filterNavigationByPermissions,
  buildBreadcrumbs,
} from "./helpers";
