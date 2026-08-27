/**
 * ============================================================================
 * Hela360 Enterprise Role Service
 * ============================================================================
 *
 * Service responsible for role management and role-based authorization.
 *
 * Responsibilities
 * ----------------
 * • Role CRUD operations
 * • Retrieve system roles
 * • Retrieve role permissions
 * • Retrieve role users
 * • Assign permissions
 * • Remove permissions
 * • Clone roles
 * • Activate / deactivate roles
 *
 * Every authorization decision in Hela360 ultimately originates from a role.
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

export interface Role {
  id: string;

  name: string;

  code: string;

  description?: string;

  system: boolean;

  active: boolean;

  createdAt: string;

  updatedAt: string;
}

export interface CreateRoleRequest {
  name: string;

  code: string;

  description?: string;
}

export interface UpdateRoleRequest {
  name?: string;

  code?: string;

  description?: string;

  active?: boolean;
}

export interface RolePermission {
  id: string;

  name: string;

  code: string;

  module: string;
}

export interface RoleUser {
  id: string;

  username: string;

  fullName: string;

  email: string;

  active: boolean;
}

/* ============================================================================
 * Role Service
 * ============================================================================
 */

export class RoleService extends BaseService<
  Role,
  CreateRoleRequest,
  UpdateRoleRequest
> {
  constructor() {
    super(API_ENDPOINTS.ROLES.ROOT);
  }

  /* ==========================================================================
   * Permissions
   * ==========================================================================
   */

  /**
   * Returns permissions assigned to a role.
   */
  async permissions(
    roleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<RolePermission[]>> {
    const response =
      await this.getRequest<ApiResponse<RolePermission[]>>(
        `${this.resource}/${roleId}/permissions`,
        config,
      );

    return response.data;
  }

  /**
   * Assign permissions.
   */
  async assignPermissions(
    roleId: string,
    permissionIds: string[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${roleId}/permissions`,
        {
          permissionIds,
        },
        config,
      );

    return response.data;
  }

  /**
   * Replace all permissions assigned to a role.
   */
  async updatePermissions(
    roleId: string,
    permissionIds: string[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.putRequest<ApiResponse<void>>(
        `${this.resource}/${roleId}/permissions`,
        {
          permissionIds,
        },
        config,
      );

    return response.data;
  }

  /**
   * Remove permissions from a role.
   */
  async removePermissions(
    roleId: string,
    permissionIds: string[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.deleteRequest<ApiResponse<void>>(
        `${this.resource}/${roleId}/permissions`,
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
   * Returns users assigned to a role.
   */
  async users(
    roleId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<RoleUser>> {
    const response =
      await this.getRequest<
        PaginatedResponse<RoleUser>
      >(
        `${this.resource}/${roleId}/users`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Role Management
   * ==========================================================================
   */

  /**
   * Clone an existing role.
   */
  async clone(
    roleId: string,
    name: string,
    code: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Role>> {
    const response =
      await this.postRequest<ApiResponse<Role>>(
        `${this.resource}/${roleId}/clone`,
        {
          name,
          code,
        },
        config,
      );

    return response.data;
  }

  /**
   * Returns all built-in system roles.
   */
  async systemRoles(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Role[]>> {
    const response =
      await this.getRequest<ApiResponse<Role[]>>(
        `${this.resource}/system`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Status
   * ==========================================================================
   */

  /**
   * Activate a role.
   */
  async activate(
    roleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${roleId}/activate`,
        undefined,
        config,
      );

    return response.data;
  }

  /**
   * Deactivate a role.
   */
  async deactivate(
    roleId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${roleId}/deactivate`,
        undefined,
        config,
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const roleService = new RoleService();

export default roleService;