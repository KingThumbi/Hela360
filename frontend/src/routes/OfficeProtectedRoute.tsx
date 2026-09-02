import type { ReactNode } from "react";

import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { AccessDeniedPage } from "@/features/auth/AccessDeniedPage";
import { useAuthStore } from "@/store/authStore";
import { PATHS } from "@/routes/routes";

export interface OfficeProtectedRouteProps {
  children?: ReactNode;
}

/**
 * Hela360 Office application-boundary guard.
 *
 * Authentication remains shared with the tenant ERP.
 *
 * Office admission currently relies on the backend-derived
 * `isPlatformAdmin` identity flag.
 *
 * This is intentionally not the permanent Office action-authorization model.
 * Future Office actions will be governed by explicit platform permissions.
 */
export function OfficeProtectedRoute({
  children,
}: OfficeProtectedRouteProps) {
  const location = useLocation();

  const isInitializing = useAuthStore(
    (state) => state.isInitializing,
  );

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated,
  );

  const identity = useAuthStore(
    (state) => state.identity,
  );

  if (isInitializing) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-sm text-muted-foreground">
          Loading Hela360 Office...
        </div>
      </div>
    );
  }

  if (!isAuthenticated || identity === null) {
    return (
      <Navigate
        to={PATHS.LOGIN}
        replace
        state={{
          from: location,
        }}
      />
    );
  }

  if (identity.isPlatformAdmin !== true) {
    return <AccessDeniedPage />;
  }

  return children ?? <Outlet />;
}

export default OfficeProtectedRoute;
