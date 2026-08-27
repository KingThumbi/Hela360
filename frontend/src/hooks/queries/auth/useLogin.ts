/**
 * ============================================================================
 * Hela360 Enterprise Login Mutation
 * ============================================================================
 *
 * Authenticates a user and establishes the application session.
 *
 * Responsibilities
 * ----------------
 * • Execute authentication requests
 * • Persist authenticated identity
 * • Synchronize AuthStore
 * • Refresh authentication cache
 * • Refresh dashboard context
 * • Refresh administration context
 *
 * Components should never communicate with AuthService directly.
 *
 * ============================================================================
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createMutationOptions,
} from "@/lib/queryFactory";

import {
  invalidateAdministration,
  invalidateAuthentication,
  invalidateDashboard,
} from "@/lib/queryInvalidation";

import { authService } from "@/services/auth";

import storage from "@/lib/storage";

import { useAuthStore } from "@/store/authStore";

import type { LoginRequest } from "@/types/requests";
import type { LoginResult } from "@/types/auth";

/* ============================================================================
 * Hook
 * ============================================================================
 */

export function useLogin() {
  const queryClient = useQueryClient();

  const login = useAuthStore(
    (state) => state.login,
  );

  const setTokens = useAuthStore(
    (state) => state.setTokens,
  );

  const setInitializing = useAuthStore(
    (state) => state.setInitializing,
  );

  return useMutation(
    createMutationOptions<
      LoginResult,
      LoginRequest
    >(
      (credentials) =>
        authService.login(credentials),

      {
        onSuccess: async (response) => {
          storage.setAccessToken(
            response.accessToken,
          );

          storage.setRefreshToken(
            response.refreshToken,
          );

          if (response.identity) {
            login(
              response.identity,
              response.accessToken,
              response.refreshToken,
            );
          } else {
            setTokens(
              response.accessToken,
              response.refreshToken,
            );

            setInitializing(true);
          }

          await invalidateAuthentication(
            queryClient,
          );

          await invalidateDashboard(
            queryClient,
          );

          await invalidateAdministration(
            queryClient,
          );
        },
      },
    ),
  );
}

export default useLogin;
