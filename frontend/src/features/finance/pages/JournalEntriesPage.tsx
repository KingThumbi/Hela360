import {
  BookOpen,
  Eye,
  Landmark,
  Pencil,
  Plus,
  RefreshCw,
  RotateCcw,
  Search,
  Send,
  X,
} from "lucide-react";
import { useMemo, useState, type FormEvent } from "react";
import { toast } from "sonner";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  Page,
  PageActions,
  PageContent,
  PageDescription,
  PageHeader,
  PageSection,
  PageTitle,
  PageToolbar,
} from "@/components/page";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  useChartOfAccounts,
  useCreateJournalEntry,
  useJournalEntries,
  usePostJournalEntry,
  useReverseJournalEntry,
  useUpdateJournalEntryDraft,
} from "@/hooks/queries/finance";
import { useAuthorization } from "@/hooks/useAuthorization";
import { useQueryScope } from "@/hooks/useQueryScope";
import { PERMISSIONS } from "@/navigation/permissions";
import type {
  ChartOfAccount,
  CreateJournalEntryRequest,
  JournalEntry,
  JournalEntryLineRequest,
  JournalStatus,
} from "@/services/finance";

type StatusFilter = "all" | JournalStatus;

interface JournalLineForm {
  account_id: string;
  description: string;
  debit: string;
  credit: string;
}

interface JournalFormState {
  journal_date: string;
  description: string;
  reference: string;
  lines: JournalLineForm[];
}

interface ReversalFormState {
  journal_date: string;
  reason: string;
}

const MAX_VISIBLE_LINES = 100;

function localDateValue(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function emptyLine(): JournalLineForm {
  return {
    account_id: "",
    description: "",
    debit: "0.00",
    credit: "0.00",
  };
}

function emptyJournalForm(): JournalFormState {
  return {
    journal_date: localDateValue(),
    description: "",
    reference: "",
    lines: [emptyLine(), emptyLine()],
  };
}

function emptyReversalForm(): ReversalFormState {
  return {
    journal_date: localDateValue(),
    reason: "",
  };
}

/**
 * Parses decimal amounts into cents so ordinary balance checks avoid
 * floating-point arithmetic. Blank fields are treated as zero.
 */
function parseCents(value: string): number | null {
  const input = value.trim();

  if (!input) return 0;

  if (!/^(?:\d+(?:\.\d{1,2})?|\.\d{1,2})$/.test(input)) {
    return null;
  }

  const normalized = input.startsWith(".") ? `0${input}` : input;
  const [whole = "0", fraction = ""] = normalized.split(".");
  const cents = Number(whole) * 100 + Number(fraction.padEnd(2, "0"));

  if (!Number.isSafeInteger(cents) || cents < 0) return null;
  return cents;
}

function formatMoney(value: string | number, currency = "KES"): string {
  const amount = Number(value);

  if (!Number.isFinite(amount)) return `${currency} 0.00`;

  return `${currency} ${amount.toLocaleString("en-KE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

function typeErrorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "The request could not be completed.";
}

function statusVariant(status: JournalStatus) {
  return status === "posted" ? "secondary" as const : "outline" as const;
}

function StatCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <div className="rounded-xl border bg-background p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums">{value}</p>
      <p className="mt-1 text-xs text-muted-foreground">{description}</p>
    </div>
  );
}

function FormField({
  label,
  htmlFor,
  children,
}: {
  label: string;
  htmlFor: string;
  children: React.ReactNode;
}) {
  return (
    <div className="min-w-0 space-y-2">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
    </div>
  );
}

export function JournalEntriesPage() {
  const authorization = useAuthorization();
  const { branchId } = useQueryScope();

  const canCreatePermission = authorization.can(
    PERMISSIONS.FINANCE_JOURNALS_CREATE,
  );
  const canReadAccounts = authorization.can(
    PERMISSIONS.FINANCE_ACCOUNTS_READ,
  );
  const canManageDrafts = canCreatePermission && canReadAccounts;

  const journalsQuery = useJournalEntries({ limit: MAX_VISIBLE_LINES });
  const accountsQuery = useChartOfAccounts({
    enabled: canManageDrafts,
  });

  const createJournal = useCreateJournalEntry();
  const updateJournal = useUpdateJournalEntryDraft();
  const postJournal = usePostJournalEntry();
  const reverseJournal = useReverseJournalEntry();

  const entries = useMemo(
    () => journalsQuery.data ?? [],
    [journalsQuery.data],
  );
  const accounts = useMemo(
    () => accountsQuery.data ?? [],
    [accountsQuery.data],
  );

  const canCreate = authorization.can(PERMISSIONS.FINANCE_JOURNALS_CREATE);
  const canPost = authorization.can(PERMISSIONS.FINANCE_JOURNALS_POST);
  const canReverse = authorization.can(PERMISSIONS.FINANCE_JOURNALS_REVERSE);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");

  const [formOpen, setFormOpen] = useState(false);
  const [editingJournal, setEditingJournal] = useState<JournalEntry | null>(null);
  const [form, setForm] = useState<JournalFormState>(() => emptyJournalForm());

  const [selectedJournal, setSelectedJournal] = useState<JournalEntry | null>(null);
  const [postingTarget, setPostingTarget] = useState<JournalEntry | null>(null);
  const [reversalTarget, setReversalTarget] = useState<JournalEntry | null>(null);
  const [reversalForm, setReversalForm] = useState<ReversalFormState>(
    () => emptyReversalForm(),
  );

  const eligibleAccounts = useMemo(() => {
    const summaryAccountIds = new Set(
      accounts
        .filter((candidate) => candidate.parent_id)
        .map((candidate) => candidate.parent_id as string),
    );

    return accounts.filter((account: ChartOfAccount) =>
      account.is_active &&
      (account.branch_id === null || account.branch_id === branchId) &&
      !summaryAccountIds.has(account.id),
    );
  }, [accounts, branchId]);

  const filteredEntries = useMemo(() => {
    const needle = search.trim().toLowerCase();

    return entries.filter((entry) => {
      const matchesStatus =
        statusFilter === "all" || entry.status === statusFilter;

      const matchesSearch = !needle || [
        entry.journal_number,
        entry.journal_date,
        entry.description,
        entry.reference ?? "",
        entry.status,
        ...entry.lines.flatMap((line) => [
          line.account_code ?? "",
          line.account_name ?? "",
          line.description ?? "",
        ]),
      ].some((value) => value.toLowerCase().includes(needle));

      return matchesStatus && matchesSearch;
    });
  }, [entries, search, statusFilter]);

  const draftCount = entries.filter((entry) => entry.status === "draft").length;
  const postedCount = entries.filter((entry) => entry.status === "posted").length;

  const debitTotal = form.lines.reduce(
    (sum, line) => sum + (parseCents(line.debit) ?? 0),
    0,
  );
  const creditTotal = form.lines.reduce(
    (sum, line) => sum + (parseCents(line.credit) ?? 0),
    0,
  );

  const allAmountsValid = form.lines.every(
    (line) =>
      parseCents(line.debit) !== null &&
      parseCents(line.credit) !== null,
  );

  const canPostCurrentDraft =
    allAmountsValid && debitTotal > 0 && debitTotal === creditTotal;

  const isSaving =
    createJournal.isPending || updateJournal.isPending;

  function openCreateForm() {
    setEditingJournal(null);
    setForm(emptyJournalForm());
    setFormOpen(true);
  }

  function openEditForm(entry: JournalEntry) {
    if (entry.status !== "draft") return;

    setEditingJournal(entry);
    setForm({
      journal_date: entry.journal_date,
      description: entry.description,
      reference: entry.reference ?? "",
      lines: entry.lines.map((line) => ({
        account_id: line.account_id,
        description: line.description ?? "",
        debit: line.debit,
        credit: line.credit,
      })),
    });
    setFormOpen(true);
  }

  function changeLine(
    index: number,
    field: keyof JournalLineForm,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      lines: current.lines.map((line, lineIndex) =>
        lineIndex === index ? { ...line, [field]: value } : line,
      ),
    }));
  }

  function removeLine(index: number) {
    setForm((current) => ({
      ...current,
      lines: current.lines.filter((_line, lineIndex) => lineIndex !== index),
    }));
  }

  function closeForm(open: boolean) {
    setFormOpen(open);
    if (!open) setEditingJournal(null);
  }

  function submitJournal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!branchId) {
      toast.error("Select a branch before creating a journal.");
      return;
    }

    if (form.lines.length < 2) {
      toast.error("A journal requires at least two lines.");
      return;
    }

    if (!form.journal_date || !form.description.trim()) {
      toast.error("Enter the journal date and description.");
      return;
    }

    if (form.description.trim().length > 500) {
      toast.error("The description cannot exceed 500 characters.");
      return;
    }

    if (form.reference.trim().length > 100) {
      toast.error("The reference cannot exceed 100 characters.");
      return;
    }

    const normalizedLines: JournalEntryLineRequest[] = [];

    for (let index = 0; index < form.lines.length; index += 1) {
      const line = form.lines[index];
      const debitCents = parseCents(line.debit);
      const creditCents = parseCents(line.credit);

      if (!line.account_id) {
        toast.error(`Select an account for line ${index + 1}.`);
        return;
      }

      if (
        !eligibleAccounts.some((account) => account.id === line.account_id)
      ) {
        toast.error(
          `Select an active, posting-enabled account for line ${index + 1}.`,
        );
        return;
      }

      if (debitCents === null || creditCents === null) {
        toast.error(`Enter valid amounts with at most two decimals on line ${index + 1}.`);
        return;
      }

      if ((debitCents > 0) === (creditCents > 0)) {
        toast.error(
          `Line ${index + 1} must have a positive debit or credit, but not both.`,
        );
        return;
      }

      normalizedLines.push({
        account_id: line.account_id,
        debit: (debitCents / 100).toFixed(2),
        credit: (creditCents / 100).toFixed(2),
        description: line.description.trim() || null,
      });
    }

    const payload: CreateJournalEntryRequest = {
      branch_id: branchId,
      journal_date: form.journal_date,
      description: form.description.trim(),
      reference: form.reference.trim() || null,
      lines: normalizedLines,
    };

    if (editingJournal) {
      updateJournal.mutate(
        {
          id: editingJournal.id,
          data: {
            journal_date: payload.journal_date,
            description: payload.description,
            reference: payload.reference,
            lines: payload.lines,
          },
        },
        {
          onSuccess: () => {
            toast.success("Journal draft updated.");
            setFormOpen(false);
            setEditingJournal(null);
          },
          onError: (error) => toast.error(typeErrorMessage(error)),
        },
      );
      return;
    }

    createJournal.mutate(payload, {
      onSuccess: (entry) => {
        toast.success(`Journal draft ${entry.journal_number} created.`);
        setFormOpen(false);
      },
      onError: (error) => toast.error(typeErrorMessage(error)),
    });
  }

  function confirmPosting() {
    if (!postingTarget) return;

    if (postingTarget.status !== "draft") {
      toast.error("Only a draft journal can be posted.");
      return;
    }

    const debitCents = parseCents(postingTarget.total_debit);
    const creditCents = parseCents(postingTarget.total_credit);

    if (
      debitCents === null ||
      creditCents === null ||
      debitCents <= 0 ||
      debitCents !== creditCents
    ) {
      toast.error("The journal must have positive, equal debit and credit totals before posting.");
      return;
    }

    postJournal.mutate(postingTarget.id, {
      onSuccess: (entry) => {
        toast.success(`${entry.journal_number} posted successfully.`);
        setPostingTarget(null);
      },
      onError: (error) => toast.error(typeErrorMessage(error)),
    });
  }

  function openReversal(entry: JournalEntry) {
    setReversalTarget(entry);
    setReversalForm(emptyReversalForm());
  }

  function submitReversal(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!reversalTarget) return;

    if (!reversalForm.journal_date || !reversalForm.reason.trim()) {
      toast.error("Enter the reversal date and reason.");
      return;
    }

    if (reversalForm.reason.trim().length > 400) {
      toast.error("The reversal reason cannot exceed 400 characters.");
      return;
    }

    reverseJournal.mutate(
      {
        id: reversalTarget.id,
        data: {
          journal_date: reversalForm.journal_date,
          reason: reversalForm.reason.trim(),
        },
      },
      {
        onSuccess: (entry) => {
          toast.success(`Reversal ${entry.journal_number} posted.`);
          setReversalTarget(null);
          setSelectedJournal(null);
        },
        onError: (error) => toast.error(typeErrorMessage(error)),
      },
    );
  }

  const isInitialLoading =
    journalsQuery.isLoading && !journalsQuery.data;

  return (
    <Page>
      <PageHeader>
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Landmark className="size-4" />
            Finance
          </div>
          <PageTitle className="mt-2">Journal Entries</PageTitle>
          <PageDescription>
            Record manual accounting adjustments and review posting activity.
            Drafts can be corrected before posting; posted journals are immutable
            and must be corrected through a separate reversal.
          </PageDescription>
        </div>
        <PageActions>
          <Button
            type="button"
            variant="outline"
            onClick={() => void journalsQuery.refetch()}
            disabled={journalsQuery.isFetching}
          >
            <RefreshCw className={journalsQuery.isFetching ? "animate-spin" : undefined} />
            Refresh
          </Button>
          {canCreate ? (
            <Button
              type="button"
              onClick={openCreateForm}
              disabled={!branchId}
              title={!branchId ? "Select a branch before creating a journal" : undefined}
            >
              <Plus />
              New journal
            </Button>
          ) : null}
        </PageActions>
      </PageHeader>

      <PageContent>
        <div className="grid gap-3 sm:grid-cols-3">
          <StatCard
            label="Loaded journals"
            value={entries.length}
            description="Latest records returned by the API"
          />
          <StatCard
            label="Drafts"
            value={draftCount}
            description="Entries that may still be edited"
          />
          <StatCard
            label="Posted"
            value={postedCount}
            description="Committed entries that cannot be edited"
          />
        </div>

        <PageToolbar>
          <div className="grid w-full gap-3 md:grid-cols-[minmax(16rem,1fr)_12rem]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search journal number, reference, account or description"
                className="pl-8"
                aria-label="Search journal entries"
              />
            </div>
            <select
              aria-label="Filter journals by status"
              className="h-8 rounded-lg border border-input bg-background px-2.5 text-sm"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
            >
              <option value="all">All statuses</option>
              <option value="draft">Draft</option>
              <option value="posted">Posted</option>
            </select>
          </div>
          <div className="shrink-0 text-xs text-muted-foreground">
            Showing <span className="font-semibold text-foreground">{filteredEntries.length}</span> of {entries.length}
          </div>
        </PageToolbar>

        {canCreatePermission && !canReadAccounts ? (
          <div
            role="status"
            className="rounded-lg border bg-muted/20 p-3 text-sm text-muted-foreground"
          >
            Your role can create journal entries but cannot read the Chart of
            Accounts. Ask an administrator to grant the existing
            {" "}finance.accounts.read{" "}permission before creating or editing drafts.
          </div>
        ) : null}

        <PageSection
          title="Journal register"
          description="The register displays up to 100 recent entries within the authenticated tenant and branch scope."
        >
          {isInitialLoading ? (
            <LoadingState
              title="Loading journal entries"
              description="Retrieving journals for the active tenant."
            />
          ) : journalsQuery.isError ? (
            <ErrorState
              title="Unable to load journal entries"
              description={typeErrorMessage(journalsQuery.error)}
              onRetry={() => void journalsQuery.refetch()}
            />
          ) : entries.length === 0 ? (
            <EmptyState
              icon={<BookOpen className="size-12" />}
              title="No journal entries found"
              description="Create a draft journal to begin recording a manual accounting entry."
            />
          ) : filteredEntries.length === 0 ? (
            <EmptyState
              icon={<Search className="size-12" />}
              title="No entries match these filters"
              description="Try a different search phrase or clear the status filter."
              actionLabel="Clear filters"
              onAction={() => {
                setSearch("");
                setStatusFilter("all");
              }}
            />
          ) : (
            <div className="overflow-hidden rounded-xl border bg-background">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Journal</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Description / reference</TableHead>
                    <TableHead className="text-right">Debits</TableHead>
                    <TableHead className="text-right">Credits</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEntries.map((entry) => {
                    const debitCents = parseCents(entry.total_debit);
                    const creditCents = parseCents(entry.total_credit);
                    const isBalanced =
                      debitCents !== null &&
                      creditCents !== null &&
                      debitCents > 0 &&
                      debitCents === creditCents;

                    const canReverseThisEntry =
                      entry.status === "posted" &&
                      !entry.reversal_of_id &&
                      !entry.reversal_journal_number;

                    return (
                      <TableRow key={entry.id}>
                        <TableCell>
                          <div className="font-mono text-xs font-semibold">
                            {entry.journal_number}
                          </div>
                          <div className="mt-1 text-xs text-muted-foreground">
                            {entry.lines.length} lines
                          </div>
                        </TableCell>
                        <TableCell>{entry.journal_date}</TableCell>
                        <TableCell>
                          <div className="max-w-72 whitespace-normal font-medium">
                            {entry.description}
                          </div>
                          {entry.reference ? (
                            <div className="mt-1 text-xs text-muted-foreground">
                              Ref: {entry.reference}
                            </div>
                          ) : null}
                          {entry.reversal_of_id ? (
                            <div className="mt-1 text-xs text-muted-foreground">
                              Reversal of {entry.original_journal_number ?? "original journal"}
                            </div>
                          ) : entry.reversal_journal_number ? (
                            <div className="mt-1 text-xs text-muted-foreground">
                              Reversed by {entry.reversal_journal_number}
                            </div>
                          ) : null}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatMoney(entry.total_debit, entry.currency)}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatMoney(entry.total_credit, entry.currency)}
                        </TableCell>
                        <TableCell>
                          <div className="flex flex-col items-start gap-1">
                            <Badge variant={statusVariant(entry.status)}>
                              {entry.status}
                            </Badge>
                            {entry.status === "draft" && !isBalanced ? (
                              <span className="text-xs text-muted-foreground">Unbalanced</span>
                            ) : null}
                          </div>
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-1">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon-sm"
                              title={`View ${entry.journal_number}`}
                              onClick={() => setSelectedJournal(entry)}
                            >
                              <Eye />
                              <span className="sr-only">View journal</span>
                            </Button>
                            {canManageDrafts && entry.status === "draft" ? (
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon-sm"
                                title={`Edit ${entry.journal_number}`}
                                onClick={() => openEditForm(entry)}
                              >
                                <Pencil />
                                <span className="sr-only">Edit draft</span>
                              </Button>
                            ) : null}
                            {canPost && entry.status === "draft" ? (
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon-sm"
                                title={
                                  isBalanced
                                    ? `Post ${entry.journal_number}`
                                    : "Balance the journal before posting"
                                }
                                disabled={!isBalanced || postJournal.isPending}
                                onClick={() => setPostingTarget(entry)}
                              >
                                <Send />
                                <span className="sr-only">Post journal</span>
                              </Button>
                            ) : null}
                            {canReverse && canReverseThisEntry ? (
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon-sm"
                                title={`Reverse ${entry.journal_number}`}
                                onClick={() => openReversal(entry)}
                              >
                                <RotateCcw />
                                <span className="sr-only">Reverse journal</span>
                              </Button>
                            ) : null}
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}

          <div className="flex items-start gap-2 rounded-lg border bg-muted/20 p-3 text-xs text-muted-foreground">
            <Landmark className="mt-0.5 size-4 shrink-0" />
            <p>
              Journal entries in this register are manual entries only. POS,
              procurement, inventory, payments and M-Pesa transactions are not
              automatically posted by this workflow. Always confirm the date,
              accounts and amounts before posting.
            </p>
          </div>
        </PageSection>
      </PageContent>

      {/* Create or edit a draft */}
      <Dialog open={formOpen} onOpenChange={closeForm}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>
              {editingJournal ? `Edit draft ${editingJournal.journal_number}` : "New journal draft"}
            </DialogTitle>
            <DialogDescription>
              Use one debit or one credit per line. Drafts may be saved while
              unbalanced, but posting requires positive, equal debit and credit totals.
            </DialogDescription>
          </DialogHeader>

          <form className="grid gap-5" onSubmit={submitJournal}>
            <div className="grid gap-4 sm:grid-cols-3">
              <FormField label="Journal date" htmlFor="journal-date">
                <Input
                  id="journal-date"
                  type="date"
                  value={form.journal_date}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      journal_date: event.target.value,
                    }))
                  }
                  required
                />
              </FormField>

              <FormField label="Reference (optional)" htmlFor="journal-reference">
                <Input
                  id="journal-reference"
                  value={form.reference}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      reference: event.target.value,
                    }))
                  }
                  maxLength={100}
                  placeholder="Document or source reference"
                />
              </FormField>

              <div className="flex items-end text-xs text-muted-foreground">
                Currency: KES tenant base currency
              </div>
            </div>

            <FormField label="Description" htmlFor="journal-description">
              <Textarea
                id="journal-description"
                value={form.description}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    description: event.target.value,
                  }))
                }
                maxLength={500}
                required
                placeholder="Explain why this journal is being recorded"
              />
            </FormField>

            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="font-semibold">Journal lines</h3>
                  <p className="text-xs text-muted-foreground">
                    Only active posting accounts for this tenant and branch are shown.
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setForm((current) => ({
                      ...current,
                      lines: [...current.lines, emptyLine()],
                    }))
                  }
                  disabled={form.lines.length >= MAX_VISIBLE_LINES}
                >
                  <Plus />
                  Add line
                </Button>
              </div>

              {accountsQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading chart accounts…</p>
              ) : accountsQuery.isError ? (
                <p className="text-sm text-destructive">
                  Chart accounts could not be loaded. Refresh the page before creating a journal.
                </p>
              ) : eligibleAccounts.length === 0 ? (
                <p className="text-sm text-destructive">
                  No active posting accounts are available for this branch.
                </p>
              ) : (
                <div className="space-y-3">
                  {form.lines.map((line, index) => (
                    <div key={index} className="rounded-xl border p-3">
                      <div className="mb-3 flex items-center justify-between gap-2">
                        <p className="text-sm font-medium">Line {index + 1}</p>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon-sm"
                          title={`Remove line ${index + 1}`}
                          onClick={() => removeLine(index)}
                          disabled={form.lines.length <= 2}
                        >
                          <X />
                          <span className="sr-only">Remove line</span>
                        </Button>
                      </div>

                      <div className="grid gap-3 lg:grid-cols-[minmax(14rem,2fr)_minmax(10rem,2fr)_minmax(7rem,1fr)_minmax(7rem,1fr)]">
                        <FormField
                          label="Posting account"
                          htmlFor={`journal-line-account-${index}`}
                        >
                          <select
                            id={`journal-line-account-${index}`}
                            className="h-9 w-full min-w-0 rounded-lg border border-input bg-background px-2.5 text-sm"
                            value={line.account_id}
                            onChange={(event) =>
                              changeLine(index, "account_id", event.target.value)
                            }
                            required
                          >
                            <option value="">Select account</option>
                            {eligibleAccounts.map((account) => (
                              <option key={account.id} value={account.id}>
                                {account.account_code} — {account.account_name}
                              </option>
                            ))}
                          </select>
                        </FormField>

                        <FormField
                          label="Line description"
                          htmlFor={`journal-line-description-${index}`}
                        >
                          <Input
                            id={`journal-line-description-${index}`}
                            value={line.description}
                            onChange={(event) =>
                              changeLine(index, "description", event.target.value)
                            }
                            maxLength={500}
                            placeholder="Optional"
                          />
                        </FormField>

                        <FormField label="Debit (KES)" htmlFor={`journal-line-debit-${index}`}>
                          <Input
                            id={`journal-line-debit-${index}`}
                            type="number"
                            inputMode="decimal"
                            min="0"
                            step="0.01"
                            value={line.debit}
                            onChange={(event) =>
                              changeLine(index, "debit", event.target.value)
                            }
                            required
                          />
                        </FormField>

                        <FormField label="Credit (KES)" htmlFor={`journal-line-credit-${index}`}>
                          <Input
                            id={`journal-line-credit-${index}`}
                            type="number"
                            inputMode="decimal"
                            min="0"
                            step="0.01"
                            value={line.credit}
                            onChange={(event) =>
                              changeLine(index, "credit", event.target.value)
                            }
                            required
                          />
                        </FormField>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="grid gap-3 rounded-xl border bg-muted/20 p-4 sm:grid-cols-3">
              <div>
                <p className="text-sm text-muted-foreground">Total debit</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {formatMoney(debitTotal / 100)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total credit</p>
                <p className="mt-1 text-lg font-semibold tabular-nums">
                  {formatMoney(creditTotal / 100)}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Balance status</p>
                {canPostCurrentDraft ? (
                  <Badge variant="secondary" className="mt-2">Balanced</Badge>
                ) : (
                  <div className="mt-1 text-sm text-muted-foreground">
                    Difference: {formatMoney(Math.abs(debitTotal - creditTotal) / 100)}
                    <div className="text-xs">Draft may be saved; posting is blocked until balanced.</div>
                  </div>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => closeForm(false)}
                disabled={isSaving}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={
                  isSaving ||
                  !branchId ||
                  accountsQuery.isLoading ||
                  accountsQuery.isError ||
                  eligibleAccounts.length === 0
                }
              >
                {isSaving ? "Saving…" : editingJournal ? "Save draft changes" : "Save draft"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Journal details */}
      <Dialog
        open={Boolean(selectedJournal)}
        onOpenChange={(open) => {
          if (!open) setSelectedJournal(null);
        }}
      >
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-4xl">
          {selectedJournal ? (
            <>
              <DialogHeader>
                <DialogTitle>{selectedJournal.journal_number}</DialogTitle>
                <DialogDescription>
                  {selectedJournal.journal_date} · {selectedJournal.description}
                </DialogDescription>
              </DialogHeader>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={statusVariant(selectedJournal.status)}>
                  {selectedJournal.status}
                </Badge>
                {selectedJournal.reference ? (
                  <span className="text-sm text-muted-foreground">
                    Reference: {selectedJournal.reference}
                  </span>
                ) : null}
                {selectedJournal.reversal_of_id ? (
                  <span className="text-sm text-muted-foreground">
                    Reversal of {selectedJournal.original_journal_number ?? "original journal"}
                  </span>
                ) : null}
                {selectedJournal.reversal_journal_number ? (
                  <span className="text-sm text-muted-foreground">
                    Reversed by {selectedJournal.reversal_journal_number}
                  </span>
                ) : null}
              </div>

              <div className="overflow-hidden rounded-xl border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Account</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Debit</TableHead>
                      <TableHead className="text-right">Credit</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedJournal.lines.map((line) => (
                      <TableRow key={line.id}>
                        <TableCell>
                          <div className="font-mono text-xs text-muted-foreground">
                            {line.account_code ?? "—"}
                          </div>
                          <div className="font-medium">
                            {line.account_name ?? line.account_id}
                          </div>
                        </TableCell>
                        <TableCell className="whitespace-normal">
                          {line.description ?? "—"}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatMoney(line.debit, selectedJournal.currency)}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {formatMoney(line.credit, selectedJournal.currency)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="grid gap-3 rounded-xl border bg-muted/20 p-4 sm:grid-cols-2">
                <div>
                  <p className="text-sm text-muted-foreground">Total debit</p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(selectedJournal.total_debit, selectedJournal.currency)}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total credit</p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(selectedJournal.total_credit, selectedJournal.currency)}
                  </p>
                </div>
              </div>
            </>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Explicit post confirmation */}
      <Dialog
        open={Boolean(postingTarget)}
        onOpenChange={(open) => {
          if (!open) setPostingTarget(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Post journal entry?</DialogTitle>
            <DialogDescription>
              {postingTarget
                ? `You are about to post ${postingTarget.journal_number}. Posting makes the entry immutable. Corrections require a separate reversal journal.`
                : ""}
            </DialogDescription>
          </DialogHeader>
          {postingTarget ? (
            <div className="rounded-lg border bg-muted/20 p-3 text-sm">
              <p className="font-medium">{postingTarget.description}</p>
              <div className="mt-2 flex justify-between gap-4 text-muted-foreground">
                <span>Debits</span>
                <span>{formatMoney(postingTarget.total_debit, postingTarget.currency)}</span>
              </div>
              <div className="mt-1 flex justify-between gap-4 text-muted-foreground">
                <span>Credits</span>
                <span>{formatMoney(postingTarget.total_credit, postingTarget.currency)}</span>
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setPostingTarget(null)}
              disabled={postJournal.isPending}
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={confirmPosting}
              disabled={postJournal.isPending}
            >
              {postJournal.isPending ? "Posting…" : "Confirm posting"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reversal date and reason */}
      <Dialog
        open={Boolean(reversalTarget)}
        onOpenChange={(open) => {
          if (!open) setReversalTarget(null);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reverse posted journal</DialogTitle>
            <DialogDescription>
              {reversalTarget
                ? `A separate reversal journal will be created for ${reversalTarget.journal_number}. The original posted entry will remain unchanged.`
                : ""}
            </DialogDescription>
          </DialogHeader>

          <form className="grid gap-4" onSubmit={submitReversal}>
            <FormField label="Reversal date" htmlFor="journal-reversal-date">
              <Input
                id="journal-reversal-date"
                type="date"
                value={reversalForm.journal_date}
                onChange={(event) =>
                  setReversalForm((current) => ({
                    ...current,
                    journal_date: event.target.value,
                  }))
                }
                required
              />
            </FormField>
            <FormField label="Reason for reversal" htmlFor="journal-reversal-reason">
              <Textarea
                id="journal-reversal-reason"
                value={reversalForm.reason}
                onChange={(event) =>
                  setReversalForm((current) => ({
                    ...current,
                    reason: event.target.value,
                  }))
                }
                maxLength={400}
                placeholder="Explain why the original posting must be reversed"
                required
              />
            </FormField>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setReversalTarget(null)}
                disabled={reverseJournal.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={reverseJournal.isPending}
              >
                {reverseJournal.isPending ? "Reversing…" : "Confirm reversal"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Page>
  );
}

export default JournalEntriesPage;
