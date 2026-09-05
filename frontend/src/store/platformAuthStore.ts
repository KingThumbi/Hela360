/**
 * ============================================================================
 * Hela360 Platform Authentication Store
 * ============================================================================
 *
 * Authentication state for Hela360 Office.
 *
 * This store MUST remain independent of tenant AuthStore.
 * ============================================================================
 */

import { create } from "zustand";

import type {
  PlatformAuthenticatedSession,
  PlatformAuthorization,
  PlatformSession,
  PlatformUser,
} from "@/types/platformAuth";

export interface PlatformAuthState {
  user: PlatformUser | null;
  authorization: PlatformAuthorization | null;
  session: PlatformSession | null;

  accessToken: string | null;
  refreshToken: string | null;

  isAuthenticated: boolean;
  isLoading: boolean;
  isInitializing: boolean;
}

export interface PlatformAuthActions {
  establishSession: (
    authenticatedSession: PlatformAuthenticatedSession,
    accessToken: string,
    refreshToken: string,
  ) => void;

  hydrateSession: (
    authenticatedSession: PlatformAuthenticatedSession,
    accessToken: string,
    refreshToken: string,
  ) => void;

  setTokens: (
    accessToken: string,
    refreshToken: string,
  ) => void;

  setLoading: (
    loading: boolean,
  ) => void;

  setInitializing: (
    initializing: boolean,
  ) => void;

  reset: () => void;
}

export type PlatformAuthStore =
  PlatformAuthState &
  PlatformAuthActions;

const initialState: PlatformAuthState = {
  user: null,
  authorization: null,
  session: null,

  accessToken: null,
  refreshToken: null,

  isAuthenticated: false,
  isLoading: false,
  isInitializing: true,
};

export const usePlatformAuthStore =
  create<PlatformAuthStore>((set) => ({
    ...initialState,

    establishSession: (
      authenticatedSession,
      accessToken,
      refreshToken,
    ) =>
      set({
        user: authenticatedSession.user,
        authorization:
          authenticatedSession.authorization,
        session: authenticatedSession.session,

        accessToken,
        refreshToken,

        isAuthenticated: true,
        isLoading: false,
        isInitializing: false,
      }),

    hydrateSession: (
      authenticatedSession,
      accessToken,
      refreshToken,
    ) =>
      set({
        user: authenticatedSession.user,
        authorization:
          authenticatedSession.authorization,
        session: authenticatedSession.session,

        accessToken,
        refreshToken,

        isAuthenticated: true,
        isLoading: false,
        isInitializing: false,
      }),

    setTokens: (
      accessToken,
      refreshToken,
    ) =>
      set((state) => ({
        ...state,

        accessToken,
        refreshToken,

        isAuthenticated:
          state.user !== null &&
          state.session !== null,
      })),

    setLoading: (loading) =>
      set({
        isLoading: loading,
      }),

    setInitializing: (initializing) =>
      set({
        isInitializing: initializing,
      }),

    reset: () =>
      set({
        ...initialState,
        isInitializing: false,
      }),
  }));

export default usePlatformAuthStore;
