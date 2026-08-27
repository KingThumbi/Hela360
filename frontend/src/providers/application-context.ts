import { createContext } from "react";

import type {
  ApplicationContextValue,
} from "./ApplicationProvider";


export const ApplicationContext =
  createContext<ApplicationContextValue | null>(null);