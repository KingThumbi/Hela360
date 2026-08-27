/**
 * ============================================================================
 * Hela360 Enterprise Application Provider
 * ============================================================================
 *
 * Composes application-wide infrastructure providers that do not depend on
 * React Router context.
 *
 * Responsibilities
 * ----------------
 * • Initialize global application infrastructure
 * • Compose framework-level providers
 * • Configure authentication and authorization context
 * • Configure global UI services
 * • Provide application-wide notifications and tooltips
 *
 * Architectural Boundary
 * ----------------------
 * Router-dependent providers MUST NOT be mounted here.
 *
 * In particular:
 *
 * • ShellProvider depends on useNavigation()
 * • useNavigation() depends on React Router's useLocation()
 * • therefore ShellProvider must be rendered beneath RouterProvider
 *
 * ApplicationProvider is composed together with ShellProvider inside the
 * routed application tree so that shell-aware application context is only
 * initialized where Router context is available.
 *
 * Provider Hierarchy
 * ------------------
 *
 * ThemeProvider
 *   ↓
 * QueryProvider
 *   ↓
 * AuthProvider
 *   ↓
 * AuthorizationProvider
 *   ↓
 * TooltipProvider
 *   ↓
 * Application Router
 *   ↓
 * Route-aware providers
 *
 * Global UI services such as the application toaster are registered here.
 *
 * ============================================================================
 */

import type { PropsWithChildren } from "react";

import { Toaster } from "sonner";

import { TooltipProvider } from "@/components/ui/tooltip";

import { AuthorizationProvider } from "./AuthorizationProvider";
import { AuthProvider } from "./AuthProvider";
import { QueryProvider } from "./QueryProvider";
import { ThemeProvider } from "./ThemeProvider";


/* ============================================================================
 * Application Provider
 * ============================================================================
 */

/**
 * Compose router-independent application infrastructure.
 */
export function AppProvider({
  children,
}: PropsWithChildren) {
  return (
    <ThemeProvider>
      <QueryProvider>
        <AuthProvider>
          <AuthorizationProvider>
            <TooltipProvider delay={250}>
              {children}

              <Toaster
                position="top-right"
                richColors
                closeButton
                expand
                duration={4000}
              />
            </TooltipProvider>
          </AuthorizationProvider>
        </AuthProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}

export default AppProvider;