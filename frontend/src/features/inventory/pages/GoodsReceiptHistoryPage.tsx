import {
  ArrowLeft,
  Eye,
  History,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  useMemo,
  useState,
  type FormEvent,
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
  useGoodsReceipts,
} from "@/hooks/queries/inventory";
import {
  useSuppliers,
} from "@/hooks/queries/suppliers";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import { useQueryScope } from "@/hooks/useQueryScope";
import { PATHS } from "@/routes/routes";
import type {
  GoodsReceiptSummary,
} from "@/types/responses";

const PAGE_SIZE = 25;
const SUPPLIER_PAGE_SIZE = 10;

function dateTimeLabel(value: string | null): string {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString();
}

function money(value: string): string {
  const normalized = Number(value);
  return Number.isFinite(normalized)
    ? normalized.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })
    : value;
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

export function GoodsReceiptHistoryPage() {
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    page,
    setPage,
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
    dateFrom,
    setDateFrom,
  ] = useState("");
  const [
    dateTo,
    setDateTo,
  ] = useState("");
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    supplierSearchInput,
    setSupplierSearchInput,
  ] = useState("");
  const [
    supplierSearch,
    setSupplierSearch,
  ] = useState("");
  const [
    supplierId,
    setSupplierId,
  ] = useState("");

  const params = useMemo(
    () => ({
      page,
      per_page: PAGE_SIZE,
      search:
        submittedSearch.trim().length > 0
          ? submittedSearch.trim()
          : undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      warehouse_id: warehouseId || undefined,
      supplier_id: supplierId || undefined,
    }),
    [
      dateFrom,
      dateTo,
      page,
      submittedSearch,
      supplierId,
      warehouseId,
    ],
  );

  const receiptsQuery = useGoodsReceipts(params);
  const warehousesQuery = useWarehouses();
  const suppliersQuery = useSuppliers({
    page: 1,
    per_page: SUPPLIER_PAGE_SIZE,
    search: supplierSearch || undefined,
  });

  const warehouses = useMemo(
    () => (warehousesQuery.data ?? []).filter((warehouse) => warehouse.is_active),
    [warehousesQuery.data],
  );
  const suppliers = (suppliersQuery.data?.items ?? []).filter(
    (supplier) => supplier.is_active,
  );
  const receipts = receiptsQuery.data?.items ?? [];
  const pagination = receiptsQuery.data?.pagination;
  const hasFilters =
    submittedSearch.trim().length > 0 ||
    dateFrom.length > 0 ||
    dateTo.length > 0 ||
    warehouseId.length > 0 ||
    supplierId.length > 0;

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
    setSubmittedSearch(searchInput.trim());
  };

  const resetFilters = () => {
    setPage(1);
    setSearchInput("");
    setSubmittedSearch("");
    setDateFrom("");
    setDateTo("");
    setWarehouseId("");
    setSupplierId("");
    setSupplierSearch("");
    setSupplierSearchInput("");
  };

  if (!isBranchScopeReady) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>Receiving History</PageTitle>
            <PageDescription>
              Select an active branch before viewing receiving history.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <EmptyState
              title="Branch required"
              description="Goods Receipt history is branch-scoped."
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
          <PageTitle>Receiving History</PageTitle>
          <PageDescription>
            Review posted Goods Receipts by Warehouse, Supplier, receiver, and reference.
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
            onClick={() => receiptsQuery.refetch()}
            disabled={receiptsQuery.isFetching}
          >
            <RefreshCw
              className={receiptsQuery.isFetching ? "animate-spin" : undefined}
            />
            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageSection>
          <PageToolbar>
            <div className="grid w-full gap-3 xl:grid-cols-[minmax(220px,1fr)_160px_160px_190px_minmax(260px,1fr)_auto]">
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
                    placeholder="Receipt or supplier reference"
                    className="pl-8"
                  />
                </div>
                <Button type="submit">
                  Search
                </Button>
              </form>

              <Input
                type="date"
                value={dateFrom}
                onChange={(event) => {
                  setPage(1);
                  setDateFrom(event.target.value);
                }}
                aria-label="Received from"
              />

              <Input
                type="date"
                value={dateTo}
                onChange={(event) => {
                  setPage(1);
                  setDateTo(event.target.value);
                }}
                aria-label="Received to"
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

              <div className="flex gap-2">
                <Input
                  type="search"
                  value={supplierSearchInput}
                  onChange={(event) =>
                    setSupplierSearchInput(event.target.value)
                  }
                  placeholder="Search suppliers"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setSupplierSearch(supplierSearchInput.trim());
                    setSupplierId("");
                  }}
                >
                  <Search />
                  Search
                </Button>
              </div>

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

          <div className="mb-3 max-w-sm">
            <NativeSelect
              value={supplierId}
              onChange={(value) => {
                setPage(1);
                setSupplierId(value);
              }}
              placeholder={
                suppliersQuery.isLoading
                  ? "Loading suppliers"
                  : "All suppliers"
              }
              options={suppliers.map((supplier) => ({
                value: supplier.id,
                label: `${supplier.supplier_code} - ${supplier.name}`,
              }))}
            />
          </div>

          {receiptsQuery.isLoading ? (
            <LoadingState title="Loading receiving history" />
          ) : receiptsQuery.isError ? (
            <ErrorState
              title="Receiving history unavailable"
              description={errorMessage(receiptsQuery.error)}
            />
          ) : receipts.length === 0 ? (
            <EmptyState
              icon={<History className="h-12 w-12" />}
              title={
                hasFilters
                  ? "No Goods Receipts matched"
                  : "No Goods Receipts recorded"
              }
              description={
                hasFilters
                  ? "Adjust the filters to widen the receiving audit view."
                  : "Posted receiving documents will appear here once stock is received."
              }
            />
          ) : (
            <GoodsReceiptHistoryTable
              receipts={receipts}
            />
          )}

          {pagination ? (
            <div className="flex items-center justify-between gap-3 text-sm text-muted-foreground">
              <span>
                Page {pagination.page} of {Math.max(pagination.pages, 1)} · {pagination.total} receipts
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setPage((value) => Math.max(1, value - 1))
                  }
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

function GoodsReceiptHistoryTable({
  receipts,
}: {
  receipts: GoodsReceiptSummary[];
}) {
  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full min-w-[1080px] text-sm">
        <thead className="bg-muted/50 text-left text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2 font-medium">Receipt</th>
            <th className="px-3 py-2 font-medium">Received</th>
            <th className="px-3 py-2 font-medium">Warehouse</th>
            <th className="px-3 py-2 font-medium">Supplier</th>
            <th className="px-3 py-2 font-medium">Supplier Ref</th>
            <th className="px-3 py-2 text-right font-medium">Items</th>
            <th className="px-3 py-2 text-right font-medium">Value</th>
            <th className="px-3 py-2 font-medium">Received By</th>
            <th className="px-3 py-2 font-medium">Status</th>
            <th className="px-3 py-2 text-right font-medium">Action</th>
          </tr>
        </thead>
        <tbody>
          {receipts.map((receipt) => (
            <tr
              key={receipt.id}
              className="border-t"
            >
              <td className="px-3 py-3 font-medium">
                {receipt.receipt_number}
              </td>
              <td className="px-3 py-3">
                {dateTimeLabel(receipt.received_at)}
              </td>
              <td className="px-3 py-3">
                {receipt.warehouse.code} · {receipt.warehouse.name}
              </td>
              <td className="px-3 py-3">
                {receipt.supplier
                  ? `${receipt.supplier.supplier_code} · ${receipt.supplier.name}`
                  : "No supplier"}
              </td>
              <td className="px-3 py-3">
                {receipt.supplier_reference ?? "None"}
              </td>
              <td className="px-3 py-3 text-right">
                {receipt.item_count}
              </td>
              <td className="px-3 py-3 text-right">
                {money(receipt.total_cost)}
              </td>
              <td className="px-3 py-3">
                {receipt.received_by?.name ??
                  receipt.received_by?.username ??
                  "Unknown"}
              </td>
              <td className="px-3 py-3">
                <Badge variant="outline">
                  {receipt.status}
                </Badge>
              </td>
              <td className="px-3 py-3 text-right">
                <Link
                  to={PATHS.INVENTORY.receipt(receipt.id)}
                  className={buttonVariants({
                    variant: "outline",
                    size: "sm",
                  })}
                >
                  <Eye />
                  View Receipt
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

export default GoodsReceiptHistoryPage;
