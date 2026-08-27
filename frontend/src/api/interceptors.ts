/**
 * ============================================================================
 * Hela360 Enterprise API Interceptors
 * ============================================================================
 *
 * Registers the application's HTTP request and response interceptors.
 *
 * Responsibilities
 * ----------------
 * • Attach authentication headers
 * • Attach tenant context
 * • Attach branch context
 * • Generate request correlation IDs
 * • Normalize API errors
 * • Coordinate token refresh
 * • Replay failed requests after refresh
 * • Invalidate expired sessions
 *
 * Business logic intentionally lives outside this module.
 *
 * Authentication lifecycle is delegated to:
 *
 *     api/refresh.ts
 *
 * ============================================================================
 */

import type {
  AxiosError,
  AxiosInstance,
  InternalAxiosRequestConfig,
} from "axios";
import { createClientId } from "@/lib/clientId";
import { API } from "@/constants";
import {
  invalidateSession,
  refreshAccessToken,
} from "@/api/refresh";
import { AppError } from "@/lib/errors";
import { storage } from "@/lib/storage";

/* ============================================================================
 * Header Names
 * ============================================================================
 */

const TENANT_HEADER = "X-Tenant-ID";

const BRANCH_HEADER = "X-Branch-ID";

const REQUEST_ID_HEADER = "X-Request-ID";

/* ============================================================================
 * Internal Types
 * ============================================================================
 */

interface RetryableRequestConfig
  extends InternalAxiosRequestConfig {
  /**
   * Prevents infinite refresh loops.
   */
  _retry?: boolean;
}

/* ============================================================================
 * Utilities
 * ============================================================================
 */

function createRequestId(): string {
  return createClientId();
}
/**
 * Enrich outgoing requests with authentication and context headers.
 */
function enrichRequest(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  const accessToken = storage.getAccessToken();

  const tenantId = storage.getTenantId();

  const branchId = storage.getBranchId();

  config.headers.set(
    REQUEST_ID_HEADER,
    createRequestId(),
  );

  if (accessToken) {
    config.headers.set(
      API.authorizationHeader,
      `${API.bearerPrefix} ${accessToken}`,
    );
  }

  if (tenantId) {
    config.headers.set(
      TENANT_HEADER,
      tenantId,
    );
  }

  if (branchId) {
    config.headers.set(
      BRANCH_HEADER,
      branchId,
    );
  }

  return config;
}

/* ============================================================================
 * Request Interceptors
 * ============================================================================
 */

function onRequest(
  config: InternalAxiosRequestConfig,
): InternalAxiosRequestConfig {
  return enrichRequest(config);
}

function onRequestError(
  error: unknown,
): Promise<never> {
  return Promise.reject(error);
}

/* ============================================================================
 * Response Interceptors
 * ============================================================================
 */

function onResponse<T>(
  response: T,
): T {
  return response;
}

async function onResponseError(
  client: AxiosInstance,
  error: AxiosError,
): Promise<never> {
  const response = error.response;

  const request =
    error.config as RetryableRequestConfig | undefined;

  /**
   * ------------------------------------------------------------------------
   * Authentication Recovery
   * ------------------------------------------------------------------------
   */

  if (
    response?.status === 401 &&
    request &&
    !request._retry
  ) {
    request._retry = true;

    try {
      const accessToken =
        await refreshAccessToken();

      request.headers.set(
        API.authorizationHeader,
        `${API.bearerPrefix} ${accessToken}`,
      );

      return client.request(request);
    } catch {
      invalidateSession();
    }
  }

  /**
   * ------------------------------------------------------------------------
   * Error Normalization
   * ------------------------------------------------------------------------
   */

  throw AppError.fromAxios(error);
}

/* ============================================================================
 * Registration
 * ============================================================================
 */

/**
 * Registers all enterprise HTTP interceptors.
 */
export function registerInterceptors(
  client: AxiosInstance,
): void {
  client.interceptors.request.use(
    onRequest,
    onRequestError,
  );

  client.interceptors.response.use(
    onResponse,
    (error) =>
      onResponseError(client, error),
  );
}

export default registerInterceptors;