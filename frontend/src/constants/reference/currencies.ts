/**
 * ============================================================================
 * Hela360 Currency Reference Data
 * ============================================================================
 *
 * Common ISO 4217 currencies used by Hela360 tenants.
 *
 * This is deliberately a controlled selector rather than arbitrary free text.
 *
 * ============================================================================
 */

export interface CurrencyOption {
  code: string;
  name: string;
}

export const CURRENCIES: readonly CurrencyOption[] = [
  { code: "KES", name: "Kenyan Shilling" },
  { code: "USD", name: "US Dollar" },
  { code: "EUR", name: "Euro" },
  { code: "GBP", name: "Pound Sterling" },
  { code: "AED", name: "UAE Dirham" },
  { code: "SAR", name: "Saudi Riyal" },
  { code: "OMR", name: "Omani Rial" },
  { code: "QAR", name: "Qatari Riyal" },
  { code: "UGX", name: "Ugandan Shilling" },
  { code: "TZS", name: "Tanzanian Shilling" },
  { code: "RWF", name: "Rwandan Franc" },
  { code: "ETB", name: "Ethiopian Birr" },
  { code: "ZAR", name: "South African Rand" },
  { code: "INR", name: "Indian Rupee" },
  { code: "CNY", name: "Chinese Yuan" },
  { code: "JPY", name: "Japanese Yen" },
  { code: "CAD", name: "Canadian Dollar" },
  { code: "AUD", name: "Australian Dollar" },
] as const;

export function currencyName(
  code: string | null | undefined,
): string {
  if (!code) {
    return "";
  }

  return (
    CURRENCIES.find(
      (currency) => currency.code === code.toUpperCase(),
    )?.name ?? code
  );
}
