/**
 * ============================================================================
 * Hela360 Enterprise Tenant Service
 * ============================================================================
 *
 * Service responsible for tenant management and tenant-specific operations.
 *
 * Responsibilities
 * ----------------
 * • Tenant CRUD operations
 * • Retrieve current tenant
 * • Switch tenant context
 * • Retrieve tenant branches
 * • Retrieve tenant users
 * • Retrieve tenant settings
 * • Activate / deactivate tenants
 *
 * This service extends BaseService to inherit standardized CRUD operations
 * while exposing tenant-specific endpoints.
 *
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";

import BaseService from "@/services/base";

import type { ApiResponse } from "@/types/api";

import type { PaginatedResponse } from "@/types/api";
/* ============================================================================
 * Tenant Types
 * ============================================================================
 */

export interface Tenant {
  id: string;

  name: string;

  slug: string;

  description?: string;

  active: boolean;

  createdAt: string;

  updatedAt: string;
}

export interface CreateTenantRequest {
  name: string;

  slug: string;

  description?: string;
}

export interface UpdateTenantRequest {
  name?: string;

  slug?: string;

  description?: string;

  active?: boolean;
}

export interface TenantBranch {
  id: string;

  name: string;

  code: string;

  active: boolean;
}

export interface TenantUser {
  id: string;

  username: string;

  fullName: string;

  email: string;

  active: boolean;
}

/* ============================================================================
 * Tenant Service
 * ============================================================================
 */

export class TenantService extends BaseService<
  Tenant,
  CreateTenantRequest,
  UpdateTenantRequest
> {
  constructor() {
    super(API_ENDPOINTS.TENANTS.ROOT);
  }

  /* ==========================================================================
   * Tenant Context
   * ==========================================================================
   */

  /**
   * Returns the currently selected tenant.
   */
  async current(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Tenant>> {
    const response =
      await this.getRequest<ApiResponse<Tenant>>(
        `${this.resource}/current`,
        config,
      );

    return response.data;
  }

  /**
   * Switch the current tenant context.
   */
  async switchTenant(
    tenantId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${tenantId}/switch`,
        undefined,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Branches
   * ==========================================================================
   */

  /**
   * Returns all branches belonging to a tenant.
   */
  async branches(
    tenantId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<TenantBranch[]>> {
    const response =
      await this.getRequest<ApiResponse<TenantBranch[]>>(
        `${this.resource}/${tenantId}/branches`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Users
   * ==========================================================================
   */

  /**
   * Returns all users belonging to a tenant.
   */
  async users(
    tenantId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<TenantUser>> {
    const response =
      await this.getRequest<
        PaginatedResponse<TenantUser>
      >(
        `${this.resource}/${tenantId}/users`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Settings
   * ==========================================================================
   */

  /**
   * Returns tenant settings.
   */
  async settings<TSettings>(
    tenantId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<TSettings>> {
    const response =
      await this.getRequest<ApiResponse<TSettings>>(
        `${this.resource}/${tenantId}/settings`,
        config,
      );

    return response.data;
  }

  /**
   * Updates tenant settings.
   */
  async updateSettings<TSettings>(
    tenantId: string,
    settings: TSettings,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<TSettings>> {
    const response =
      await this.putRequest<ApiResponse<TSettings>>(
        `${this.resource}/${tenantId}/settings`,
        settings,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Status
   * ==========================================================================
   */

  /**
   * Activate a tenant.
   */
  async activate(
    tenantId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${tenantId}/activate`,
        undefined,
        config,
      );

    return response.data;
  }

  /**
   * Deactivate a tenant.
   */
  async deactivate(
    tenantId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${tenantId}/deactivate`,
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

export const tenantService =
  new TenantService();

export default tenantService;