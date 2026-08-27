import type { LucideIcon } from "lucide-react";

import type { Permission } from "@/navigation/permissions";
import type {
  NavigationItemId,
  NavigationSectionId,
} from "@/navigation/ids";

/**
 * ============================================================================
 * Navigation Item Identifiers
 * ============================================================================
 *
 * Canonical identifiers for every navigation entry in Hela360.
 * These identifiers should be used throughout the application instead of
 * hardcoded strings.
 * ============================================================================
 */
export type {
  NavigationItemId,
  NavigationSectionId,
} from "@/navigation/ids";

/**
 * ============================================================================
 * Navigation Item
 * ============================================================================
 *
 * Represents a single navigable item within the enterprise application shell.
 *
 * Navigation items power:
 *
 * • Sidebar
 * • Breadcrumbs
 * • Route highlighting
 * • Permission filtering
 * • Future global search
 * • Future command palette
 * ============================================================================
 */
export interface NavigationItem {
  /**
   * Canonical identifier.
   */
  id: NavigationItemId;

  /**
   * Sidebar label.
   */
  title: string;

  /**
   * Optional breadcrumb label.
   *
   * Defaults to `title` when omitted.
   */
  breadcrumb?: string;

  /**
   * Application route.
   */
  href: string;

  /**
   * Sidebar icon.
   */
  icon: LucideIcon;

  /**
   * Permission required to display this item.
   */
  permission?: Permission;

  /**
   * Alternative permissions that may grant access.
   *
   * When present, the user may see the navigation item when at least one
   * permission is granted.
   */
  anyOfPermissions?: readonly Permission[];

  /**
   * Optional badge.
   *
   * Examples:
   * 3
   * "NEW"
   * "Beta"
   */
  badge?: string | number;

  /**
   * Prevent user interaction.
   */
  disabled?: boolean;

  /**
   * Opens in a new tab.
   */
  external?: boolean;

  /**
   * Reserved for future nested navigation support.
   */
  children?: NavigationItem[];
}

/**
 * ============================================================================
 * Navigation Section
 * ============================================================================
 *
 * Groups navigation items within the application sidebar.
 * ============================================================================
 */
export interface NavigationSection {
  /**
   * Canonical section identifier.
   */
  id: NavigationSectionId;

  /**
   * Sidebar heading.
   *
   * Use an empty string ("") when the heading should be hidden.
   */
  title: string;

  /**
   * Navigation items belonging to this section.
   */
  items: NavigationItem[];
}
