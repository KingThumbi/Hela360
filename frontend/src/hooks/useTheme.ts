import { useEffect, useMemo } from "react";

import {
  type ThemeMode,
  useShellStore,
} from "@/store/shellStore";

/**
 * ============================================================================
 * useTheme
 * ============================================================================
 *
 * Enterprise theme management.
 *
 * Responsibilities
 * ----------------
 * • Read the current theme preference
 * • Persist the user's theme selection
 * • Resolve the effective application theme
 * • Apply the resolved theme to the document
 * • React to operating system theme changes
 *
 * This hook is the single source of truth for theme management.
 * Components should never manipulate document.documentElement or access
 * localStorage directly.
 *
 * Future Integrations
 * -------------------
 * • User profile preferences
 * • Tenant branding
 * • Accessibility themes
 * • High-contrast mode
 * • Theme synchronization across devices
 * ============================================================================
 */

const STORAGE_KEY = "hela360.theme";

export interface UseThemeResult {
  /**
   * User-selected theme preference.
   *
   * light | dark | system
   */
  theme: ThemeMode;

  /**
   * Effective application theme after resolving the
   * user's preference and operating system settings.
   */
  resolvedTheme: "light" | "dark";

  /**
   * Convenience flag for presentation components.
   *
   * Components should consume this instead of comparing
   * resolvedTheme === "dark".
   */
  isDark: boolean;

  /**
   * Update the user's preferred theme.
   */
  setTheme: (theme: ThemeMode) => void;

  /**
   * Toggle between light and dark themes.
   *
   * If the current preference is "system", the toggle
   * switches to the opposite of the currently resolved theme.
   */
  toggleTheme: () => void;
}

export function useTheme(): UseThemeResult {
  const theme = useShellStore((state) => state.theme);

  const setTheme = useShellStore(
    (state) => state.setTheme,
  );

  /**
   * Restore the persisted theme preference.
   *
   * Runs once during application startup.
   */
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (
      stored === "light" ||
      stored === "dark" ||
      stored === "system"
    ) {
      setTheme(stored);
    }
  }, [setTheme]);

  /**
   * Persist the current preference.
   */
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  /**
   * Determine the effective application theme.
   */
  const resolvedTheme = useMemo<"light" | "dark">(() => {
    if (theme !== "system") {
      return theme;
    }

    return window.matchMedia(
      "(prefers-color-scheme: dark)",
    ).matches
      ? "dark"
      : "light";
  }, [theme]);

  /**
   * Convenience flag used by presentation components.
   */
  const isDark = resolvedTheme === "dark";

  /**
   * Apply the resolved theme to the document root.
   */
  useEffect(() => {
    const root = document.documentElement;

    root.classList.remove("light", "dark");
    root.classList.add(resolvedTheme);
  }, [resolvedTheme]);

  /**
   * React to operating system theme changes while the
   * user preference is set to "system".
   */
  useEffect(() => {
    if (theme !== "system") {
      return;
    }

    const mediaQuery = window.matchMedia(
      "(prefers-color-scheme: dark)",
    );

    const handleChange = (
      event: MediaQueryListEvent,
    ) => {
      const root = document.documentElement;

      root.classList.remove("light", "dark");
      root.classList.add(
        event.matches ? "dark" : "light",
      );
    };

    mediaQuery.addEventListener(
      "change",
      handleChange,
    );

    return () => {
      mediaQuery.removeEventListener(
        "change",
        handleChange,
      );
    };
  }, [theme]);

  /**
   * Toggle between light and dark themes.
   *
   * The current resolved theme is used rather than the
   * stored preference, ensuring correct behaviour even
   * when the preference is "system".
   */
  const toggleTheme = () => {
    setTheme(isDark ? "light" : "dark");
  };

  return {
    theme,
    resolvedTheme,
    isDark,
    setTheme,
    toggleTheme,
  };
}

export default useTheme;
