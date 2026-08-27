/**
 * ============================================================================
 * Hela360 Enterprise Application Provider
 * ============================================================================
 *
 * Top-level application composition provider.
 *
 * Responsibilities
 * ----------------
 * • Compose the enterprise application context
 * • Expose application-wide services
 * • Provide a stable API for feature modules
 * • Decouple features from provider implementation details
 *
 * This provider does not own application state. It composes existing
 * providers and contexts into a single application context.
 *
 * Current Composition
 * -------------------
 * • Authentication
 * • Enterprise Shell
 *
 * Future Composition
 * ------------------
 * • Authorization
 * • Tenant
 * • Workspace
 * • Feature Flags
 * • Localization
 * • User Preferences
 * • Environment
 *
 * ============================================================================
 */

import {
  useMemo,
  type PropsWithChildren,
} from "react";

import {
  useShell,
} from "@/providers/useShell";

import type {
  ShellContextValue,
} from "@/providers/ShellProvider";

import {
  ApplicationContext,
} from "./application-context";

import {
  useAuthStore,
  type AuthStore,
} from "@/store/authStore";

/* ============================================================================
 * Application Context
 * ============================================================================
 */

export interface ApplicationContextValue {
  /**
   * Authentication.
   */
  auth: AuthStore;

  /**
   * Enterprise shell.
   */
  shell: ShellContextValue;
}

/* ============================================================================
 * Application Provider
 * ============================================================================
 */

export function ApplicationProvider({
  children,
}: PropsWithChildren) {
  /**
   * Existing application subsystems.
   */
  const auth = useAuthStore();

  const shell = useShell();

  /**
   * Stable context value.
   */
  const value = useMemo<ApplicationContextValue>(
    () => ({
      auth,
      shell,
    }),
    [auth, shell],
  );

  return (
    <ApplicationContext.Provider value={value}>
      {children}
    </ApplicationContext.Provider>
  );
}

/* ============================================================================
 * Application Context Hook
 * ============================================================================
 */

/**
 * Provides access to the enterprise application context.
 *
 * Feature modules should consume this hook whenever they require access to
 * multiple application services.
 */

export default ApplicationProvider;
