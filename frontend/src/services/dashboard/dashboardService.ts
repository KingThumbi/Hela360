/**
 * ============================================================================
 * Hela360 Tenant Dashboard Service
 * ============================================================================
 *
 * Typed frontend transport for the authenticated tenant dashboard API.
 *
 * Architectural Responsibilities
 * ------------------------------
 * • Consume the canonical backend dashboard read projection
 * • Preserve backend transport field names exactly
 * • Keep dashboard aggregation on the backend
 * • Use the shared Hela360 API client through BaseService
 * • Preserve authenticated tenant and branch scope
 *
 * Security
 * --------
 * Tenant and branch scope are resolved by the authenticated backend identity.
 * This service MUST NOT send tenant_id or branch_id as dashboard scope
 * overrides.
 *
 * Dashboard data is a read projection only. Authoritative business state
 * remains owned by the corresponding Hela360 business domains.
 * ============================================================================
 */

import type { AxiosRequestConfig } from "axios";

import { API_ENDPOINTS } from "@/api/endpoints";
import BaseService from "@/services/base";

/* ============================================================================
 * Request Types
 * ============================================================================
 */

export interface DashboardOverviewParams {
  operational_date?: string;
}

/* ============================================================================
 * Scope
 * ============================================================================
 */

export interface DashboardScope {
  tenant_id: string;
  branch_id: string;
  generated_at: string;
  operational_date: string;
  timezone: string;
  currency: string;
}

/* ============================================================================
 * Sales
 * ============================================================================
 */

export interface DashboardSalesSummary {
  gross_sales: string;
  discounts: string;
  refunds: string;
  net_sales: string;
  transactions: number;
  average_basket: string;
  paid_amount: string;
  balance_due: string;
}

export interface DashboardSales {
  today: DashboardSalesSummary;
  month_to_date: DashboardSalesSummary;
}

/* ============================================================================
 * Payments
 * ============================================================================
 */

export interface DashboardPaymentMixItem {
  payment_method_id: string;
  code: string;
  name: string;
  method_type: string;
  amount: string;
  transaction_count: number;
}

export interface DashboardPayments {
  today: DashboardPaymentMixItem[];
}

/* ============================================================================
 * Inventory
 * ============================================================================
 */

export interface DashboardInventoryHealth {
  stock_records: number;
  low_stock: number;
  out_of_stock: number;
  expiring_soon: number;
  expired: number;
}

/* ============================================================================
 * Recent Sales
 * ============================================================================
 */

export interface DashboardRecentSale {
  id: string;
  sale_number: string;
  sale_date: string;
  status: string;
  total_amount: string;
  paid_amount: string;
  balance_due: string;
}

/* ============================================================================
 * Alerts
 * ============================================================================
 *
 * Dashboard v1 currently returns an empty alert collection. Keep the transport
 * type intentionally conservative until the backend establishes the alert
 * object contract.
 */

export type DashboardAlert = Record<string, unknown>;

/* ============================================================================
 * Dashboard Projection
 * ============================================================================
 */

export interface DashboardOverview {
  scope: DashboardScope;
  sales: DashboardSales;
  payments: DashboardPayments;
  inventory: DashboardInventoryHealth;
  recent_sales: DashboardRecentSale[];
  alerts: DashboardAlert[];
}

export interface DashboardOverviewResponse {
  success: true;
  dashboard: DashboardOverview;
}

/* ============================================================================
 * Service
 * ============================================================================
 */

export class DashboardService extends BaseService<DashboardOverview> {
  constructor() {
    super(API_ENDPOINTS.DASHBOARD.ROOT);
  }

  async overview(
    params?: DashboardOverviewParams,
    config?: AxiosRequestConfig,
  ): Promise<DashboardOverview> {
    const response =
      await this.getRequest<DashboardOverviewResponse>(
        API_ENDPOINTS.DASHBOARD.OVERVIEW,
        {
          ...config,
          params: {
            ...config?.params,
            ...params,
          },
        },
      );

    return response.data.dashboard;
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const dashboardService =
  new DashboardService();

export default dashboardService;
