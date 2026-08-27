import {
  ArrowLeft,
  FilePlus2,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import {
  useMemo,
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  useNavigate,
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
import { Textarea } from "@/components/ui/textarea";
import {
  useCreateStockAdjustment,
  useInventory,
  useInventoryBatches,
} from "@/hooks/queries/inventory";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import { useQueryScope } from "@/hooks/useQueryScope";
import { createClientId } from "@/lib/clientId";
import { PATHS } from "@/routes/routes";
import type {
  InventoryBatchSummary,
  InventoryStockSummary,
} from "@/types/responses";
import type {
  CreateStockAdjustmentRequest,
  StockAdjustmentReasonCode,
} from "@/types/requests";

const PAGE_SIZE = 10;

type ManualReasonCode = Exclude<StockAdjustmentReasonCode, "stock_count">;

const REASON_OPTIONS: Array<{
  value: ManualReasonCode;
  label: string;
}> = [
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

interface AdjustmentLine {
  id: string;
  stock: InventoryStockSummary;
  batch: InventoryBatchSummary | null;
  quantity_delta: string;
  reason: string;
}

function createDraftId(): string {
  return createClientId();
}

function createIdempotencyKey(): string {
  return `stock-adjustment-${createClientId()}`;
}

function quantity(value: string): string {
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        maximumFractionDigits: 4,
      })
    : value;
}

function signedQuantity(value: string): string {
  const normalized = Number(value);
  if (!Number.isFinite(normalized)) {
    return value;
  }

  return `${normalized > 0 ? "+" : ""}${quantity(value)}`;
}

function dateLabel(value: string | null): string {
  if (!value) {
    return "None";
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function requiresBatch(stock: InventoryStockSummary): boolean {
  return stock.product.track_batches || stock.product.track_expiry;
}

function signedDecimalIsValid(value: string): boolean {
  return /^[+-]?\d+(?:\.\d+)?$/.test(value.trim()) &&
    Number(value) !== 0;
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function lineIdentity(line: AdjustmentLine): string {
  return `${line.stock.product.id}::${line.batch?.id ?? "none"}`;
}

function requestSnapshot(
  payload: Omit<CreateStockAdjustmentRequest, "idempotency_key">,
): string {
  return JSON.stringify(payload);
}

function buildRequestBase({
  warehouseId,
  reasonCode,
  reason,
  notes,
  lines,
}: {
  warehouseId: string;
  reasonCode: ManualReasonCode;
  reason: string;
  notes: string;
  lines: AdjustmentLine[];
}): Omit<CreateStockAdjustmentRequest, "idempotency_key"> {
  return {
    warehouse_id: warehouseId,
    reason_code: reasonCode,
    ...(reason.trim() ? { reason: reason.trim() } : {}),
    ...(notes.trim() ? { notes: notes.trim() } : {}),
    items: lines.map((line) => ({
      product_id: line.stock.product.id,
      ...(line.batch ? { batch_id: line.batch.id } : {}),
      quantity_delta: line.quantity_delta.trim(),
      ...(line.reason.trim() ? { reason: line.reason.trim() } : {}),
    })),
  };
}

function validateLines(lines: AdjustmentLine[]): string | null {
  if (lines.length === 0) {
    return "Add at least one stock line.";
  }

  const seen = new Set<string>();
  for (const line of lines) {
    if (requiresBatch(line.stock) && !line.batch) {
      return `${line.stock.product.name}: select an existing batch.`;
    }

    if (!signedDecimalIsValid(line.quantity_delta)) {
      return `${line.stock.product.name}: Quantity Adjustment must be a non-zero signed decimal.`;
    }

    const identity = lineIdentity(line);
    if (seen.has(identity)) {
      return "Duplicate Product and batch lines are not allowed.";
    }
    seen.add(identity);
  }

  return null;
}

export function CreateStockAdjustmentPage() {
  const navigate = useNavigate();
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    reasonCode,
    setReasonCode,
  ] = useState<ManualReasonCode>("correction");
  const [
    reason,
    setReason,
  ] = useState("");
  const [
    notes,
    setNotes,
  ] = useState("");
  const [
    searchInput,
    setSearchInput,
  ] = useState("");
  const [
    submittedSearch,
    setSubmittedSearch,
  ] = useState("");
  const [
    selectedStockId,
    setSelectedStockId,
  ] = useState("");
  const [
    selectedBatchId,
    setSelectedBatchId,
  ] = useState("");
  const [
    lines,
    setLines,
  ] = useState<AdjustmentLine[]>([]);
  const [
    idempotencyKey,
    setIdempotencyKey,
  ] = useState(createIdempotencyKey);
  const [
    submittedSnapshot,
    setSubmittedSnapshot,
  ] = useState<string | null>(null);
  const [
    confirmOpen,
    setConfirmOpen,
  ] = useState(false);

  const warehousesQuery = useWarehouses();
  const inventoryQuery = useInventory({
    page: 1,
    per_page: PAGE_SIZE,
    warehouse_id: warehouseId || undefined,
    search: submittedSearch || undefined,
  });
  const createAdjustment = useCreateStockAdjustment();

  const warehouses = useMemo(
    () => (warehousesQuery.data ?? []).filter((warehouse) => warehouse.is_active),
    [warehousesQuery.data],
  );
  const stockRows = (inventoryQuery.data?.items ?? []).filter(
    (item) => item.product.is_active && item.product.track_inventory,
  );
  const selectedStock = stockRows.find((item) => item.id === selectedStockId);
  const batchesQuery = useInventoryBatches(
    selectedStock && requiresBatch(selectedStock)
      ? selectedStock.id
      : null,
  );
  const batches = batchesQuery.data?.items ?? [];
  const selectedBatch = batches.find((batch) => batch.id === selectedBatchId);
  const hasNegativeLine = lines.some((line) => Number(line.quantity_delta) < 0);

  const submitSearch = () => {
    setSubmittedSearch(searchInput.trim());
  };

  const addLine = () => {
    if (!selectedStock) {
      toast.error("Select a stock row.");
      return;
    }

    if (requiresBatch(selectedStock) && !selectedBatch) {
      toast.error("Select an existing batch for this product.");
      return;
    }

    const line: AdjustmentLine = {
      id: createDraftId(),
      stock: selectedStock,
      batch: requiresBatch(selectedStock) ? selectedBatch ?? null : null,
      quantity_delta: "1",
      reason: "",
    };

    if (lines.some((current) => lineIdentity(current) === lineIdentity(line))) {
      toast.error("Duplicate Product and batch lines are not allowed.");
      return;
    }

    setLines((current) => [
      ...current,
      line,
    ]);
    setSelectedStockId("");
    setSelectedBatchId("");
  };

  const updateLine = (
    lineId: string,
    updates: Partial<Pick<AdjustmentLine, "quantity_delta" | "reason">>,
  ) => {
    setLines((current) =>
      current.map((line) =>
        line.id === lineId
          ? {
              ...line,
              ...updates,
            }
          : line,
      ),
    );
  };

  const removeLine = (lineId: string) => {
    setLines((current) => current.filter((line) => line.id !== lineId));
  };

  const openConfirmation = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!warehouseId) {
      toast.error("Select a Warehouse.");
      return;
    }

    const lineError = validateLines(lines);
    if (lineError) {
      toast.error(lineError);
      return;
    }

    setConfirmOpen(true);
  };

  const postAdjustment = () => {
    const base = buildRequestBase({
      warehouseId,
      reasonCode,
      reason,
      notes,
      lines,
    });
    const snapshot = requestSnapshot(base);
    const nextKey =
      submittedSnapshot && submittedSnapshot !== snapshot
        ? createIdempotencyKey()
        : idempotencyKey;

    if (nextKey !== idempotencyKey) {
      setIdempotencyKey(nextKey);
    }
    setSubmittedSnapshot(snapshot);

    createAdjustment.mutate(
      {
        ...base,
        idempotency_key: nextKey,
      },
      {
        onSuccess: (adjustment) => {
          toast.success("Stock Adjustment posted.");
          setConfirmOpen(false);
          setIdempotencyKey(createIdempotencyKey());
          setSubmittedSnapshot(null);
          navigate(PATHS.INVENTORY.stockAdjustment(adjustment.id));
        },
        onError: (error) => {
          toast.error(errorMessage(error));
        },
      },
    );
  };

  if (!isBranchScopeReady) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>New Stock Adjustment</PageTitle>
            <PageDescription>
              Select an active branch before posting a Stock Adjustment.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <EmptyState
              title="Branch required"
              description="Stock Adjustment posting is branch-scoped."
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
          <PageTitle>New Stock Adjustment</PageTitle>
          <PageDescription>
            Post signed quantity corrections against current Warehouse stock.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.STOCK_ADJUSTMENTS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Stock Adjustments
          </Link>
          <Button
            type="button"
            variant="outline"
            onClick={() => inventoryQuery.refetch()}
            disabled={inventoryQuery.isFetching}
          >
            <RefreshCw
              className={inventoryQuery.isFetching ? "animate-spin" : undefined}
            />
            Refresh Stock
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        <form
          className="space-y-4"
          onSubmit={openConfirmation}
        >
          <PageSection>
            <div className="grid gap-4 lg:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="warehouse">Warehouse</Label>
                <NativeSelect
                  value={warehouseId}
                  onChange={(value) => {
                    setWarehouseId(value);
                    setSelectedStockId("");
                    setSelectedBatchId("");
                    setLines([]);
                  }}
                  placeholder={
                    warehousesQuery.isLoading
                      ? "Loading warehouses"
                      : "Select Warehouse"
                  }
                  options={warehouses.map((warehouse) => ({
                    value: warehouse.id,
                    label: `${warehouse.code} - ${warehouse.name}`,
                  }))}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reason-code">Reason</Label>
                <NativeSelect
                  value={reasonCode}
                  onChange={(value) => setReasonCode(value as ManualReasonCode)}
                  placeholder="Reason"
                  options={REASON_OPTIONS}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="reason">Reason Notes</Label>
                <Input
                  id="reason"
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  placeholder="Shelf correction, expiry cleanup"
                />
              </div>
            </div>

            <div className="mt-4 space-y-2">
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Optional operational notes"
              />
            </div>
          </PageSection>

          <PageSection>
            <PageToolbar>
              <div className="grid w-full gap-3 xl:grid-cols-[minmax(220px,1fr)_minmax(260px,1fr)_minmax(220px,1fr)_auto]">
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      type="search"
                      value={searchInput}
                      onChange={(event) => setSearchInput(event.target.value)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter") {
                          event.preventDefault();
                          submitSearch();
                        }
                      }}
                      placeholder="Search product or SKU"
                      className="pl-8"
                      disabled={!warehouseId}
                    />
                  </div>
                  <Button
                    type="button"
                    onClick={submitSearch}
                    disabled={!warehouseId}
                  >
                    Search
                  </Button>
                </div>

                <NativeSelect
                  value={selectedStockId}
                  onChange={(value) => {
                    setSelectedStockId(value);
                    setSelectedBatchId("");
                  }}
                  placeholder={
                    !warehouseId
                      ? "Select Warehouse first"
                      : inventoryQuery.isLoading
                        ? "Loading stock"
                        : "Select stock row"
                  }
                  options={stockRows.map((stock) => ({
                    value: stock.id,
                    label: `${stock.product.internal_sku} - ${stock.product.name} (${quantity(stock.quantity_on_hand)} on hand)`,
                  }))}
                />

                <NativeSelect
                  value={selectedBatchId}
                  onChange={setSelectedBatchId}
                  placeholder={
                    selectedStock && requiresBatch(selectedStock)
                      ? batchesQuery.isLoading
                        ? "Loading batches"
                        : "Select existing batch"
                      : "No batch required"
                  }
                  options={
                    selectedStock && requiresBatch(selectedStock)
                      ? batches.map((batch) => ({
                          value: batch.id,
                          label: `${batch.batch_number ?? batch.id} · ${quantity(batch.quantity_on_hand)} on hand · ${dateLabel(batch.expiry_date)}${batch.is_expired ? " · Expired" : ""}`,
                        }))
                      : []
                  }
                />

                <Button
                  type="button"
                  onClick={addLine}
                  disabled={
                    !selectedStock ||
                    (requiresBatch(selectedStock) && !selectedBatch)
                  }
                >
                  <FilePlus2 />
                  Add Line
                </Button>
              </div>
            </PageToolbar>

            {!warehouseId ? (
              <EmptyState
                title="Warehouse required"
                description="Select a Warehouse before choosing stock lines."
              />
            ) : inventoryQuery.isLoading ? (
              <LoadingState title="Loading stock rows" />
            ) : inventoryQuery.isError ? (
              <ErrorState
                title="Stock rows unavailable"
                description={errorMessage(inventoryQuery.error)}
              />
            ) : lines.length === 0 ? (
              <EmptyState
                title="No adjustment lines"
                description="Select current Warehouse stock, choose an exact batch when required, then add a signed quantity delta."
              />
            ) : (
              <AdjustmentLinesTable
                lines={lines}
                onUpdateLine={updateLine}
                onRemoveLine={removeLine}
              />
            )}
          </PageSection>

          {hasNegativeLine ? (
            <PageSection>
              <div className="rounded-md border bg-muted/20 p-4 text-sm text-muted-foreground">
                One or more lines will decrease recorded stock. The server will reject any correction that violates physical or reserved-stock constraints.
              </div>
            </PageSection>
          ) : null}

          <PageSection>
            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={createAdjustment.isPending}
              >
                Post Stock Adjustment
              </Button>
            </div>
          </PageSection>
        </form>
      </PageContent>

      <AlertDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Post Stock Adjustment</AlertDialogTitle>
            <AlertDialogDescription>
              Posting this adjustment will immediately change recorded inventory quantities and create an audit movement.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <div className="space-y-2 text-sm">
            <div>
              Warehouse: {warehouses.find((warehouse) => warehouse.id === warehouseId)?.name ?? "Selected Warehouse"}
            </div>
            <div>Reason: {REASON_OPTIONS.find((option) => option.value === reasonCode)?.label}</div>
            <div>Lines: {lines.length}</div>
            <div>
              Effect: {hasNegativeLine ? "Includes stock decreases" : "Stock increases only"}
            </div>
          </div>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={createAdjustment.isPending}>
              Review
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={postAdjustment}
              disabled={createAdjustment.isPending}
            >
              Post Adjustment
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Page>
  );
}

function AdjustmentLinesTable({
  lines,
  onUpdateLine,
  onRemoveLine,
}: {
  lines: AdjustmentLine[];
  onUpdateLine: (
    lineId: string,
    updates: Partial<Pick<AdjustmentLine, "quantity_delta" | "reason">>,
  ) => void;
  onRemoveLine: (lineId: string) => void;
}) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <Table className="min-w-[1080px]">
        <TableHeader>
          <TableRow>
            <TableHead>Product</TableHead>
            <TableHead>Warehouse</TableHead>
            <TableHead>Batch</TableHead>
            <TableHead className="text-right">Current On Hand</TableHead>
            <TableHead className="text-right">Reserved</TableHead>
            <TableHead>Quantity Adjustment</TableHead>
            <TableHead>Line Reason</TableHead>
            <TableHead className="text-right">Action</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lines.map((line) => (
            <TableRow key={line.id}>
              <TableCell>
                <div className="font-medium">{line.stock.product.name}</div>
                <div className="text-xs text-muted-foreground">
                  {line.stock.product.internal_sku}
                </div>
              </TableCell>
              <TableCell>
                {line.stock.warehouse.code} · {line.stock.warehouse.name}
              </TableCell>
              <TableCell>
                <div className="space-y-1">
                  <div>{line.batch?.batch_number ?? "None"}</div>
                  {line.batch?.is_expired ? (
                    <Badge variant="outline">Expired</Badge>
                  ) : null}
                  {requiresBatch(line.stock) && !line.batch ? (
                    <Badge variant="destructive">Batch required</Badge>
                  ) : null}
                </div>
              </TableCell>
              <TableCell className="text-right">
                {quantity(line.batch?.quantity_on_hand ?? line.stock.quantity_on_hand)}
              </TableCell>
              <TableCell className="text-right">
                {quantity(line.batch?.quantity_reserved ?? line.stock.quantity_reserved)}
              </TableCell>
              <TableCell>
                <div className="space-y-1">
                  <Input
                    inputMode="decimal"
                    value={line.quantity_delta}
                    onChange={(event) =>
                      onUpdateLine(line.id, {
                        quantity_delta: event.target.value,
                      })
                    }
                    aria-label={`Quantity Adjustment for ${line.stock.product.name}`}
                  />
                  <div className="text-xs text-muted-foreground">
                    +5 increases stock. -2 decreases stock.
                  </div>
                  {signedDecimalIsValid(line.quantity_delta) ? (
                    <div className="text-xs text-muted-foreground">
                      {signedQuantity(line.quantity_delta)}
                    </div>
                  ) : null}
                </div>
              </TableCell>
              <TableCell>
                <Input
                  value={line.reason}
                  onChange={(event) =>
                    onUpdateLine(line.id, {
                      reason: event.target.value,
                    })
                  }
                  placeholder="Optional line note"
                />
              </TableCell>
              <TableCell className="text-right">
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  onClick={() => onRemoveLine(line.id)}
                  aria-label={`Remove ${line.stock.product.name}`}
                >
                  <Trash2 />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
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

export default CreateStockAdjustmentPage;
