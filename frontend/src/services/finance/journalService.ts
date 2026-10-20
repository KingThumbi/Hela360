/**
 * Hela360 Manual Journal Entry Service
 *
 * Transports typed journal requests through the shared API client.
 * Tenant and branch authorization, validation, posting and reversal rules
 * remain enforced by the backend.
 *
 * Posted journals are immutable. Corrections are made through reversals.
 */
import { apiClient } from "@/api";
import { API_ENDPOINTS } from "@/api/endpoints";

export type JournalStatus = "draft" | "posted";

export interface JournalEntryLine {
  id: string;
  line_number: number;
  account_id: string;
  account_code: string | null;
  account_name: string | null;
  description: string | null;
  debit: string;
  credit: string;
}

export interface JournalEntry {
  id: string;
  tenant_id: string;
  branch_id: string;
  journal_number: string;
  journal_date: string;
  description: string;
  reference: string | null;
  currency: string;
  status: JournalStatus;
  total_debit: string;
  total_credit: string;
  created_by: string | null;
  updated_by: string | null;
  posted_by: string | null;
  posted_at: string | null;
  reversal_of_id: string | null;
  original_journal_number: string | null;
  reversal_journal_number: string | null;
  lines: JournalEntryLine[];
  created_at: string | null;
  updated_at: string | null;
}

export interface JournalEntryLineRequest {
  account_id: string;
  debit: string;
  credit: string;
  description?: string | null;
}

export interface CreateJournalEntryRequest {
  branch_id: string;
  journal_date: string;
  description: string;
  reference?: string | null;
  lines: JournalEntryLineRequest[];
}

export interface UpdateJournalEntryRequest {
  journal_date?: string;
  description?: string;
  reference?: string | null;
  lines?: JournalEntryLineRequest[];
}

export interface ReverseJournalEntryRequest {
  journal_date: string;
  reason: string;
}

export interface ListJournalEntriesParams {
  status?: JournalStatus;
  limit?: number;
}

interface JournalEntryListResponse {
  ok: true;
  count: number;
  items: JournalEntry[];
}

interface JournalEntryItemResponse {
  ok: true;
  item: JournalEntry;
  message?: string;
}

class JournalService {
  async list(
    params: ListJournalEntriesParams = {},
  ): Promise<JournalEntry[]> {
    const response = await apiClient.get<JournalEntryListResponse>(
      API_ENDPOINTS.FINANCE.JOURNALS,
      { params },
    );

    return response.data.items;
  }

  async get(journalId: string): Promise<JournalEntry> {
    const response = await apiClient.get<JournalEntryItemResponse>(
      API_ENDPOINTS.FINANCE.JOURNAL(journalId),
    );

    return response.data.item;
  }

  async create(
    payload: CreateJournalEntryRequest,
  ): Promise<JournalEntry> {
    const response = await apiClient.post<JournalEntryItemResponse>(
      API_ENDPOINTS.FINANCE.JOURNALS,
      payload,
    );

    return response.data.item;
  }

  async updateDraft(
    journalId: string,
    payload: UpdateJournalEntryRequest,
  ): Promise<JournalEntry> {
    const response = await apiClient.patch<JournalEntryItemResponse>(
      API_ENDPOINTS.FINANCE.JOURNAL(journalId),
      payload,
    );

    return response.data.item;
  }

  async post(journalId: string): Promise<JournalEntry> {
    const response = await apiClient.post<JournalEntryItemResponse>(
      API_ENDPOINTS.FINANCE.POST_JOURNAL(journalId),
    );

    return response.data.item;
  }

  async reverse(
    journalId: string,
    payload: ReverseJournalEntryRequest,
  ): Promise<JournalEntry> {
    const response = await apiClient.post<JournalEntryItemResponse>(
      API_ENDPOINTS.FINANCE.REVERSE_JOURNAL(journalId),
      payload,
    );

    return response.data.item;
  }
}

export const journalService = new JournalService();
