import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type AdministrationPermission,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

export function useAdministrationUserPermissions(
  userId: string | null | undefined,
): UseQueryResult<
  AdministrationPermission[],
  DefaultError
> {
  return useQuery({
    queryKey:
      administrationQueryKeys.userPermissions(
        userId ?? "",
      ),
    queryFn: () =>
      tenantAdministrationApi.getUserEffectivePermissions(
        userId as string,
      ),
    enabled: Boolean(userId),
  });
}

export default useAdministrationUserPermissions;
