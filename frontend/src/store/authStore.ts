import { create } from "zustand";

import type { Branch, Tenant, User } from "@/types/auth";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;

  user: User | null;

  tenant: Tenant | null;

  branch: Branch | null;

  permissions: string[];

  isAuthenticated: boolean;

  setTokens: (access: string, refresh: string) => void;

  setUser: (user: User) => void;

  setTenant: (tenant: Tenant) => void;

  setBranch: (branch: Branch) => void;

  setPermissions: (permissions: string[]) => void;

  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,

  refreshToken: null,

  user: null,

  tenant: null,

  branch: null,

  permissions: [],

  isAuthenticated: false,

  setTokens: (access, refresh) =>
    set({
      accessToken: access,
      refreshToken: refresh,
      isAuthenticated: true,
    }),

  setUser: (user) =>
    set({
      user,
    }),

  setTenant: (tenant) =>
    set({
      tenant,
    }),

  setBranch: (branch) =>
    set({
      branch,
    }),

  setPermissions: (permissions) =>
    set({
      permissions,
    }),

  logout: () =>
    set({
      accessToken: null,
      refreshToken: null,
      user: null,
      tenant: null,
      branch: null,
      permissions: [],
      isAuthenticated: false,
    }),
}));