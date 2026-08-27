/**
 * ============================================================================
 * Hela360 Enterprise Protected Route
 * ============================================================================
 *
 * Guards authenticated application routes.
 *
 * Responsibilities
 * ----------------
 * • Wait for authentication initialization
 * • Display a loading screen while restoring the session
 * • Redirect unauthenticated users
 * • Render an access-denied boundary for forbidden users
 * • Render protected content
 *
 * Authentication Responsibilities
 * -------------------------------
 * Authentication lifecycle (login, logout, refresh, hydration and current user
 * loading) is owned by AuthProvider.
 *
 * This component simply consumes the resulting authentication state.
 *
 * ============================================================================
 */

import type { ReactElement } from "react";

import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { LoadingState } from "@/components/page";
import { AccessDeniedPage } from "@/features/auth/AccessDeniedPage";
import { useAuthorization } from "@/hooks/useAuthorization";
import { useApplication } from "@/hooks/useApplication";
import { PATHS } from "@/routes/routes";
import type { PermissionCode } from "@/types/auth";

/* ============================================================================
 * Types
 * ============================================================================
 */

export interface ProtectedRouteProps {
  /**
   * Optional children.
   *
   * If omitted, an <Outlet /> is rendered to support nested routing.
   */
  children?: ReactElement;

  /**
   * Optional custom redirect path.
   */
  redirectTo?: string;

  /**
   * Optional permission required to render the route.
   */
  permission?: PermissionCode;
}

/* ============================================================================
 * Component
 * ============================================================================
 */

export function ProtectedRoute({
  children,
  permission,
  redirectTo = PATHS.LOGIN,
}: ProtectedRouteProps): ReactElement {
  const location = useLocation();

  const {
    auth,
  } = useApplication();

  const authorization = useAuthorization();

  /**
   * --------------------------------------------------------------------------
   * Wait for session restoration.
   * --------------------------------------------------------------------------
   */

  if (auth.isInitializing) {
    return (
      <LoadingState
        title="Restoring session..."
        description="Please wait while we securely restore your session."
      />
    );
  }

  /**
   * --------------------------------------------------------------------------
   * Redirect unauthenticated users.
   * --------------------------------------------------------------------------
   */

  if (!auth.isAuthenticated) {
    return (
      <Navigate
        to={redirectTo}
        replace
        state={{
          from: location,
        }}
      />
    );
  }

  /**
   * --------------------------------------------------------------------------
   * Forbidden authenticated users stay on the requested URL and see an
   * access-denied boundary instead of being redirected to login.
   * --------------------------------------------------------------------------
   */

  if (permission) {
    if (!authorization.isAuthorizationReady) {
      return (
        <LoadingState
          title="Checking access..."
          description="Please wait while we verify your route access."
        />
      );
    }

    if (!authorization.can(permission)) {
      return <AccessDeniedPage />;
    }
  }

  /**
   * --------------------------------------------------------------------------
   * Authenticated.
   * --------------------------------------------------------------------------
   */

  return children ?? <Outlet />;
}

export default ProtectedRoute;
