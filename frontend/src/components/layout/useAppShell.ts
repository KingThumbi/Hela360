import {
  useContext,
} from "react";

import {
  AppShellContext,
} from "./AppShellContext";

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

export default useAppShell;
