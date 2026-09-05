/**
 * ============================================================================
 * Hela360 Platform Authentication Provider
 * ============================================================================
 *
 * Restores and validates Hela360 Office authentication independently of tenant
 * ERP authentication.
 * ============================================================================
 */

import {
  useEffect,
  type PropsWithChildren,
} from "react";

import {
  platformAuthStorage,
} from "@/lib/platformAuthStorage";

import {
  platformAuthService,
} from "@/services/platform-auth";

import {
  usePlatformAuthStore,
} from "@/store/platformAuthStore";

function PlatformAuthInitializer() {
  const user = usePlatformAuthStore(
    (state) => state.user,
  );

  const accessToken = usePlatformAuthStore(
    (state) => state.accessToken,
  );

  const refreshToken = usePlatformAuthStore(
    (state) => state.refreshToken,
  );

  const hydrateSession =
    usePlatformAuthStore(
      (state) => state.hydrateSession,
    );

  const reset = usePlatformAuthStore(
    (state) => state.reset,
  );

  const setInitializing =
    usePlatformAuthStore(
      (state) => state.setInitializing,
    );

  useEffect(() => {
    const storedAccessToken =
      platformAuthStorage.getAccessToken();

    const storedRefreshToken =
      platformAuthStorage.getRefreshToken();

    const effectiveAccessToken =
      accessToken ?? storedAccessToken;

    const effectiveRefreshToken =
      refreshToken ?? storedRefreshToken;

    if (
      !effectiveAccessToken ||
      !effectiveRefreshToken
    ) {
      platformAuthStorage.clearTokens();
      reset();
      setInitializing(false);

      return;
    }

    if (user) {
      setInitializing(false);

      return;
    }

    let cancelled = false;

    setInitializing(true);

    void platformAuthService
      .getCurrentSession()
      .then((session) => {
        if (cancelled) {
          return;
        }

        const hydratedAccessToken =
          platformAuthStorage.getAccessToken()
          ?? effectiveAccessToken;

        const hydratedRefreshToken =
          platformAuthStorage.getRefreshToken()
          ?? effectiveRefreshToken;

        hydrateSession(
          session,
          hydratedAccessToken,
          hydratedRefreshToken,
        );
      })
      .catch(() => {
        if (cancelled) {
          return;
        }

        platformAuthStorage.clearTokens();
        reset();
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
    user,
    hydrateSession,
    reset,
    setInitializing,
  ]);

  return null;
}

export function PlatformAuthProvider({
  children,
}: PropsWithChildren) {
  return (
    <>
      <PlatformAuthInitializer />
      {children}
    </>
  );
}

export default PlatformAuthProvider;
