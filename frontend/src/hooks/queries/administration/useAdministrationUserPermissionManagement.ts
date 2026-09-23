import {
  useQuery,
  type DefaultError,
  type UseQueryResult,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type AdministrationManagedPermission,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

export function useAdministrationUserPermissionManagement(
  userId: string | null | undefined,
): UseQueryResult<
  AdministrationManagedPermission[],
  DefaultError
> {
  return useQuery({
    queryKey:
      administrationQueryKeys.userPermissionManagement(
        userId ?? "",
      ),

    queryFn: () =>
      tenantAdministrationApi.getUserPermissions(
        userId as string,
      ),

    enabled: Boolean(userId),
  });
}

export default useAdministrationUserPermissionManagement;
