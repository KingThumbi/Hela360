/**
 * Hela360 Chart of Accounts Service
 *
 * Tenant and branch authorization are enforced by the backend. This service
 * only transports typed requests through the shared enterprise API client.
 */
import { apiClient } from "@/api";
import { API_ENDPOINTS } from "@/api/endpoints";

export type ChartOfAccountType =
  | "asset"
  | "liability"
  | "equity"
  | "revenue"
  | "expense";

export type NormalBalance = "debit" | "credit";

export interface ChartOfAccountParent {
  id: string;
  account_code: string;
  account_name: string;
}

export interface ChartOfAccountBranch {
  id: string;
  code: string;
  name: string;
}

export interface ChartOfAccount {
  id: string;
  tenant_id: string;
  branch_id: string | null;
  account_code: string;
  account_name: string;
  account_type: ChartOfAccountType;
  parent_id: string | null;
  parent: ChartOfAccountParent | null;
  description: string | null;
  normal_balance: NormalBalance;
  is_active: boolean;
  is_system_account: boolean;
  currency: string | null;
  branch: ChartOfAccountBranch | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface CreateChartOfAccountRequest {
  account_code: string;
  account_name: string;
  account_type: ChartOfAccountType;
  normal_balance: NormalBalance;
  parent_id?: string | null;
  description?: string | null;
  branch_id: string;
  currency?: string | null;
}

export interface UpdateChartOfAccountRequest {
  account_name?: string;
  account_type?: ChartOfAccountType;
  normal_balance?: NormalBalance;
  parent_id?: string | null;
  description?: string | null;
  is_active?: boolean;
}

interface ChartOfAccountsListResponse {
  ok: true;
  count: number;
  items: ChartOfAccount[];
}

interface ChartOfAccountItemResponse {
  ok: true;
  item: ChartOfAccount;
  message?: string;
}

class ChartOfAccountsService {
  async list(): Promise<ChartOfAccount[]> {
    const response = await apiClient.get<ChartOfAccountsListResponse>(
      API_ENDPOINTS.FINANCE.ACCOUNTS,
    );
    return response.data.items;
  }

  async create(
    payload: CreateChartOfAccountRequest,
  ): Promise<ChartOfAccount> {
    const response = await apiClient.post<ChartOfAccountItemResponse>(
      API_ENDPOINTS.FINANCE.ACCOUNTS,
      payload,
    );
    return response.data.item;
  }

  async update(
    accountId: string,
    payload: UpdateChartOfAccountRequest,
  ): Promise<ChartOfAccount> {
    const response = await apiClient.patch<ChartOfAccountItemResponse>(
      API_ENDPOINTS.FINANCE.ACCOUNT(accountId),
      payload,
    );
    return response.data.item;
  }
}

export const chartOfAccountsService = new ChartOfAccountsService();
