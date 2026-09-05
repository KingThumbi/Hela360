/**
 * ============================================================================
 * Hela360 Platform Token Refresh
 * ============================================================================
 *
 * Refreshes Hela360 Office credentials independently of tenant credentials.
 * ============================================================================
 */

import axios, {
  type AxiosInstance,
} from "axios";

import { API } from "@/constants";
import { PLATFORM_AUTH_ENDPOINTS } from "@/api/platformAuthEndpoints";
import { platformAuthStorage } from "@/lib/platformAuthStorage";
import { usePlatformAuthStore } from "@/store/platformAuthStore";

import type {
  PlatformRefreshResponse,
} from "@/types/platformAuth";

let refreshPromise: Promise<string> | null = null;

const platformRefreshClient: AxiosInstance =
  axios.create({
    baseURL: API.baseUrl,

    timeout: API.timeout,

    headers: {
      Accept: API.contentType,
      "Content-Type": API.contentType,
    },

    withCredentials: false,
    responseType: "json",
  });

async function performPlatformRefresh():
  Promise<string> {
  const refreshToken =
    platformAuthStorage.getRefreshToken();

  if (!refreshToken) {
    throw new Error(
      "Missing Platform refresh token.",
    );
  }

  const response =
    await platformRefreshClient
      .post<PlatformRefreshResponse>(
        PLATFORM_AUTH_ENDPOINTS.REFRESH,
        {
          refresh_token: refreshToken,
        },
      );

  const tokens = response.data;

  platformAuthStorage.setTokens(
    tokens.access_token,
    tokens.refresh_token,
  );

  usePlatformAuthStore
    .getState()
    .setTokens(
      tokens.access_token,
      tokens.refresh_token,
    );

  return tokens.access_token;
}

export async function refreshPlatformAccessToken():
  Promise<string> {
  if (!refreshPromise) {
    refreshPromise =
      performPlatformRefresh().finally(
        () => {
          refreshPromise = null;
        },
      );
  }

  return refreshPromise;
}

export function invalidatePlatformSession(): void {
  platformAuthStorage.clearTokens();

  usePlatformAuthStore
    .getState()
    .reset();
}

export default refreshPlatformAccessToken;
