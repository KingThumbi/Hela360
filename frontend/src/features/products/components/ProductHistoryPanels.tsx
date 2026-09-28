import {
  Boxes,
  ClipboardCheck,
  PackageSearch,
  ReceiptText,
  ShoppingCart,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useProductMovementHistory,
  useProductPurchaseHistory,
  useProductSalesHistory,
  useProductStockCountHistory,
} from "@/hooks/queries/products";
import { PATHS } from "@/routes/routes";
import type { PaginationMeta } from "@/types/api";
import type {
  ProductMovementHistoryItem,
} from "@/types/responses/product-history";

const PAGE_SIZE_OPTIONS = [
  25,
  50,
  100,
] as const;

type PageSize =
  (typeof PAGE_SIZE_OPTIONS)[number];

const sourceLinkClassName = `
  inline-flex
  h-8
  items-center
  justify-center
  gap-2
  rounded-md
  border
  bg-background
  px-3
  text-sm
  font-medium
  transition-colors
  hover:bg-accent
  hover:text-accent-foreground
  focus-visible:outline-none
  focus-visible:ring-2
  focus-visible:ring-ring
`;

function displayNumber(
  value:
    | string
    | number
    | null
    | undefined,
) {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return String(value);
  }

  return new Intl.NumberFormat(
    undefined,
    {
      maximumFractionDigits: 6,
    },
  ).format(parsed);
}

function displayDate(
  value: string | null | undefined,
) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString();
}

function EmptyPanel({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-dashed p-8">
      <p className="font-medium">
        {title}
      </p>

      <p className="mt-1 text-sm text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

function DateRangeFilters({
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
}: {
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <label className="space-y-1.5">
        <span className="text-xs font-medium text-muted-foreground">
          From
        </span>

        <Input
          type="date"
          value={dateFrom}
          onChange={(event) =>
            onDateFromChange(
              event.target.value,
            )
          }
        />
      </label>

      <label className="space-y-1.5">
        <span className="text-xs font-medium text-muted-foreground">
          To
        </span>

        <Input
          type="date"
          value={dateTo}
          onChange={(event) =>
            onDateToChange(
              event.target.value,
            )
          }
        />
      </label>
    </div>
  );
}

function HistoryPagination({
  pagination,
  pageSize,
  noun,
  isFetching,
  onPageChange,
  onPageSizeChange,
}: {
  pagination: PaginationMeta | undefined;
  pageSize: PageSize;
  noun: string;
  isFetching: boolean;
  onPageChange: (page: number) => void;
  onPageSizeChange: (
    pageSize: PageSize,
  ) => void;
}) {
  if (!pagination) {
    return null;
  }

  return (
    <div className="flex flex-col gap-3 text-sm text-muted-foreground lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span>
          {pagination.total > 0
            ? `${(
                (pagination.page - 1) *
                  pagination.per_page
              ) + 1}-${Math.min(
                pagination.page *
                  pagination.per_page,
                pagination.total,
              )} of ${pagination.total} ${noun}`
            : `0 ${noun}`}
        </span>

        <span>
          Page {pagination.page} of{" "}
          {pagination.pages || 1}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <span className="whitespace-nowrap">
          Rows per page
        </span>

        <Select
          value={String(pageSize)}
          onValueChange={(value) => {
            const next =
              Number(value) as PageSize;

            if (
              !PAGE_SIZE_OPTIONS.includes(
                next,
              )
            ) {
              return;
            }

            onPageSizeChange(next);
          }}
          disabled={isFetching}
        >
          <SelectTrigger
            className="w-[90px]"
            aria-label="Rows per page"
          >
            <SelectValue />
          </SelectTrigger>

          <SelectContent>
            {PAGE_SIZE_OPTIONS.map(
              (option) => (
                <SelectItem
                  key={option}
                  value={String(option)}
                >
                  {option}
                </SelectItem>
              ),
            )}
          </SelectContent>
        </Select>

        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={
            !pagination.has_prev ||
            isFetching
          }
          onClick={() =>
            onPageChange(
              Math.max(
                pagination.page - 1,
                1,
              ),
            )
          }
        >
          Previous
        </Button>

        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={
            !pagination.has_next ||
            isFetching
          }
          onClick={() =>
            onPageChange(
              pagination.page + 1,
            )
          }
        >
          Next
        </Button>
      </div>
    </div>
  );
}

function MovementReference({
  item,
}: {
  item: ProductMovementHistoryItem;
}) {
  const reference = item.reference;

  if (
    !reference?.type ||
    !reference?.id
  ) {
    return null;
  }

  if (reference.type === "sale") {
    return (
      <Link
        to={PATHS.SALES.receipt(
          reference.id,
        )}
        className={sourceLinkClassName}
      >
        <ReceiptText className="size-4" />
        Receipt
      </Link>
    );
  }

  if (
    reference.type ===
    "goods_receipt"
  ) {
    return (
      <Link
        to={PATHS.INVENTORY.receipt(
          reference.id,
        )}
        className={sourceLinkClassName}
      >
        <ReceiptText className="size-4" />
        Goods Receipt
      </Link>
    );
  }

  if (
    reference.type ===
    "stock_adjustment"
  ) {
    return (
      <Link
        to={
          PATHS.INVENTORY.stockAdjustment(
            reference.id,
          )
        }
        className={sourceLinkClassName}
      >
        <ReceiptText className="size-4" />
        View Adjustment
      </Link>
    );
  }

  /*
   * Refund and void references currently
   * have no canonical detail destination.
   * Preserve the evidence without inventing
   * a route.
   */
  return (
    <Badge variant="outline">
      {reference.type} ·{" "}
      {reference.id}
    </Badge>
  );
}

function stockCountLifecycleLabel(
  lifecycle: string,
) {
  if (lifecycle === "counting") {
    return "Counting";
  }

  if (lifecycle === "awaiting_posting") {
    return "Awaiting Posting";
  }

  if (lifecycle === "posted") {
    return "Posted";
  }

  if (lifecycle === "completed") {
    return "Completed";
  }

  if (lifecycle === "cancelled") {
    return "Cancelled";
  }

  if (lifecycle === "superseded") {
    return "Superseded";
  }

  return lifecycle;
}

function stockCountLifecycleClassName(
  lifecycle: string,
) {
  if (lifecycle === "posted") {
    return (
      "border-emerald-200 bg-emerald-50 " +
      "text-emerald-700 dark:border-emerald-900 " +
      "dark:bg-emerald-950/40 dark:text-emerald-300"
    );
  }

  if (lifecycle === "awaiting_posting") {
    return (
      "border-amber-200 bg-amber-50 " +
      "text-amber-700 dark:border-amber-900 " +
      "dark:bg-amber-950/40 dark:text-amber-300"
    );
  }

  if (lifecycle === "counting") {
    return (
      "border-sky-200 bg-sky-50 " +
      "text-sky-700 dark:border-sky-900 " +
      "dark:bg-sky-950/40 dark:text-sky-300"
    );
  }

  if (lifecycle === "superseded") {
    return (
      "border-violet-200 bg-violet-50 " +
      "text-violet-700 dark:border-violet-900 " +
      "dark:bg-violet-950/30 dark:text-violet-300"
    );
  }

  if (lifecycle === "cancelled") {
    return (
      "border-slate-200 bg-slate-50 " +
      "text-slate-600 dark:border-slate-800 " +
      "dark:bg-slate-900/50 dark:text-slate-300"
    );
  }

  return (
    "border-emerald-200 bg-emerald-50 " +
    "text-emerald-700 dark:border-emerald-900 " +
    "dark:bg-emerald-950/40 dark:text-emerald-300"
  );
}

export function ProductSalesHistoryPanel({
  productId,
  enabled,
}: {
  productId: string;
  enabled: boolean;
}) {
  const [page, setPage] =
    useState(1);

  const [pageSize, setPageSize] =
    useState<PageSize>(25);

  const [dateFrom, setDateFrom] =
    useState("");

  const [dateTo, setDateTo] =
    useState("");

  const query =
    useProductSalesHistory(
      productId,
      {
        page,
        per_page: pageSize,
        date_from:
          dateFrom || undefined,
        date_to:
          dateTo || undefined,
      },
      {
        enabled,
      },
    );

  const sales =
    query.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            Sales filters
          </CardTitle>

          <CardDescription>
            Filter persisted sale-line
            evidence without changing
            historical values.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <DateRangeFilters
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={(value) => {
              setDateFrom(value);
              setPage(1);
            }}
            onDateToChange={(value) => {
              setDateTo(value);
              setPage(1);
            }}
          />
        </CardContent>
      </Card>

      {query.isLoading ? (
        <EmptyPanel
          title="Loading sales history"
          description="Loading persisted sales evidence for this product."
        />
      ) : query.isError ? (
        <EmptyPanel
          title="Unable to load sales history"
          description={
            query.error instanceof Error
              ? query.error.message
              : "Sales history could not be loaded."
          }
        />
      ) : sales.length === 0 ? (
        <EmptyPanel
          title="No sales history"
          description="No matching sales lines were found for this product."
        />
      ) : (
        <div className="space-y-3">
          {sales.map((item) => (
            <Card
              key={item.sale_item_id}
            >
              <CardContent className="flex flex-col gap-4 p-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <ShoppingCart className="size-4" />

                    <span className="font-medium">
                      {
                        item.sale
                          .sale_number
                      }
                    </span>

                    <Badge variant="outline">
                      {item.sale.status}
                    </Badge>

                    {item.sale
                      .refund_status &&
                    item.sale
                      .refund_status !==
                      "not_refunded" ? (
                      <Badge variant="outline">
                        {
                          item.sale
                            .refund_status
                        }
                      </Badge>
                    ) : null}
                  </div>

                  <p className="mt-2 text-sm text-muted-foreground">
                    {displayDate(
                      item.sale
                        .sale_date,
                    )}
                    {" · "}
                    {displayNumber(
                      item.quantity,
                    )}{" "}
                    {item.uom.code ?? ""}
                    {" · "}
                    Transaction price{" "}
                    {displayNumber(
                      item.unit_price,
                    )}
                  </p>

                  <p className="mt-1 text-sm">
                    Base-unit price:{" "}
                    <span className="font-medium">
                      {displayNumber(
                        item.normalized_base_unit_price,
                      )}
                    </span>
                  </p>
                </div>

                <Link
                  to={PATHS.SALES.receipt(
                    item.sale.id,
                  )}
                  className={
                    sourceLinkClassName
                  }
                >
                  <ReceiptText className="size-4" />
                  Receipt
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <HistoryPagination
        pagination={
          query.data?.pagination
        }
        pageSize={pageSize}
        noun="sales lines"
        isFetching={
          query.isFetching
        }
        onPageChange={setPage}
        onPageSizeChange={(next) => {
          setPageSize(next);
          setPage(1);
        }}
      />
    </div>
  );
}

export function ProductPurchaseHistoryPanel({
  productId,
  enabled,
}: {
  productId: string;
  enabled: boolean;
}) {
  const [page, setPage] =
    useState(1);

  const [pageSize, setPageSize] =
    useState<PageSize>(25);

  const [dateFrom, setDateFrom] =
    useState("");

  const [dateTo, setDateTo] =
    useState("");

  const query =
    useProductPurchaseHistory(
      productId,
      {
        page,
        per_page: pageSize,
        date_from:
          dateFrom || undefined,
        date_to:
          dateTo || undefined,
      },
      {
        enabled,
      },
    );

  const purchases =
    query.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            Purchase filters
          </CardTitle>

          <CardDescription>
            Filter posted Goods Receipt
            evidence by receipt date.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <DateRangeFilters
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={(value) => {
              setDateFrom(value);
              setPage(1);
            }}
            onDateToChange={(value) => {
              setDateTo(value);
              setPage(1);
            }}
          />
        </CardContent>
      </Card>

      {query.isLoading ? (
        <EmptyPanel
          title="Loading purchase history"
          description="Loading posted Goods Receipt evidence for this product."
        />
      ) : query.isError ? (
        <EmptyPanel
          title="Unable to load purchase history"
          description={
            query.error instanceof Error
              ? query.error.message
              : "Purchase history could not be loaded."
          }
        />
      ) : purchases.length === 0 ? (
        <EmptyPanel
          title="No purchase history"
          description="No posted receipt lines were found for this product."
        />
      ) : (
        <div className="space-y-3">
          {purchases.map((item) => (
            <Card
              key={
                item.receipt_item_id
              }
            >
              <CardContent className="flex flex-col gap-4 p-4 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <PackageSearch className="size-4" />

                    <span className="font-medium">
                      {
                        item.receipt
                          .receipt_number
                      }
                    </span>

                    {item.supplier ? (
                      <Badge variant="outline">
                        {
                          item.supplier
                            .name
                        }
                      </Badge>
                    ) : null}
                  </div>

                  <p className="mt-2 text-sm text-muted-foreground">
                    {displayDate(
                      item.receipt
                        .posted_at,
                    )}
                    {" · "}
                    {displayNumber(
                      item.quantity,
                    )}{" "}
                    {item.uom.code ?? ""}
                  </p>

                  <p className="mt-1 text-sm">
                    Unit cost{" "}
                    <span className="font-medium">
                      {displayNumber(
                        item.unit_cost,
                      )}
                    </span>
                    {" · "}
                    Base cost{" "}
                    <span className="font-medium">
                      {displayNumber(
                        item.base_unit_cost,
                      )}
                    </span>
                  </p>
                </div>

                <Link
                  to={
                    PATHS.INVENTORY.receipt(
                      item.receipt.id,
                    )
                  }
                  className={
                    sourceLinkClassName
                  }
                >
                  <ReceiptText className="size-4" />
                  Goods Receipt
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <HistoryPagination
        pagination={
          query.data?.pagination
        }
        pageSize={pageSize}
        noun="receipt lines"
        isFetching={
          query.isFetching
        }
        onPageChange={setPage}
        onPageSizeChange={(next) => {
          setPageSize(next);
          setPage(1);
        }}
      />
    </div>
  );
}

export function ProductMovementHistoryPanel({
  productId,
  enabled,
}: {
  productId: string;
  enabled: boolean;
}) {
  const [page, setPage] =
    useState(1);

  const [pageSize, setPageSize] =
    useState<PageSize>(25);

  const [dateFrom, setDateFrom] =
    useState("");

  const [dateTo, setDateTo] =
    useState("");

  const [
    movementType,
    setMovementType,
  ] = useState("all");

  const query =
    useProductMovementHistory(
      productId,
      {
        page,
        per_page: pageSize,
        date_from:
          dateFrom || undefined,
        date_to:
          dateTo || undefined,
        movement_type:
          movementType === "all"
            ? undefined
            : movementType,
      },
      {
        enabled,
      },
    );

  const movements =
    query.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            Movement filters
          </CardTitle>

          <CardDescription>
            Filter the product inventory
            ledger while preserving source
            evidence.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <DateRangeFilters
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={(value) => {
              setDateFrom(value);
              setPage(1);
            }}
            onDateToChange={(value) => {
              setDateTo(value);
              setPage(1);
            }}
          />

          <label className="block space-y-1.5">
            <span className="text-xs font-medium text-muted-foreground">
              Movement type
            </span>

            <Select
              value={movementType}
              onValueChange={(value) => {
                if (!value) {
                  return;
                }

                setMovementType(value);
                setPage(1);
              }}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>

              <SelectContent>
                <SelectItem value="all">
                  All movement types
                </SelectItem>

                <SelectItem value="goods_receipt">
                  Goods receipt
                </SelectItem>

                <SelectItem value="sale">
                  Sale
                </SelectItem>

                <SelectItem value="sale_refund_return">
                  Sale refund return
                </SelectItem>

                <SelectItem value="sale_void">
                  Sale void
                </SelectItem>

                <SelectItem value="stock_adjustment">
                  Stock adjustment
                </SelectItem>
              </SelectContent>
            </Select>
          </label>
        </CardContent>
      </Card>

      {query.isLoading ? (
        <EmptyPanel
          title="Loading stock movements"
          description="Loading inventory-ledger evidence for this product."
        />
      ) : query.isError ? (
        <EmptyPanel
          title="Unable to load stock movements"
          description={
            query.error instanceof Error
              ? query.error.message
              : "Movement history could not be loaded."
          }
        />
      ) : movements.length === 0 ? (
        <EmptyPanel
          title="No stock movements"
          description="No matching inventory ledger movements were found."
        />
      ) : (
        <div className="space-y-3">
          {movements.map((item) => {
            const quantity =
              Number(item.quantity);

            const direction =
              quantity > 0
                ? "In"
                : quantity < 0
                  ? "Out"
                  : "Neutral";

            return (
              <Card key={item.id}>
                <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Boxes className="size-4" />

                      <span className="font-medium">
                        {
                          item.movement_type
                        }
                      </span>

                      <Badge variant="outline">
                        {direction}
                      </Badge>
                    </div>

                    <p className="mt-2 text-sm text-muted-foreground">
                      {displayDate(
                        item.created_at,
                      )}
                      {" · "}
                      Qty{" "}
                      {displayNumber(
                        item.quantity,
                      )}
                      {item.warehouse?.name
                        ? ` · ${item.warehouse.name}`
                        : ""}
                    </p>

                    {item.batch
                      ?.batch_number ? (
                      <p className="mt-1 text-xs text-muted-foreground">
                        Batch{" "}
                        {
                          item.batch
                            .batch_number
                        }
                      </p>
                    ) : null}
                  </div>

                  <MovementReference
                    item={item}
                  />
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <HistoryPagination
        pagination={
          query.data?.pagination
        }
        pageSize={pageSize}
        noun="movements"
        isFetching={
          query.isFetching
        }
        onPageChange={setPage}
        onPageSizeChange={(next) => {
          setPageSize(next);
          setPage(1);
        }}
      />
    </div>
  );
}

export function ProductStockCountHistoryPanel({
  productId,
  enabled,
  canViewAdjustment,
}: {
  productId: string;
  enabled: boolean;
  canViewAdjustment: boolean;
}) {
  const [page, setPage] =
    useState(1);

  const [pageSize, setPageSize] =
    useState<PageSize>(25);

  const [dateFrom, setDateFrom] =
    useState("");

  const [dateTo, setDateTo] =
    useState("");

  const query =
    useProductStockCountHistory(
      productId,
      {
        page,
        per_page: pageSize,
        date_from:
          dateFrom || undefined,
        date_to:
          dateTo || undefined,
      },
      {
        enabled,
      },
    );

  const counts =
    query.data?.items ?? [];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>
            Stock count filters
          </CardTitle>

          <CardDescription>
            Review physical-count evidence and
            trace posted variances back to their
            source inventory documents.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <DateRangeFilters
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={(value) => {
              setDateFrom(value);
              setPage(1);
            }}
            onDateToChange={(value) => {
              setDateTo(value);
              setPage(1);
            }}
          />
        </CardContent>
      </Card>

      {query.isLoading ? (
        <EmptyPanel
          title="Loading stock-count history"
          description="Loading physical inventory-count evidence for this product."
        />
      ) : query.isError ? (
        <EmptyPanel
          title="Unable to load stock-count history"
          description={
            query.error instanceof Error
              ? query.error.message
              : "Stock-count history could not be loaded."
          }
        />
      ) : counts.length === 0 ? (
        <EmptyPanel
          title="No stock-count history"
          description="No physical stock-count lines were found for this product."
        />
      ) : (
        <div className="space-y-3">
          {counts.map((item) => {
            const line = item.line;

            const batchNumber =
              line.batch?.batch_number ??
              line.observed_batch_number;

            const expiryDate =
              line.batch?.expiry_date ??
              line.observed_expiry_date;

            const countedUnit =
              line.counted_unit_code ??
              line.counted_unit_name;

            const exposesExpected =
              line.expected_quantity !==
              undefined;

            const exposesVariance =
              line.variance_quantity !==
              undefined;

            const variance =
              line.variance_quantity == null
                ? null
                : Number(
                    line.variance_quantity,
                  );

            return (
              <Card key={line.id}>
                <CardContent className="space-y-4 p-4">
                  <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                    <div className="space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <ClipboardCheck className="size-4" />

                        <span className="font-medium">
                          {
                            item.stock_count
                              .count_number
                          }
                        </span>

                        <Badge
                          variant="outline"
                          className={
                            stockCountLifecycleClassName(
                              item.stock_count
                                .lifecycle,
                            )
                          }
                        >
                          {stockCountLifecycleLabel(
                            item.stock_count
                              .lifecycle,
                          )}
                        </Badge>

                        <Badge variant="outline">
                          {
                            item.stock_count
                              .count_mode
                          }
                        </Badge>
                      </div>

                      <div className="text-sm text-muted-foreground">
                        {displayDate(
                          item.stock_count
                            .completed_at ??
                            item.stock_count
                              .started_at,
                        )}
                        {" · "}
                        {item.warehouse.name}
                      </div>

                      {batchNumber ? (
                        <div className="text-sm text-muted-foreground">
                          Batch{" "}
                          <span className="font-medium text-foreground">
                            {batchNumber}
                          </span>

                          {expiryDate
                            ? ` · Expiry ${expiryDate}`
                            : ""}
                        </div>
                      ) : null}

                      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                        {exposesExpected ? (
                          <div className="rounded-lg border bg-muted/30 p-3">
                            <p className="text-xs text-muted-foreground">
                              Expected
                            </p>

                            <p className="mt-1 font-medium">
                              {displayNumber(
                                line.expected_quantity,
                              )}
                            </p>
                          </div>
                        ) : null}

                        <div className="rounded-lg border bg-muted/30 p-3">
                          <p className="text-xs text-muted-foreground">
                            Counted
                          </p>

                          <p className="mt-1 font-medium">
                            {line.counted_unit_quantity !=
                              null &&
                            countedUnit
                              ? `${displayNumber(
                                  line.counted_unit_quantity,
                                )} ${countedUnit}`
                              : displayNumber(
                                  line.counted_quantity,
                                )}
                          </p>

                          {line.counted_unit_quantity !=
                            null &&
                          countedUnit &&
                          line.counted_quantity !=
                            null ? (
                            <p className="mt-1 text-xs text-muted-foreground">
                              ={" "}
                              {displayNumber(
                                line.counted_quantity,
                              )}{" "}
                              base units
                            </p>
                          ) : null}
                        </div>

                        {exposesVariance ? (
                          <div className="rounded-lg border bg-muted/30 p-3">
                            <p className="text-xs text-muted-foreground">
                              Variance
                            </p>

                            <p className="mt-1 font-medium">
                              {variance != null &&
                              Number.isFinite(
                                variance,
                              ) &&
                              variance > 0
                                ? "+"
                                : ""}
                              {displayNumber(
                                line.variance_quantity,
                              )}
                            </p>
                          </div>
                        ) : null}

                        {line.counted_conversion_factor_to_base ? (
                          <div className="rounded-lg border bg-muted/30 p-3">
                            <p className="text-xs text-muted-foreground">
                              Historical conversion
                            </p>

                            <p className="mt-1 font-medium">
                              1{" "}
                              {countedUnit ??
                                "entered unit"}
                              {" = "}
                              {displayNumber(
                                line.counted_conversion_factor_to_base,
                              )}{" "}
                              base units
                            </p>
                          </div>
                        ) : null}
                      </div>

                      {!exposesExpected &&
                      item.stock_count
                        .count_mode ===
                        "blind" &&
                      item.stock_count.status ===
                        "open" ? (
                        <p className="text-xs text-muted-foreground">
                          System quantities are
                          intentionally hidden while
                          this blind count remains
                          open.
                        </p>
                      ) : null}

                      {line.source_type ===
                        "discovered" ? (
                        <Badge variant="outline">
                          Discovered during count
                        </Badge>
                      ) : null}

                      {line.notes ? (
                        <p className="text-sm text-muted-foreground">
                          {line.notes}
                        </p>
                      ) : null}
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <Link
                        to={
                          PATHS.INVENTORY.stockCount(
                            item.stock_count.id,
                          )
                        }
                        className={
                          sourceLinkClassName
                        }
                      >
                        <ClipboardCheck className="size-4" />
                        View Stock Count
                      </Link>

                      {item.adjustment &&
                      canViewAdjustment ? (
                        <Link
                          to={
                            PATHS.INVENTORY
                              .stockAdjustment(
                                item.adjustment.id,
                              )
                          }
                          className={
                            sourceLinkClassName
                          }
                        >
                          <ReceiptText className="size-4" />
                          View Adjustment
                        </Link>
                      ) : item.adjustment ? (
                        <Badge variant="outline">
                          Adjustment{" "}
                          {
                            item.adjustment
                              .adjustment_number
                          }
                        </Badge>
                      ) : null}
                    </div>
                  </div>

                  {item.adjustment ? (
                    <div className="border-t pt-3 text-xs text-muted-foreground">
                      Adjustment{" "}
                      <span className="font-medium text-foreground">
                        {
                          item.adjustment
                            .adjustment_number
                        }
                      </span>

                      {item.adjustment
                        .quantity_delta != null
                        ? ` · Inventory delta ${
                            Number(
                              item.adjustment
                                .quantity_delta,
                            ) > 0
                              ? "+"
                              : ""
                          }${displayNumber(
                            item.adjustment
                              .quantity_delta,
                          )}`
                        : ""}

                      {item.adjustment.posted_at
                        ? ` · Posted ${displayDate(
                            item.adjustment
                              .posted_at,
                          )}`
                        : ""}
                    </div>
                  ) : null}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <HistoryPagination
        pagination={
          query.data?.pagination
        }
        pageSize={pageSize}
        noun="stock-count lines"
        isFetching={query.isFetching}
        onPageChange={setPage}
        onPageSizeChange={(next) => {
          setPageSize(next);
          setPage(1);
        }}
      />
    </div>
  );
}
