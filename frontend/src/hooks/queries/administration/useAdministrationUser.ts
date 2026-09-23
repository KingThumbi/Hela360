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

export function useAdministrationUser(
  userId: string | null | undefined,
): UseQueryResult<
  AdministrationUser,
  DefaultError
> {
  return useQuery({
    queryKey: administrationQueryKeys.user(
      userId ?? "",
    ),
    queryFn: () =>
      tenantAdministrationApi.getUser(
        userId as string,
      ),
    enabled: Boolean(userId),
  });
}

export default useAdministrationUser;
