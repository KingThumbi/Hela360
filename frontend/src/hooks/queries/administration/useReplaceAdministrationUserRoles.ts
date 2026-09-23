import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type ReplaceAdministrationUserRolesRequest,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

interface ReplaceUserRolesVariables {
  userId: string;
  payload: ReplaceAdministrationUserRolesRequest;
}

export function useReplaceAdministrationUserRoles() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      payload,
    }: ReplaceUserRolesVariables) =>
      tenantAdministrationApi.replaceUserRoles(
        userId,
        payload,
      ),

    onSuccess: async (_result, variables) => {
      const { userId } = variables;

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            administrationQueryKeys.users(),
        }),

        queryClient.invalidateQueries({
          queryKey:
            administrationQueryKeys.user(userId),
        }),

        queryClient.invalidateQueries({
          queryKey:
            administrationQueryKeys.userRoles(
              userId,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            administrationQueryKeys.userPermissions(
              userId,
            ),
        }),
      ]);
    },
  });
}

export default useReplaceAdministrationUserRoles;
