import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  tenantAdministrationApi,
  type SetAdministrationUserPermissionRequest,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  administrationQueryKeys,
} from "./queryKeys";

interface SetUserPermissionVariables {
  userId: string;
  permissionCode: string;
  payload: SetAdministrationUserPermissionRequest;
}

export function useSetAdministrationUserPermission() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      userId,
      permissionCode,
      payload,
    }: SetUserPermissionVariables) =>
      tenantAdministrationApi.setUserPermission(
        userId,
        permissionCode,
        payload,
      ),

    onSuccess: async (_result, variables) => {
      const { userId } = variables;

      await Promise.all([
        queryClient.invalidateQueries({
          queryKey:
            administrationQueryKeys.userPermissions(
              userId,
            ),
        }),

        queryClient.invalidateQueries({
          queryKey:
            administrationQueryKeys.userPermissionManagement(
              userId,
            ),
        }),
      ]);
    },
  });
}

export default useSetAdministrationUserPermission;
