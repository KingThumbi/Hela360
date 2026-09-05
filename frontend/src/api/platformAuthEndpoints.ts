/**
 * Hela360 Office authentication endpoints.
 */

export const PLATFORM_AUTH_ENDPOINTS = {
  LOGIN: "/platform-auth/login",
  REFRESH: "/platform-auth/refresh",
  LOGOUT: "/platform-auth/logout",
  LOGOUT_ALL: "/platform-auth/logout-all",
  SESSION: "/platform-auth/session",
} as const;

export default PLATFORM_AUTH_ENDPOINTS;
