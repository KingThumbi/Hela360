import {
  useMemo,
  useState,
} from "react";

import {
  useProductUnits,
} from "@/hooks/queries/products";
import type {
  ProductUnit,
} from "@/types/entities";

function numericValue(
  value: string | number | null | undefined,
): number {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return 0;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed
    : Number.NaN;
}

function displayQuantity(value: number): string {
  if (!Number.isFinite(value)) {
    return "0";
  }

  return value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 6,
    },
  );
}

function stockCountUnitLabel(
  productUnit: ProductUnit,
): string {
  const unitName =
    productUnit.unit?.name ??
    productUnit.unit?.code ??
    "Unit";

  const factor = numericValue(
    productUnit.conversion_factor_to_base,
  );

  if (
    Number.isFinite(factor) &&
    factor !== 1
  ) {
    return `${unitName} · ×${displayQuantity(factor)}`;
  }

  if (productUnit.is_base) {
    return `${unitName} · base`;
  }

  return unitName;
}

interface StockCountUnitSelectorProps {
  productId: string;
  value: string;
  quantityValue: string;
  onChange: (productUnitId: string) => void;
  disabled?: boolean;
}

export function StockCountUnitSelector({
  productId,
  value,
  quantityValue,
  onChange,
  disabled = false,
}: StockCountUnitSelectorProps) {
  const [
    activated,
    setActivated,
  ] = useState(Boolean(value));

  const productUnitsQuery =
    useProductUnits(
      productId,
      {
        enabled:
          activated ||
          Boolean(value),
      },
    );

  const activeUnits = useMemo(
    () =>
      (productUnitsQuery.data ?? []).filter(
        (productUnit) =>
          productUnit.is_active,
      ),
    [productUnitsQuery.data],
  );

  const selectedUnit =
    activeUnits.find(
      (productUnit) =>
        productUnit.id === value,
    ) ?? null;

  const factor = selectedUnit
    ? numericValue(
        selectedUnit.conversion_factor_to_base,
      )
    : 1;

  const enteredQuantity =
    numericValue(quantityValue);

  const baseQuantity =
    enteredQuantity * factor;

  const selectedUnitName =
    selectedUnit?.unit?.name ??
    selectedUnit?.unit?.code ??
    "unit";

  return (
    <div className="min-w-[180px] space-y-1.5">
      <select
        value={value}
        onFocus={() =>
          setActivated(true)
        }
        onChange={(event) =>
          onChange(event.target.value)
        }
        disabled={
          disabled ||
          productUnitsQuery.isLoading
        }
        className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm disabled:cursor-not-allowed disabled:opacity-50"
      >
        <option value="">
          Base quantity (default)
        </option>

        {activeUnits.map(
          (productUnit) => (
            <option
              key={productUnit.id}
              value={productUnit.id}
            >
              {stockCountUnitLabel(
                productUnit,
              )}
            </option>
          ),
        )}
      </select>

      {productUnitsQuery.isLoading ? (
        <div className="text-xs text-muted-foreground">
          Loading configured units…
        </div>
      ) : null}

      {productUnitsQuery.isError ? (
        <div className="text-xs text-destructive">
          Unable to load alternate units.
          Base quantity can still be entered.
        </div>
      ) : null}

      {selectedUnit ? (
        <div className="space-y-0.5 text-xs text-muted-foreground">
          <div>
            1 {selectedUnitName} ={" "}
            {displayQuantity(factor)}{" "}
            base units
          </div>

          {Number.isFinite(
            enteredQuantity,
          ) &&
          enteredQuantity >= 0 ? (
            <div>
              Stock equivalent:{" "}
              <span className="font-medium text-foreground">
                {displayQuantity(
                  baseQuantity,
                )}{" "}
                base units
              </span>
            </div>
          ) : null}
        </div>
      ) : (
        <div className="text-xs text-muted-foreground">
          Quantity is interpreted as base stock.
        </div>
      )}
    </div>
  );
}

export default StockCountUnitSelector;
