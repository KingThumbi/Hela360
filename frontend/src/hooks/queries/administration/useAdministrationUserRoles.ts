import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type AdministrationUserRole,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

export function useAdministrationUserRoles(
  userId: string | null | undefined,
): UseQueryResult<
  AdministrationUserRole[],
  DefaultError
> {
  return useQuery({
    queryKey: administrationQueryKeys.userRoles(
      userId ?? "",
    ),
    queryFn: () =>
      tenantAdministrationApi.getUserRoles(
        userId as string,
      ),
    enabled: Boolean(userId),
  });
}

export default useAdministrationUserRoles;
