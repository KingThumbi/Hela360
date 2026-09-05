import type {
  ReactNode,
} from "react";

import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import {
  LoadingState,
} from "@/components/page";

import {
  AccessDeniedPage,
} from "@/features/auth/AccessDeniedPage";

import {
  OFFICE_PATHS,
} from "@/routes/officeRoutes";

import {
  usePlatformAuthStore,
} from "@/store/platformAuthStore";

export interface OfficeProtectedRouteProps {
  children?: ReactNode;
}

const OFFICE_ACCESS_PERMISSION =
  "platform.office.access";

export function OfficeProtectedRoute({
  children,
}: OfficeProtectedRouteProps) {
  const location = useLocation();

  const isInitializing =
    usePlatformAuthStore(
      (state) => state.isInitializing,
    );

  const isAuthenticated =
    usePlatformAuthStore(
      (state) => state.isAuthenticated,
    );

  const user =
    usePlatformAuthStore(
      (state) => state.user,
    );

  const authorization =
    usePlatformAuthStore(
      (state) => state.authorization,
    );

  if (isInitializing) {
    return (
      <LoadingState
        title="Restoring Hela360 Office session..."
        description="Please wait while we securely restore your platform session."
      />
    );
  }

  if (
    !isAuthenticated ||
    user === null
  ) {
    return (
      <Navigate
        to={OFFICE_PATHS.LOGIN}
        replace
        state={{
          from: location,
        }}
      />
    );
  }

  const permissions =
    authorization?.permissions ?? [];

  const hasOfficeAccess =
    permissions.includes("*") ||
    permissions.includes(
      OFFICE_ACCESS_PERMISSION,
    );

  if (!hasOfficeAccess) {
    return <AccessDeniedPage />;
  }

  return children ?? <Outlet />;
}

export default OfficeProtectedRoute;
