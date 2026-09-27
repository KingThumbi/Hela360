import {
  Boxes,
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
