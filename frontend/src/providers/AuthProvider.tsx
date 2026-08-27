/**
 * ============================================================================
 * Hela360 Enterprise Authentication Provider
 * ============================================================================
 *
 * Initializes the application's authentication lifecycle.
 *
 * Responsibilities
 * ----------------
 * • Restore persisted authentication tokens
 * • Validate the current session
 * • Load the authenticated identity
 * • Populate the authentication store
 * • Handle invalid sessions
 *
 * Authentication logic belongs in services and hooks.
 * This provider orchestrates application startup.
 *
 * ============================================================================
 */

import type { PropsWithChildren } from "react";
import { useEffect } from "react";

import { storage } from "@/lib/storage";
import { authService } from "@/services/auth";
import { useAuthStore } from "@/store/authStore";
import { useShellStore } from "@/store/shellStore";

import type { AuthenticatedSession } from "@/types/auth";

function resolveSelectedBranchId(
  session: AuthenticatedSession,
): string | undefined {
  const accessibleBranchIds = new Set(
    session.branches.map((branch) => branch.id),
  );

  const storedBranchId = storage.getBranchId();

  if (
    storedBranchId &&
    accessibleBranchIds.has(storedBranchId)
  ) {
    return storedBranchId;
  }

  if (
    session.defaultBranchId &&
    accessibleBranchIds.has(session.defaultBranchId)
  ) {
    return session.defaultBranchId;
  }

  return undefined;
}

function synchronizeScopePersistence(
  session: AuthenticatedSession,
): string | undefined {
  const previousTenantId = storage.getTenantId();

  storage.setTenantId(
    session.identity.tenantId,
  );

  if (
    previousTenantId &&
    previousTenantId !== session.identity.tenantId
  ) {
    storage.removeBranchId();
  }

  const selectedBranchId =
    resolveSelectedBranchId(session);

  if (selectedBranchId) {
    storage.setBranchId(selectedBranchId);
  } else {
    storage.removeBranchId();
  }

  return selectedBranchId;
}

/* ============================================================================
 * Authentication Initializer
 * ============================================================================
 */

function AuthInitializer() {
  const accessToken = useAuthStore(
    (state) => state.accessToken,
  );

  const refreshToken = useAuthStore(
    (state) => state.refreshToken,
  );

  const identity = useAuthStore(
    (state) => state.identity,
  );

  const hydrateSession = useAuthStore(
    (state) => state.hydrateSession,
  );

  const setInitializing = useAuthStore(
    (state) => state.setInitializing,
  );

  const logout = useAuthStore(
    (state) => state.logout,
  );

  const setSelectedBranch = useShellStore(
    (state) => state.setSelectedBranch,
  );

  useEffect(() => {
    const storedAccessToken =
      storage.getAccessToken();

    const storedRefreshToken =
      storage.getRefreshToken();

    const effectiveAccessToken =
      accessToken ?? storedAccessToken;

    const effectiveRefreshToken =
      refreshToken ?? storedRefreshToken;

    if (!effectiveAccessToken || !effectiveRefreshToken) {
      storage.clearSession();
      setSelectedBranch(undefined);
      logout();
      setInitializing(false);

      return;
    }

    if (identity) {
      setInitializing(false);

      return;
    }

    let cancelled = false;

    setInitializing(true);

    void authService
      .getCurrentSession()
      .then((session) => {
        if (cancelled) {
          return;
        }

        const selectedBranchId =
          synchronizeScopePersistence(session);

        setSelectedBranch(selectedBranchId);

        hydrateSession(
          session,
          effectiveAccessToken,
          effectiveRefreshToken,
        );
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        storage.clearSession();
        setSelectedBranch(undefined);
        logout();
      })
      .finally(() => {
        if (!cancelled) {
          setInitializing(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    accessToken,
    refreshToken,
    identity,
    hydrateSession,
    logout,
    setInitializing,
    setSelectedBranch,
  ]);

  return null;
}

/* ============================================================================
 * Authentication Provider
 * ============================================================================
 */

export function AuthProvider({
  children,
}: PropsWithChildren) {
  return (
    <>
      <AuthInitializer />

      {children}
    </>
  );
}

export default AuthProvider;
