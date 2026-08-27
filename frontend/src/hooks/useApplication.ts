/**
 * ============================================================================
 * Hela360 Enterprise Application Hook
 * ============================================================================
 *
 * Provides access to the application's unified context.
 *
 * Responsibilities
 * ----------------
 * • Consume the ApplicationContext
 * • Expose a strongly typed application API
 * • Decouple feature modules from provider implementation details
 *
 * This hook is the preferred entry point for feature modules requiring access
 * to application-wide services. Consumers should avoid importing individual
 * providers or stores directly whenever the application context already
 * exposes the required functionality.
 *
 * Architecture
 * ------------
 * ApplicationProvider
 *         │
 *         ▼
 * ApplicationContext
 *         │
 *         ▼
 * useApplication()
 *         │
 *         ▼
 * Feature Modules
 *
 * Future Composition
 * ------------------
 * • Authentication
 * • Authorization
 * • Tenant
 * • Branch
 * • Workspace
 * • Feature Flags
 * • Localization
 * • User Preferences
 * • Environment
 * ============================================================================
 */

import {
  useApplicationContext,
  type ApplicationContextValue,
} from "@/providers";

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Returns the enterprise application context.
 *
 * Feature modules should use this hook as the primary access point to
 * application-wide services.
 */
export function useApplication(): ApplicationContextValue {
  return useApplicationContext();
}

export default useApplication;
