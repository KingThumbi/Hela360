import { Activity } from "lucide-react";
import { Link } from "react-router-dom";

import { useAuthorization } from "@/hooks/useAuthorization";
import {
  useProductHistory,
  useProductPurchaseHistory,
  useProductSalesHistory,
} from "@/hooks/queries/products";
import { PATHS } from "@/routes/routes";
import type { Product } from "@/types/entities";

function formatNumber(
  value: string | null | undefined,
) {
  if (value == null || value === "") {
    return "—";
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return value;
  }

  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 6,
  }).format(parsed);
}

function formatDate(
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

function Metric({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>

      <p className="mt-1 font-semibold">
        {value}
      </p>

      {hint ? (
        <p className="mt-1 text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export function ProductIntelligencePreview({
  product,
}: {
  product: Product;
}) {
  const authorization = useAuthorization();

  const canReadSales =
    authorization.can("sales.read");

  const canReadInventory =
    authorization.can("inventory.read");

  const summaryQuery =
    useProductHistory(product.id);

  const salesQuery =
    useProductSalesHistory(
      product.id,
      {
        page: 1,
        per_page: 1,
      },
      {
        enabled: canReadSales,
      },
    );

  const purchaseQuery =
    useProductPurchaseHistory(
      product.id,
      {
        page: 1,
        per_page: 1,
      },
      {
        enabled: canReadInventory,
      },
    );

  if (summaryQuery.isLoading) {
    return (
      <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
        Loading Product Intelligence…
      </div>
    );
  }

  if (
    summaryQuery.isError ||
    !summaryQuery.data
  ) {
    return (
      <div className="rounded-lg border border-destructive/30 p-4 text-sm">
        Product Intelligence could not be loaded.
      </div>
    );
  }

  const summary = summaryQuery.data;

  const latestSale =
    salesQuery.data?.items?.[0] ?? null;

  const latestPurchase =
    purchaseQuery.data?.items?.[0] ?? null;

  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <Metric
          label="On hand"
          value={formatNumber(
            summary.current_stock
              .quantity_on_hand,
          )}
        />

        <Metric
          label="Last movement"
          value={formatDate(
            summary.activity
              .last_movement_at,
          )}
          hint={`${summary.activity.movement_count} ledger movement${
            summary.activity.movement_count === 1
              ? ""
              : "s"
          }`}
        />

        <Metric
          label="Latest selling price"
          value={
            canReadSales
              ? formatNumber(
                  latestSale
                    ?.normalized_base_unit_price,
                )
              : "Restricted"
          }
          hint={
            latestSale
              ? `Base-unit price · ${latestSale.sale.sale_number}`
              : canReadSales
                ? "No sales evidence yet"
                : "Requires sales.read"
          }
        />

        <Metric
          label="Latest purchase cost"
          value={
            canReadInventory
              ? formatNumber(
                  latestPurchase
                    ?.base_unit_cost,
                )
              : "Restricted"
          }
          hint={
            latestPurchase
              ? `Base-unit cost · ${latestPurchase.receipt.receipt_number}`
              : canReadInventory
                ? "No posted receipt evidence yet"
                : "Requires inventory.read"
          }
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          Historical transaction evidence is kept
          separate from current catalogue pricing.
        </p>

        <Link
          to={PATHS.PRODUCTS.detail(
            product.id,
          )}
          className="
            inline-flex
            h-8
            items-center
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
          "
        >
          <Activity className="size-4" />
          Open Product Intelligence
        </Link>
      </div>
    </div>
  );
}

export default ProductIntelligencePreview;
