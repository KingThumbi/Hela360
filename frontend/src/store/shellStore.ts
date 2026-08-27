import { create } from "zustand";

export type ThemeMode = "light" | "dark" | "system";

export interface ShellState {
  /**
   * Sidebar
   */
  sidebarCollapsed: boolean;
  sidebarOpen: boolean;

  /**
   * Theme
   */
  theme: ThemeMode;

  /**
   * Global UI
   */
  commandPaletteOpen: boolean;
  notificationsOpen: boolean;
  userMenuOpen: boolean;

  /**
   * Context
   */
  selectedBranchId?: string;

  /**
   * Sidebar Actions
   */
  collapseSidebar: () => void;
  expandSidebar: () => void;
  toggleSidebar: () => void;
  openSidebar: () => void;
  closeSidebar: () => void;

  /**
   * Theme Actions
   */
  setTheme: (theme: ThemeMode) => void;

  /**
   * Command Palette
   */
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  toggleCommandPalette: () => void;

  /**
   * Notifications
   */
  openNotifications: () => void;
  closeNotifications: () => void;
  toggleNotifications: () => void;

  /**
   * User Menu
   */
  openUserMenu: () => void;
  closeUserMenu: () => void;
  toggleUserMenu: () =>void;

  /**
   * Branch
   */
  setSelectedBranch: (branchId?: string) => void;

  /**
   * Reset
   */
  resetShell: () => void;
}

const initialState = {
  sidebarCollapsed: false,
  sidebarOpen: false,

  theme: "system" as ThemeMode,

  commandPaletteOpen: false,
  notificationsOpen: false,
  userMenuOpen: false,

  selectedBranchId: undefined,
};

export const useShellStore = create<ShellState>((set) => ({
  ...initialState,

  collapseSidebar: () =>
    set({
      sidebarCollapsed: true,
    }),

  expandSidebar: () =>
    set({
      sidebarCollapsed: false,
    }),

  toggleSidebar: () =>
    set((state) => ({
      sidebarCollapsed: !state.sidebarCollapsed,
    })),

  openSidebar: () =>
    set({
      sidebarOpen: true,
    }),

  closeSidebar: () =>
    set({
      sidebarOpen: false,
    }),

  setTheme: (theme) =>
    set({
      theme,
    }),

  openCommandPalette: () =>
    set({
      commandPaletteOpen: true,
    }),

  closeCommandPalette: () =>
    set({
      commandPaletteOpen: false,
    }),

  toggleCommandPalette: () =>
    set((state) => ({
      commandPaletteOpen: !state.commandPaletteOpen,
    })),

  openNotifications: () =>
    set({
      notificationsOpen: true,
    }),

  closeNotifications: () =>
    set({
      notificationsOpen: false,
    }),

  toggleNotifications: () =>
    set((state) => ({
      notificationsOpen: !state.notificationsOpen,
    })),

  openUserMenu: () =>
    set({
      userMenuOpen: true,
    }),

  closeUserMenu: () =>
    set({
      userMenuOpen: false,
    }),

  toggleUserMenu: () =>
    set((state) => ({
      userMenuOpen: !state.userMenuOpen,
    })),

  setSelectedBranch: (branchId) =>
    set({
      selectedBranchId: branchId,
    }),

  resetShell: () =>
    set({
      ...initialState,
    }),
}));