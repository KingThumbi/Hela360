import { useContext } from "react";

import {
  ShellContext,
} from "./shell-context";

import type {
  ShellContextValue,
} from "./ShellProvider";


export function useShell(): ShellContextValue {
  const context = useContext(
    ShellContext,
  );

  if (!context) {
    throw new Error(
      "useShell must be used within a ShellProvider.",
    );
  }

  return context;
}

export default useShell;