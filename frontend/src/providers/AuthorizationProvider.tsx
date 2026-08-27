import {
  createContext,
  useMemo,
  type PropsWithChildren,
} from "react";

import {
  can as canPermission,
  canAll as canAllPermissions,
  canAny as canAnyPermission,
  cannot as cannotPermission,
} from "@/authorization/authorizationService";
import { useAuthStore } from "@/store/authStore";

import type { PermissionCode } from "@/types/auth";


export interface AuthorizationContextValue {
  permissions: readonly PermissionCode[];

  isAuthorizationReady: boolean;

  can: (permission: PermissionCode) => boolean;

  canAny: (
    permissions: readonly PermissionCode[],
  ) => boolean;

  canAll: (
    permissions: readonly PermissionCode[],
  ) => boolean;

  cannot: (permission: PermissionCode) => boolean;
}


export const AuthorizationContext =
  createContext<AuthorizationContextValue | null>(
    null,
  );


export function AuthorizationProvider({
  children,
}: PropsWithChildren) {
  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated,
  );

  const isInitializing = useAuthStore(
    (state) => state.isInitializing,
  );

  const identity = useAuthStore(
    (state) => state.identity,
  );

  const sessionPermissions = useAuthStore(
    (state) => state.permissions,
  );

  const permissions = useMemo<readonly PermissionCode[]>(
    () =>
      !isInitializing &&
      isAuthenticated &&
      identity
        ? [...sessionPermissions]
        : [],
    [
      identity,
      isAuthenticated,
      isInitializing,
      sessionPermissions,
    ],
  );

  const permissionSet = useMemo(
    () => new Set(permissions),
    [permissions],
  );

  const isOwner =
    !isInitializing &&
    isAuthenticated &&
    identity?.isOwner === true;

  const value = useMemo<AuthorizationContextValue>(
    () => ({
      permissions,

      isAuthorizationReady:
        !isInitializing &&
        isAuthenticated &&
        identity !== null,

      can: (permission) =>
        isOwner ||
        canPermission(
          permissionSet,
          permission,
        ),

      canAny: (requiredPermissions) =>
        isOwner ||
        canAnyPermission(
          permissionSet,
          requiredPermissions,
        ),

      canAll: (requiredPermissions) =>
        isOwner ||
        canAllPermissions(
          permissionSet,
          requiredPermissions,
        ),

      cannot: (permission) =>
        !isOwner &&
        cannotPermission(
          permissionSet,
          permission,
        ),
    }),
    [
      identity,
      isAuthenticated,
      isInitializing,
      isOwner,
      permissionSet,
      permissions,
    ],
  );

  return (
    <AuthorizationContext.Provider value={value}>
      {children}
    </AuthorizationContext.Provider>
  );
}


export default AuthorizationProvider;
