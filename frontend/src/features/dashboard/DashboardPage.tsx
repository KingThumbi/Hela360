import {
  AlertTriangle,
  Banknote,
  Boxes,
  CalendarDays,
  CreditCard,
  PackageCheck,
  PackageX,
  ReceiptText,
  RefreshCcw,
  ShoppingBasket,
  TrendingUp,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
import { Link } from "react-router-dom";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  Page,
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
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  useDashboardOverview,
} from "@/hooks/queries/dashboard";
import { useAuthorization } from "@/hooks/useAuthorization";
import { PATHS } from "@/routes/routes";
import type {
  DashboardOverview,
  DashboardRecentSale,
  DashboardSalesSummary,
} from "@/services/dashboard";


function todayIsoDate(): string {
  const now = new Date();

  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}


function money(
  value: string,
  currency: string,
): string {
  const numeric = Number(value);

  if (!Number.isFinite(numeric)) {
    return `${currency} ${value}`;
  }

  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(numeric);
  } catch {
    return `${currency} ${numeric.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }
}


function numberLabel(value: number): string {
  return value.toLocaleString();
}


function dateTimeLabel(
  value: string,
  timezone: string,
): string {
  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  try {
    return parsed.toLocaleString(undefined, {
      timeZone: timezone,
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return parsed.toLocaleString();
  }
}


function statusLabel(value: string): string {
  return value
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase(),
    );
}


function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "The dashboard could not be loaded.";
}


export function DashboardPage() {
  const { can } = useAuthorization();

  const canViewManagementOverview =
    can("reports.view");

  const canCreateSales =
    can("sales.create");

  const canViewSales =
    can("sales.read");

  const canViewInventory =
    can("inventory.read");

  const [
    operationalDate,
    setOperationalDate,
  ] = useState(todayIsoDate);

  const dashboardQuery = useDashboardOverview({
    params: {
      operational_date: operationalDate,
    },
    enabled: canViewManagementOverview,
  });

  const dashboard = dashboardQuery.data;

  const hasWorkspace =
    canCreateSales ||
    canViewSales ||
    canViewInventory;

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Dashboard</PageTitle>
          <PageDescription>
            Your workspace for today's work and business activity.
          </PageDescription>
        </div>

        {canViewManagementOverview ? (
          <Button
            type="button"
            variant="outline"
            onClick={() =>
              void dashboardQuery.refetch()
            }
            disabled={dashboardQuery.isFetching}
          >
            <RefreshCcw
              className={
                dashboardQuery.isFetching
                  ? "size-4 animate-spin"
                  : "size-4"
              }
            />
            Refresh
          </Button>
        ) : null}
      </PageHeader>

      <PageContent>
        {hasWorkspace ? (
          <PageSection>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">
                  Your workspace
                </CardTitle>
              </CardHeader>

              <CardContent>
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {canCreateSales ? (
                    <WorkspaceCard
                      title="Start selling"
                      description="Serve customers and record a new sale."
                      icon={ShoppingBasket}
                      href={PATHS.SALES.POS}
                    />
                  ) : null}

                  {canViewSales ? (
                    <WorkspaceCard
                      title="View sales"
                      description="Review recent sales and transactions."
                      icon={ReceiptText}
                      href={PATHS.SALES.HISTORY}
                    />
                  ) : null}

                  {canViewInventory ? (
                    <WorkspaceCard
                      title="View stock"
                      description="Check products and available stock."
                      icon={Boxes}
                      href={PATHS.INVENTORY.ROOT}
                    />
                  ) : null}
                </div>
              </CardContent>
            </Card>
          </PageSection>
        ) : null}

        {canViewManagementOverview ? (
          <>
            <PageSection>
              <PageToolbar>
                <div className="flex w-full flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      Business overview
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Choose a day to review sales and business activity.
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <CalendarDays className="size-4 text-muted-foreground" />

                    <Input
                      type="date"
                      value={operationalDate}
                      onChange={(event) =>
                        setOperationalDate(
                          event.target.value,
                        )
                      }
                      aria-label="Choose dashboard date"
                      className="w-[170px]"
                    />
                  </div>
                </div>
              </PageToolbar>
            </PageSection>

            {dashboardQuery.isPending ? (
              <LoadingState />
            ) : dashboardQuery.isError ? (
              <ErrorState
                title="We couldn't load your business overview"
                description={errorMessage(
                  dashboardQuery.error,
                )}
                retryLabel="Try again"
                onRetry={() =>
                  void dashboardQuery.refetch()
                }
              />
            ) : dashboard ? (
              <DashboardContent
                dashboard={dashboard}
              />
            ) : (
              <EmptyState
                title="No activity to show"
                description="Business activity for this day will appear here."
              />
            )}
          </>
        ) : null}
      </PageContent>
    </Page>
  );
}


function DashboardContent({
  dashboard,
}: {
  dashboard: DashboardOverview;
}) {
  const {
    scope,
    sales,
    payments,
    inventory,
    recent_sales: recentSales,
  } = dashboard;

  return (
    <>
      <PageSection>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            title="Net Sales"
            value={money(
              sales.today.net_sales,
              scope.currency,
            )}
            description="Today's net sales"
            icon={TrendingUp}
          />

          <MetricCard
            title="Transactions"
            value={numberLabel(
              sales.today.transactions,
            )}
            description="Completed sales today"
            icon={ReceiptText}
          />

          <MetricCard
            title="Average Basket"
            value={money(
              sales.today.average_basket,
              scope.currency,
            )}
            description="Average transaction value"
            icon={ShoppingBasket}
          />

          <MetricCard
            title="Refunds"
            value={money(
              sales.today.refunds,
              scope.currency,
            )}
            description="Refunded value today"
            icon={Banknote}
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-4 xl:grid-cols-2">
          <SalesPerformanceCard
            today={sales.today}
            monthToDate={sales.month_to_date}
            currency={scope.currency}
          />

          <PaymentMixCard
            payments={payments.today}
            currency={scope.currency}
          />
        </div>
      </PageSection>

      <PageSection>
        <InventoryHealthCard
          inventory={inventory}
        />
      </PageSection>

      <PageSection>
        <RecentSalesCard
          sales={recentSales}
          currency={scope.currency}
          timezone={scope.timezone}
        />
      </PageSection>
    </>
  );
}

function WorkspaceCard({
  title,
  description,
  icon: Icon,
  href,
}: {
  title: string;
  description: string;
  icon: MetricIcon;
  href: string;
}) {
  return (
    <Link
      to={href}
      className="group flex min-h-28 items-start gap-3 rounded-lg border bg-background p-4 transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted transition-colors group-hover:bg-background">
        <Icon className="size-4" />
      </div>

      <div className="min-w-0">
        <p className="font-medium">
          {title}
        </p>

        <p className="mt-1 text-sm leading-5 text-muted-foreground">
          {description}
        </p>
      </div>
    </Link>
  );
}


type MetricIcon = typeof TrendingUp;


function MetricCard({
  title,
  value,
  description,
  icon: Icon,
}: {
  title: string;
  value: string;
  description: string;
  icon: MetricIcon;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {title}
        </CardTitle>

        <Icon className="size-4 text-muted-foreground" />
      </CardHeader>

      <CardContent>
        <div className="text-2xl font-semibold tracking-tight">
          {value}
        </div>

        <p className="mt-1 text-xs text-muted-foreground">
          {description}
        </p>
      </CardContent>
    </Card>
  );
}


function SalesPerformanceCard({
  today,
  monthToDate,
  currency,
}: {
  today: DashboardSalesSummary;
  monthToDate: DashboardSalesSummary;
  currency: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Sales Performance
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        <SalesPeriod
          title="Today"
          summary={today}
          currency={currency}
        />

        <div className="border-t" />

        <SalesPeriod
          title="Month to date"
          summary={monthToDate}
          currency={currency}
        />
      </CardContent>
    </Card>
  );
}


function SalesPeriod({
  title,
  summary,
  currency,
}: {
  title: string;
  summary: DashboardSalesSummary;
  currency: string;
}) {
  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm font-medium">
          {title}
        </p>

        <p className="text-sm font-semibold">
          {money(summary.net_sales, currency)}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm sm:grid-cols-3">
        <SummaryValue
          label="Gross sales"
          value={money(
            summary.gross_sales,
            currency,
          )}
        />

        <SummaryValue
          label="Discounts"
          value={money(
            summary.discounts,
            currency,
          )}
        />

        <SummaryValue
          label="Refunds"
          value={money(
            summary.refunds,
            currency,
          )}
        />

        <SummaryValue
          label="Transactions"
          value={numberLabel(
            summary.transactions,
          )}
        />

        <SummaryValue
          label="Paid"
          value={money(
            summary.paid_amount,
            currency,
          )}
        />

        <SummaryValue
          label="Balance due"
          value={money(
            summary.balance_due,
            currency,
          )}
        />
      </div>
    </div>
  );
}


function SummaryValue({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 font-medium">
        {value}
      </p>
    </div>
  );
}


function PaymentMixCard({
  payments,
  currency,
}: {
  payments: DashboardOverview["payments"]["today"];
  currency: string;
}) {
  const total = useMemo(
    () =>
      payments.reduce(
        (sum, payment) =>
          sum + Number(payment.amount || 0),
        0,
      ),
    [payments],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Payment Mix
        </CardTitle>
      </CardHeader>

      <CardContent>
        {payments.length === 0 ? (
          <div className="py-8 text-center text-sm text-muted-foreground">
            No payments recorded for this date.
          </div>
        ) : (
          <div className="space-y-4">
            {payments.map((payment) => {
              const amount = Number(
                payment.amount,
              );

              const percentage =
                total > 0 &&
                Number.isFinite(amount)
                  ? (amount / total) * 100
                  : 0;

              return (
                <div
                  key={payment.payment_method_id}
                  className="space-y-2"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex min-w-0 items-center gap-3">
                      <div className="flex size-9 shrink-0 items-center justify-center rounded-md border">
                        <CreditCard className="size-4 text-muted-foreground" />
                      </div>

                      <div className="min-w-0">
                        <p className="truncate text-sm font-medium">
                          {payment.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {numberLabel(
                            payment.transaction_count,
                          )}{" "}
                          transaction
                          {payment.transaction_count === 1
                            ? ""
                            : "s"}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {money(
                          payment.amount,
                          currency,
                        )}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {percentage.toLocaleString(
                          undefined,
                          {
                            maximumFractionDigits: 1,
                          },
                        )}
                        %
                      </p>
                    </div>
                  </div>

                  <div className="h-2 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-[width]"
                      style={{
                        width: `${Math.min(
                          100,
                          Math.max(0, percentage),
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}


function InventoryHealthCard({
  inventory,
}: {
  inventory: DashboardOverview["inventory"];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Inventory Health
        </CardTitle>
      </CardHeader>

      <CardContent>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <InventoryMetric
            title="Stock records"
            value={inventory.stock_records}
            icon={Boxes}
          />

          <InventoryMetric
            title="Low stock"
            value={inventory.low_stock}
            icon={AlertTriangle}
          />

          <InventoryMetric
            title="Out of stock"
            value={inventory.out_of_stock}
            icon={PackageX}
          />

          <InventoryMetric
            title="Expiring soon"
            value={inventory.expiring_soon}
            icon={AlertTriangle}
          />

          <InventoryMetric
            title="Expired"
            value={inventory.expired}
            icon={PackageX}
          />
        </div>
      </CardContent>
    </Card>
  );
}


function InventoryMetric({
  title,
  value,
  icon: Icon,
}: {
  title: string;
  value: number;
  icon: MetricIcon;
}) {
  return (
    <div className="rounded-lg border p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          {title}
        </p>
        <Icon className="size-4 text-muted-foreground" />
      </div>

      <p className="mt-3 text-2xl font-semibold tracking-tight">
        {numberLabel(value)}
      </p>
    </div>
  );
}


function RecentSalesCard({
  sales,
  currency,
  timezone,
}: {
  sales: DashboardRecentSale[];
  currency: string;
  timezone: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Recent Sales
        </CardTitle>
      </CardHeader>

      <CardContent>
        {sales.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 text-center">
            <PackageCheck className="mb-3 size-8 text-muted-foreground" />
            <p className="text-sm font-medium">
              No recent sales
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Sales will appear here after transactions are recorded.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-3 pr-4 font-medium">
                    Sale
                  </th>
                  <th className="pb-3 pr-4 font-medium">
                    Date
                  </th>
                  <th className="pb-3 pr-4 font-medium">
                    Status
                  </th>
                  <th className="pb-3 pr-4 text-right font-medium">
                    Paid
                  </th>
                  <th className="pb-3 text-right font-medium">
                    Total
                  </th>
                </tr>
              </thead>

              <tbody>
                {sales.map((sale) => (
                  <RecentSaleRow
                    key={sale.id}
                    sale={sale}
                    currency={currency}
                    timezone={timezone}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}


function RecentSaleRow({
  sale,
  currency,
  timezone,
}: {
  sale: DashboardRecentSale;
  currency: string;
  timezone: string;
}) {
  return (
    <tr className="border-b last:border-0">
      <td className="py-3 pr-4 font-medium">
        {sale.sale_number}
      </td>

      <td className="whitespace-nowrap py-3 pr-4 text-muted-foreground">
        {dateTimeLabel(
          sale.sale_date,
          timezone,
        )}
      </td>

      <td className="py-3 pr-4">
        <Badge variant="outline">
          {statusLabel(sale.status)}
        </Badge>
      </td>

      <td className="whitespace-nowrap py-3 pr-4 text-right">
        {money(
          sale.paid_amount,
          currency,
        )}
      </td>

      <td className="whitespace-nowrap py-3 text-right font-medium">
        {money(
          sale.total_amount,
          currency,
        )}
      </td>
    </tr>
  );
}
