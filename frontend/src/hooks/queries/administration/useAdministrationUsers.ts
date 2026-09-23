import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type AdministrationUser,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

export function useAdministrationUsers(): UseQueryResult<
  AdministrationUser[],
  DefaultError
> {
  return useQuery({
    queryKey: administrationQueryKeys.users(),
    queryFn: () => tenantAdministrationApi.listUsers(),
  });
}

export default useAdministrationUsers;
