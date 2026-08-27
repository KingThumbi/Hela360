/**
 * ============================================================================
 * Hela360 Enterprise Logout Mutation
 * ============================================================================
 *
 * Terminates the authenticated session.
 *
 * Responsibilities
 * ----------------
 * • Notify the backend
 * • Clear AuthStore
 * • Clear persisted session
 * • Invalidate authenticated queries
 * • Reset application state
 *
 * Components should never communicate with AuthService directly.
 *
 * ============================================================================
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createMutationOptions } from "@/lib/queryFactory";

import {
  invalidateAdministration,
  invalidateAuthentication,
  invalidateDashboard,
} from "@/lib/queryInvalidation";

import { authService } from "@/services/auth";

import storage from "@/lib/storage";

import { useAuthStore } from "@/store/authStore";
import { useShellStore } from "@/store/shellStore";

/* ============================================================================
 * Hook
 * ============================================================================
 */

export function useLogout() {
  const queryClient = useQueryClient();

  const logout = useAuthStore(
    (state) => state.logout,
  );

  const setSelectedBranch = useShellStore(
    (state) => state.setSelectedBranch,
  );

  return useMutation(
    createMutationOptions(
      async () => {
        /**
         * Even if the backend logout fails (for example because the
         * access token has already expired), the local session should
         * still be cleared.
         */
        try {
          await authService.logout();
        } finally {
          logout();

          storage.clearSession();

          setSelectedBranch(undefined);
        }
      },
      {
        onSettled: async () => {
          /**
           * Clear all authentication-dependent caches.
           */
          await invalidateAuthentication(
            queryClient,
          );

          await invalidateDashboard(
            queryClient,
          );

          await invalidateAdministration(
            queryClient,
          );

          /**
           * Remove any remaining cached data.
           */
          await queryClient.clear();
        },
      },
    ),
  );
}

export default useLogout;
