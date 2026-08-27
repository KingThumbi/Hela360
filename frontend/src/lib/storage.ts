/**
 * ============================================================================
 * Hela360 Enterprise Storage Service
 * ============================================================================
 *
 * Centralized application storage abstraction.
 *
 * Responsibilities
 * ----------------
 * • Persist authentication tokens
 * • Persist shell preferences
 * • Persist tenant context
 * • Persist branch context
 * • Persist user preferences
 * • Abstract the underlying browser storage implementation
 *
 * Components, hooks, stores and services must never access browser storage
 * directly. All persistence should flow through this service.
 *
 * Future Storage Providers
 * ------------------------
 * • Local Storage
 * • Session Storage
 * • Secure Cookies
 * • IndexedDB
 * • Electron Storage
 * ============================================================================
 */

import { STORAGE } from "@/constants";
import type { ThemeMode } from "@/store/shellStore";

/* ============================================================================
 * Storage Adapter
 * ============================================================================
 */

/**
 * Abstraction over the underlying browser storage mechanism.
 */
export interface StorageAdapter {
  getItem(key: string): string | null;

  setItem(
    key: string,
    value: string,
  ): void;

  removeItem(key: string): void;

  clear(): void;
}

/**
 * LocalStorage adapter.
 */
export class LocalStorageAdapter
  implements StorageAdapter
{
  getItem(
    key: string,
  ): string | null {
    return window.localStorage.getItem(key);
  }

  setItem(
    key: string,
    value: string,
  ): void {
    window.localStorage.setItem(key, value);
  }

  removeItem(key: string): void {
    window.localStorage.removeItem(key);
  }

  clear(): void {
    window.localStorage.clear();
  }
}

/* ============================================================================
 * Storage Service
 * ============================================================================
 */

export class StorageService {
  private readonly adapter: StorageAdapter;

  constructor(adapter: StorageAdapter) {
    this.adapter = adapter;
  }

  /* ------------------------------------------------------------------------
   * Generic Helpers
   * ------------------------------------------------------------------------
   */

  get<T>(key: string): T | null {
    const value = this.adapter.getItem(key);

    if (value === null) {
      return null;
    }

    try {
      return JSON.parse(value) as T;
    } catch {
      return value as T;
    }
  }

  set<T>(
    key: string,
    value: T,
  ): void {
    if (typeof value === "string") {
      this.adapter.setItem(key, value);

      return;
    }

    this.adapter.setItem(
      key,
      JSON.stringify(value),
    );
  }

  remove(key: string): void {
    this.adapter.removeItem(key);
  }

  clear(): void {
    this.adapter.clear();
  }

  /* ------------------------------------------------------------------------
   * Authentication
   * ------------------------------------------------------------------------
   */

  getAccessToken(): string | null {
    return this.get<string>(
      STORAGE.ACCESS_TOKEN,
    );
  }

  setAccessToken(
    token: string,
  ): void {
    this.set(
      STORAGE.ACCESS_TOKEN,
      token,
    );
  }

  removeAccessToken(): void {
    this.remove(
      STORAGE.ACCESS_TOKEN,
    );
  }

  getRefreshToken(): string | null {
    return this.get<string>(
      STORAGE.REFRESH_TOKEN,
    );
  }

  setRefreshToken(
    token: string,
  ): void {
    this.set(
      STORAGE.REFRESH_TOKEN,
      token,
    );
  }

  removeRefreshToken(): void {
    this.remove(
      STORAGE.REFRESH_TOKEN,
    );
  }

  clearTokens(): void {
    this.removeAccessToken();

    this.removeRefreshToken();
  }

  /* ------------------------------------------------------------------------
   * Theme
   * ------------------------------------------------------------------------
   */

  getTheme(): ThemeMode | null {
    return this.get<ThemeMode>(
      STORAGE.THEME,
    );
  }

  setTheme(
    theme: ThemeMode,
  ): void {
    this.set(
      STORAGE.THEME,
      theme,
    );
  }

  /* ------------------------------------------------------------------------
   * Sidebar
   * ------------------------------------------------------------------------
   */

  isSidebarCollapsed(): boolean {
    return (
      this.get<boolean>(
        STORAGE.SIDEBAR_COLLAPSED,
      ) ?? false
    );
  }

  setSidebarCollapsed(
    collapsed: boolean,
  ): void {
    this.set(
      STORAGE.SIDEBAR_COLLAPSED,
      collapsed,
    );
  }

  /* ------------------------------------------------------------------------
   * Tenant
   * ------------------------------------------------------------------------
   */

  getTenantId(): string | null {
    return this.get<string>(
      STORAGE.TENANT_ID,
    );
  }

  setTenantId(
    tenantId: string,
  ): void {
    this.set(
      STORAGE.TENANT_ID,
      tenantId,
    );
  }

  removeTenantId(): void {
    this.remove(
      STORAGE.TENANT_ID,
    );
  }

  /* ------------------------------------------------------------------------
   * Branch
   * ------------------------------------------------------------------------
   */

  getBranchId(): string | null {
    return this.get<string>(
      STORAGE.BRANCH_ID,
    );
  }

  setBranchId(
    branchId: string,
  ): void {
    this.set(
      STORAGE.BRANCH_ID,
      branchId,
    );
  }

  removeBranchId(): void {
    this.remove(
      STORAGE.BRANCH_ID,
    );
  }

  /* ------------------------------------------------------------------------
   * Remember Me
   * ------------------------------------------------------------------------
   */

  getRememberMe(): boolean {
    return (
      this.get<boolean>(
        STORAGE.REMEMBER_ME,
      ) ?? false
    );
  }

  setRememberMe(
    remember: boolean,
  ): void {
    this.set(
      STORAGE.REMEMBER_ME,
      remember,
    );
  }

  /* ------------------------------------------------------------------------
   * Session
   * ------------------------------------------------------------------------
   */

  /**
   * Clears all authentication and tenant-specific session data while
   * preserving user interface preferences such as theme and sidebar state.
   */
  clearSession(): void {
    this.clearTokens();

    this.removeTenantId();

    this.removeBranchId();
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

/**
 * Shared application storage service.
 */
export const storage = new StorageService(
  new LocalStorageAdapter(),
);

export default storage;
