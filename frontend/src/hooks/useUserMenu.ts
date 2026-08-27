import { useMemo } from "react";

import { useAuthStore } from "@/store/authStore";
import { useShellStore } from "@/store/shellStore";

import type {
  Identity,
  SessionRole,
} from "@/types/auth";

/**
 * ============================================================================
 * useUserMenu
 * ============================================================================
 *
 * Presentation adapter for the authenticated user menu.
 *
 * Identity answers who the authenticated user is.
 *
 * Tenant roles are supplied independently from the authenticated session and
 * must not be inferred from user identity fields, POS state, till state, or
 * permissions.
 * ============================================================================
 */

export interface UseUserMenuResult {
  identity: Identity | null;

  roles: SessionRole[];

  isAuthenticated: boolean;

  isOpen: boolean;

  open: () => void;

  close: () => void;

  toggle: () => void;

  logout: () => void;
}

export function useUserMenu(): UseUserMenuResult {
  const identity = useAuthStore(
    (state) => state.identity,
  );

  const roles = useAuthStore(
    (state) => state.roles,
  );

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated,
  );

  const logout = useAuthStore(
    (state) => state.logout,
  );

  const isOpen = useShellStore(
    (state) => state.userMenuOpen,
  );

  const open = useShellStore(
    (state) => state.openUserMenu,
  );

  const close = useShellStore(
    (state) => state.closeUserMenu,
  );

  const toggle = useShellStore(
    (state) => state.toggleUserMenu,
  );

  return useMemo(
    () => ({
      identity,
      roles,
      isAuthenticated,
      isOpen,
      open,
      close,
      toggle,
      logout,
    }),
    [
      identity,
      roles,
      isAuthenticated,
      isOpen,
      open,
      close,
      toggle,
      logout,
    ],
  );
}

export default useUserMenu;
