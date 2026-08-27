import {
  ArrowLeft,
  Eye,
  FileClock,
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
  useStockAdjustments,
} from "@/hooks/queries/inventory";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import { useQueryScope } from "@/hooks/useQueryScope";
import { PATHS } from "@/routes/routes";
import type {
  StockAdjustmentReasonCode,
} from "@/types/requests";
import type {
  StockAdjustmentListItem,
} from "@/types/responses";

const PAGE_SIZE = 25;

const REASON_OPTIONS: Array<{
  value: Exclude<StockAdjustmentReasonCode, "stock_count"> | "stock_count";
  label: string;
}> = [
  {
    value: "stock_count",
    label: "Stock Count",
  },
  {
    value: "correction",
    label: "Correction",
  },
  {
    value: "damage",
    label: "Damage",
  },
  {
    value: "expiry",
    label: "Expiry",
  },
  {
    value: "breakage",
    label: "Breakage",
  },
  {
    value: "opening_balance",
    label: "Opening Balance",
  },
  {
    value: "other",
    label: "Other",
  },
];

function dateTimeLabel(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString();
}

function reasonLabel(value: StockAdjustmentReasonCode): string {
  return REASON_OPTIONS.find((option) => option.value === value)?.label ??
    value.replaceAll("_", " ");
}

function sourceLabel(item: StockAdjustmentListItem): string {
  if (item.source.type === "stock_count") {
    return item.source.stock_count
      ? `Stock Count ${item.source.stock_count.count_number}`
      : "Stock Count";
  }

  return "Manual";
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

export function StockAdjustmentsPage() {
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    page,
    setPage,
  ] = useState(1);
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    reasonCode,
    setReasonCode,
  ] = useState<StockAdjustmentReasonCode | "">("");
  const [
    sourceType,
    setSourceType,
  ] = useState<"manual" | "stock_count" | "">("");
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
      warehouse_id: warehouseId || undefined,
      reason_code: reasonCode || undefined,
      source_type: sourceType || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [
      dateFrom,
      dateTo,
      page,
      reasonCode,
      sourceType,
      warehouseId,
    ],
  );

  const adjustmentsQuery = useStockAdjustments(params);
  const warehousesQuery = useWarehouses();
  const adjustments = adjustmentsQuery.data?.items ?? [];
  const pagination = adjustmentsQuery.data?.pagination;
  const warehouses = useMemo(
    () => (warehousesQuery.data ?? []).filter((warehouse) => warehouse.is_active),
    [warehousesQuery.data],
  );
  const hasFilters =
    warehouseId.length > 0 ||
    reasonCode.length > 0 ||
    sourceType.length > 0 ||
    dateFrom.length > 0 ||
    dateTo.length > 0;

  const resetFilters = () => {
    setPage(1);
    setWarehouseId("");
    setReasonCode("");
    setSourceType("");
    setDateFrom("");
    setDateTo("");
  };

  if (!isBranchScopeReady) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>Stock Adjustments</PageTitle>
            <PageDescription>
              Select an active branch before viewing Stock Adjustments.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <EmptyState
              title="Branch required"
              description="Stock Adjustments are branch-scoped."
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
          <PageTitle>Stock Adjustments</PageTitle>
          <PageDescription>
            Review posted quantity corrections by Warehouse, reason, source, and user.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.ROOT}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Inventory
          </Link>
          <Button
            type="button"
            variant="outline"
            onClick={() => adjustmentsQuery.refetch()}
            disabled={adjustmentsQuery.isFetching}
          >
            <RefreshCw
              className={adjustmentsQuery.isFetching ? "animate-spin" : undefined}
            />
            Refresh
          </Button>
          <Link
            to={PATHS.INVENTORY.STOCK_ADJUSTMENT_NEW}
            className={buttonVariants()}
          >
            <Plus />
            New Stock Adjustment
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageSection>
          <PageToolbar>
            <div className="grid w-full gap-3 xl:grid-cols-[minmax(220px,1fr)_180px_170px_170px_170px_auto]">
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

              <NativeSelect
                value={reasonCode}
                onChange={(value) => {
                  setPage(1);
                  setReasonCode(value as StockAdjustmentReasonCode | "");
                }}
                placeholder="All reasons"
                options={REASON_OPTIONS}
              />

              <NativeSelect
                value={sourceType}
                onChange={(value) => {
                  setPage(1);
                  setSourceType(value as "manual" | "stock_count" | "");
                }}
                placeholder="All sources"
                options={[
                  {
                    value: "manual",
                    label: "Manual",
                  },
                  {
                    value: "stock_count",
                    label: "Stock Count",
                  },
                ]}
              />

              <Input
                type="date"
                value={dateFrom}
                onChange={(event) => {
                  setPage(1);
                  setDateFrom(event.target.value);
                }}
                aria-label="Posted from"
              />

              <Input
                type="date"
                value={dateTo}
                onChange={(event) => {
                  setPage(1);
                  setDateTo(event.target.value);
                }}
                aria-label="Posted to"
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

          {adjustmentsQuery.isLoading ? (
            <LoadingState title="Loading Stock Adjustments" />
          ) : adjustmentsQuery.isError ? (
            <ErrorState
              title="Stock Adjustments unavailable"
              description={errorMessage(adjustmentsQuery.error)}
            />
          ) : adjustments.length === 0 ? (
            <EmptyState
              icon={<FileClock className="h-12 w-12" />}
              title={
                hasFilters
                  ? "No Stock Adjustments matched"
                  : "No Stock Adjustments posted"
              }
              description={
                hasFilters
                  ? "Adjust the filters to widen the adjustment history."
                  : "Manual corrections and posted Stock Count variances will appear here."
              }
            />
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full min-w-[1080px] text-sm">
                <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">Adjustment #</th>
                    <th className="px-3 py-2 font-medium">Posted</th>
                    <th className="px-3 py-2 font-medium">Warehouse</th>
                    <th className="px-3 py-2 font-medium">Reason</th>
                    <th className="px-3 py-2 font-medium">Source</th>
                    <th className="px-3 py-2 text-right font-medium">Items</th>
                    <th className="px-3 py-2 font-medium">Posted By</th>
                    <th className="px-3 py-2 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {adjustments.map((adjustment) => (
                    <tr
                      key={adjustment.id}
                      className="border-t"
                    >
                      <td className="px-3 py-3 font-medium">
                        {adjustment.adjustment_number}
                      </td>
                      <td className="px-3 py-3">
                        {dateTimeLabel(adjustment.posted_at)}
                      </td>
                      <td className="px-3 py-3">
                        {adjustment.warehouse.code} · {adjustment.warehouse.name}
                      </td>
                      <td className="px-3 py-3">
                        <div>{reasonLabel(adjustment.reason_code)}</div>
                        {adjustment.reason ? (
                          <div className="text-xs text-muted-foreground">
                            {adjustment.reason}
                          </div>
                        ) : null}
                      </td>
                      <td className="px-3 py-3">
                        <Badge variant="outline">{sourceLabel(adjustment)}</Badge>
                      </td>
                      <td className="px-3 py-3 text-right">
                        {adjustment.item_count}
                      </td>
                      <td className="px-3 py-3">
                        {adjustment.posted_by?.name ??
                          adjustment.posted_by?.username ??
                          "Unknown"}
                      </td>
                      <td className="px-3 py-3 text-right">
                        <Link
                          to={PATHS.INVENTORY.stockAdjustment(adjustment.id)}
                          className={buttonVariants({
                            variant: "outline",
                            size: "sm",
                          })}
                        >
                          <Eye />
                          View Adjustment
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {pagination ? (
            <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
              <span>
                Page {pagination.page} of {Math.max(pagination.pages, 1)} · {pagination.total} Stock Adjustments
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
      <option value="">{placeholder}</option>
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

export default StockAdjustmentsPage;
