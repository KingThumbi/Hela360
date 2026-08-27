/**
 * ============================================================================
 * Hela360 Enterprise API Client
 * ============================================================================
 *
 * Centralized HTTP client for the Hela360 frontend.
 *
 * Responsibilities
 * ----------------
 * • Create the application's Axios instance
 * • Apply enterprise HTTP defaults
 * • Register request/response interceptors
 * • Expose a singleton API client
 *
 * This is the only HTTP client that should be used throughout the application.
 *
 * Authentication, tenant resolution, branch resolution and token refresh are
 * delegated to dedicated infrastructure modules.
 *
 * ============================================================================
 */

import axios, {
  type AxiosInstance,
} from "axios";

import { API } from "@/constants";
import { registerInterceptors } from "@/api/interceptors";

/* ============================================================================
 * Axios Client
 * ============================================================================
 */

const apiClient: AxiosInstance = axios.create({
  /**
   * Base API URL.
   */
  baseURL: API.baseUrl,

  /**
   * Request timeout.
   */
  timeout: API.timeout,

  /**
   * Default headers.
   */
  headers: {
    Accept: API.contentType,

    "Content-Type": API.contentType,
  },

  /**
   * Authentication uses Bearer tokens rather than cookies.
   */
  withCredentials: false,

  /**
   * Axios automatically parses JSON responses.
   */
  responseType: "json",
});

/* ============================================================================
 * Enterprise Interceptors
 * ============================================================================
 *
 * Responsibilities delegated to the interceptor layer:
 *
 * • Authorization header
 * • Tenant context
 * • Branch context
 * • Correlation IDs
 * • Automatic token refresh
 * • Request replay
 * • Session invalidation
 * • Error normalization
 */

registerInterceptors(apiClient);

/* ============================================================================
 * Public API
 * ============================================================================
 */

/**
 * Singleton enterprise HTTP client.
 */
export { apiClient };

/**
 * Default export for convenience.
 */
export default apiClient;