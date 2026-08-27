/**
 * ============================================================================
 * Hela360 Enterprise Branch Service
 * ============================================================================
 *
 * Service responsible for branch management and branch-specific operations.
 *
 * Responsibilities
 * ----------------
 * • Branch CRUD operations
 * • Retrieve current branch
 * • Switch branch context
 * • Retrieve branch users
 * • Retrieve branch inventory
 * • Activate / deactivate branches
 *
 * This service extends BaseService to inherit standardized CRUD operations
 * while exposing branch-specific endpoints.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";
/* ============================================================================
 * Branch Types
 * ============================================================================
 */

export interface Branch {
  id: string;

  tenantId: string;

  code: string;

  name: string;

  phone?: string;

  email?: string;

  address?: string;

  city?: string;

  country?: string;

  active: boolean;

  createdAt: string;

  updatedAt: string;
}

export interface CreateBranchRequest {
  code: string;

  name: string;

  phone?: string;

  email?: string;

  address?: string;

  city?: string;

  country?: string;
}

export interface UpdateBranchRequest {
  code?: string;

  name?: string;

  phone?: string;

  email?: string;

  address?: string;

  city?: string;

  country?: string;

  active?: boolean;
}

export interface BranchUser {
  id: string;

  username: string;

  fullName: string;

  email: string;

  active: boolean;
}

/* ============================================================================
 * Branch Service
 * ============================================================================
 */

export class BranchService extends BaseService<
  Branch,
  CreateBranchRequest,
  UpdateBranchRequest
> {
  constructor() {
    super(API_ENDPOINTS.BRANCHES.ROOT);
  }

  /* ==========================================================================
   * Branch Context
   * ==========================================================================
   */

  /**
   * Returns the currently selected branch.
   */
  async current(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Branch>> {
    const response =
      await this.getRequest<ApiResponse<Branch>>(
        `${this.resource}/current`,
        config,
      );

    return response.data;
  }

  /**
   * Switch the current branch context.
   */
  async switchBranch(
    branchId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${branchId}/switch`,
        undefined,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Users
   * ==========================================================================
   */

  /**
   * Returns users assigned to a branch.
   */
  async users(
    branchId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<BranchUser>> {
    const response =
      await this.getRequest<
        PaginatedResponse<BranchUser>
      >(
        `${this.resource}/${branchId}/users`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Inventory
   * ==========================================================================
   */

  /**
   * Returns inventory summary for a branch.
   */
  async inventory(
    branchId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<unknown>> {
    const response =
      await this.getRequest<ApiResponse<unknown>>(
        `${this.resource}/${branchId}/inventory`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Status
   * ==========================================================================
   */

  /**
   * Activate a branch.
   */
  async activate(
    branchId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${branchId}/activate`,
        undefined,
        config,
      );

    return response.data;
  }

  /**
   * Deactivate a branch.
   */
  async deactivate(
    branchId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${branchId}/deactivate`,
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

export const branchService =
  new BranchService();

export default branchService;