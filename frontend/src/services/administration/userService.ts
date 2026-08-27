/**
 * ============================================================================
 * Hela360 Enterprise User Service
 * ============================================================================
 *
 * Service responsible for enterprise user administration.
 *
 * Responsibilities
 * ----------------
 * • User CRUD operations
 * • User profile management
 * • User activation
 * • User deactivation
 * • User locking
 * • User unlocking
 * • Password reset
 * • Password change
 * • Role assignment
 * • Branch assignment
 * • Tenant assignment
 * • Permission inspection
 * • Session management
 *
 * This service is the primary administrative interface for enterprise user
 * management and identity lifecycle operations.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

/* ============================================================================
 * Types
 * ============================================================================
 */

export interface User {
  id: string;

  username: string;

  email: string;

  firstName: string;

  lastName: string;

  fullName: string;

  phone?: string;

  tenantId: string;

  branchId?: string;

  active: boolean;

  locked: boolean;

  createdAt: string;

  updatedAt: string;
}

export interface CreateUserRequest {
  username: string;

  email: string;

  firstName: string;

  lastName: string;

  phone?: string;

  password: string;

  roleIds: string[];

  branchId?: string;
}

export interface UpdateUserRequest {
  email?: string;

  firstName?: string;

  lastName?: string;

  phone?: string;

  branchId?: string;

  active?: boolean;
}

export interface ResetPasswordRequest {
  password: string;

  requirePasswordChange?: boolean;
}

export interface ChangePasswordRequest {
  currentPassword: string;

  newPassword: string;
}

export interface UserRole {
  id: string;

  name: string;

  code: string;
}

export interface UserPermission {
  id: string;

  code: string;

  module: string;
}

/* ============================================================================
 * User Service
 * ============================================================================
 */

export class UserService extends BaseService<
  User,
  CreateUserRequest,
  UpdateUserRequest
> {
  constructor() {
    super(API_ENDPOINTS.USERS.ROOT);
  }

  /* ==========================================================================
   * Profile
   * ==========================================================================
   */

  async current(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<User>> {
    const response =
      await this.getRequest<ApiResponse<User>>(
        `${this.resource}/me`,
        config,
      );

    return response.data;
  }

  async profile(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<User>> {
    const response =
      await this.getRequest<ApiResponse<User>>(
        `${this.resource}/${userId}/profile`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Roles
   * ==========================================================================
   */

  async roles(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<UserRole[]>> {
    const response =
      await this.getRequest<ApiResponse<UserRole[]>>(
        `${this.resource}/${userId}/roles`,
        config,
      );

    return response.data;
  }

  async assignRoles(
    userId: string,
    roleIds: string[],
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.putRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/roles`,
        { roleIds },
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Permissions
   * ==========================================================================
   */

  async permissions(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<UserPermission[]>> {
    const response =
      await this.getRequest<ApiResponse<UserPermission[]>>(
        `${this.resource}/${userId}/permissions`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Passwords
   * ==========================================================================
   */

  async resetPassword(
    userId: string,
    payload: ResetPasswordRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/reset-password`,
        payload,
        config,
      );

    return response.data;
  }

  async changePassword(
    payload: ChangePasswordRequest,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/change-password`,
        payload,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Status
   * ==========================================================================
   */

  async activate(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/activate`,
        undefined,
        config,
      );

    return response.data;
  }

  async deactivate(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/deactivate`,
        undefined,
        config,
      );

    return response.data;
  }

  async lock(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/lock`,
        undefined,
        config,
      );

    return response.data;
  }

  async unlock(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/unlock`,
        undefined,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Sessions
   * ==========================================================================
   */

  async sessions(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<unknown[]>> {
    const response =
      await this.getRequest<ApiResponse<unknown[]>>(
        `${this.resource}/${userId}/sessions`,
        config,
      );

    return response.data;
  }

  async revokeSessions(
    userId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${userId}/sessions/revoke`,
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

export const userService = new UserService();

export default userService;