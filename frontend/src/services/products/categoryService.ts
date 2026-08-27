/**
 * ============================================================================
 * Hela360 Enterprise Category Service
 * ============================================================================
 *
 * Service responsible for product category management.
 *
 * Responsibilities
 * ----------------
 * • Category CRUD operations
 * • Category hierarchy
 * • Parent / child categories
 * • Product counts
 * • Category activation
 * • Category deactivation
 * • Category tree
 * • Category search
 *
 * Categories organize the enterprise product catalogue and support inventory,
 * procurement, reporting, and merchandising workflows.
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

export interface Category {
  id: string;

  code: string;

  name: string;

  description?: string;

  parentId?: string;

  level: number;

  path: string;

  productCount: number;

  active: boolean;

  createdAt: string;

  updatedAt: string;
}

export interface CreateCategoryRequest {
  code: string;

  name: string;

  description?: string;

  parentId?: string;
}

export interface UpdateCategoryRequest {
  code?: string;

  name?: string;

  description?: string;

  parentId?: string;

  active?: boolean;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
}

/* ============================================================================
 * Category Service
 * ============================================================================
 */

export class CategoryService extends BaseService<
  Category,
  CreateCategoryRequest,
  UpdateCategoryRequest
> {
  constructor() {
    super(API_ENDPOINTS.CATEGORIES.ROOT);
  }

  /* ==========================================================================
   * Hierarchy
   * ==========================================================================
   */

  /**
   * Returns the complete category hierarchy.
   */
  async tree(
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<CategoryTree[]>> {
    const response =
      await this.getRequest<ApiResponse<CategoryTree[]>>(
        `${this.resource}/tree`,
        config,
      );

    return response.data;
  }

  /**
   * Returns children of a category.
   */
  async children(
    categoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Category[]>> {
    const response =
      await this.getRequest<ApiResponse<Category[]>>(
        `${this.resource}/${categoryId}/children`,
        config,
      );

    return response.data;
  }

  /**
   * Returns the parent category.
   */
  async parent(
    categoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<Category>> {
    const response =
      await this.getRequest<ApiResponse<Category>>(
        `${this.resource}/${categoryId}/parent`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Products
   * ==========================================================================
   */

  /**
   * Returns products belonging to a category.
   */
  async products(
    categoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<PaginatedResponse<unknown>> {
    const response =
      await this.getRequest<
        PaginatedResponse<unknown>
      >(
        `${this.resource}/${categoryId}/products`,
        config,
      );

    return response.data;
  }

  /**
   * Returns the number of products in a category.
   */
  async productCount(
    categoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<number>> {
    const response =
      await this.getRequest<ApiResponse<number>>(
        `${this.resource}/${categoryId}/count`,
        config,
      );

    return response.data;
  }

  /* ==========================================================================
   * Status
   * ==========================================================================
   */

  /**
   * Activate a category.
   */
  async activate(
    categoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${categoryId}/activate`,
        undefined,
        config,
      );

    return response.data;
  }

  /**
   * Deactivate a category.
   */
  async deactivate(
    categoryId: string,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<void>> {
    const response =
      await this.postRequest<ApiResponse<void>>(
        `${this.resource}/${categoryId}/deactivate`,
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

export const categoryService =
  new CategoryService();

export default categoryService;