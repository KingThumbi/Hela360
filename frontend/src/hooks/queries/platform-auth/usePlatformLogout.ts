import { useMutation } from "@tanstack/react-query";

import {
  platformAuthStorage,
} from "@/lib/platformAuthStorage";

import {
  platformAuthService,
} from "@/services/platform-auth";

import {
  usePlatformAuthStore,
} from "@/store/platformAuthStore";

export function usePlatformLogout() {
  const refreshToken =
    usePlatformAuthStore(
      (state) => state.refreshToken,
    );

  const reset =
    usePlatformAuthStore(
      (state) => state.reset,
    );

  return useMutation<void, Error>({
    mutationFn: async () => {
      if (!refreshToken) {
        return;
      }

      await platformAuthService.logout(
        refreshToken,
      );
    },

    onSettled: () => {
      platformAuthStorage.clearTokens();
      reset();
    },
  });
}

export default usePlatformLogout;
