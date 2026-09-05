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

import type {
  PlatformLoginRequest,
  PlatformLoginResult,
} from "@/types/platformAuth";

export function usePlatformLogin() {
  const establishSession =
    usePlatformAuthStore(
      (state) => state.establishSession,
    );

  return useMutation<
    PlatformLoginResult,
    Error,
    PlatformLoginRequest
  >({
    mutationFn: (credentials) =>
      platformAuthService.login(
        credentials,
      ),

    onSuccess: (result) => {
      platformAuthStorage.setTokens(
        result.accessToken,
        result.refreshToken,
      );

      establishSession(
        result.authenticatedSession,
        result.accessToken,
        result.refreshToken,
      );
    },
  });
}

export default usePlatformLogin;
