import type { QueryClient } from "@tanstack/react-query";

import {
  useCreateEntity,
  useEntity,
  useEntityList,
  useUpdateEntity,
} from "@/hooks/queries/common";
import type { InvalidateCallback } from "@/hooks/queries/common";
import { useQueryScope } from "@/hooks/useQueryScope";
import { QUERY_KEYS } from "@/lib/queryKeys";
import { journalService } from "@/services/finance";
import type {
  CreateJournalEntryRequest,
  JournalEntry,
  ListJournalEntriesParams,
  ReverseJournalEntryRequest,
  UpdateJournalEntryRequest,
} from "@/services/finance";
import type { TenantQueryScope } from "@/types/domains/query-scope";

function getJournalInvalidation(
  tenantScope: TenantQueryScope | null,
  branchId: string | null,
): InvalidateCallback | undefined {
  if (!tenantScope) return undefined;

  return async (queryClient: QueryClient): Promise<void> => {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.finance.journalLists(
          tenantScope,
          branchId,
        ),
      }),
      queryClient.invalidateQueries({
        queryKey: QUERY_KEYS.finance.journalDetails(
          tenantScope,
          branchId,
        ),
      }),
    ]);
  };
}

export function useJournalEntries(
  params: ListJournalEntriesParams = {},
) {
  const { tenantScope, branchId, isTenantScopeReady } =
    useQueryScope();

  const queryKey = tenantScope
    ? QUERY_KEYS.finance.journals(tenantScope, branchId, params)
    : QUERY_KEYS.finance.disabled("journal-entries");

  return useEntityList<JournalEntry>(
    queryKey,
    () => journalService.list(params),
    { enabled: isTenantScopeReady },
  );
}

export function useJournalEntry(
  journalId: string | null | undefined,
) {
  const { tenantScope, branchId, isTenantScopeReady } =
    useQueryScope();

  const queryKey =
    tenantScope && journalId
      ? QUERY_KEYS.finance.journal(
          tenantScope,
          branchId,
          journalId,
        )
      : QUERY_KEYS.finance.disabled(
          "journal-entry",
          journalId ?? "missing",
        );

  return useEntity<JournalEntry>(
    queryKey,
    () => {
      if (!journalId) {
        throw new Error("A journal ID is required.");
      }
      return journalService.get(journalId);
    },
    {
      enabled: isTenantScopeReady && Boolean(journalId),
    },
  );
}

export function useCreateJournalEntry() {
  const { tenantScope, branchId } = useQueryScope();

  return useCreateEntity<JournalEntry, CreateJournalEntryRequest>(
    (payload) => {
      if (!tenantScope) {
        throw new Error("Tenant scope is required to create a journal.");
      }
      return journalService.create(payload);
    },
    getJournalInvalidation(tenantScope, branchId),
  );
}

export function useUpdateJournalEntryDraft() {
  const { tenantScope, branchId } = useQueryScope();

  return useUpdateEntity<JournalEntry, UpdateJournalEntryRequest>(
    ({ id, data }) => {
      if (!tenantScope) {
        throw new Error("Tenant scope is required to update a journal.");
      }
      return journalService.updateDraft(String(id), data);
    },
    getJournalInvalidation(tenantScope, branchId),
  );
}

export function usePostJournalEntry() {
  const { tenantScope, branchId } = useQueryScope();

  return useCreateEntity<JournalEntry, string>(
    (journalId) => {
      if (!tenantScope) {
        throw new Error("Tenant scope is required to post a journal.");
      }
      return journalService.post(journalId);
    },
    getJournalInvalidation(tenantScope, branchId),
  );
}

export interface ReverseJournalEntryVariables {
  id: string;
  data: ReverseJournalEntryRequest;
}

export function useReverseJournalEntry() {
  const { tenantScope, branchId } = useQueryScope();

  return useCreateEntity<
    JournalEntry,
    ReverseJournalEntryVariables
  >(
    ({ id, data }) => {
      if (!tenantScope) {
        throw new Error("Tenant scope is required to reverse a journal.");
      }
      return journalService.reverse(id, data);
    },
    getJournalInvalidation(tenantScope, branchId),
  );
}
