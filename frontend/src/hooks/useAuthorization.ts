import { useContext } from "react";

import {
  AuthorizationContext,
  type AuthorizationContextValue,
} from "@/providers/AuthorizationProvider";

export function useAuthorization(): AuthorizationContextValue {
  const context = useContext(AuthorizationContext);

  if (!context) {
    throw new Error(
      "useAuthorization must be used within an AuthorizationProvider.",
    );
  }

  return context;
}

export default useAuthorization;

