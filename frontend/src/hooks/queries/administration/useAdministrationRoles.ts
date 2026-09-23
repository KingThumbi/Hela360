import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type AdministrationRole,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

export function useAdministrationRoles(): UseQueryResult<
  AdministrationRole[],
  DefaultError
> {
  return useQuery({
    queryKey: administrationQueryKeys.roles(),
    queryFn: () => tenantAdministrationApi.listRoles(),
  });
}

export default useAdministrationRoles;
