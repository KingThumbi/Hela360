import {
  ArrowLeft,
} from "lucide-react";
import { useState } from "react";
import {
  Link,
  useNavigate,
  useParams,
} from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  Page,
  PageContent,
  PageDescription,
  PageHeader,
  PageTitle,
} from "@/components/page";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

import { useAuthorization } from "@/hooks/useAuthorization";
import {
  useProductHistory,
  useProductMovementTimeline,
  useProductPurchasePriceTrend,
  useProductSalesPriceTrend,
  useProductStockCountVarianceTrend,
} from "@/hooks/queries/products";

import { PATHS } from "@/routes/routes";

import type {
  ProductMovementHistoryItem,
  ProductStockCountHistoryItem,
} from "@/types/responses/product-history";

import {
  ProductUnifiedActivityTimeline,
} from "../components/ProductUnifiedActivityTimeline";

import {
  ProductOperationalInsights,
} from "../components/ProductOperationalInsights";

import {
  ProductSupplierIntelligence,
} from "../components/ProductSupplierIntelligence";

import {
  ProductBatchHistoryPanel,
  ProductMovementHistoryPanel,
  ProductPurchaseHistoryPanel,
  ProductSalesHistoryPanel,
  ProductStockCountHistoryPanel,
} from "../components/ProductHistoryPanels";

type PriceTrendChartPoint = {
  id: string;
  date: string;
  label: string;
  value: number | null;
  rawValue: string;
  quantity: string;
  uom: string | null;
  sourceId: string;
  sourceType: "sale" | "goods_receipt";
  status?: string | null;
  refundStatus?: string | null;
  isReturned?: boolean;
  supplier?: string | null;
};

function priceTrendSourcePath(
  point: PriceTrendChartPoint,
) {
  if (point.sourceType === "sale") {
    return PATHS.SALES.receipt(
      point.sourceId,
    );
  }

  if (
    point.sourceType ===
    "goods_receipt"
  ) {
    return PATHS.INVENTORY.receipt(
      point.sourceId,
    );
  }

  return null;
}

function priceTrendSourceLabel(
  point: PriceTrendChartPoint,
) {
  return point.sourceType === "sale"
    ? "Sale Receipt"
    : "Goods Receipt";
}

function movementSourcePath(
  item: ProductMovementHistoryItem,
) {
  const referenceType =
    item.reference?.type;

  const referenceId =
    item.reference?.id;

  if (!referenceId) {
    return null;
  }

  if (referenceType === "sale") {
    return PATHS.SALES.receipt(
      referenceId,
    );
  }

  if (referenceType === "goods_receipt") {
    return PATHS.INVENTORY.receipt(
      referenceId,
    );
  }

  if (referenceType === "stock_adjustment") {
    return PATHS.INVENTORY.stockAdjustment(
      referenceId,
    );
  }

  return null;
}

function movementSourceLabel(
  item: ProductMovementHistoryItem,
) {
  const referenceType =
    item.reference?.type;

  if (referenceType === "sale") {
    return "Sale Receipt";
  }

  if (referenceType === "goods_receipt") {
    return "Goods Receipt";
  }

  if (referenceType === "stock_adjustment") {
    return "Stock Adjustment";
  }

  return null;
}

function stockCountPath(
  item: ProductStockCountHistoryItem,
) {
  return PATHS.INVENTORY.stockCount(
    item.stock_count.id,
  );
}

function stockAdjustmentPath(
  item: ProductStockCountHistoryItem,
) {
  if (!item.adjustment?.id) {
    return null;
  }

  return PATHS.INVENTORY.stockAdjustment(
    item.adjustment.id,
  );
}

function stockCountLifecycleLabel(
  lifecycle: string,
) {
  switch (lifecycle) {
    case "counting":
      return "Counting";
    case "awaiting_posting":
      return "Awaiting posting";
    case "posted":
      return "Posted";
    case "completed":
      return "Completed";
    case "cancelled":
      return "Cancelled";
    case "superseded":
      return "Superseded";
    default:
      return lifecycle;
  }
}

function numeric(value: string | null | undefined) {
  if (value == null || value === "") {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : null;
}

function displayNumber(
  value: string | number | null | undefined,
) {
  if (value == null || value === "") {
    return "—";
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return String(value);
  }

  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 6,
  }).format(parsed);
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
    <div className="rounded-xl border border-dashed p-8 text-center">
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-sm text-muted-foreground">
        {description}
      </p>
    </div>
  );
}

export function ProductIntelligencePage() {
  const { productId = "" } = useParams();
  const navigate = useNavigate();

  const authorization = useAuthorization();

  const canReadSales =
    authorization.can("sales.read");

  const canReadInventory =
    authorization.can("inventory.read");

  const canCountInventory =
    authorization.can("inventory.count");

  const canAdjustInventory =
    authorization.can("inventory.adjust");

  const summaryQuery =
    useProductHistory(productId);

  const [trendDateFrom, setTrendDateFrom] =
    useState("");

  const [trendDateTo, setTrendDateTo] =
    useState("");

  const trendParams = {
    date_from:
      trendDateFrom || undefined,
    date_to:
      trendDateTo || undefined,
  };

  const salesTrendQuery =
    useProductSalesPriceTrend(
      productId,
      trendParams,
      {
        enabled: canReadSales,
      },
    );

  const purchaseTrendQuery =
    useProductPurchasePriceTrend(
      productId,
      trendParams,
      {
        enabled: canReadInventory,
      },
    );

  const movementTimelineQuery =
    useProductMovementTimeline(
      productId,
      {
        date_from:
          trendDateFrom || undefined,
        date_to:
          trendDateTo || undefined,
      },
      {
        enabled: canReadInventory,
      },
    );

  const stockCountVarianceQuery =
    useProductStockCountVarianceTrend(
      productId,
      {
        date_from:
          trendDateFrom || undefined,
        date_to:
          trendDateTo || undefined,
      },
      {
        enabled: canCountInventory,
      },
    );



  if (summaryQuery.isLoading) {
    return (
      <Page>
        <PageContent>
          <div className="rounded-xl border p-8 text-sm text-muted-foreground">
            Loading product intelligence…
          </div>
        </PageContent>
      </Page>
    );
  }

  if (summaryQuery.isError || !summaryQuery.data) {
    return (
      <Page>
        <PageContent>
          <div className="rounded-xl border border-destructive/30 p-8">
            <p className="font-medium">
              Unable to load Product Intelligence.
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {summaryQuery.error instanceof Error
                ? summaryQuery.error.message
                : "The product history could not be loaded."}
            </p>
          </div>
        </PageContent>
      </Page>
    );
  }

  const summary = summaryQuery.data;

  const canViewStockHistory =
    canCountInventory &&
    summary.capabilities.stock_history;

  const canViewActivity =
    canReadSales ||
    canReadInventory ||
    canCountInventory;

  const salesChartData: PriceTrendChartPoint[] =
    (salesTrendQuery.data?.items ?? [])
      .filter(
        (item) =>
          item.occurred_at &&
          numeric(item.value) !== null,
      )
      .map((item) => ({
        id: item.id,
        date: item.occurred_at!,
        label: item.source.number,
        value: numeric(item.value),
        rawValue: item.transaction_value,
        quantity: item.quantity,
        uom: item.uom.code,
        sourceId: item.source.id,
        sourceType: item.source.type,
        status: item.status,
        refundStatus: item.refund_status,
        isReturned: item.is_returned,
      }));

  const purchaseChartData: PriceTrendChartPoint[] =
    (purchaseTrendQuery.data?.items ?? [])
      .filter(
        (item) =>
          item.occurred_at &&
          numeric(item.value) !== null,
      )
      .map((item) => ({
        id: item.id,
        date: item.occurred_at!,
        label: item.source.number,
        value: numeric(item.value),
        rawValue: item.transaction_value,
        quantity: item.quantity,
        uom: item.uom.code,
        sourceId: item.source.id,
        sourceType: item.source.type,
        supplier: item.supplier?.name ?? null,
      }));

  const movementChartData =
    (movementTimelineQuery.data?.items ?? [])
      .filter(
        (item) =>
          item.created_at &&
          numeric(item.quantity) !== null,
      )
      .map((item) => ({
        ...item,
        created_at: item.created_at!,
        numericQuantity:
          numeric(item.quantity),
      }));

  const stockCountVarianceData =
    (stockCountVarianceQuery.data?.items ?? [])
      .map((item) => ({
        ...item,
        occurredAt:
          item.stock_count.completed_at ??
          item.stock_count.started_at,
        expectedQuantity:
          numeric(
            item.line.expected_quantity,
          ),
        countedQuantity:
          numeric(
            item.line.counted_quantity,
          ),
        varianceQuantity:
          numeric(
            item.line.variance_quantity,
          ),
      }));

  const activityIsLoading =
    (
      canReadSales &&
      salesTrendQuery.isLoading
    ) ||
    (
      canReadInventory &&
      (
        purchaseTrendQuery.isLoading ||
        movementTimelineQuery.isLoading
      )
    ) ||
    (
      canCountInventory &&
      stockCountVarianceQuery.isLoading
    );

  const activitySourceErrors = [
    canReadSales &&
    salesTrendQuery.isError
      ? "sales"
      : null,

    canReadInventory &&
    purchaseTrendQuery.isError
      ? "purchases"
      : null,

    canReadInventory &&
    movementTimelineQuery.isError
      ? "inventory movements"
      : null,

    canCountInventory &&
    stockCountVarianceQuery.isError
      ? "stock counts"
      : null,
  ].filter(
    (value): value is string =>
      Boolean(value),
  );

  const stock =
    summary.current_stock ?? {};

  return (
    <Page>
      <PageHeader>
        <div className="space-y-2">
          <Link
            to={PATHS.PRODUCTS.ROOT}
            className="
              -ml-2
              inline-flex
              h-8
              items-center
              gap-2
              rounded-md
              px-3
              text-sm
              font-medium
              transition-colors
              hover:bg-accent
              hover:text-accent-foreground
              focus-visible:outline-none
              focus-visible:ring-2
              focus-visible:ring-ring
            "
          >
            <ArrowLeft className="size-4" />
            Products
          </Link>

          <div>
            <PageTitle>
              {summary.product.name}
            </PageTitle>
            <PageDescription>
              Product Intelligence ·{" "}
              {summary.product.internal_sku}
            </PageDescription>
          </div>
        </div>
      </PageHeader>

      <PageContent>
        <div className="space-y-6">
          <div className="flex flex-wrap gap-2">
            <Badge
              variant={
                summary.product.is_active
                  ? "secondary"
                  : "outline"
              }
            >
              {summary.product.is_active
                ? "Active"
                : "Archived"}
            </Badge>

            {summary.product.unit?.code ? (
              <Badge variant="outline">
                Base unit:{" "}
                {summary.product.unit.code}
              </Badge>
            ) : null}

            {summary.product.track_batches ? (
              <Badge variant="outline">
                Batch tracked
              </Badge>
            ) : null}

            {summary.product.track_expiry ? (
              <Badge variant="outline">
                Expiry tracked
              </Badge>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  On hand
                </CardDescription>
                <CardTitle className="text-2xl">
                  {displayNumber(
                    stock.quantity_on_hand as
                      | string
                      | undefined,
                  )}
                </CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  Available
                </CardDescription>
                <CardTitle className="text-2xl">
                  {displayNumber(
                    stock.quantity_available as
                      | string
                      | undefined,
                  )}
                </CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  Ledger movements
                </CardDescription>
                <CardTitle className="text-2xl">
                  {summary.activity.movement_count}
                </CardTitle>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardDescription>
                  Last movement
                </CardDescription>
                <CardTitle className="text-sm">
                  {displayDate(
                    summary.activity
                      .last_movement_at,
                  )}
                </CardTitle>
              </CardHeader>
            </Card>
          </div>

          <Tabs defaultValue="overview">
            <TabsList className="flex h-auto flex-wrap justify-start">
              <TabsTrigger value="overview">
                Overview
              </TabsTrigger>

              {canViewActivity ? (
                <TabsTrigger value="activity">
                  Activity
                </TabsTrigger>
              ) : null}

              {canReadSales ? (
                <TabsTrigger value="sales">
                  Sales
                </TabsTrigger>
              ) : null}

              {canReadInventory ? (
                <>
                  <TabsTrigger value="purchases">
                    Purchases
                  </TabsTrigger>
                  <TabsTrigger value="batches">
                    Batches
                  </TabsTrigger>

                  <TabsTrigger value="movements">
                    Movements
                  </TabsTrigger>
                </>
              ) : null}

              {canViewStockHistory ? (
                <TabsTrigger value="stock-counts">
                  Stock Counts
                </TabsTrigger>
              ) : null}
            </TabsList>

            <TabsContent
              value="overview"
              className="space-y-4"
            >
              <Card>
                <CardHeader>
                  <CardTitle>
                    Product intelligence period
                  </CardTitle>
                  <CardDescription>
                    Filter authoritative price and
                    inventory-ledger evidence across the
                    Product Intelligence overview.
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="space-y-1.5">
                      <span className="text-xs font-medium text-muted-foreground">
                        From
                      </span>
                      <Input
                        type="date"
                        value={trendDateFrom}
                        onChange={(event) =>
                          setTrendDateFrom(
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
                        value={trendDateTo}
                        onChange={(event) =>
                          setTrendDateTo(
                            event.target.value,
                          )
                        }
                      />
                    </label>
                  </div>

                  <p className="mt-3 text-xs text-muted-foreground">
                    Overview graphs are not paginated.
                    Every matching persisted evidence point
                    in the selected period is represented.
                  </p>
                </CardContent>
              </Card>

              <ProductOperationalInsights
                product={summary.product}
                quantityAvailable={
                  stock.quantity_available as
                    | string
                    | undefined
                }
                sales={
                  canReadSales
                    ? (
                        salesTrendQuery.data
                          ?.items ?? []
                      )
                    : []
                }
                purchases={
                  canReadInventory
                    ? (
                        purchaseTrendQuery.data
                          ?.items ?? []
                      )
                    : []
                }
                stockCounts={
                  canCountInventory
                    ? (
                        stockCountVarianceQuery.data
                          ?.items ?? []
                      )
                    : []
                }
              />

              {canReadInventory ? (
                <ProductSupplierIntelligence
                  purchases={
                    purchaseTrendQuery.data
                      ?.items ?? []
                  }
                />
              ) : null}

              <div className="grid gap-4 xl:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>
                      Selling price history
                    </CardTitle>
                    <CardDescription>
                      Normalized to the product base
                      unit so different pack sizes are
                      comparable.
                    </CardDescription>
                  </CardHeader>

                  <CardContent>
                    {!canReadSales ? (
                      <EmptyPanel
                        title="Sales history unavailable"
                        description="You do not have permission to view sales history."
                      />
                    ) : salesTrendQuery.isLoading ? (
                      <EmptyPanel
                        title="Loading selling-price trend"
                        description="Loading complete persisted selling-price evidence."
                      />
                    ) : salesTrendQuery.isError ? (
                      <EmptyPanel
                        title="Unable to load selling-price trend"
                        description={
                          salesTrendQuery.error instanceof Error
                            ? salesTrendQuery.error.message
                            : "Selling-price trend could not be loaded."
                        }
                      />
                    ) : salesChartData.length === 0 ? (
                      <EmptyPanel
                        title="No sales-price evidence yet"
                        description="Historical transaction prices will appear after the product has been sold."
                      />
                    ) : (
                      <div className="h-72">
                        <ResponsiveContainer
                          width="100%"
                          height="100%"
                        >
                          <LineChart
                            data={salesChartData}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                            />
                            <XAxis
                              dataKey="date"
                              tickFormatter={(value) =>
                                new Date(
                                  value,
                                ).toLocaleDateString()
                              }
                            />
                            <YAxis />
                            <Tooltip
                              wrapperStyle={{
                                pointerEvents: "auto",
                              }}
                              content={({
                                active,
                                payload,
                              }) => {
                                if (
                                  !active ||
                                  !payload?.length
                                ) {
                                  return null;
                                }

                                const point =
                                  payload[0]
                                    .payload as
                                    PriceTrendChartPoint;

                                const sourcePath =
                                  priceTrendSourcePath(
                                    point,
                                  );

                                return (
                                  <div className="min-w-64 rounded-xl border bg-background p-4 text-sm shadow-lg">
                                    <p className="font-medium">
                                      {point.label}
                                    </p>

                                    <p className="mt-1 text-xs text-muted-foreground">
                                      {displayDate(
                                        point.date,
                                      )}
                                    </p>

                                    <div className="mt-3 space-y-1.5">
                                      <p>
                                        Base-unit price:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            point.value,
                                          )}
                                        </span>
                                      </p>

                                      <p>
                                        Transaction price:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            point.rawValue,
                                          )}
                                        </span>
                                        {point.uom
                                          ? ` / ${point.uom}`
                                          : ""}
                                      </p>

                                      <p>
                                        Base quantity:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            point.quantity,
                                          )}
                                        </span>
                                      </p>

                                      {point.status ? (
                                        <p>
                                          Status:{" "}
                                          <span className="font-medium">
                                            {point.status}
                                          </span>
                                        </p>
                                      ) : null}

                                      {point.refundStatus &&
                                      point.refundStatus !==
                                        "not_refunded" ? (
                                        <p>
                                          Refund:{" "}
                                          <span className="font-medium">
                                            {
                                              point.refundStatus
                                            }
                                          </span>
                                        </p>
                                      ) : null}

                                      {point.isReturned ? (
                                        <p className="font-medium text-amber-700 dark:text-amber-300">
                                          Returned sale evidence
                                        </p>
                                      ) : null}
                                    </div>

                                    {sourcePath ? (
                                      <Link
                                        to={sourcePath}
                                        className="mt-3 inline-flex h-8 items-center rounded-md border px-3 font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                                      >
                                        Open{" "}
                                        {priceTrendSourceLabel(
                                          point,
                                        )}
                                      </Link>
                                    ) : null}
                                  </div>
                                );
                              }}
                            />

                            <Line
                              type="monotone"
                              dataKey="value"
                              stroke="currentColor"
                              dot={(props) => {
                                const {
                                  cx,
                                  cy,
                                  payload,
                                } = props;

                                const point =
                                  payload as
                                    PriceTrendChartPoint;

                                const sourcePath =
                                  priceTrendSourcePath(
                                    point,
                                  );

                                return (
                                  <circle
                                    cx={cx}
                                    cy={cy}
                                    r={4}
                                    fill="currentColor"
                                    stroke="var(--background)"
                                    strokeWidth={2}
                                    className={
                                      sourcePath
                                        ? "cursor-pointer"
                                        : undefined
                                    }
                                    onClick={() => {
                                      if (
                                        sourcePath
                                      ) {
                                        navigate(
                                          sourcePath,
                                        );
                                      }
                                    }}
                                  />
                                );
                              }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {salesChartData.length > 0 ? (
                      <p className="mt-3 text-xs text-muted-foreground">
                        Hover for transaction evidence.
                        Select a chart point to open its
                        source Sale Receipt.
                      </p>
                    ) : null}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>
                      Purchase cost history
                    </CardTitle>
                    <CardDescription>
                      Posted goods-receipt cost
                      normalized to the base unit.
                    </CardDescription>
                  </CardHeader>

                  <CardContent>
                    {!canReadInventory ? (
                      <EmptyPanel
                        title="Purchase history unavailable"
                        description="You do not have permission to view inventory purchase history."
                      />
                    ) : purchaseTrendQuery.isLoading ? (
                      <EmptyPanel
                        title="Loading purchase-cost trend"
                        description="Loading complete posted Goods Receipt cost evidence."
                      />
                    ) : purchaseTrendQuery.isError ? (
                      <EmptyPanel
                        title="Unable to load purchase-cost trend"
                        description={
                          purchaseTrendQuery.error instanceof Error
                            ? purchaseTrendQuery.error.message
                            : "Purchase-cost trend could not be loaded."
                        }
                      />
                    ) : purchaseChartData.length === 0 ? (
                      <EmptyPanel
                        title="No purchase-cost evidence yet"
                        description="Posted receipt costs will appear here when available."
                      />
                    ) : (
                      <div className="h-72">
                        <ResponsiveContainer
                          width="100%"
                          height="100%"
                        >
                          <LineChart
                            data={purchaseChartData}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                            />
                            <XAxis
                              dataKey="date"
                              tickFormatter={(value) =>
                                new Date(
                                  value,
                                ).toLocaleDateString()
                              }
                            />
                            <YAxis />
                            <Tooltip
                              wrapperStyle={{
                                pointerEvents: "auto",
                              }}
                              content={({
                                active,
                                payload,
                              }) => {
                                if (
                                  !active ||
                                  !payload?.length
                                ) {
                                  return null;
                                }

                                const point =
                                  payload[0]
                                    .payload as
                                    PriceTrendChartPoint;

                                const sourcePath =
                                  priceTrendSourcePath(
                                    point,
                                  );

                                return (
                                  <div className="min-w-64 rounded-xl border bg-background p-4 text-sm shadow-lg">
                                    <p className="font-medium">
                                      {point.label}
                                    </p>

                                    <p className="mt-1 text-xs text-muted-foreground">
                                      {displayDate(
                                        point.date,
                                      )}
                                    </p>

                                    <div className="mt-3 space-y-1.5">
                                      <p>
                                        Base-unit cost:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            point.value,
                                          )}
                                        </span>
                                      </p>

                                      <p>
                                        Transaction cost:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            point.rawValue,
                                          )}
                                        </span>
                                        {point.uom
                                          ? ` / ${point.uom}`
                                          : ""}
                                      </p>

                                      <p>
                                        Base quantity:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            point.quantity,
                                          )}
                                        </span>
                                      </p>

                                      {point.supplier ? (
                                        <p>
                                          Supplier:{" "}
                                          <span className="font-medium">
                                            {point.supplier}
                                          </span>
                                        </p>
                                      ) : null}
                                    </div>

                                    {sourcePath ? (
                                      <Link
                                        to={sourcePath}
                                        className="mt-3 inline-flex h-8 items-center rounded-md border px-3 font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                                      >
                                        Open{" "}
                                        {priceTrendSourceLabel(
                                          point,
                                        )}
                                      </Link>
                                    ) : null}
                                  </div>
                                );
                              }}
                            />

                            <Line
                              type="monotone"
                              dataKey="value"
                              stroke="currentColor"
                              dot={(props) => {
                                const {
                                  cx,
                                  cy,
                                  payload,
                                } = props;

                                const point =
                                  payload as
                                    PriceTrendChartPoint;

                                const sourcePath =
                                  priceTrendSourcePath(
                                    point,
                                  );

                                return (
                                  <circle
                                    cx={cx}
                                    cy={cy}
                                    r={4}
                                    fill="currentColor"
                                    stroke="var(--background)"
                                    strokeWidth={2}
                                    className={
                                      sourcePath
                                        ? "cursor-pointer"
                                        : undefined
                                    }
                                    onClick={() => {
                                      if (
                                        sourcePath
                                      ) {
                                        navigate(
                                          sourcePath,
                                        );
                                      }
                                    }}
                                  />
                                );
                              }}
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    {purchaseChartData.length > 0 ? (
                      <p className="mt-3 text-xs text-muted-foreground">
                        Hover for persisted receipt
                        evidence. Select a chart point to
                        open its source Goods Receipt.
                      </p>
                    ) : null}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>
                    Inventory movement timeline
                  </CardTitle>

                  <CardDescription>
                    Signed base-unit inventory ledger
                    movements. Positive quantities move
                    stock in; negative quantities move
                    stock out.
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  {!canReadInventory ? (
                    <EmptyPanel
                      title="Movement timeline unavailable"
                      description="You do not have permission to view inventory movements."
                    />
                  ) : movementTimelineQuery.isLoading ? (
                    <EmptyPanel
                      title="Loading movement timeline"
                      description="Loading complete persisted inventory-ledger evidence."
                    />
                  ) : movementTimelineQuery.isError ? (
                    <EmptyPanel
                      title="Unable to load movement timeline"
                      description={
                        movementTimelineQuery.error instanceof Error
                          ? movementTimelineQuery.error.message
                          : "Inventory movement timeline could not be loaded."
                      }
                    />
                  ) : movementChartData.length === 0 ? (
                    <EmptyPanel
                      title="No movement evidence"
                      description="No inventory ledger movements were found for the selected period."
                    />
                  ) : (
                    <>
                      <div className="h-80">
                        <ResponsiveContainer
                          width="100%"
                          height="100%"
                        >
                          <BarChart
                            data={movementChartData}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                            />

                            <XAxis
                              dataKey="created_at"
                              tickFormatter={(value) =>
                                new Date(
                                  String(value),
                                ).toLocaleDateString()
                              }
                            />

                            <YAxis />

                            <ReferenceLine y={0} />

                            <Tooltip
                              wrapperStyle={{
                                pointerEvents: "auto",
                              }}
                              content={({
                                active,
                                payload,
                              }) => {
                                if (
                                  !active ||
                                  !payload?.length
                                ) {
                                  return null;
                                }

                                const item =
                                  payload[0]
                                    .payload as
                                    ProductMovementHistoryItem & {
                                      numericQuantity:
                                        number | null;
                                    };

                                const sourcePath =
                                  movementSourcePath(
                                    item,
                                  );

                                const sourceLabel =
                                  movementSourceLabel(
                                    item,
                                  );

                                const quantity =
                                  Number(
                                    item.quantity,
                                  );

                                const direction =
                                  quantity > 0
                                    ? "Stock in"
                                    : quantity < 0
                                      ? "Stock out"
                                      : "Neutral";

                                return (
                                  <div className="min-w-64 rounded-xl border bg-background p-4 text-sm shadow-lg">
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="font-medium">
                                        {
                                          item.movement_type
                                        }
                                      </span>

                                      <Badge variant="outline">
                                        {direction}
                                      </Badge>
                                    </div>

                                    <p className="mt-1 text-xs text-muted-foreground">
                                      {displayDate(
                                        item.created_at,
                                      )}
                                    </p>

                                    <div className="mt-3 space-y-1.5">
                                      <p>
                                        Quantity:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            item.quantity,
                                          )}
                                        </span>
                                      </p>

                                      {item.warehouse?.name ? (
                                        <p>
                                          Warehouse:{" "}
                                          <span className="font-medium">
                                            {
                                              item
                                                .warehouse
                                                .name
                                            }
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.batch?.batch_number ? (
                                        <p>
                                          Batch:{" "}
                                          <span className="font-medium">
                                            {
                                              item.batch
                                                .batch_number
                                            }
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.unit_cost != null ? (
                                        <p>
                                          Persisted unit cost:{" "}
                                          <span className="font-medium">
                                            {displayNumber(
                                              item.unit_cost,
                                            )}
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.unit_price != null ? (
                                        <p>
                                          Persisted unit price:{" "}
                                          <span className="font-medium">
                                            {displayNumber(
                                              item.unit_price,
                                            )}
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.performed_by ? (
                                        <p>
                                          Performed by:{" "}
                                          <span className="font-medium">
                                            {item.performed_by.name ??
                                              item.performed_by.username ??
                                              "Unknown"}
                                          </span>
                                        </p>
                                      ) : null}
                                    </div>

                                    {sourcePath &&
                                    sourceLabel ? (
                                      <Link
                                        to={sourcePath}
                                        className="mt-3 inline-flex h-8 items-center rounded-md border px-3 font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                                      >
                                        Open{" "}
                                        {sourceLabel}
                                      </Link>
                                    ) : item.reference?.type ? (
                                      <p className="mt-3 text-xs text-muted-foreground">
                                        Source evidence:{" "}
                                        {
                                          item.reference
                                            .type
                                        }
                                      </p>
                                    ) : null}
                                  </div>
                                );
                              }}
                            />

                            <Bar
                              dataKey="numericQuantity"
                              fill="currentColor"
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      <p className="mt-3 text-xs text-muted-foreground">
                        This graph shows persisted signed
                        movements, not a reconstructed
                        historical stock balance. Hover a
                        movement for its ledger evidence and
                        source document where a canonical
                        route exists.
                      </p>
                    </>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>
                    Stock count & variance intelligence
                  </CardTitle>

                  <CardDescription>
                    Compare system quantity with physical
                    counts and follow each variance through
                    its Stock Count lifecycle and resulting
                    inventory adjustment.
                  </CardDescription>
                </CardHeader>

                <CardContent>
                  {!canCountInventory ? (
                    <EmptyPanel
                      title="Stock count intelligence unavailable"
                      description="You do not have permission to view Stock Count evidence."
                    />
                  ) : stockCountVarianceQuery.isLoading ? (
                    <EmptyPanel
                      title="Loading stock count intelligence"
                      description="Loading complete physical-count and variance evidence."
                    />
                  ) : stockCountVarianceQuery.isError ? (
                    <EmptyPanel
                      title="Unable to load stock count intelligence"
                      description={
                        stockCountVarianceQuery.error instanceof Error
                          ? stockCountVarianceQuery.error.message
                          : "Stock Count variance evidence could not be loaded."
                      }
                    />
                  ) : stockCountVarianceData.length === 0 ? (
                    <EmptyPanel
                      title="No stock count evidence"
                      description="No Stock Count lines were found for this product in the selected period."
                    />
                  ) : (
                    <>
                      <div className="h-80">
                        <ResponsiveContainer
                          width="100%"
                          height="100%"
                        >
                          <BarChart
                            data={stockCountVarianceData}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                            />

                            <XAxis
                              dataKey="stock_count.count_number"
                            />

                            <YAxis />

                            <ReferenceLine y={0} />

                            <Tooltip
                              wrapperStyle={{
                                pointerEvents: "auto",
                              }}
                              content={({
                                active,
                                payload,
                              }) => {
                                if (
                                  !active ||
                                  !payload?.length
                                ) {
                                  return null;
                                }

                                const item =
                                  payload[0]
                                    .payload as
                                    ProductStockCountHistoryItem & {
                                      occurredAt:
                                        string | null;
                                      expectedQuantity:
                                        number | null;
                                      countedQuantity:
                                        number | null;
                                      varianceQuantity:
                                        number | null;
                                    };

                                const adjustmentPath =
                                  stockAdjustmentPath(
                                    item,
                                  );

                                return (
                                  <div className="min-w-72 rounded-xl border bg-background p-4 text-sm shadow-lg">
                                    <div className="flex flex-wrap items-center gap-2">
                                      <span className="font-medium">
                                        {
                                          item.stock_count
                                            .count_number
                                        }
                                      </span>

                                      <Badge variant="outline">
                                        {stockCountLifecycleLabel(
                                          item.stock_count
                                            .lifecycle,
                                        )}
                                      </Badge>
                                    </div>

                                    <p className="mt-1 text-xs text-muted-foreground">
                                      {displayDate(
                                        item.occurredAt,
                                      )}
                                      {" · "}
                                      {
                                        item.warehouse
                                          .name
                                      }
                                    </p>

                                    <div className="mt-3 space-y-1.5">
                                      {item.line
                                        .expected_quantity !==
                                      undefined ? (
                                        <p>
                                          System quantity:{" "}
                                          <span className="font-medium">
                                            {displayNumber(
                                              item.line
                                                .expected_quantity,
                                            )}
                                          </span>
                                        </p>
                                      ) : (
                                        <p className="text-muted-foreground">
                                          System quantity hidden
                                          during blind counting
                                        </p>
                                      )}

                                      <p>
                                        Counted quantity:{" "}
                                        <span className="font-medium">
                                          {displayNumber(
                                            item.line
                                              .counted_quantity,
                                          )}
                                        </span>
                                      </p>

                                      {item.line
                                        .variance_quantity !==
                                      undefined ? (
                                        <p>
                                          Variance:{" "}
                                          <span className="font-medium">
                                            {displayNumber(
                                              item.line
                                                .variance_quantity,
                                            )}
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.line
                                        .counted_unit_quantity !=
                                        null ? (
                                        <p>
                                          Physical entry:{" "}
                                          <span className="font-medium">
                                            {displayNumber(
                                              item.line
                                                .counted_unit_quantity,
                                            )}{" "}
                                            {item.line
                                              .counted_unit_code ??
                                              item.line
                                                .counted_unit_name ??
                                              ""}
                                          </span>

                                          {item.line
                                            .counted_conversion_factor_to_base !=
                                          null ? (
                                            <>
                                              {" · "}
                                              ×{" "}
                                              {displayNumber(
                                                item.line
                                                  .counted_conversion_factor_to_base,
                                              )}
                                              {" → "}
                                              {displayNumber(
                                                item.line
                                                  .counted_quantity,
                                              )}{" "}
                                              base units
                                            </>
                                          ) : null}
                                        </p>
                                      ) : null}

                                      {item.line.batch
                                        ?.batch_number ? (
                                        <p>
                                          Batch:{" "}
                                          <span className="font-medium">
                                            {
                                              item.line
                                                .batch
                                                .batch_number
                                            }
                                          </span>
                                        </p>
                                      ) : item.line
                                          .observed_batch_number ? (
                                        <p>
                                          Observed batch:{" "}
                                          <span className="font-medium">
                                            {
                                              item.line
                                                .observed_batch_number
                                            }
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.line
                                        .counted_by ? (
                                        <p>
                                          Counted by:{" "}
                                          <span className="font-medium">
                                            {item.line
                                              .counted_by
                                              .name ??
                                              item.line
                                                .counted_by
                                                .username ??
                                              "Unknown"}
                                          </span>
                                        </p>
                                      ) : null}

                                      {item.adjustment ? (
                                        <p>
                                          Adjustment:{" "}
                                          <span className="font-medium">
                                            {
                                              item.adjustment
                                                .adjustment_number
                                            }
                                          </span>
                                          {" · "}
                                          {displayNumber(
                                            item.adjustment
                                              .quantity_delta,
                                          )}
                                        </p>
                                      ) : null}
                                    </div>

                                    <div className="mt-3 flex flex-wrap gap-2">
                                      <Link
                                        to={stockCountPath(
                                          item,
                                        )}
                                        className="inline-flex h-8 items-center rounded-md border px-3 font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                                      >
                                        Open Stock Count
                                      </Link>

                                      {adjustmentPath ? (
                                        <Link
                                          to={
                                            adjustmentPath
                                          }
                                          className="inline-flex h-8 items-center rounded-md border px-3 font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                                        >
                                          Open Adjustment
                                        </Link>
                                      ) : null}
                                    </div>
                                  </div>
                                );
                              }}
                            />

                            <Bar
                              dataKey="expectedQuantity"
                              name="System quantity"
                              fill="currentColor"
                              fillOpacity={0.3}
                            />

                            <Bar
                              dataKey="countedQuantity"
                              name="Counted quantity"
                              fill="currentColor"
                              fillOpacity={0.65}
                            />

                            <Bar
                              dataKey="varianceQuantity"
                              name="Variance"
                              fill="currentColor"
                              fillOpacity={1}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted-foreground">
                        <span>
                          System quantity = persisted expected
                          quantity at count time
                        </span>

                        <span>
                          Counted quantity = canonical base
                          quantity from the physical count
                        </span>

                        <span>
                          Variance = counted minus expected
                        </span>
                      </div>

                      <p className="mt-2 text-xs text-muted-foreground">
                        Open blind counts deliberately do not
                        expose system or variance quantities
                        until the Stock Count contract permits
                        them.
                      </p>
                    </>
                  )}
                </CardContent>
              </Card>

              {!summary.capabilities.profitability ? (
                <Card>
                  <CardHeader>
                    <CardTitle>
                      Profitability
                    </CardTitle>
                    <CardDescription>
                      Not displayed yet.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground">
                    Historical COGS has not yet been
                    validated as reliable enough for
                    margin and markup analysis.
                  </CardContent>
                </Card>
              ) : null}
            </TabsContent>

            {canViewActivity ? (
              <TabsContent
                value="activity"
                className="space-y-4"
              >
                <Card>
                  <CardHeader>
                    <CardTitle>
                      Activity period
                    </CardTitle>

                    <CardDescription>
                      Filter the complete authorized
                      Product Activity evidence trail.
                    </CardDescription>
                  </CardHeader>

                  <CardContent>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="space-y-1.5">
                        <span className="text-xs font-medium text-muted-foreground">
                          From
                        </span>

                        <Input
                          type="date"
                          value={trendDateFrom}
                          onChange={(event) =>
                            setTrendDateFrom(
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
                          value={trendDateTo}
                          onChange={(event) =>
                            setTrendDateTo(
                              event.target.value,
                            )
                          }
                        />
                      </label>
                    </div>

                    <p className="mt-3 text-xs text-muted-foreground">
                      This uses the same non-paginated
                      evidence feeds as the Product
                      Intelligence overview.
                    </p>
                  </CardContent>
                </Card>

                <ProductUnifiedActivityTimeline
                  sales={
                    canReadSales
                      ? (
                          salesTrendQuery.data
                            ?.items ?? []
                        )
                      : []
                  }
                  purchases={
                    canReadInventory
                      ? (
                          purchaseTrendQuery.data
                            ?.items ?? []
                        )
                      : []
                  }
                  movements={
                    canReadInventory
                      ? (
                          movementTimelineQuery.data
                            ?.items ?? []
                        )
                      : []
                  }
                  stockCounts={
                    canCountInventory
                      ? (
                          stockCountVarianceQuery.data
                            ?.items ?? []
                        )
                      : []
                  }
                  isLoading={
                    activityIsLoading
                  }
                  sourceErrors={
                    activitySourceErrors
                  }
                />
              </TabsContent>
            ) : null}

            <TabsContent
                value="sales"
                className="space-y-4"
              >
                <ProductSalesHistoryPanel
                  productId={productId}
                  enabled={canReadSales}
                />
              </TabsContent>

              <TabsContent
                value="purchases"
                className="space-y-4"
              >
                <ProductPurchaseHistoryPanel
                  productId={productId}
                  enabled={canReadInventory}
                />
              </TabsContent>

              <TabsContent
                value="batches"
                className="space-y-4"
              >
                <ProductBatchHistoryPanel
                  productId={productId}
                  enabled={canReadInventory}
                />
              </TabsContent>

              <TabsContent
                value="movements"
                className="space-y-4"
              >
                <ProductMovementHistoryPanel
                  productId={productId}
                  enabled={canReadInventory}
                />
              </TabsContent>

              {canViewStockHistory ? (
                <TabsContent
                  value="stock-counts"
                  className="space-y-4"
                >
                  <ProductStockCountHistoryPanel
                    productId={productId}
                    enabled={canViewStockHistory}
                    canViewAdjustment={
                      canAdjustInventory
                    }
                  />
                </TabsContent>
              ) : null}
              </Tabs>
        </div>
      </PageContent>
    </Page>
  );
}

export default ProductIntelligencePage;
