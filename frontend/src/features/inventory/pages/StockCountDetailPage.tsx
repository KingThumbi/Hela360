import {
  ArrowLeft,
  CheckCircle2,
  ClipboardList,
  FileClock,
  RefreshCw,
  Search,
  XCircle,
} from "lucide-react";
import {
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
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
  useCancelStockCount,
  useCompleteStockCount,
  useCreateStockAdjustmentFromCount,
  useStockCount,
  useUpdateStockCountItem,
} from "@/hooks/queries/inventory";
import {
  useAuthorization,
} from "@/hooks/useAuthorization";
import { createClientId } from "@/lib/clientId";
import { PATHS } from "@/routes/routes";
import type {
  StockCount,
  StockCountItem,
} from "@/types/entities";

type ItemFilter = "all" | "uncounted" | "variance" | "expired";

const ITEM_FILTERS: Array<{
  value: ItemFilter;
  label: string;
}> = [
  {
    value: "all",
    label: "All",
  },
  {
    value: "uncounted",
    label: "Uncounted",
  },
  {
    value: "variance",
    label: "Variance only",
  },
  {
    value: "expired",
    label: "Expired",
  },
];

function dateTimeLabel(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString();
}

function dateLabel(value: string | null): string {
  if (!value) {
    return "None";
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function quantity(value: string | null): string {
  if (value === null) {
    return "Not counted";
  }
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        maximumFractionDigits: 4,
      })
    : value;
}

function trimDecimalZeros(value: string): string {
  if (!value.includes(".")) {
    return value;
  }
  return value.replace(/\.?0+$/, "");
}

function decimalParts(value: string): {
  sign: -1 | 0 | 1;
  normalized: string;
} {
  const trimmed = value.trim();
  const sign = trimmed.startsWith("-") ? -1 : 1;
  const unsigned = trimmed.replace(/^[+-]/, "");
  const [
    wholeRaw,
    fractionalRaw = "",
  ] = unsigned.split(".");
  const whole = wholeRaw.replace(/^0+(?=\d)/, "") || "0";
  const fractional = fractionalRaw.replace(/0+$/, "");
  const normalized = fractional
    ? `${whole}.${fractional}`
    : whole;

  if (/^0(?:\.0*)?$/.test(normalized)) {
    return {
      sign: 0,
      normalized: "0",
    };
  }

  return {
    sign,
    normalized: trimDecimalZeros(normalized),
  };
}

function varianceState(value: string | null): "uncounted" | "matched" | "over" | "short" {
  if (value === null) {
    return "uncounted";
  }
  const parsed = decimalParts(value);
  if (parsed.sign === 0) {
    return "matched";
  }
  return parsed.sign > 0 ? "over" : "short";
}

function varianceLabel(value: string | null): string {
  const state = varianceState(value);
  if (state === "uncounted") {
    return "Not counted";
  }
  if (state === "matched") {
    return "0 · Matched";
  }
  const parsed = decimalParts(value ?? "0");
  return `${parsed.sign > 0 ? "+" : "-"}${quantity(parsed.normalized)} · ${
    state === "over" ? "Over" : "Short"
  }`;
}

function varianceBadgeVariant(
  value: string | null,
): "default" | "outline" | "secondary" {
  const state = varianceState(value);
  if (state === "matched") {
    return "secondary";
  }
  if (state === "uncounted") {
    return "outline";
  }
  return "default";
}

function statusLabel(value: string): string {
  if (value === "open") {
    return "Open";
  }
  if (value === "completed") {
    return "Completed";
  }
  if (value === "cancelled") {
    return "Cancelled";
  }
  return value.replaceAll("_", " ");
}

function decimalInputIsValid(value: string): boolean {
  return /^\d+(?:\.\d+)?$/.test(value.trim());
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function createAdjustmentIdempotencyKey(): string {
  return `stock-count-adjustment-${createClientId()}`;
}

export function StockCountDetailPage() {
  const navigate = useNavigate();
  const {
    countId,
  } = useParams();
  const stockCountQuery = useStockCount(countId);
  const completeStockCount = useCompleteStockCount();
  const cancelStockCount = useCancelStockCount();
  const createAdjustmentFromCount = useCreateStockAdjustmentFromCount();
  const authorization = useAuthorization();
  const [
    completeOpen,
    setCompleteOpen,
  ] = useState(false);
  const [
    cancelOpen,
    setCancelOpen,
  ] = useState(false);
  const [
    adjustmentOpen,
    setAdjustmentOpen,
  ] = useState(false);
  const [
    adjustmentIdempotencyKey,
    setAdjustmentIdempotencyKey,
  ] = useState(createAdjustmentIdempotencyKey);

  const count = stockCountQuery.data;
  const canAdjustStock = authorization.can("inventory.adjust");
  const canPostAdjustment =
    Boolean(count) &&
    count?.status === "completed" &&
    canAdjustStock &&
    count.summary.variance_items > 0 &&
    !count.adjustment;

  const completeCount = () => {
    if (!count) {
      return;
    }
    completeStockCount.mutate(count.id, {
      onSuccess: () => {
        toast.success("Stock Count completed.");
        setCompleteOpen(false);
        stockCountQuery.refetch();
      },
      onError: (error) => {
        toast.error(errorMessage(error));
        stockCountQuery.refetch();
      },
    });
  };

  const cancelCount = () => {
    if (!count) {
      return;
    }
    cancelStockCount.mutate(count.id, {
      onSuccess: () => {
        toast.success("Stock Count cancelled.");
        setCancelOpen(false);
        stockCountQuery.refetch();
      },
      onError: (error) => {
        toast.error(errorMessage(error));
        stockCountQuery.refetch();
      },
    });
  };

  const postAdjustment = () => {
    if (!count) {
      return;
    }

    createAdjustmentFromCount.mutate(
      {
        countId: count.id,
        payload: {
          idempotency_key: adjustmentIdempotencyKey,
          reason_code: "stock_count",
        },
      },
      {
        onSuccess: (adjustment) => {
          toast.success("Stock Adjustment posted.");
          setAdjustmentOpen(false);
          setAdjustmentIdempotencyKey(createAdjustmentIdempotencyKey());
          stockCountQuery.refetch();
          navigate(PATHS.INVENTORY.stockAdjustment(adjustment.id));
        },
        onError: (error) => {
          toast.error(errorMessage(error));
          stockCountQuery.refetch();
        },
      },
    );
  };

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Stock Count</PageTitle>
          <PageDescription>
            Snapshot, expected quantity, physical count, and server-derived variance.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.STOCK_COUNTS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Stock Counts
          </Link>
          <Button
            type="button"
            variant="outline"
            onClick={() => stockCountQuery.refetch()}
            disabled={stockCountQuery.isFetching}
          >
            <RefreshCw
              className={stockCountQuery.isFetching ? "animate-spin" : undefined}
            />
            Refresh
          </Button>
          {count?.status === "open" ? (
            <>
              <Button
                type="button"
                variant="outline"
                onClick={() => setCancelOpen(true)}
                disabled={cancelStockCount.isPending}
              >
                <XCircle />
                Cancel
              </Button>
              <Button
                type="button"
                onClick={() => setCompleteOpen(true)}
                disabled={
                  completeStockCount.isPending ||
                  count.summary.uncounted_items > 0
                }
              >
                <CheckCircle2 />
                Complete
              </Button>
            </>
          ) : null}
          {canPostAdjustment ? (
            <Button
              type="button"
              onClick={() => setAdjustmentOpen(true)}
              disabled={createAdjustmentFromCount.isPending}
            >
              <FileClock />
              Post Stock Adjustment
            </Button>
          ) : null}
          {count?.adjustment && canAdjustStock ? (
            <Link
              to={PATHS.INVENTORY.stockAdjustment(count.adjustment.id)}
              className={buttonVariants({
                variant: "outline",
              })}
            >
              <FileClock />
              View Adjustment
            </Link>
          ) : null}
        </PageActions>
      </PageHeader>

      <PageContent>
        {!countId ? (
          <PageSection>
            <EmptyState
              title="Stock Count not selected"
              description="Open a Stock Count to review physical observations."
            />
          </PageSection>
        ) : stockCountQuery.isLoading ? (
          <PageSection>
            <LoadingState title="Loading Stock Count" />
          </PageSection>
        ) : stockCountQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Stock Count unavailable"
              description={errorMessage(stockCountQuery.error)}
            />
          </PageSection>
        ) : count ? (
          <StockCountDetail
            count={count}
            onLineUpdated={() => stockCountQuery.refetch()}
            canAdjustStock={canAdjustStock}
          />
        ) : null}
      </PageContent>

      <AlertDialog
        open={completeOpen}
        onOpenChange={setCompleteOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Complete Stock Count</AlertDialogTitle>
            <AlertDialogDescription>
              Completing this count records the final physical observations and variances. It does not adjust inventory quantities.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={completeStockCount.isPending}>
              Keep Open
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={completeCount}
              disabled={completeStockCount.isPending}
            >
              Complete Count
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Stock Count</AlertDialogTitle>
            <AlertDialogDescription>
              Cancelling ends this count without changing inventory.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={cancelStockCount.isPending}>
              Keep Counting
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={cancelCount}
              disabled={cancelStockCount.isPending}
            >
              Cancel Count
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog
        open={adjustmentOpen}
        onOpenChange={setAdjustmentOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Post Variance Adjustment</AlertDialogTitle>
            <AlertDialogDescription>
              This will create a separate Stock Adjustment using the final recorded Stock Count variances and will change inventory quantities. The Stock Count itself will remain unchanged.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {count ? (
            <div className="space-y-2 text-sm">
              <div>Count: {count.count_number}</div>
              <div>Warehouse: {count.warehouse.code} - {count.warehouse.name}</div>
              <div>Variance lines: {count.summary.variance_items}</div>
            </div>
          ) : null}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={createAdjustmentFromCount.isPending}>
              Review Count
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={postAdjustment}
              disabled={createAdjustmentFromCount.isPending}
            >
              Post Adjustment
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Page>
  );
}

function StockCountDetail({
  count,
  onLineUpdated,
  canAdjustStock,
}: {
  count: StockCount;
  onLineUpdated: () => void;
  canAdjustStock: boolean;
}) {
  const isOpen = count.status === "open";

  return (
    <>
      <PageSection>
        <div className="grid gap-4 lg:grid-cols-4">
          <DetailBlock
            label="Count #"
            value={count.count_number}
          />
          <DetailBlock
            label="Warehouse"
            value={`${count.warehouse.code} - ${count.warehouse.name}`}
          />
          <DetailBlock
            label="Status"
            value={<Badge variant={isOpen ? "default" : "outline"}>{statusLabel(count.status)}</Badge>}
          />
          <DetailBlock
            label="Scope"
            value={count.scope_type === "selected" ? "Selected Products" : "Full Warehouse"}
          />
          <DetailBlock
            label="Snapshot"
            value={dateTimeLabel(count.snapshot_at)}
          />
          <DetailBlock
            label="Started"
            value={dateTimeLabel(count.started_at)}
          />
          <DetailBlock
            label="Started By"
            value={count.started_by?.name ?? count.started_by?.username ?? "Unknown"}
          />
          <DetailBlock
            label="Progress"
            value={`${count.summary.counted_items} of ${count.summary.total_items}`}
          />
          {count.completed_at ? (
            <>
              <DetailBlock
                label="Completed"
                value={dateTimeLabel(count.completed_at)}
              />
              <DetailBlock
                label="Completed By"
                value={count.completed_by?.name ?? count.completed_by?.username ?? "Unknown"}
              />
            </>
          ) : null}
          {count.cancelled_at ? (
            <>
              <DetailBlock
                label="Cancelled"
                value={dateTimeLabel(count.cancelled_at)}
              />
              <DetailBlock
                label="Cancelled By"
                value={count.cancelled_by?.name ?? count.cancelled_by?.username ?? "Unknown"}
              />
            </>
          ) : null}
          <DetailBlock
            label="Notes"
            value={count.notes ?? "None"}
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-3 md:grid-cols-3">
          <SummaryBlock
            label="Counted"
            value={`${count.summary.counted_items} / ${count.summary.total_items}`}
          />
          <SummaryBlock
            label="Variance Lines"
            value={`${count.summary.variance_items}`}
            detail={`${count.summary.positive_variance_items} over · ${count.summary.negative_variance_items} short`}
          />
          <SummaryBlock
            label="Readiness"
            value={
              count.summary.uncounted_items === 0
                ? "Ready to complete"
                : `${count.summary.uncounted_items} uncounted`
            }
            detail="Count variance is not an inventory adjustment."
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="rounded-md border bg-muted/20 p-4 text-sm text-muted-foreground">
          Expected Qty accounts for stock movements after the count snapshot. Snapshot Qty, Expected Qty, and Variance are read-only server values.
        </div>
      </PageSection>

      {count.status === "completed" ? (
        <PageSection>
          <div className="rounded-md border bg-muted/20 p-4 text-sm text-muted-foreground">
            {count.adjustment ? (
              <>
                Adjustment posted:{" "}
                {canAdjustStock ? (
                  <Link
                    to={PATHS.INVENTORY.stockAdjustment(count.adjustment.id)}
                    className="font-medium underline"
                  >
                    {count.adjustment.adjustment_number}
                  </Link>
                ) : (
                  count.adjustment.adjustment_number
                )}
              </>
            ) : count.summary.variance_items === 0 ? (
              "No stock adjustment required."
            ) : (
              "Final variances can be posted as a separate Stock Adjustment. The recorded count observations remain unchanged."
            )}
          </div>
        </PageSection>
      ) : null}

      <PageSection>
        <StockCountItemsTable
          key={count.id}
          count={count}
          isOpen={isOpen}
          onLineUpdated={onLineUpdated}
        />
      </PageSection>
    </>
  );
}

function StockCountItemsTable({
  count,
  isOpen,
  onLineUpdated,
}: {
  count: StockCount;
  isOpen: boolean;
  onLineUpdated: () => void;
}) {
  const updateItem = useUpdateStockCountItem();
  const [
    search,
    setSearch,
  ] = useState("");
  const [
    filter,
    setFilter,
  ] = useState<ItemFilter>("all");

  const [
    drafts,
    setDrafts,
  ] = useState<Record<string, string>>(
    () =>
      Object.fromEntries(
        count.items.map((item) => [
          item.id,
          item.counted_quantity ?? "",
        ]),
      ),
  );

  const [
    pendingItemId,
    setPendingItemId,
  ] = useState<string | null>(null);

  const visibleItems = useMemo(
    () =>
      count.items.filter((item) => {
        const query = search.trim().toLowerCase();
        const matchesSearch =
          query.length === 0 ||
          item.product.name.toLowerCase().includes(query) ||
          item.product.internal_sku.toLowerCase().includes(query) ||
          (item.batch?.batch_number ?? "").toLowerCase().includes(query);
        const matchesFilter =
          filter === "all" ||
          (filter === "uncounted" && item.counted_quantity === null) ||
          (filter === "variance" && varianceState(item.variance_quantity) !== "matched" && item.counted_quantity !== null) ||
          (filter === "expired" && item.batch?.is_expired === true);

        return matchesSearch && matchesFilter;
      }),
    [
      count.items,
      filter,
      search,
    ],
  );

  const saveItem = (item: StockCountItem) => {
    const draft = (drafts[item.id] ?? "").trim();
    if (!draft) {
      toast.error("Enter a Physical Count before saving. Blank means not counted.");
      return;
    }
    if (!decimalInputIsValid(draft)) {
      toast.error("Physical Count must be a non-negative decimal.");
      return;
    }

    setPendingItemId(item.id);
    updateItem.mutate(
      {
        countId: count.id,
        itemId: item.id,
        payload: {
          counted_quantity: draft,
        },
      },
      {
        onSuccess: () => {
          toast.success("Count line saved.");
          setPendingItemId(null);
          onLineUpdated();
        },
        onError: (error) => {
          toast.error(errorMessage(error));
          setPendingItemId(null);
          onLineUpdated();
        },
      },
    );
  };

  return (
    <div className="space-y-3">
      <PageToolbar>
        <div className="grid w-full gap-3 md:grid-cols-[minmax(240px,1fr)_180px]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Filter Product, SKU, or batch"
              className="pl-8"
            />
          </div>
          <NativeSelect
            value={filter}
            onChange={(value) => setFilter(value as ItemFilter)}
            placeholder="All"
            options={ITEM_FILTERS}
          />
        </div>
      </PageToolbar>

      {visibleItems.length === 0 ? (
        <EmptyState
          icon={<ClipboardList className="h-12 w-12" />}
          title="No count lines matched"
          description="Adjust the local item filters to show more persisted count lines."
        />
      ) : (
        <div className="overflow-x-auto rounded-md border">
          <Table className="min-w-[1180px]">
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Batch</TableHead>
                <TableHead>Expiry</TableHead>
                <TableHead className="text-right">Snapshot Qty</TableHead>
                <TableHead className="text-right">Expected Qty</TableHead>
                <TableHead>Physical Count</TableHead>
                <TableHead>Variance</TableHead>
                <TableHead>Counted By / At</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleItems.map((item) => {
                const isPending = pendingItemId === item.id;
                return (
                  <TableRow key={item.id}>
                    <TableCell className="whitespace-normal">
                      <div className="font-medium">
                        {item.product.name}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {item.product.internal_sku}
                      </div>
                    </TableCell>
                    <TableCell>
                      {item.batch?.batch_number ?? "—"}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div>{dateLabel(item.batch?.expiry_date ?? null)}</div>
                        {item.batch?.is_expired ? (
                          <Badge variant="outline">Expired</Badge>
                        ) : null}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {quantity(item.snapshot_quantity)}
                    </TableCell>
                    <TableCell className="text-right">
                      {quantity(item.expected_quantity)}
                    </TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <Label
                          htmlFor={`physical-count-${item.id}`}
                          className="sr-only"
                        >
                          Physical Count for {item.product.name}
                        </Label>
                        <Input
                          id={`physical-count-${item.id}`}
                          inputMode="decimal"
                          value={drafts[item.id] ?? ""}
                          onChange={(event) =>
                            setDrafts((current) => ({
                              ...current,
                              [item.id]: event.target.value,
                            }))
                          }
                          onKeyDown={(event) => {
                            if (event.key === "Enter" && isOpen) {
                              event.preventDefault();
                              saveItem(item);
                            }
                          }}
                          placeholder="Not counted"
                          disabled={!isOpen || isPending}
                        />
                        <div className="text-xs text-muted-foreground">
                          Blank is not counted. 0 is physically zero.
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={varianceBadgeVariant(item.variance_quantity)}>
                        {varianceLabel(item.variance_quantity)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div>
                        {item.counted_by?.name ??
                          item.counted_by?.username ??
                          "Not counted"}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {dateTimeLabel(item.counted_at)}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {isOpen ? (
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => saveItem(item)}
                          disabled={isPending || updateItem.isPending}
                        >
                          Save
                        </Button>
                      ) : (
                        <Badge variant="outline">Read-only</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function DetailBlock({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="space-y-1 rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">
        {label}
      </div>
      <div className="text-sm font-medium">
        {value}
      </div>
    </div>
  );
}

function SummaryBlock({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <div className="space-y-1 rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">
        {label}
      </div>
      <div className="text-lg font-semibold">
        {value}
      </div>
      {detail ? (
        <div className="text-xs text-muted-foreground">
          {detail}
        </div>
      ) : null}
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

export default StockCountDetailPage;
