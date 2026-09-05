/**
 * ============================================================================
 * Hela360 Platform Authentication Storage
 * ============================================================================
 *
 * Persists Hela360 Office credentials independently of tenant ERP credentials.
 * ============================================================================
 */

import { STORAGE } from "@/constants";
import { storage } from "@/lib/storage";

export const platformAuthStorage = {
  getAccessToken(): string | null {
    return storage.get<string>(
      STORAGE.PLATFORM_ACCESS_TOKEN,
    );
  },

  setAccessToken(token: string): void {
    storage.set(
      STORAGE.PLATFORM_ACCESS_TOKEN,
      token,
    );
  },

  removeAccessToken(): void {
    storage.remove(
      STORAGE.PLATFORM_ACCESS_TOKEN,
    );
  },

  getRefreshToken(): string | null {
    return storage.get<string>(
      STORAGE.PLATFORM_REFRESH_TOKEN,
    );
  },

  setRefreshToken(token: string): void {
    storage.set(
      STORAGE.PLATFORM_REFRESH_TOKEN,
      token,
    );
  },

  removeRefreshToken(): void {
    storage.remove(
      STORAGE.PLATFORM_REFRESH_TOKEN,
    );
  },

  setTokens(
    accessToken: string,
    refreshToken: string,
  ): void {
    this.setAccessToken(accessToken);
    this.setRefreshToken(refreshToken);
  },

  clearTokens(): void {
    this.removeAccessToken();
    this.removeRefreshToken();
  },
};

export default platformAuthStorage;
