/**
 * ============================================================================
 * Hela360 Enterprise Authentication Store
 * ============================================================================
 *
 * Centralized authentication state.
 *
 * Responsibilities
 * ----------------
 * • Store authenticated identity
 * • Store authentication tokens
 * • Track authentication status
 * • Track authentication loading state
 * • Support session hydration
 * • Support session reset
 * • Expose lightweight selector hooks
 *
 * This store is the single source of truth for the authenticated session.
 * Persistent storage is handled separately by StorageService.
 *
 * ============================================================================
 */

import { create } from "zustand";

import type {
  AuthenticatedSession,
  Branch,
  Identity,
  SessionRole,
} from "@/types/auth";

/* ============================================================================
 * State
 * ============================================================================
 */

export interface AuthState {
  /**
   * Current authenticated identity.
   */
  identity: Identity | null;

  /**
   * Branches accessible in the authenticated session.
   */
  accessibleBranches: Branch[];

  /**
   * Session roles. Inert until Authorization Context is implemented.
   */
  roles: SessionRole[];

  /**
   * Effective permissions. Inert until Authorization Context is implemented.
   */
  permissions: string[];

  /**
   * Verified default branch, when the backend provides one.
   */
  defaultBranchId: string | null;

  /**
   * Current JWT access token.
   */
  accessToken: string | null;

  /**
   * Current JWT refresh token.
   */
  refreshToken: string | null;

  /**
   * Indicates whether an authenticated session exists.
   */
  isAuthenticated: boolean;

  /**
   * Authentication loading state.
   */
  isLoading: boolean;

  /**
   * Indicates whether persisted authentication state is being restored.
   */
  isInitializing: boolean;
}

/* ============================================================================
 * Actions
 * ============================================================================
 */

export interface AuthActions {
  /**
   * Establishes an authenticated session.
   */
  login: (
    identity: Identity,
    accessToken: string,
    refreshToken: string,
  ) => void;

  /**
   * Restores a previously authenticated session.
   *
   * Used during application startup.
   */
  hydrate: (
    identity: Identity,
    accessToken: string,
    refreshToken: string,
  ) => void;

  /**
   * Hydrates a verified authenticated session.
   */
  hydrateSession: (
    session: AuthenticatedSession,
    accessToken: string,
    refreshToken: string,
  ) => void;

  /**
   * Updates the authenticated identity without modifying tokens.
   */
  updateIdentity: (
    identity: Identity,
  ) => void;

  /**
   * Updates authentication tokens.
   */
  setTokens: (
    accessToken: string,
    refreshToken: string,
  ) => void;

  /**
   * Updates loading state.
   */
  setLoading: (
    loading: boolean,
  ) => void;

  /**
   * Updates authentication initialization state.
   */
  setInitializing: (
    initializing: boolean,
  ) => void;

  /**
   * Clears all authentication state.
   */
  reset: () => void;

  /**
   * Terminates the authenticated session.
   */
  logout: () => void;
}

/* ============================================================================
 * Store Type
 * ============================================================================
 */

export type AuthStore = AuthState &
  AuthActions;

/* ============================================================================
 * Initial State
 * ============================================================================
 */

const initialState: AuthState = {
  identity: null,

  accessibleBranches: [],

  roles: [],

  permissions: [],

  defaultBranchId: null,

  accessToken: null,

  refreshToken: null,

  isAuthenticated: false,

  isLoading: false,

  isInitializing: true,
};

/* ============================================================================
 * Store
 * ============================================================================
 */

export const useAuthStore =
  create<AuthStore>((set) => ({
    ...initialState,

    login: (
      identity,
      accessToken,
      refreshToken,
    ) =>
      set({
        identity,
        accessToken,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
        isInitializing: false,
      }),

    hydrate: (
      identity,
      accessToken,
      refreshToken,
    ) =>
      set({
        identity,
        accessibleBranches: [],
        roles: [],
        permissions: [],
        defaultBranchId: null,
        accessToken,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
        isInitializing: false,
      }),

    hydrateSession: (
      session,
      accessToken,
      refreshToken,
    ) =>
      set({
        identity: session.identity,
        accessibleBranches: session.branches,
        roles: session.roles,
        permissions: session.permissions,
        defaultBranchId: session.defaultBranchId,
        accessToken,
        refreshToken,
        isAuthenticated: true,
        isLoading: false,
        isInitializing: false,
      }),

    updateIdentity: (identity) =>
      set({
        identity,
        isAuthenticated: identity !== null,
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
        isAuthenticated: true,
        isInitializing: state.isInitializing,
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

    logout: () =>
      set({
        ...initialState,
        isInitializing: false,
      }),
  }));

/* ============================================================================
 * Enterprise Selectors
 * ============================================================================
 *
 * Components should subscribe only to the state they require.
 * This minimizes unnecessary re-renders and improves scalability.
 * ============================================================================
 */

export const useIdentity = () =>
  useAuthStore((state) => state.identity);

export const useAccessToken = () =>
  useAuthStore(
    (state) => state.accessToken,
  );

export const useRefreshToken = () =>
  useAuthStore(
    (state) => state.refreshToken,
  );

export const useIsAuthenticated =
  () =>
    useAuthStore(
      (state) => state.isAuthenticated,
    );

export const useAuthLoading = () =>
  useAuthStore(
    (state) => state.isLoading,
  );

/* ============================================================================
 * Export
 * ============================================================================
 */

export default useAuthStore;
