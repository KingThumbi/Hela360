/**
 * ============================================================================
 * Hela360 Enterprise API Constants
 * ============================================================================
 *
 * Shared API configuration.
 *
 * These values are consumed by the API client and should never be duplicated.
 * ============================================================================
 */

export const API = {
  /**
   * Base URL.
   *
   * Provided by Vite.
   */
  baseUrl:
    import.meta.env.VITE_API_BASE_URL ??
    "/api",

  /**
   * HTTP request timeout (milliseconds).
   */
  timeout: 30_000,

  /**
   * JSON content type.
   */
  contentType: "application/json",

  /**
   * Authorization header.
   */
  authorizationHeader: "Authorization",

  /**
   * Bearer token prefix.
   */
  bearerPrefix: "Bearer",
} as const;

export default API;