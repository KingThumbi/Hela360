/**
 * ============================================================================
 * Hela360 Enterprise Shell Provider
 * ============================================================================
 *
 * Central composition root for the enterprise application shell.
 *
 * Responsibilities
 * ----------------
 * • Initialize the application shell
 * • Compose enterprise shell services
 * • Expose shell context
 * • Decouple layout components from individual hooks
 *
 * The ShellProvider is the single entry point into the application's shell
 * layer. Layout components should consume the shell context instead of
 * importing individual hooks.
 *
 * Initialization
 * --------------
 * Shell initialization is delegated to useInitializeShell(), allowing the
 * provider to remain focused on composition while initialization concerns
 * remain isolated.
 *
 * Future Responsibilities
 * -----------------------
 * • Workspace context
 * • Command palette
 * • Global search
 * • Quick actions
 * • Keyboard shortcuts
 * • Feature flags
 * • Tenant preferences
 * • Workspace persistence
 * • User preferences
 * ============================================================================
 */

import {
  useMemo,
  type PropsWithChildren,
} from "react";
import {
  ShellContext,
} from "./shell-context";
import { useCurrentBranch } from "@/hooks/useCurrentBranch";
import { useInitializeShell } from "@/hooks/useInitializeShell";
import { useNavigation } from "@/hooks/useNavigation";
import { useNotifications } from "@/hooks/useNotifications";
import { useTheme } from "@/hooks/useTheme";
import { useUserMenu } from "@/hooks/useUserMenu";

/* ============================================================================
 * Shell Context
 * ============================================================================
 */

export interface ShellContextValue {
  /**
   * Enterprise navigation.
   */
  navigation: ReturnType<typeof useNavigation>;

  /**
   * Active branch context.
   */
  branch: ReturnType<typeof useCurrentBranch>;

  /**
   * Notification center.
   */
  notifications: ReturnType<typeof useNotifications>;

  /**
   * Theme management.
   */
  theme: ReturnType<typeof useTheme>;

  /**
   * User menu state.
   */
  userMenu: ReturnType<typeof useUserMenu>;
}


/* ============================================================================
 * Shell Provider
 * ============================================================================
 */

export function ShellProvider({
  children,
}: PropsWithChildren) {
  /**
   * Initialize the enterprise shell.
   *
   * This hook restores persisted shell state and prepares the application
   * before any layout component consumes the shell context.
   */
  useInitializeShell();

  /**
   * Compose shell services.
   */
  const navigation = useNavigation();

  const branch = useCurrentBranch();

  const notifications = useNotifications();

  const theme = useTheme();

  const userMenu = useUserMenu();

  /**
   * Memoize the shell context to avoid unnecessary re-renders caused by
   * recreating the context object on every render.
   */
  const value = useMemo<ShellContextValue>(
    () => ({
      navigation,
      branch,
      notifications,
      theme,
      userMenu,
    }),
    [
      navigation,
      branch,
      notifications,
      theme,
      userMenu,
    ],
  );

  return (
    <ShellContext.Provider value={value}>
      {children}
    </ShellContext.Provider>
  );
}

/* ============================================================================
 * Shell Context Hook
 * ============================================================================
 */

/**
 * Provides access to the enterprise application shell.
 *
 * All layout components should consume this hook rather than importing
 * multiple shell hooks directly.
 */

export default ShellProvider;