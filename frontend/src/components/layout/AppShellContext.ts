import {
  createContext,
} from "react";

export interface AppShellContextValue {
  sidebarCollapsed: boolean;
  mobileSidebarOpen: boolean;

  toggleSidebar: () => void;

  setSidebarCollapsed: (
    collapsed: boolean,
  ) => void;

  openMobileSidebar: () => void;

  closeMobileSidebar: () => void;

  setMobileSidebarOpen: (
    open: boolean,
  ) => void;
}

export const AppShellContext =
  createContext<AppShellContextValue | null>(
    null,
  );
