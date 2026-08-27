import {
  ArrowLeft,
  ClipboardList,
  Eye,
  Plus,
  RefreshCw,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
import {
  Link,
} from "react-router-dom";

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
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  useStockCounts,
} from "@/hooks/queries/inventory";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import {
  useAuthorization,
} from "@/hooks/useAuthorization";
import { useQueryScope } from "@/hooks/useQueryScope";
import { PATHS } from "@/routes/routes";
import type {
  ListStockCountsRequest,
} from "@/types/requests";
import type {
  StockCountListItem,
} from "@/types/responses";

const PAGE_SIZE = 25;

type StockCountStatus = NonNullable<ListStockCountsRequest["status"]>;

const STATUS_OPTIONS: Array<{
  value: StockCountStatus;
  label: string;
}> = [
  {
    value: "open",
    label: "Open",
  },
  {
    value: "completed",
    label: "Completed",
  },
  {
    value: "cancelled",
    label: "Cancelled",
  },
];

function dateTimeLabel(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString();
}

function statusLabel(value: string): string {
  return STATUS_OPTIONS.find((option) => option.value === value)?.label ??
    value.replaceAll("_", " ");
}

function statusVariant(value: string): "default" | "outline" | "secondary" {
  if (value === "open") {
    return "default";
  }
  if (value === "completed") {
    return "secondary";
  }
  return "outline";
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

export function StockCountsPage() {
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    page,
    setPage,
  ] = useState(1);
  const [
    status,
    setStatus,
  ] = useState<StockCountStatus | "">("");
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    dateFrom,
    setDateFrom,
  ] = useState("");
  const [
    dateTo,
    setDateTo,
  ] = useState("");

  const params = useMemo(
    () => ({
      page,
      per_page: PAGE_SIZE,
      status: status || undefined,
      warehouse_id: warehouseId || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [
      dateFrom,
      dateTo,
      page,
      status,
      warehouseId,
    ],
  );

  const countsQuery = useStockCounts(params);
  const warehousesQuery = useWarehouses();
  const authorization = useAuthorization();
  const counts = countsQuery.data?.items ?? [];
  const pagination = countsQuery.data?.pagination;
  const warehouses = useMemo(
    () => (warehousesQuery.data ?? []).filter((warehouse) => warehouse.is_active),
    [warehousesQuery.data],
  );
  const hasFilters =
    status.length > 0 ||
    warehouseId.length > 0 ||
    dateFrom.length > 0 ||
    dateTo.length > 0;
  const canReadInventory = authorization.can("inventory.read");

  const resetFilters = () => {
    setPage(1);
    setStatus("");
    setWarehouseId("");
    setDateFrom("");
    setDateTo("");
  };

  if (!isBranchScopeReady) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>Stock Counts</PageTitle>
            <PageDescription>
              Select an active branch before viewing Stock Counts.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <EmptyState
              title="Branch required"
              description="Stock Counts are branch-scoped."
            />
          </PageSection>
        </PageContent>
      </Page>
    );
  }

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Stock Counts</PageTitle>
          <PageDescription>
            Create, perform, complete, cancel, and revisit physical stock observations.
          </PageDescription>
        </div>

        <PageActions>
          {canReadInventory ? (
            <Link
              to={PATHS.INVENTORY.ROOT}
              className={buttonVariants({
                variant: "outline",
              })}
            >
              <ArrowLeft />
              Inventory
            </Link>
          ) : null}
          <Button
            type="button"
            variant="outline"
            onClick={() => countsQuery.refetch()}
            disabled={countsQuery.isFetching}
          >
            <RefreshCw
              className={countsQuery.isFetching ? "animate-spin" : undefined}
            />
            Refresh
          </Button>
          <Link
            to={PATHS.INVENTORY.STOCK_COUNT_NEW}
            className={buttonVariants()}
          >
            <Plus />
            New Stock Count
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageSection>
          <PageToolbar>
            <div className="grid w-full gap-3 lg:grid-cols-[180px_minmax(220px,1fr)_160px_160px_auto]">
              <NativeSelect
                value={status}
                onChange={(value) => {
                  setPage(1);
                  setStatus(value as StockCountStatus | "");
                }}
                placeholder="All statuses"
                options={STATUS_OPTIONS}
              />

              <NativeSelect
                value={warehouseId}
                onChange={(value) => {
                  setPage(1);
                  setWarehouseId(value);
                }}
                placeholder={
                  warehousesQuery.isLoading
                    ? "Loading warehouses"
                    : "All warehouses"
                }
                options={warehouses.map((warehouse) => ({
                  value: warehouse.id,
                  label: `${warehouse.code} - ${warehouse.name}`,
                }))}
              />

              <Input
                type="date"
                value={dateFrom}
                onChange={(event) => {
                  setPage(1);
                  setDateFrom(event.target.value);
                }}
                aria-label="Started from"
              />

              <Input
                type="date"
                value={dateTo}
                onChange={(event) => {
                  setPage(1);
                  setDateTo(event.target.value);
                }}
                aria-label="Started to"
              />

              {hasFilters ? (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={resetFilters}
                >
                  Clear
                </Button>
              ) : null}
            </div>
          </PageToolbar>

          {countsQuery.isLoading ? (
            <LoadingState title="Loading Stock Counts" />
          ) : countsQuery.isError ? (
            <ErrorState
              title="Stock Counts unavailable"
              description={errorMessage(countsQuery.error)}
            />
          ) : counts.length === 0 ? (
            <EmptyState
              icon={<ClipboardList className="h-12 w-12" />}
              title={
                hasFilters
                  ? "No Stock Counts matched"
                  : "No Stock Counts recorded"
              }
              description={
                hasFilters
                  ? "Adjust the filters to widen the Stock Count list."
                  : "Create a Stock Count to snapshot Warehouse stock for physical observation."
              }
            />
          ) : (
            <StockCountsTable counts={counts} />
          )}

          {pagination ? (
            <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
              <span>
                Page {pagination.page} of {Math.max(pagination.pages, 1)} · {pagination.total} Stock Counts
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                  disabled={!pagination.has_prev}
                >
                  Previous
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((value) => value + 1)}
                  disabled={!pagination.has_next}
                >
                  Next
                </Button>
              </div>
            </div>
          ) : null}
        </PageSection>
      </PageContent>
    </Page>
  );
}

function StockCountsTable({
  counts,
}: {
  counts: StockCountListItem[];
}) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full min-w-[980px] text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Count #</th>
            <th className="px-3 py-2 font-medium">Warehouse</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 font-medium">Started</th>
            <th className="px-3 py-2 font-medium">Started By</th>
            <th className="px-3 py-2 text-right font-medium">Progress</th>
            <th className="px-3 py-2 text-right font-medium">Variance Lines</th>
            <th className="px-3 py-2 font-medium">Completed</th>
            <th className="px-3 py-2 text-right font-medium">Action</th>
          </tr>
        </thead>
        <tbody>
          {counts.map((count) => (
            <tr
              key={count.id}
              className="border-t"
            >
              <td className="px-3 py-3 font-medium">
                {count.count_number}
              </td>
              <td className="px-3 py-3">
                {count.warehouse.code} · {count.warehouse.name}
              </td>
              <td className="px-3 py-3">
                <Badge variant={statusVariant(count.status)}>
                  {statusLabel(count.status)}
                </Badge>
              </td>
              <td className="px-3 py-3">
                {dateTimeLabel(count.started_at)}
              </td>
              <td className="px-3 py-3">
                {count.started_by?.name ??
                  count.started_by?.username ??
                  "Unknown"}
              </td>
              <td className="px-3 py-3 text-right">
                {count.summary.counted_items} / {count.summary.total_items}
              </td>
              <td className="px-3 py-3 text-right">
                {count.summary.variance_items}
                <div className="text-xs text-muted-foreground">
                  {count.summary.positive_variance_items} over · {count.summary.negative_variance_items} short
                </div>
              </td>
              <td className="px-3 py-3">
                {dateTimeLabel(count.completed_at)}
              </td>
              <td className="px-3 py-3 text-right">
                <Link
                  to={PATHS.INVENTORY.stockCount(count.id)}
                  className={buttonVariants({
                    variant: "outline",
                    size: "sm",
                  })}
                >
                  <Eye />
                  {count.status === "open" ? "Open" : "View"}
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function NativeSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Array<{
    value: string;
    label: string;
  }>;
  placeholder: string;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
    >
      <option value="">
        {placeholder}
      </option>
      {options.map((option) => (
        <option
          key={option.value}
          value={option.value}
        >
          {option.label}
        </option>
      ))}
    </select>
  );
}

export default StockCountsPage;
