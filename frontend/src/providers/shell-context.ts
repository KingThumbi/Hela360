import { createContext } from "react";

import type {
  ShellContextValue,
} from "./ShellProvider";


export const ShellContext =
  createContext<ShellContextValue | null>(null);