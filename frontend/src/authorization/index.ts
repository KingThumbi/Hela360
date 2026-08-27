export {
  can,
  canAll,
  canAny,
  cannot,
} from "./authorizationService";

export type {
  PermissionCollection,
} from "./authorizationService";

export {
  useAuthorization,
  default as useAuthorizationDefault,
} from "@/hooks/useAuthorization";

export type {
  AuthorizationContextValue,
} from "@/providers/AuthorizationProvider";
