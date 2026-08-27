import {
  Eye,
  RefreshCcw,
  Search,
} from "lucide-react";
import {
  type FormEvent,
  useMemo,
  useState,
} from "react";
import {
  Link,
} from "react-router-dom";

import {
  Page,
  PageContent,
  PageDescription,
  PageHeader,
  PageSection,
  PageTitle,
  PageToolbar,
} from "@/components/page";
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
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
import {
  useSales,
} from "@/hooks/queries/sales";
import { useQueryScope } from "@/hooks/useQueryScope";
import { PATHS } from "@/routes/routes";
import {
  SALE_STATUSES,
} from "@/types/enums";
import type {
  ListSalesRequest,
} from "@/types/requests";
import type {
  SaleSummary,
} from "@/types/responses";

const PAGE_SIZE = 10;

const STATUS_OPTIONS = [
  SALE_STATUSES.PAID,
  SALE_STATUSES.PARTIALLY_PAID,
  SALE_STATUSES.PARTIALLY_REFUNDED,
  SALE_STATUSES.REFUNDED,
  SALE_STATUSES.VOIDED,
];

function displayDate(value: string | null): string {
  if (!value) {
    return "Not recorded";
  }

  return new Date(value).toLocaleString();
}

function displayMoney(value: string): string {
  return value;
}

function customerLabel(sale: SaleSummary): string {
  if (!sale.customer) {
    return "Walk-in";
  }

  return sale.customer.full_name || sale.customer.customer_number;
}

function cashierLabel(sale: SaleSummary): string {
  if (!sale.cashier) {
    return "Not recorded";
  }

  return sale.cashier.name || sale.cashier.username || sale.cashier.id;
}

function tillLabel(sale: SaleSummary): string {
  if (!sale.till) {
    return "Not recorded";
  }

  return `${sale.till.code} - ${sale.till.name}`;
}

function hasFilters(filters: ListSalesRequest): boolean {
  return Boolean(
    filters.search ||
      filters.date_from ||
      filters.date_to ||
      filters.status,
  );
}

export function SalesHistoryPage() {
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    searchInput,
    setSearchInput,
  ] = useState("");
  const [
    dateFromInput,
    setDateFromInput,
  ] = useState("");
  const [
    dateToInput,
    setDateToInput,
  ] = useState("");
  const [
    statusInput,
    setStatusInput,
  ] = useState("");
  const [
    page,
    setPage,
  ] = useState(1);
  const [
    submittedFilters,
    setSubmittedFilters,
  ] = useState<ListSalesRequest>({
    page: 1,
    per_page: PAGE_SIZE,
  });

  const queryParams = useMemo(
    () => ({
      ...submittedFilters,
      page,
      per_page: PAGE_SIZE,
    }),
    [page, submittedFilters],
  );

  const salesQuery = useSales(queryParams);
  const items = salesQuery.data?.items ?? [];
  const pagination = salesQuery.data?.pagination;

  const submitFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
    setSubmittedFilters({
      page: 1,
      per_page: PAGE_SIZE,
      ...(searchInput.trim()
        ? { search: searchInput.trim() }
        : {}),
      ...(dateFromInput
        ? { date_from: dateFromInput }
        : {}),
      ...(dateToInput
        ? { date_to: dateToInput }
        : {}),
      ...(statusInput
        ? { status: statusInput }
        : {}),
    });
  };

  const clearFilters = () => {
    setSearchInput("");
    setDateFromInput("");
    setDateToInput("");
    setStatusInput("");
    setPage(1);
    setSubmittedFilters({
      page: 1,
      per_page: PAGE_SIZE,
    });
  };

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Sales History</PageTitle>
          <PageDescription>
            Branch sales with persisted receipt reprint.
          </PageDescription>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => void salesQuery.refetch()}
          disabled={salesQuery.isFetching}
        >
          <RefreshCcw className="size-4" />
          Refresh
        </Button>
      </PageHeader>

      <PageContent>
        {!isBranchScopeReady ? (
          <Alert>
            <AlertTitle>Branch required</AlertTitle>
            <AlertDescription>
              Select an active branch before viewing Sales History.
            </AlertDescription>
          </Alert>
        ) : null}

        <PageSection>
          <PageToolbar>
            <form
              className="grid w-full gap-3 lg:grid-cols-[1fr_160px_160px_180px_auto_auto]"
              onSubmit={submitFilters}
            >
              <div className="relative">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={searchInput}
                  onChange={(event) =>
                    setSearchInput(event.target.value)
                  }
                  placeholder="Sale number or customer"
                  className="pl-8"
                />
              </div>
              <DateField
                label="From"
                value={dateFromInput}
                onChange={setDateFromInput}
              />
              <DateField
                label="To"
                value={dateToInput}
                onChange={setDateToInput}
              />
              <select
                value={statusInput}
                onChange={(event) =>
                  setStatusInput(event.target.value)
                }
                className="h-9 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="">All statuses</option>
                {STATUS_OPTIONS.map((status) => (
                  <option
                    key={status}
                    value={status}
                  >
                    {status.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
              <Button type="submit">
                <Search className="size-4" />
                Search
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={clearFilters}
              >
                Clear
              </Button>
            </form>
          </PageToolbar>
        </PageSection>

        {salesQuery.isError ? (
          <Alert variant="destructive">
            <AlertTitle>Sales History unavailable</AlertTitle>
            <AlertDescription>
              {salesQuery.error.message}
            </AlertDescription>
          </Alert>
        ) : null}

        <PageSection>
          <div className="overflow-hidden rounded-md border bg-background">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sale</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Customer</TableHead>
                  <TableHead>Cashier</TableHead>
                  <TableHead>Till</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Total</TableHead>
                  <TableHead className="text-right">Paid</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {salesQuery.isLoading ? (
                  <TableRow>
                    <TableCell
                      colSpan={10}
                      className="py-8 text-center text-sm text-muted-foreground"
                    >
                      Loading sales...
                    </TableCell>
                  </TableRow>
                ) : items.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={10}
                      className="py-8 text-center text-sm text-muted-foreground"
                    >
                      {hasFilters(submittedFilters)
                        ? "No sales match the current filters."
                        : "No sales exist for this branch."}
                    </TableCell>
                  </TableRow>
                ) : (
                  items.map((sale) => (
                    <TableRow key={sale.id}>
                      <TableCell className="font-medium">
                        {sale.sale_number || sale.id}
                      </TableCell>
                      <TableCell>
                        {displayDate(sale.sold_at)}
                      </TableCell>
                      <TableCell>
                        {customerLabel(sale)}
                      </TableCell>
                      <TableCell>
                        {cashierLabel(sale)}
                      </TableCell>
                      <TableCell>
                        {tillLabel(sale)}
                      </TableCell>
                      <TableCell className="capitalize">
                        {(sale.status || "unknown").replaceAll("_", " ")}
                      </TableCell>
                      <TableCell className="text-right">
                        {displayMoney(sale.total_amount)}
                      </TableCell>
                      <TableCell className="text-right">
                        {displayMoney(sale.paid_amount)}
                      </TableCell>
                      <TableCell className="text-right">
                        {displayMoney(sale.balance_due)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Link
                          to={PATHS.SALES.receipt(sale.id)}
                          className={buttonVariants({
                            variant: "outline",
                            size: "sm",
                          })}
                        >
                          <Eye className="size-4" />
                          Receipt
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="text-muted-foreground">
              Page {pagination?.page ?? page} of {pagination?.pages ?? 1}
              {pagination ? ` · ${pagination.total} sales` : ""}
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={!pagination?.has_prev || salesQuery.isFetching}
              >
                Previous
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => setPage((current) => current + 1)}
                disabled={!pagination?.has_next || salesQuery.isFetching}
              >
                Next
              </Button>
            </div>
          </div>
        </PageSection>
      </PageContent>
    </Page>
  );
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="grid gap-1">
      <Label className="sr-only">{label}</Label>
      <Input
        type="date"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label={label}
      />
    </div>
  );
}

export default SalesHistoryPage;
