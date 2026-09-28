import {
  ArrowLeft,
} from "lucide-react";
import {
  Link,
  useParams,
} from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
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
  useProductPurchaseHistory,
  useProductSalesHistory,
} from "@/hooks/queries/products";

import { PATHS } from "@/routes/routes";

import type {
  ProductPurchaseHistoryItem,
  ProductSalesHistoryItem,
} from "@/types/responses/product-history";

import {
  ProductMovementHistoryPanel,
  ProductPurchaseHistoryPanel,
  ProductSalesHistoryPanel,
  ProductStockCountHistoryPanel,
} from "../components/ProductHistoryPanels";

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

  const salesQuery =
    useProductSalesHistory(
      productId,
      {
        page: 1,
        per_page: 50,
      },
      {
        enabled: canReadSales,
      },
    );

  const purchaseQuery =
    useProductPurchaseHistory(
      productId,
      {
        page: 1,
        per_page: 50,
      },
      {
        enabled: canReadInventory,
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

  const sales: ProductSalesHistoryItem[] =
    salesQuery.data?.items ?? [];

  const purchases: ProductPurchaseHistoryItem[] =
    purchaseQuery.data?.items ?? [];



  const salesChartData = [...sales]
    .filter(
      (item) =>
        item.normalized_base_unit_price != null &&
        item.sale.sale_date,
    )
    .reverse()
    .map((item) => ({
      id: item.sale_item_id,
      date: item.sale.sale_date,
      label: item.sale.sale_number,
      value: numeric(
        item.normalized_base_unit_price,
      ),
      rawPrice: item.unit_price,
      uom: item.uom.code,
    }));

  const purchaseChartData = [...purchases]
    .filter(
      (item) =>
        item.base_unit_cost != null &&
        item.receipt.posted_at,
    )
    .reverse()
    .map((item) => ({
      id: item.receipt_item_id,
      date: item.receipt.posted_at,
      label: item.receipt.receipt_number,
      value: numeric(item.base_unit_cost),
      rawCost: item.unit_cost,
      uom: item.uom.code,
    }));

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
                              formatter={(
                                value,
                              ) => [
                                displayNumber(
                                  value as number,
                                ),
                                "Base-unit selling price",
                              ]}
                              labelFormatter={(
                                value,
                              ) =>
                                displayDate(
                                  String(value),
                                )
                              }
                            />
                            <Line
                              type="monotone"
                              dataKey="value"
                              stroke="currentColor"
                              dot
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}
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
                              formatter={(
                                value,
                              ) => [
                                displayNumber(
                                  value as number,
                                ),
                                "Base-unit purchase cost",
                              ]}
                              labelFormatter={(
                                value,
                              ) =>
                                displayDate(
                                  String(value),
                                )
                              }
                            />
                            <Line
                              type="monotone"
                              dataKey="value"
                              stroke="currentColor"
                              dot
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

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
