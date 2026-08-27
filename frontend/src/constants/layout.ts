/**
 * ============================================================================
 * Hela360 Enterprise Layout System
 * ============================================================================
 *
 * Centralized design tokens for the Hela360 application shell.
 *
 * This file is the single source of truth for:
 *
 * • Application shell dimensions
 * • Sidebar configuration
 * • Workspace sizing
 * • Layout spacing
 * • Border radius
 * • Animation timings
 * • Z-index hierarchy
 * • Responsive breakpoints
 *
 * UI components should consume these constants instead of hardcoding layout
 * values. This keeps the application visually consistent and greatly simplifies
 * future design changes.
 * ============================================================================
 */

/* ============================================================================
 * Sidebar
 * ========================================================================== */

export const SIDEBAR_WIDTH = 280;

export const SIDEBAR_COLLAPSED_WIDTH = 72;

export const SIDEBAR_MOBILE_WIDTH = 320;

export const SIDEBAR_HEADER_HEIGHT = 72;

export const SIDEBAR_FOOTER_HEIGHT = 72;

/**
 * Sidebar spacing utilities.
 * These map directly to Tailwind utility classes.
 */
export const SIDEBAR_PADDING = "p-4";

export const SIDEBAR_GROUP_SPACING = "space-y-6";

export const SIDEBAR_SECTION_SPACING = "space-y-2";

export const SIDEBAR_ITEM_SPACING = "space-y-1";

/* ============================================================================
 * Topbar
 * ========================================================================== */

export const TOPBAR_HEIGHT = 72;

/* ============================================================================
 * Footer
 * ========================================================================== */

export const FOOTER_HEIGHT = 48;

/* ============================================================================
 * Workspace
 * ========================================================================== */

export const CONTENT_MAX_WIDTH = "100%";

export const CONTENT_PADDING = "1.5rem";

export const CONTENT_PADDING_MOBILE = "1rem";

/* ============================================================================
 * Page Layout
 * ========================================================================== */

export const PAGE_GAP = 24;

export const SECTION_GAP = 32;

export const CARD_GAP = 20;

/* ============================================================================
 * Border Radius
 * ========================================================================== */

export const SHELL_RADIUS = 12;

export const CARD_RADIUS = 12;

/* ============================================================================
 * Animation Durations (milliseconds)
 * ========================================================================== */

export const SIDEBAR_ANIMATION_DURATION = 200;

export const DRAWER_ANIMATION_DURATION = 250;

export const DROPDOWN_ANIMATION_DURATION = 150;

/* ============================================================================
 * Z-Index Scale
 * ========================================================================== */

export const Z_INDEX = {
  BASE: 0,

  SIDEBAR: 20,

  TOPBAR: 30,

  DROPDOWN: 40,

  DRAWER: 50,

  MODAL: 60,

  POPOVER: 70,

  TOOLTIP: 80,

  TOAST: 90,
} as const;

/* ============================================================================
 * Responsive Breakpoints
 * ========================================================================== */

export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  "2XL": 1536,
} as const;

/* ============================================================================
 * Application Shell
 * ========================================================================== */

export const SHELL = {
  sidebarWidth: SIDEBAR_WIDTH,
  sidebarCollapsedWidth: SIDEBAR_COLLAPSED_WIDTH,
  sidebarMobileWidth: SIDEBAR_MOBILE_WIDTH,

  sidebarHeaderHeight: SIDEBAR_HEADER_HEIGHT,
  sidebarFooterHeight: SIDEBAR_FOOTER_HEIGHT,

  topbarHeight: TOPBAR_HEIGHT,

  footerHeight: FOOTER_HEIGHT,

  contentMaxWidth: CONTENT_MAX_WIDTH,
  contentPadding: CONTENT_PADDING,
  contentPaddingMobile: CONTENT_PADDING_MOBILE,
} as const;