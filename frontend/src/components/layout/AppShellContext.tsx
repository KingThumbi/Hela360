import {
  createContext,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

interface AppShellContextValue {
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

const AppShellContext =
  createContext<AppShellContextValue | null>(
    null,
  );

interface AppShellProviderProps {
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

  const value = useMemo<AppShellContextValue>(
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
    <AppShellContext.Provider value={value}>
      {children}
    </AppShellContext.Provider>
  );
}

export function useAppShell() {
  const context = useContext(
    AppShellContext,
  );

  if (!context) {
    throw new Error(
      "useAppShell must be used within AppShellProvider.",
    );
  }

  return context;
}
