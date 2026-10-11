import {
  BookOpen,
  Building2,
  Eye,
  Landmark,
  LockKeyhole,
  Pencil,
  Plus,
  RefreshCw,
  Search,
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
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuthorization } from "@/hooks/useAuthorization";
import { useQueryScope } from "@/hooks/useQueryScope";
import {
  useChartOfAccounts,
  useCreateChartOfAccount,
  useUpdateChartOfAccount,
} from "@/hooks/queries/finance";
import type {
  ChartOfAccount,
  ChartOfAccountType,
  NormalBalance,
} from "@/services/finance";

const ACCOUNT_TYPES: readonly ChartOfAccountType[] = [
  "asset",
  "liability",
  "equity",
  "revenue",
  "expense",
];

type TypeFilter = "all" | ChartOfAccountType;
type StatusFilter = "all" | "active" | "inactive";

interface AccountFormState {
  account_code: string;
  account_name: string;
  account_type: ChartOfAccountType;
  normal_balance: NormalBalance;
  parent_id: string;
  description: string;
  is_active: boolean;
}

const EMPTY_FORM: AccountFormState = {
  account_code: "",
  account_name: "",
  account_type: "asset",
  normal_balance: "debit",
  parent_id: "",
  description: "",
  is_active: true,
};

function defaultNormalBalance(type: ChartOfAccountType): NormalBalance {
  return type === "asset" || type === "expense" ? "debit" : "credit";
}

function typeLabel(type: ChartOfAccountType): string {
  return type.charAt(0).toUpperCase() + type.slice(1);
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The request could not be completed.";
}

function isDescendant(
  candidateId: string,
  ancestorId: string,
  accounts: ChartOfAccount[],
): boolean {
  const byId = new Map(accounts.map((account) => [account.id, account]));
  let current = byId.get(candidateId);
  const seen = new Set<string>();
  while (current?.parent_id) {
    if (current.parent_id === ancestorId) return true;
    if (seen.has(current.parent_id)) return true;
    seen.add(current.parent_id);
    current = byId.get(current.parent_id);
  }
  return false;
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

export function ChartOfAccountsPage() {
  const authorization = useAuthorization();
  const { branchId } = useQueryScope();
  const accountsQuery = useChartOfAccounts();
  const createAccount = useCreateChartOfAccount();
  const updateAccount = useUpdateChartOfAccount();

  const accounts = useMemo(
    () => accountsQuery.data ?? [],
    [accountsQuery.data],
  );
  const canCreate = authorization.can("finance.accounts.create");
  const canUpdate = authorization.can("finance.accounts.update");

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState<ChartOfAccount | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<ChartOfAccount | null>(null);
  const [form, setForm] = useState<AccountFormState>(EMPTY_FORM);

  const filteredAccounts = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return accounts.filter((account) => {
      const matchesSearch = !needle || [
        account.account_code,
        account.account_name,
        account.description ?? "",
        account.parent?.account_code ?? "",
        account.parent?.account_name ?? "",
      ].some((value) => value.toLowerCase().includes(needle));
      const matchesType = typeFilter === "all" || account.account_type === typeFilter;
      const matchesStatus = statusFilter === "all" ||
        (statusFilter === "active" ? account.is_active : !account.is_active);
      return matchesSearch && matchesType && matchesStatus;
    });
  }, [accounts, search, statusFilter, typeFilter]);

  const parentCandidates = useMemo(() => accounts.filter((account) => {
    if (!account.is_active || account.account_type !== form.account_type) return false;
    if (account.id === editingAccount?.id) return false;
    if (editingAccount && isDescendant(account.id, editingAccount.id, accounts)) return false;
    return account.branch_id === null || account.branch_id === branchId;
  }), [accounts, branchId, editingAccount, form.account_type]);

  const activeCount = accounts.filter((account) => account.is_active).length;
  const systemCount = accounts.filter((account) => account.is_system_account).length;
  const customCount = accounts.length - systemCount;
  const isSaving = createAccount.isPending || updateAccount.isPending;

  const openCreate = () => {
    setEditingAccount(null);
    setForm({ ...EMPTY_FORM });
    setFormOpen(true);
  };

  const openEdit = (account: ChartOfAccount) => {
    setEditingAccount(account);
    setForm({
      account_code: account.account_code,
      account_name: account.account_name,
      account_type: account.account_type,
      normal_balance: account.normal_balance,
      parent_id: account.parent_id ?? "",
      description: account.description ?? "",
      is_active: account.is_active,
    });
    setFormOpen(true);
  };

  const handleFormOpenChange = (open: boolean) => {
    setFormOpen(open);
    if (!open) setEditingAccount(null);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const accountName = form.account_name.trim();
    if (!accountName) {
      toast.error("Enter an account name.");
      return;
    }

    const commonPayload = {
      account_name: accountName,
      account_type: form.account_type,
      normal_balance: form.normal_balance,
      parent_id: form.parent_id || null,
      description: form.description.trim() || null,
    };

    if (editingAccount) {
      updateAccount.mutate(
        {
          id: editingAccount.id,
          data: { ...commonPayload, is_active: form.is_active },
        },
        {
          onSuccess: () => {
            toast.success("Chart account updated.");
            setFormOpen(false);
            setEditingAccount(null);
          },
          onError: (error) => toast.error(getErrorMessage(error)),
        },
      );
      return;
    }

    if (!branchId) {
      toast.error("Select a branch before creating a custom account.");
      return;
    }

    const accountCode = form.account_code.trim();
    if (!accountCode) {
      toast.error("Enter an account code.");
      return;
    }

    createAccount.mutate(
      {
        account_code: accountCode,
        ...commonPayload,
        branch_id: branchId,
      },
      {
        onSuccess: () => {
          toast.success("Chart account created.");
          setFormOpen(false);
        },
        onError: (error) => toast.error(getErrorMessage(error)),
      },
    );
  };

  const isInitialLoading = accountsQuery.isLoading && !accountsQuery.data;
  const isFilteredEmpty = accounts.length > 0 && filteredAccounts.length === 0;

  return (
    <Page>
      <PageHeader>
        <div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Landmark className="size-4" />
            Finance
          </div>
          <PageTitle className="mt-2">Chart of Accounts</PageTitle>
          <PageDescription>
            Manage the account structure used to classify pharmacy assets, liabilities,
            equity, revenue and expenses. This is the account catalogue; it does not
            contain balances or posted journal transactions.
          </PageDescription>
        </div>
        <PageActions>
          <Button
            type="button"
            variant="outline"
            onClick={() => void accountsQuery.refetch()}
            disabled={accountsQuery.isFetching}
          >
            <RefreshCw className={accountsQuery.isFetching ? "animate-spin" : undefined} />
            Refresh
          </Button>
          {canCreate ? (
            <Button
              type="button"
              onClick={openCreate}
              disabled={!branchId}
              title={!branchId ? "Select a branch before creating a custom account" : undefined}
            >
              <Plus />
              New account
            </Button>
          ) : null}
        </PageActions>
      </PageHeader>

      <PageContent>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Total accounts" value={accounts.length} description="Across the current tenant and branch scope" />
          <StatCard label="Active accounts" value={activeCount} description="Available for future finance workflows" />
          <StatCard label="Standard accounts" value={systemCount} description="Seeded defaults with protected structure" />
          <StatCard label="Custom accounts" value={customCount} description="Tenant-created branch accounts" />
        </div>

        <PageToolbar>
          <div className="grid w-full gap-3 md:grid-cols-[minmax(16rem,1fr)_12rem_10rem]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search code, account, parent or description"
                className="pl-8"
                aria-label="Search chart of accounts"
              />
            </div>
            <select
              aria-label="Filter by account type"
              className="h-8 rounded-lg border border-input bg-background px-2.5 text-sm"
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value as TypeFilter)}
            >
              <option value="all">All account types</option>
              {ACCOUNT_TYPES.map((type) => <option key={type} value={type}>{typeLabel(type)}</option>)}
            </select>
            <select
              aria-label="Filter by status"
              className="h-8 rounded-lg border border-input bg-background px-2.5 text-sm"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
            >
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div className="shrink-0 text-xs text-muted-foreground">
            Showing <span className="font-semibold text-foreground">{filteredAccounts.length}</span> of {accounts.length}
          </div>
        </PageToolbar>

        <PageSection title="Accounts" description="Standard accounts are protected. Custom accounts created here belong to the selected branch.">
          {isInitialLoading ? (
            <LoadingState title="Loading Chart of Accounts" description="Retrieving accounts for the active tenant." />
          ) : accountsQuery.isError ? (
            <ErrorState
              title="Unable to load Chart of Accounts"
              description={getErrorMessage(accountsQuery.error)}
              onRetry={() => void accountsQuery.refetch()}
            />
          ) : accounts.length === 0 ? (
            <EmptyState
              icon={<BookOpen className="size-12" />}
              title="No chart accounts found"
              description="The current tenant has no Chart of Accounts records. Confirm that the default chart has been initialized for this tenant."
            />
          ) : isFilteredEmpty ? (
            <EmptyState
              icon={<Search className="size-12" />}
              title="No accounts match these filters"
              description="Try a different search phrase or clear the account-type and status filters."
              actionLabel="Clear filters"
              onAction={() => { setSearch(""); setTypeFilter("all"); setStatusFilter("all"); }}
            />
          ) : (
            <div className="overflow-hidden rounded-xl border bg-background">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Normal balance</TableHead>
                    <TableHead>Parent</TableHead>
                    <TableHead>Scope</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAccounts.map((account) => {
                    const canEditThisAccount = canUpdate &&
                      !account.is_system_account &&
                      Boolean(branchId) &&
                      account.branch_id === branchId;
                    return (
                      <TableRow key={account.id}>
                        <TableCell>
                          <div className={`min-w-44 ${account.parent_id ? "pl-5" : ""}`}>
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs text-muted-foreground">{account.account_code}</span>
                              {account.is_system_account ? (
                                <span title="Protected standard account"><LockKeyhole className="size-3.5 text-muted-foreground" /></span>
                              ) : null}
                            </div>
                            <div className="mt-0.5 font-medium">{account.account_name}</div>
                          </div>
                        </TableCell>
                        <TableCell><Badge variant="outline">{typeLabel(account.account_type)}</Badge></TableCell>
                        <TableCell><span className="capitalize">{account.normal_balance}</span></TableCell>
                        <TableCell>
                          {account.parent ? (
                            <span className="text-sm"><span className="font-mono text-xs text-muted-foreground">{account.parent.account_code}</span> {account.parent.account_name}</span>
                          ) : <span className="text-muted-foreground">—</span>}
                        </TableCell>
                        <TableCell>
                          <span className="inline-flex items-center gap-1.5 text-sm text-muted-foreground">
                            {account.branch ? <Building2 className="size-3.5" /> : <Landmark className="size-3.5" />}
                            {account.branch?.name ?? "All branches"}
                          </span>
                        </TableCell>
                        <TableCell>
                          <Badge variant={account.is_active ? "secondary" : "outline"}>
                            {account.is_active ? "Active" : "Inactive"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-1">
                            <Button type="button" variant="ghost" size="icon-sm" title={`View ${account.account_name}`} onClick={() => setSelectedAccount(account)}>
                              <Eye /><span className="sr-only">View account</span>
                            </Button>
                            {canEditThisAccount ? (
                              <Button type="button" variant="ghost" size="icon-sm" title={`Edit ${account.account_name}`} onClick={() => openEdit(account)}>
                                <Pencil /><span className="sr-only">Edit account</span>
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
            <LockKeyhole className="mt-0.5 size-4 shrink-0" />
            <p>Standard seeded accounts are tenant-wide and their structure is protected. This first UI release creates branch-scoped custom accounts only; posted balances and journal activity will be added in later Finance checkpoints.</p>
          </div>
        </PageSection>
      </PageContent>

      <Dialog open={formOpen} onOpenChange={handleFormOpenChange}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingAccount ? "Edit custom account" : "Create custom account"}</DialogTitle>
            <DialogDescription>
              {editingAccount
                ? "Update the account's descriptive and classification fields. Standard seeded accounts cannot be edited here."
                : "Create a branch-scoped account. Its code must be unique across the tenant."}
            </DialogDescription>
          </DialogHeader>
          <form className="grid gap-4" onSubmit={handleSubmit}>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="finance-account-code">Account code</Label>
                <Input
                  id="finance-account-code"
                  value={form.account_code}
                  onChange={(event) => setForm((current) => ({ ...current, account_code: event.target.value }))}
                  maxLength={30}
                  autoComplete="off"
                  disabled={Boolean(editingAccount)}
                  required={!editingAccount}
                  placeholder="e.g. 6700"
                />
                {editingAccount ? <p className="text-xs text-muted-foreground">Account codes stay fixed in this UI to avoid accidental reclassification.</p> : null}
              </div>
              <div className="space-y-2">
                <Label htmlFor="finance-account-name">Account name</Label>
                <Input
                  id="finance-account-name"
                  value={form.account_name}
                  onChange={(event) => setForm((current) => ({ ...current, account_name: event.target.value }))}
                  maxLength={200}
                  required
                  autoComplete="off"
                  placeholder="Enter account name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="finance-account-type">Account type</Label>
                <select
                  id="finance-account-type"
                  className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                  value={form.account_type}
                  onChange={(event) => {
                    const accountType = event.target.value as ChartOfAccountType;
                    setForm((current) => ({ ...current, account_type: accountType, normal_balance: defaultNormalBalance(accountType), parent_id: "" }));
                  }}
                >
                  {ACCOUNT_TYPES.map((type) => <option key={type} value={type}>{typeLabel(type)}</option>)}
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="finance-account-normal-balance">Normal balance</Label>
                <select
                  id="finance-account-normal-balance"
                  className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                  value={form.normal_balance}
                  onChange={(event) => setForm((current) => ({ ...current, normal_balance: event.target.value as NormalBalance }))}
                >
                  {form.account_type === "revenue" ? (
                    <>
                      <option value="credit">Credit</option>
                      <option value="debit">Debit (contra-revenue)</option>
                    </>
                  ) : (
                    <option value={defaultNormalBalance(form.account_type)}>
                      {defaultNormalBalance(form.account_type) === "debit" ? "Debit" : "Credit"}
                    </option>
                  )}
                </select>
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="finance-account-parent">Parent account (optional)</Label>
                <select
                  id="finance-account-parent"
                  className="h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                  value={form.parent_id}
                  onChange={(event) => setForm((current) => ({ ...current, parent_id: event.target.value }))}
                >
                  <option value="">No parent — top-level account</option>
                  {parentCandidates.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.account_code} — {account.account_name}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-muted-foreground">Parent choices are limited to active accounts of the same type in this tenant/branch scope.</p>
              </div>
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="finance-account-description">Description (optional)</Label>
                <Textarea
                  id="finance-account-description"
                  value={form.description}
                  onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                  maxLength={5000}
                  placeholder="Explain the intended use of this account"
                />
              </div>
            </div>
            {editingAccount ? (
              <label className="flex items-start gap-3 rounded-lg border p-3 text-sm">
                <input
                  type="checkbox"
                  className="mt-0.5 size-4 accent-primary"
                  checked={form.is_active}
                  onChange={(event) => setForm((current) => ({ ...current, is_active: event.target.checked }))}
                />
                <span>
                  <span className="block font-medium">Account is active</span>
                  <span className="text-xs text-muted-foreground">Deactivation is blocked by the backend when active child accounts exist.</span>
                </span>
              </label>
            ) : null}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => handleFormOpenChange(false)} disabled={isSaving}>Cancel</Button>
              <Button type="submit" disabled={isSaving || (!editingAccount && !branchId)}>
                {isSaving ? "Saving…" : editingAccount ? "Save changes" : "Create account"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(selectedAccount)} onOpenChange={(open) => { if (!open) setSelectedAccount(null); }}>
        <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
          <DialogHeader>
            <DialogTitle>Account details</DialogTitle>
            <DialogDescription>Account master data only; balance and posted activity are not yet part of this checkpoint.</DialogDescription>
          </DialogHeader>
          {selectedAccount ? (
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">Account code</p><p className="mt-1 font-mono font-semibold">{selectedAccount.account_code}</p></div>
              <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">Currency</p><p className="mt-1 font-semibold">{selectedAccount.currency ?? "Tenant base currency"}</p></div>
              <div className="rounded-lg border p-3 sm:col-span-2"><p className="text-xs text-muted-foreground">Account name</p><p className="mt-1 font-semibold">{selectedAccount.account_name}</p></div>
              <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">Account type</p><p className="mt-1">{typeLabel(selectedAccount.account_type)}</p></div>
              <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">Normal balance</p><p className="mt-1 capitalize">{selectedAccount.normal_balance}</p></div>
              <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">Parent account</p><p className="mt-1">{selectedAccount.parent ? `${selectedAccount.parent.account_code} — ${selectedAccount.parent.account_name}` : "No parent"}</p></div>
              <div className="rounded-lg border p-3"><p className="text-xs text-muted-foreground">Scope</p><p className="mt-1">{selectedAccount.branch?.name ?? "All branches"}</p></div>
              <div className="rounded-lg border p-3 sm:col-span-2"><p className="text-xs text-muted-foreground">Description</p><p className="mt-1 whitespace-pre-wrap">{selectedAccount.description || "No description provided."}</p></div>
              <div className="flex flex-wrap items-center gap-2 sm:col-span-2">
                <Badge variant={selectedAccount.is_active ? "secondary" : "outline"}>{selectedAccount.is_active ? "Active" : "Inactive"}</Badge>
                {selectedAccount.is_system_account ? <Badge variant="outline"><LockKeyhole className="mr-1 size-3" />Standard protected account</Badge> : <Badge variant="outline">Custom account</Badge>}
              </div>
            </div>
          ) : null}
          <DialogFooter>
            {selectedAccount && canUpdate && !selectedAccount.is_system_account && selectedAccount.branch_id === branchId ? (
              <Button type="button" variant="outline" onClick={() => { const account = selectedAccount; setSelectedAccount(null); openEdit(account); }}><Pencil /> Edit account</Button>
            ) : null}
            <Button type="button" onClick={() => setSelectedAccount(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Page>
  );
}
