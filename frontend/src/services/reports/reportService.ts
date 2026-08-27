/**
 * ============================================================================
 * Hela360 Enterprise Report Service
 * ============================================================================
 *
 * Central reporting service.
 *
 * Responsibilities
 * ----------------
 * • Sales reports
 * • Inventory reports
 * • Procurement reports
 * • Customer reports
 * • Supplier reports
 * • Financial reports
 * • Audit reports
 * • Tax reports
 * • Stock valuation
 * • Profitability
 * • Dashboard exports
 * • PDF generation
 * • Excel generation
 * • CSV generation
 *
 * Reports aggregate business information but never mutate business state.
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

export type ReportFormat =
  | "pdf"
  | "excel"
  | "csv"
  | "json";

export interface ReportPeriod {
  startDate: string;

  endDate: string;
}

export interface SalesReport {
  totalSales: number;

  totalTransactions: number;

  averageBasket: number;

  grossProfit: number;
}

export interface InventoryReport {
  stockValue: number;

  totalProducts: number;

  lowStockItems: number;

  expiredItems: number;
}

export interface FinanceReport {
  revenue: number;

  expenses: number;

  profit: number;

  outstandingInvoices: number;
}

export interface ProcurementReport {
  purchaseOrders: number;

  goodsReceived: number;

  supplierSpend: number;
}

export interface CustomerReport {
  totalCustomers: number;

  activeCustomers: number;

  newCustomers: number;
}

export interface SupplierReport {
  totalSuppliers: number;

  activeSuppliers: number;

  purchaseVolume: number;
}

export interface AuditReport {
  totalEvents: number;

  loginEvents: number;

  inventoryEvents: number;

  salesEvents: number;
}

export interface TaxReport {
  taxableSales: number;

  taxCollected: number;

  taxPaid: number;
}

/* ============================================================================
 * Report Service
 * ============================================================================
 */

export class ReportService extends BaseService<never> {
  constructor() {
    super(API_ENDPOINTS.REPORTS.ROOT);
  }

  /* ==========================================================================
   * Sales
   * ==========================================================================
   */

  async sales(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<SalesReport>> {
    const response =
      await this.getRequest<ApiResponse<SalesReport>>(
        `${this.resource}/sales`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Inventory
   * ==========================================================================
   */

  async inventory(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<InventoryReport>> {
    const response =
      await this.getRequest<ApiResponse<InventoryReport>>(
        `${this.resource}/inventory`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Finance
   * ==========================================================================
   */

  async finance(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<FinanceReport>> {
    const response =
      await this.getRequest<ApiResponse<FinanceReport>>(
        `${this.resource}/finance`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Procurement
   * ==========================================================================
   */

  async procurement(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<ProcurementReport>> {
    const response =
      await this.getRequest<ApiResponse<ProcurementReport>>(
        `${this.resource}/procurement`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Customers
   * ==========================================================================
   */

  async customers(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<CustomerReport>> {
    const response =
      await this.getRequest<ApiResponse<CustomerReport>>(
        `${this.resource}/customers`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Suppliers
   * ==========================================================================
   */

  async suppliers(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<SupplierReport>> {
    const response =
      await this.getRequest<ApiResponse<SupplierReport>>(
        `${this.resource}/suppliers`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Audit
   * ==========================================================================
   */

  async audit(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<AuditReport>> {
    const response =
      await this.getRequest<ApiResponse<AuditReport>>(
        `${this.resource}/audit`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Tax
   * ==========================================================================
   */

  async tax(
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<ApiResponse<TaxReport>> {
    const response =
      await this.getRequest<ApiResponse<TaxReport>>(
        `${this.resource}/tax`,
        {
          ...config,
          params: period,
        },
      );

    return response.data;
  }

  /* ==========================================================================
   * Export
   * ==========================================================================
   */

  async export(
    report: string,
    format: ReportFormat,
    period: ReportPeriod,
    config?: AxiosRequestConfig,
  ): Promise<Blob> {
    const response =
      await this.download(
        `${this.resource}/${report}/export`,
        {
          ...config,
          params: {
            format,
            ...period,
          },
          responseType: "blob",
        },
      );

    return response.data;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const reportService =
  new ReportService();

export default reportService;