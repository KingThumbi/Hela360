/**
 * ============================================================================
 * Hela360 Enterprise Theme Provider
 * ============================================================================
 *
 * Initializes the application's theme infrastructure.
 *
 * Responsibilities
 * ----------------
 * • Initialize the persisted theme preference
 * • Apply the resolved theme
 * • Synchronize with operating system theme changes
 * • Expose the application theme through useTheme()
 *
 * Theme state itself is managed by the shell store and useTheme().
 * This provider ensures the theme system is initialized once at the
 * application root.
 *
 * ============================================================================
 */

import type { PropsWithChildren } from "react";

import { useTheme } from "@/hooks/useTheme";

/* ============================================================================
 * Theme Initializer
 * ============================================================================
 */

function ThemeInitializer() {
  /**
   * Initialize and synchronize the application theme.
   *
   * The hook performs all side effects:
   * • restores persisted preference
   * • resolves system theme
   * • updates document.documentElement
   * • listens for OS theme changes
   */
  useTheme();

  return null;
}

/* ============================================================================
 * Theme Provider
 * ============================================================================
 */

export function ThemeProvider({
  children,
}: PropsWithChildren) {
  return (
    <>
      <ThemeInitializer />

      {children}
    </>
  );
}

export default ThemeProvider;