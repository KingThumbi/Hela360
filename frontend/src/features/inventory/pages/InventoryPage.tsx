import {
  Boxes,
  ClipboardList,
  Eye,
  FileClock,
  History,
  PackagePlus,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
import type {
  FormEvent,
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
import { Button } from "@/components/ui/button";
import {
  buttonVariants,
} from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  useInventory,
  useInventoryBatches,
  useInventoryMovements,
} from "@/hooks/queries/inventory";
import {
  useAuthorization,
} from "@/hooks/useAuthorization";
import {
  PATHS,
} from "@/routes/routes";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import type {
  InventoryStockStatusFilter,
} from "@/types/requests";
import type {
  InventoryMovementSummary,
  InventoryStockSummary,
} from "@/types/responses";
import type {
  Warehouse,
} from "@/types/entities";

const PAGE_SIZE = 25;

const STOCK_STATUS_OPTIONS: Array<{
  value: InventoryStockStatusFilter;
  label: string;
}> = [
  {
    value: "in_stock",
    label: "In stock",
  },
  {
    value: "low_stock",
    label: "Low stock",
  },
  {
    value: "out_of_stock",
    label: "Out of stock",
  },
  {
    value: "expired_stock",
    label: "Expired stock",
  },
];

const MOVEMENT_TYPE_OPTIONS = [
  {
    value: "goods_receipt",
    label: "Goods Receipt",
  },
  {
    value: "sale",
    label: "Sale",
  },
  {
    value: "sale_refund_return",
    label: "Refund return",
  },
  {
    value: "sale_void",
    label: "Sale void",
  },
  {
    value: "stock_adjustment",
    label: "Stock Adjustment",
  },
];

type InventoryView = "stock" | "activity";

function quantity(value: string): string {
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        maximumFractionDigits: 4,
      })
    : value;
}

function dateLabel(value: string | null): string {
  if (!value) {
    return "None";
  }

  return new Date(`${value}T00:00:00`).toLocaleDateString();
}

function dateTimeLabel(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString();
}

function movementTypeLabel(value: string): string {
  const known = MOVEMENT_TYPE_OPTIONS.find(
    (option) => option.value === value,
  );

  return known?.label ?? value.replaceAll("_", " ");
}

function movementDirection(value: string): "In" | "Out" | "Neutral" {
  const normalized = Number(value);
  if (!Number.isFinite(normalized) || normalized === 0) {
    return "Neutral";
  }

  return normalized < 0 ? "Out" : "In";
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

export function InventoryPage() {
  const [
    view,
    setView,
  ] = useState<InventoryView>("stock");
  const [
    page,
    setPage,
  ] = useState(1);
  const [
    activityPage,
    setActivityPage,
  ] = useState(1);
  const [
    searchInput,
    setSearchInput,
  ] = useState("");
  const [
    submittedSearch,
    setSubmittedSearch,
  ] = useState("");
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    stockStatus,
    setStockStatus,
  ] = useState<InventoryStockStatusFilter | "">("");
  const [
    expiresBefore,
    setExpiresBefore,
  ] = useState("");
  const [
    selectedStock,
    setSelectedStock,
  ] = useState<InventoryStockSummary | null>(null);
  const [
    activityWarehouseId,
    setActivityWarehouseId,
  ] = useState("");
  const [
    movementType,
    setMovementType,
  ] = useState("");
  const [
    dateFrom,
    setDateFrom,
  ] = useState("");
  const [
    dateTo,
    setDateTo,
  ] = useState("");
  const [
    referenceId,
    setReferenceId,
  ] = useState("");

  const params = useMemo(
    () => ({
      page,
      per_page: PAGE_SIZE,
      search:
        submittedSearch.trim().length > 0
          ? submittedSearch.trim()
          : undefined,
      warehouse_id: warehouseId || undefined,
      stock_status: stockStatus || undefined,
      expires_before: expiresBefore || undefined,
    }),
    [
      expiresBefore,
      page,
      submittedSearch,
      stockStatus,
      warehouseId,
    ],
  );

  const activityParams = useMemo(
    () => ({
      page: activityPage,
      per_page: PAGE_SIZE,
      warehouse_id: activityWarehouseId || undefined,
      movement_type: movementType || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      reference_id:
        referenceId.trim().length > 0
          ? referenceId.trim()
          : undefined,
    }),
    [
      activityPage,
      activityWarehouseId,
      dateFrom,
      dateTo,
      movementType,
      referenceId,
    ],
  );

  const inventoryQuery = useInventory(params);
  const movementsQuery = useInventoryMovements(activityParams);
  const warehousesQuery = useWarehouses();
  const batchesQuery = useInventoryBatches(
    selectedStock?.id,
  );
  const authorization = useAuthorization();

  const items = inventoryQuery.data?.items ?? [];
  const pagination = inventoryQuery.data?.pagination;
  const movements = movementsQuery.data?.items ?? [];
  const movementPagination = movementsQuery.data?.pagination;
  const warehouses = warehousesQuery.data ?? [];
  const canReadSales = authorization.can("sales.read");
  const canReceiveStock = authorization.can("inventory.receive");
  const canCountStock = authorization.can("inventory.count");
  const canAdjustStock = authorization.can("inventory.adjust");

  const hasFilters =
    submittedSearch.trim().length > 0 ||
    warehouseId.length > 0 ||
    stockStatus.length > 0 ||
    expiresBefore.length > 0;

  const hasActivityFilters =
    activityWarehouseId.length > 0 ||
    movementType.length > 0 ||
    dateFrom.length > 0 ||
    dateTo.length > 0 ||
    referenceId.trim().length > 0;

  const submitSearch = (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setPage(1);
    setSubmittedSearch(searchInput);
  };

  const resetActivityFilters = () => {
    setActivityPage(1);
    setActivityWarehouseId("");
    setMovementType("");
    setDateFrom("");
    setDateTo("");
    setReferenceId("");
  };

  const resetFilters = () => {
    setPage(1);
    setSearchInput("");
    setSubmittedSearch("");
    setWarehouseId("");
    setStockStatus("");
    setExpiresBefore("");
  };

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Inventory</PageTitle>
          <PageDescription>
            Branch stock visibility by warehouse, product, batch, and expiry state.
          </PageDescription>
        </div>

        <PageActions>
          {canReceiveStock ? (
            <>
              <Link
                to={PATHS.INVENTORY.RECEIVE}
                className={buttonVariants()}
              >
                <PackagePlus />
                Receive Stock
              </Link>
              <Link
                to={PATHS.INVENTORY.RECEIPTS}
                className={buttonVariants({
                  variant: "outline",
                })}
              >
                <History />
                Receiving History
              </Link>
            </>
          ) : null}
          {canCountStock ? (
            <Link
              to={PATHS.INVENTORY.STOCK_COUNTS}
              className={buttonVariants({
                variant: "outline",
              })}
            >
              <ClipboardList />
              Stock Counts
            </Link>
          ) : null}
          {canAdjustStock ? (
            <Link
              to={PATHS.INVENTORY.STOCK_ADJUSTMENTS}
              className={buttonVariants({
                variant: "outline",
              })}
            >
              <FileClock />
              Stock Adjustments
            </Link>
          ) : null}
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              if (view === "activity") {
                movementsQuery.refetch();
              } else {
                inventoryQuery.refetch();
              }
            }}
            disabled={
              view === "activity"
                ? movementsQuery.isFetching
                : inventoryQuery.isFetching
            }
          >
            <RefreshCw
              className={
                (
                  view === "activity"
                    ? movementsQuery.isFetching
                    : inventoryQuery.isFetching
                )
                  ? "animate-spin"
                  : undefined
              }
            />
            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageSection>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant={view === "stock" ? "default" : "outline"}
              onClick={() => setView("stock")}
            >
              <Boxes />
              Stock
            </Button>
            <Button
              type="button"
              variant={view === "activity" ? "default" : "outline"}
              onClick={() => setView("activity")}
            >
              <History />
              Activity
            </Button>
          </div>

          {view === "stock" ? (
            <>
          <PageToolbar>
            <div className="grid w-full gap-3 xl:grid-cols-[minmax(220px,1fr)_180px_170px_170px_auto]">
              <form
                className="flex gap-2"
                onSubmit={submitSearch}
              >
                <div className="relative flex-1">
                  <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    type="search"
                    value={searchInput}
                    onChange={(event) =>
                      setSearchInput(event.target.value)
                    }
                    placeholder="Search product, SKU, generic"
                    className="pl-8"
                  />
                </div>
                <Button type="submit">
                  Search
                </Button>
              </form>

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
                value={stockStatus}
                onChange={(value) => {
                  setPage(1);
                  setStockStatus(
                    value as InventoryStockStatusFilter | "",
                  );
                }}
                placeholder="All stock"
                options={STOCK_STATUS_OPTIONS}
              />

              <Input
                type="date"
                value={expiresBefore}
                onChange={(event) => {
                  setPage(1);
                  setExpiresBefore(event.target.value);
                }}
                aria-label="Expires before"
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

          {inventoryQuery.isLoading ? (
            <LoadingState title="Loading inventory" />
          ) : inventoryQuery.isError ? (
            <ErrorState
              title="Inventory unavailable"
              description={errorMessage(inventoryQuery.error)}
            />
          ) : items.length === 0 ? (
            <EmptyState
              icon={<Boxes className="h-12 w-12" />}
              title={
                hasFilters
                  ? "No stock matched"
                  : "No stock balances found"
              }
              description={
                hasFilters
                  ? "Adjust the filters to widen the stock view."
                  : "Current branch stock will appear here once inventory exists."
              }
            />
          ) : (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full min-w-[980px] text-sm">
                <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">
                      Product
                    </th>
                    <th className="px-3 py-2 font-medium">
                      SKU
                    </th>
                    <th className="px-3 py-2 font-medium">
                      Warehouse
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      On Hand
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      Reserved
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      Available
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      Sellable
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      Batches
                    </th>
                    <th className="px-3 py-2 font-medium">
                      Earliest Expiry
                    </th>
                    <th className="px-3 py-2 font-medium">
                      Status
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      Action
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.id}
                      className="border-t"
                    >
                      <td className="px-3 py-3">
                        <div className="font-medium">
                          {item.product.name}
                        </div>
                        {item.product.generic_name ? (
                          <div className="text-xs text-muted-foreground">
                            {item.product.generic_name}
                          </div>
                        ) : null}
                      </td>
                      <td className="px-3 py-3">
                        {item.product.internal_sku}
                      </td>
                      <td className="px-3 py-3">
                        {item.warehouse.code} · {item.warehouse.name}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {quantity(item.quantity_on_hand)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {quantity(item.quantity_reserved)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {quantity(item.quantity_available)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {quantity(item.sellable_quantity)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {item.batch_count}
                      </td>
                      <td className="px-3 py-3">
                        {dateLabel(item.earliest_sellable_expiry_date)}
                      </td>
                      <td className="px-3 py-3">
                        <StockBadges item={item} />
                      </td>
                      <td className="px-3 py-3 text-right">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedStock(item)}
                        >
                          <Eye />
                          Batches
                        </Button>
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
                Page {pagination.page} of {Math.max(pagination.pages, 1)} · {pagination.total} stock rows
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
            </>
          ) : (
            <InventoryActivityView
              warehouses={warehouses}
              warehousesLoading={warehousesQuery.isLoading}
              movements={movements}
              pagination={movementPagination}
              query={movementsQuery}
              warehouseId={activityWarehouseId}
              movementType={movementType}
              dateFrom={dateFrom}
              dateTo={dateTo}
              referenceId={referenceId}
              hasFilters={hasActivityFilters}
              canReadSales={canReadSales}
              canOpenGoodsReceipts={canReceiveStock}
              canOpenStockAdjustments={canAdjustStock}
              onWarehouseChange={(value) => {
                setActivityPage(1);
                setActivityWarehouseId(value);
              }}
              onMovementTypeChange={(value) => {
                setActivityPage(1);
                setMovementType(value);
              }}
              onDateFromChange={(value) => {
                setActivityPage(1);
                setDateFrom(value);
              }}
              onDateToChange={(value) => {
                setActivityPage(1);
                setDateTo(value);
              }}
              onReferenceIdChange={(value) => {
                setActivityPage(1);
                setReferenceId(value);
              }}
              onReset={resetActivityFilters}
              onPreviousPage={() =>
                setActivityPage((value) => Math.max(1, value - 1))
              }
              onNextPage={() =>
                setActivityPage((value) => value + 1)
              }
            />
          )}
        </PageSection>
      </PageContent>

      <Dialog
        open={Boolean(selectedStock)}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedStock(null);
          }
        }}
      >
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>
              Batch Visibility
            </DialogTitle>
            <DialogDescription>
              {selectedStock
                ? `${selectedStock.product.name} in ${selectedStock.warehouse.name}`
                : "Inventory batches"}
            </DialogDescription>
          </DialogHeader>

          {batchesQuery.isLoading ? (
            <LoadingState title="Loading batches" />
          ) : batchesQuery.isError ? (
            <ErrorState
              title="Batches unavailable"
              description={errorMessage(batchesQuery.error)}
            />
          ) : batchesQuery.data?.items.length ? (
            <div className="overflow-x-auto rounded-md border">
              <table className="w-full min-w-[640px] text-sm">
                <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">
                      Batch
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      On Hand
                    </th>
                    <th className="px-3 py-2 text-right font-medium">
                      Available
                    </th>
                    <th className="px-3 py-2 font-medium">
                      Expiry
                    </th>
                    <th className="px-3 py-2 font-medium">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {batchesQuery.data.items.map((batch) => (
                    <tr
                      key={batch.id}
                      className="border-t"
                    >
                      <td className="px-3 py-3">
                        {batch.batch_number ?? batch.id}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {quantity(batch.quantity_on_hand)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        {quantity(batch.quantity_available)}
                      </td>
                      <td className="px-3 py-3">
                        {dateLabel(batch.expiry_date)}
                      </td>
                      <td className="px-3 py-3">
                        <div className="flex flex-wrap gap-1">
                          {batch.is_expired ? (
                            <Badge variant="destructive">
                              Expired
                            </Badge>
                          ) : batch.is_sellable ? (
                            <Badge variant="secondary">
                              Sellable
                            </Badge>
                          ) : (
                            <Badge variant="outline">
                              Not sellable
                            </Badge>
                          )}
                          <Badge variant="outline">
                            {batch.status}
                          </Badge>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState
              title="No current batches"
              description="Non-zero batches for this stock row will appear here."
            />
          )}
        </DialogContent>
      </Dialog>
    </Page>
  );
}

function StockBadges({
  item,
}: {
  item: InventoryStockSummary;
}) {
  return (
    <div className="flex flex-wrap gap-1">
      {item.is_out_of_stock ? (
        <Badge variant="destructive">
          Out
        </Badge>
      ) : item.is_low_stock ? (
        <Badge variant="secondary">
          Low
        </Badge>
      ) : (
        <Badge variant="outline">
          Stocked
        </Badge>
      )}
      {item.product.requires_prescription ? (
        <Badge variant="outline">
          Prescription
        </Badge>
      ) : null}
      {item.has_expired_stock ? (
        <Badge variant="destructive">
          Expired
        </Badge>
      ) : null}
      {item.has_expiring_stock ? (
        <Badge variant="secondary">
          Expiring
        </Badge>
      ) : null}
    </div>
  );
}

function InventoryActivityView({
  warehouses,
  warehousesLoading,
  movements,
  pagination,
  query,
  warehouseId,
  movementType,
  dateFrom,
  dateTo,
  referenceId,
  hasFilters,
  canReadSales,
  canOpenGoodsReceipts,
  canOpenStockAdjustments,
  onWarehouseChange,
  onMovementTypeChange,
  onDateFromChange,
  onDateToChange,
  onReferenceIdChange,
  onReset,
  onPreviousPage,
  onNextPage,
}: {
  warehouses: Warehouse[];
  warehousesLoading: boolean;
  movements: InventoryMovementSummary[];
  pagination:
    | {
        page: number;
        pages: number;
        total: number;
        has_prev: boolean;
        has_next: boolean;
      }
    | undefined;
  query: {
    isLoading: boolean;
    isError: boolean;
    error: unknown;
  };
  warehouseId: string;
  movementType: string;
  dateFrom: string;
  dateTo: string;
  referenceId: string;
  hasFilters: boolean;
  canReadSales: boolean;
  canOpenGoodsReceipts: boolean;
  canOpenStockAdjustments: boolean;
  onWarehouseChange: (value: string) => void;
  onMovementTypeChange: (value: string) => void;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onReferenceIdChange: (value: string) => void;
  onReset: () => void;
  onPreviousPage: () => void;
  onNextPage: () => void;
}) {
  return (
    <>
      <PageToolbar>
        <div className="grid w-full gap-3 xl:grid-cols-[180px_180px_170px_170px_minmax(180px,1fr)_auto]">
          <NativeSelect
            value={warehouseId}
            onChange={onWarehouseChange}
            placeholder={
              warehousesLoading
                ? "Loading warehouses"
                : "All warehouses"
            }
            options={warehouses.map((warehouse) => ({
              value: warehouse.id,
              label: `${warehouse.code} - ${warehouse.name}`,
            }))}
          />

          <NativeSelect
            value={movementType}
            onChange={onMovementTypeChange}
            placeholder="All movements"
            options={MOVEMENT_TYPE_OPTIONS}
          />

          <Input
            type="date"
            value={dateFrom}
            onChange={(event) => onDateFromChange(event.target.value)}
            aria-label="Movement date from"
          />

          <Input
            type="date"
            value={dateTo}
            onChange={(event) => onDateToChange(event.target.value)}
            aria-label="Movement date to"
          />

          <Input
            value={referenceId}
            onChange={(event) => onReferenceIdChange(event.target.value)}
            placeholder="Reference ID"
          />

          {hasFilters ? (
            <Button
              type="button"
              variant="ghost"
              onClick={onReset}
            >
              Clear
            </Button>
          ) : null}
        </div>
      </PageToolbar>

      {query.isLoading ? (
        <LoadingState title="Loading stock activity" />
      ) : query.isError ? (
        <ErrorState
          title="Stock activity unavailable"
          description={errorMessage(query.error)}
        />
      ) : movements.length === 0 ? (
        <EmptyState
          icon={<History className="h-12 w-12" />}
          title={
            hasFilters
              ? "No movement matched"
              : "No stock activity found"
          }
          description={
            hasFilters
              ? "Adjust the filters to widen the activity view."
              : "Sale, refund, and void stock movements will appear here once recorded."
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-md border">
          <table className="w-full min-w-[1100px] text-sm">
            <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">
                  Time
                </th>
                <th className="px-3 py-2 font-medium">
                  Product
                </th>
                <th className="px-3 py-2 font-medium">
                  Warehouse
                </th>
                <th className="px-3 py-2 font-medium">
                  Batch
                </th>
                <th className="px-3 py-2 font-medium">
                  Type
                </th>
                <th className="px-3 py-2 font-medium">
                  Direction
                </th>
                <th className="px-3 py-2 text-right font-medium">
                  Quantity
                </th>
                <th className="px-3 py-2 font-medium">
                  Reference
                </th>
                <th className="px-3 py-2 font-medium">
                  User
                </th>
              </tr>
            </thead>
            <tbody>
              {movements.map((movement) => (
                <InventoryActivityRow
                  key={movement.id}
                  movement={movement}
                  canReadSales={canReadSales}
                  canOpenGoodsReceipts={canOpenGoodsReceipts}
                  canOpenStockAdjustments={canOpenStockAdjustments}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}

      {pagination ? (
        <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
          <span>
            Page {pagination.page} of {Math.max(pagination.pages, 1)} · {pagination.total} movements
          </span>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onPreviousPage}
              disabled={!pagination.has_prev}
            >
              Previous
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onNextPage}
              disabled={!pagination.has_next}
            >
              Next
            </Button>
          </div>
        </div>
      ) : null}
    </>
  );
}

function InventoryActivityRow({
  movement,
  canReadSales,
  canOpenGoodsReceipts,
  canOpenStockAdjustments,
}: {
  movement: InventoryMovementSummary;
  canReadSales: boolean;
  canOpenGoodsReceipts: boolean;
  canOpenStockAdjustments: boolean;
}) {
  const direction = movementDirection(movement.quantity);
  const canOpenSale =
    canReadSales &&
    movement.reference.type === "sale" &&
    movement.reference.id.length > 0;
  const canOpenGoodsReceipt =
    canOpenGoodsReceipts &&
    movement.reference.type === "goods_receipt" &&
    movement.reference.id.length > 0;
  const canOpenStockAdjustment =
    canOpenStockAdjustments &&
    movement.reference.type === "stock_adjustment" &&
    movement.reference.id.length > 0;

  return (
    <tr className="border-t">
      <td className="px-3 py-3">
        {dateTimeLabel(movement.created_at)}
      </td>
      <td className="px-3 py-3">
        <div className="font-medium">
          {movement.product.name}
        </div>
        <div className="text-xs text-muted-foreground">
          {movement.product.internal_sku}
        </div>
      </td>
      <td className="px-3 py-3">
        {movement.warehouse.code} · {movement.warehouse.name}
      </td>
      <td className="px-3 py-3">
        {movement.batch?.batch_number ?? "None"}
      </td>
      <td className="px-3 py-3">
        {movementTypeLabel(movement.movement_type)}
      </td>
      <td className="px-3 py-3">
        <Badge
          variant={
            direction === "Out"
              ? "secondary"
              : direction === "In"
                ? "outline"
                : "ghost"
          }
        >
          {direction}
        </Badge>
      </td>
      <td className="px-3 py-3 text-right">
        {quantity(movement.quantity)}
      </td>
      <td className="px-3 py-3">
        {canOpenSale ? (
          <Link
            to={PATHS.SALES.receipt(movement.reference.id)}
            className={buttonVariants({
              variant: "outline",
              size: "sm",
            })}
          >
            Receipt
          </Link>
        ) : canOpenGoodsReceipt ? (
          <Link
            to={PATHS.INVENTORY.receipt(movement.reference.id)}
            className={buttonVariants({
              variant: "outline",
              size: "sm",
            })}
          >
            Goods Receipt
          </Link>
        ) : canOpenStockAdjustment ? (
          <Link
            to={PATHS.INVENTORY.stockAdjustment(movement.reference.id)}
            className={buttonVariants({
              variant: "outline",
              size: "sm",
            })}
          >
            View Adjustment
          </Link>
        ) : (
          <span>
            {movement.reference.type}: {movement.reference.id}
          </span>
        )}
      </td>
      <td className="px-3 py-3">
        {movement.performed_by?.name ??
          movement.performed_by?.username ??
          "Unknown"}
      </td>
    </tr>
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

export default InventoryPage;
