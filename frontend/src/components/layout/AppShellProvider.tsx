import {
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AppShellContext,
  type AppShellContextValue,
} from "./AppShellContext";

export interface AppShellProviderProps {
  children: ReactNode;
}

export function AppShellProvider({
  children,
}: AppShellProviderProps) {
  const [
    sidebarCollapsed,
    setSidebarCollapsed,
  ] = useState(false);

  const [
    mobileSidebarOpen,
    setMobileSidebarOpen,
  ] = useState(false);

  const value =
    useMemo<AppShellContextValue>(
      () => ({
        sidebarCollapsed,
        mobileSidebarOpen,

        toggleSidebar: () =>
          setSidebarCollapsed(
            (current) => !current,
          ),

        setSidebarCollapsed,

        openMobileSidebar: () =>
          setMobileSidebarOpen(true),

        closeMobileSidebar: () =>
          setMobileSidebarOpen(false),

        setMobileSidebarOpen,
      }),
      [
        sidebarCollapsed,
        mobileSidebarOpen,
      ],
    );

  return (
    <AppShellContext.Provider
      value={value}
    >
      {children}
    </AppShellContext.Provider>
  );
}

export default AppShellProvider;
