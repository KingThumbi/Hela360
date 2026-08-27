/**
 * ============================================================================
 * Hela360 Enterprise Token Refresh Service
 * ============================================================================
 *
 * Handles automatic JWT refresh and request replay.
 *
 * Responsibilities
 * ----------------
 * • Refresh expired access tokens
 * • Prevent duplicate refresh requests
 * • Queue concurrent requests during refresh
 * • Persist new tokens
 * • Logout when refresh fails
 *
 * This service is intentionally isolated from the Axios interceptors to keep
 * the HTTP pipeline maintainable and testable.
 *
 * ============================================================================
 */

import axios, {
  type AxiosInstance,
} from "axios";

import { API } from "@/constants";
import { API_ENDPOINTS } from "@/api/endpoints";
import { storage } from "@/lib/storage";
import { useAuthStore } from "@/store/authStore";
import { useShellStore } from "@/store/shellStore";

interface RefreshResponse {
  access_token: string;

  refresh_token: string;

  token_type: string;
}

let refreshPromise: Promise<string> | null = null;

/**
 * Dedicated client without interceptors.
 *
 * Prevents recursive refresh requests.
 */
const refreshClient: AxiosInstance = axios.create({
  baseURL: API.baseUrl,

  timeout: API.timeout,

  headers: {
    Accept: API.contentType,

    "Content-Type": API.contentType,
  },
});

/**
 * Refresh the current session.
 */
async function performRefresh(): Promise<string> {
  const refreshToken =
    storage.getRefreshToken();

  if (!refreshToken) {
    throw new Error(
      "Missing refresh token.",
    );
  }

  const response =
    await refreshClient.post<RefreshResponse>(
      API_ENDPOINTS.AUTH.REFRESH,
      {
        refresh_token: refreshToken,
      },
    );

  const tokens = response.data;

  storage.setAccessToken(
    tokens.access_token,
  );

  storage.setRefreshToken(
    tokens.refresh_token,
  );

  useAuthStore
    .getState()
    .setTokens(
      tokens.access_token,
      tokens.refresh_token,
    );

  return tokens.access_token;
}

/**
 * Refresh once, regardless of how many requests fail simultaneously.
 */
export async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = performRefresh().finally(
      () => {
        refreshPromise = null;
      },
    );
  }

  return refreshPromise;
}

/**
 * Destroy the authenticated session.
 */
export function invalidateSession(): void {
  storage.clearSession();

  useAuthStore.getState().logout();

  useShellStore
    .getState()
    .setSelectedBranch(undefined);
}

export default refreshAccessToken;
