/**
 * ============================================================================
 * Hela360 Platform API Interceptors
 * ============================================================================
 *
 * HTTP authentication boundary for Hela360 Office.
 *
 * Platform requests MUST NOT carry tenant or branch context headers.
 * ============================================================================
 */

import type {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from "axios";

import { API } from "@/constants";
import { createClientId } from "@/lib/clientId";
import { AppError } from "@/lib/errors";
import { platformAuthStorage } from "@/lib/platformAuthStorage";
import {
  invalidatePlatformSession,
  refreshPlatformAccessToken,
} from "@/api/platformRefresh";

const REQUEST_ID_HEADER =
  "X-Request-ID";

interface RetryablePlatformRequest
  extends InternalAxiosRequestConfig {
  _platformRetry?: boolean;
}

function enrichPlatformRequest(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  const accessToken =
    platformAuthStorage.getAccessToken();

  config.headers.set(
    REQUEST_ID_HEADER,
    createClientId(),
  );

  if (accessToken) {
    config.headers.set(
      API.authorizationHeader,
      `${API.bearerPrefix} ${accessToken}`,
    );
  }

  return config;
}

async function onPlatformResponseError(
  client: AxiosInstance,
  error: AxiosError,
): Promise<never> {
  const response = error.response;

  const request =
    error.config as
      | RetryablePlatformRequest
      | undefined;

  if (
    response?.status === 401 &&
    request &&
    !request._platformRetry
  ) {
    request._platformRetry = true;

    try {
      const accessToken =
        await refreshPlatformAccessToken();

      request.headers.set(
        API.authorizationHeader,
        `${API.bearerPrefix} ${accessToken}`,
      );

      return client.request(request);
    } catch {
      invalidatePlatformSession();
    }
  }

  throw AppError.fromAxios(error);
}

export function registerPlatformInterceptors(
  client: AxiosInstance,
): void {
  client.interceptors.request.use(
    enrichPlatformRequest,
    (error) => Promise.reject(error),
  );

  client.interceptors.response.use(
    (response) => response,
    (error) =>
      onPlatformResponseError(
        client,
        error,
      ),
  );
}

export default registerPlatformInterceptors;
