import { useContext } from "react";

import {
  ApplicationContext,
} from "./application-context";

import type {
  ApplicationContextValue,
} from "./ApplicationProvider";


export function useApplicationContext(): ApplicationContextValue {
  const context = useContext(
    ApplicationContext,
  );

  if (!context) {
    throw new Error(
      "useApplicationContext must be used within an ApplicationProvider.",
    );
  }

  return context;
}

export default useApplicationContext;