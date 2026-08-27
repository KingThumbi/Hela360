/**
 * ============================================================================
 * Hela360 Enterprise Permission Service
 * ============================================================================
 *
 * Service responsible for permission management and authorization metadata.
 *
 * Responsibilities
 * ----------------
 * • Permission CRUD operations
 * • Retrieve permission groups
 * • Retrieve permissions by module
 * • Retrieve permissions for a role
 * • Retrieve permissions for a user
 * • Assign permissions to roles
 * • Remove permissions from roles
 * • Synchronize permission registry
 *
 * This service extends BaseService while exposing authorization-specific
 * operations used throughout the enterprise application.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";
/* ============================================================================
 * Types
 * ============================================================================
 */

export interface Permission {
  id: string;

  name: string;

  code: string;

  description?: string;

  module: string;

  group: string;

  active: boolean;

  createdAt: string;

  updatedAt: string;
}

export interface CreatePermissionRequest {
  name: string;

  code: string;

  description?: string;

  module: string;

  group: string;
}

export interface UpdatePermissionRequest {
  name?: string;

  description?: string;

  module?: string;

  group?: string;

  active?: boolean;
}

export interface PermissionGroup {
  name: string;

  permissions: Permission[];
}

/* ============================================================================
 * Permission Service
 * ============================================================================
 */

export class PermissionService extends BaseService<
  Permission,
  CreatePermissionRequest,
  UpdatePermissionRequest
> {
  constructor() {
    super(API_ENDPOINTS.PERMISSIONS.ROOT);
  }

  /* ==========================================================================
   * Registry
   * ==========================================================================
   */

  /**
   * Returns all permission groups.
   */
  async groups(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<PermissionGroup[]>> {
    const response =
      await this.getRequest<ApiResponse<PermissionGroup[]>>(
        `${this.resource}/groups`,
        config,
      );

    return response.data;
  }

  /**
   * Returns permissions belonging to a module.
   */
  async byModule(
    module: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Permission[]>> {
    const response =
      await this.getRequest<ApiResponse<Permission[]>>(
        `${this.resource}/modules/${module}`,
        config,
      );

    return response.data;
  }

  /**
   * Synchronizes the permission registry.
   */
  async synchronize(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/synchronize`,
        undefined,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Roles
   * ==========================================================================
   */

  /**
   * Returns permissions assigned to a role.
   */
  async rolePermissions(
    roleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Permission[]>> {
    const response =
      await this.getRequest<ApiResponse<Permission[]>>(
        `${this.resource}/roles/${roleId}`,
        config,
      );

    return response.data;
  }

  /**
   * Assigns permissions to a role.
   */
  async assignToRole(
    roleId: string,
    permissionIds: string[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/roles/${roleId}`,
        {
          permissionIds,
        },
        config,
      );

    return response.data;
  }

  /**
   * Removes permissions from a role.
   */
  async removeFromRole(
    roleId: string,
    permissionIds: string[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.deleteRequest<ApiResponse<void>>(
        `${this.resource}/roles/${roleId}`,
        {
          ...config,
          data: {
            permissionIds,
          },
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Users
   * ==========================================================================
   */

  /**
   * Returns the effective permissions for a user.
   */
  async userPermissions(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Permission[]>> {
    const response =
      await this.getRequest<ApiResponse<Permission[]>>(
        `${this.resource}/users/${userId}`,
        config,
      );

    return response.data;
  }

  /**
   * Returns all permissions using pagination.
   */
  async registry(
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<Permission>> {
    return this.paginate(undefined, config);
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const permissionService =
  new PermissionService();

export default permissionService;