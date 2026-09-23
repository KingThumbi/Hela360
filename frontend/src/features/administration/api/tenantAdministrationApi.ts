/**
 * ============================================================================
 * Hela360 Tenant Administration API
 * ============================================================================
 *
 * Tenant ERP administration boundary.
 *
 * IMPORTANT:
 * - This module manages tenant User / Role / Permission projections only.
 * - It must never use Hela360 Office PlatformUser / PlatformRole APIs.
 * - Tenant scope and actor identity are resolved by the backend session.
 * - The frontend must never send tenant_id or actor_user_id.
 *
 * Backend namespace:
 *   /administration/users
 *   /administration/roles
 *
 * ============================================================================
 */

import apiClient from "@/api/client";

/* ============================================================================
 * Backend projections
 * ============================================================================
 */

export interface AdministrationUser {
  id: string;
  username: string;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;

  tenant_id?: string;
  branch_id: string | null;

  is_owner: boolean;
  is_active: boolean;

  created_at?: string | null;
  updated_at?: string | null;
}

export interface AdministrationUserRole {
  id: string;
  code: string;
  name: string;
  is_system: boolean;
}

export interface AdministrationRole {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_system: boolean;
}

export interface AdministrationPermission {
  id: string;
  code: string;

  name?: string | null;
  description?: string | null;
  module_code?: string | null;
}

export type AdministrationPermissionOverrideEffect =
  | "allow"
  | "deny";

export type AdministrationPermissionSource =
  | "role"
  | "direct_allow"
  | "direct_deny"
  | "implied"
  | "none";

export interface AdministrationManagedPermission {
  id: string;
  code: string;
  name: string | null;
  description: string | null;
  module: string | null;

  role_inherited: boolean;
  override_effect:
    | AdministrationPermissionOverrideEffect
    | null;
  effective: boolean;
  source: AdministrationPermissionSource;
}

export interface SetAdministrationUserPermissionRequest {
  effect: "allow" | "deny" | "inherit";
  reason?: string;
}

export interface SetAdministrationUserPermissionResult {
  user_id: string;
  permission_id: string;
  permission_code: string;
  previous_effect:
    | AdministrationPermissionOverrideEffect
    | null;
  effect:
    | AdministrationPermissionOverrideEffect
    | null;
  changed: boolean;
}

export interface ReplaceAdministrationUserRolesRequest {
  role_ids: string[];
  reason?: string;
}

export interface ReplaceAdministrationUserRolesResult {
  user_id: string;
  role_ids: string[];
  added_role_ids: string[];
  removed_role_ids: string[];
  changed: boolean;
}

/* ============================================================================
 * Response envelopes
 * ============================================================================
 */

interface ItemResponse<T> {
  ok: true;
  item: T;
}

interface ItemsResponse<T> {
  ok: true;
  items: T[];
}

/* ============================================================================
 * Endpoints
 * ============================================================================
 */

const ADMINISTRATION_ROOT = "/administration";

const endpoints = {
  users: `${ADMINISTRATION_ROOT}/users`,
  user: (userId: string) =>
    `${ADMINISTRATION_ROOT}/users/${encodeURIComponent(userId)}`,

  userRoles: (userId: string) =>
    `${ADMINISTRATION_ROOT}/users/${encodeURIComponent(userId)}/roles`,

  userEffectivePermissions: (userId: string) =>
    `${ADMINISTRATION_ROOT}/users/${encodeURIComponent(
      userId,
    )}/effective-permissions`,

  userPermissions: (userId: string) =>
    `${ADMINISTRATION_ROOT}/users/${encodeURIComponent(
      userId,
    )}/permissions`,

  userPermission: (
    userId: string,
    permissionCode: string,
  ) =>
    `${ADMINISTRATION_ROOT}/users/${encodeURIComponent(
      userId,
    )}/permissions/${encodeURIComponent(
      permissionCode,
    )}`,

  roles: `${ADMINISTRATION_ROOT}/roles`,
} as const;

/* ============================================================================
 * API
 * ============================================================================
 */

export const tenantAdministrationApi = {
  async listUsers(): Promise<AdministrationUser[]> {
    const response =
      await apiClient.get<ItemsResponse<AdministrationUser>>(
        endpoints.users,
      );

    return response.data.items;
  },

  async getUser(
    userId: string,
  ): Promise<AdministrationUser> {
    const response =
      await apiClient.get<ItemResponse<AdministrationUser>>(
        endpoints.user(userId),
      );

    return response.data.item;
  },

  async getUserRoles(
    userId: string,
  ): Promise<AdministrationUserRole[]> {
    const response =
      await apiClient.get<
        ItemsResponse<AdministrationUserRole>
      >(
        endpoints.userRoles(userId),
      );

    return response.data.items;
  },

  async getUserEffectivePermissions(
    userId: string,
  ): Promise<AdministrationPermission[]> {
    const response =
      await apiClient.get<
        ItemsResponse<AdministrationPermission>
      >(
        endpoints.userEffectivePermissions(userId),
      );

    return response.data.items;
  },

  async getUserPermissions(
    userId: string,
  ): Promise<AdministrationManagedPermission[]> {
    const response =
      await apiClient.get<
        ItemsResponse<AdministrationManagedPermission>
      >(
        endpoints.userPermissions(userId),
      );

    return response.data.items;
  },

  async setUserPermission(
    userId: string,
    permissionCode: string,
    payload: SetAdministrationUserPermissionRequest,
  ): Promise<SetAdministrationUserPermissionResult> {
    const response =
      await apiClient.put<
        ItemResponse<SetAdministrationUserPermissionResult>
      >(
        endpoints.userPermission(
          userId,
          permissionCode,
        ),
        payload,
      );

    return response.data.item;
  },

  async listRoles(): Promise<AdministrationRole[]> {
    const response =
      await apiClient.get<ItemsResponse<AdministrationRole>>(
        endpoints.roles,
      );

    return response.data.items;
  },

  async replaceUserRoles(
    userId: string,
    payload: ReplaceAdministrationUserRolesRequest,
  ): Promise<ReplaceAdministrationUserRolesResult> {
    const response =
      await apiClient.put<
        ItemResponse<ReplaceAdministrationUserRolesResult>
      >(
        endpoints.userRoles(userId),
        payload,
      );

    return response.data.item;
  },
};

export default tenantAdministrationApi;
