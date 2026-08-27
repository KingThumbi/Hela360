/**
 * ============================================================================
 * Hela360 Enterprise Authentication Constants
 * ============================================================================
 */

export const AUTH = {
  /**
   * Login route.
   */
  loginRoute: "/login",

  /**
   * Default authenticated landing page.
   */
  homeRoute: "/",

  /**
   * Token refresh endpoint.
   */
  refreshEndpoint: "/auth/refresh",

  /**
   * Current user endpoint.
   */
  meEndpoint: "/auth/me",
} as const;

export default AUTH;