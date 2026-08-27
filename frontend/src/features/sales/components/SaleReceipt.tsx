import type {
  SaleReceipt as SaleReceiptProjection,
} from "@/types/responses";

function displayDate(value: string | null): string {
  if (!value) {
    return "Not recorded";
  }

  return new Date(value).toLocaleString();
}

function displayMoney(
  value: string,
  currency: string | null,
): string {
  return currency ? `${currency} ${value}` : value;
}

function compactAddress(
  branch: SaleReceiptProjection["branch"],
): string | null {
  const parts = [
    branch.address_line1,
    branch.address_line2,
    branch.city,
    branch.country,
  ].filter(Boolean);

  return parts.length > 0 ? parts.join(", ") : null;
}

export function SaleReceipt({
  receipt,
}: {
  receipt: SaleReceiptProjection;
}) {
  const currency = receipt.totals.currency;
  const address = compactAddress(receipt.branch);

  return (
    <article className="sale-receipt mx-auto w-full max-w-[360px] bg-background text-foreground print:max-w-none">
      <header className="border-b pb-3 text-center">
        <h1 className="text-lg font-semibold">
          {receipt.seller.display_name || receipt.seller.legal_name || "Receipt"}
        </h1>
        <p className="text-sm font-medium">Sales Receipt</p>
        <div className="mt-2 text-xs text-muted-foreground">
          <p>{receipt.branch.name || receipt.branch.code}</p>
          {address ? <p>{address}</p> : null}
          {receipt.branch.phone ? <p>{receipt.branch.phone}</p> : null}
          {receipt.seller.email ? <p>{receipt.seller.email}</p> : null}
        </div>
      </header>

      <section className="grid gap-1 border-b py-3 text-xs">
        <ReceiptRow
          label="Sale"
          value={receipt.sale.sale_number || receipt.sale.id}
        />
        <ReceiptRow
          label="Date"
          value={displayDate(receipt.sale.sold_at)}
        />
        <ReceiptRow
          label="Status"
          value={receipt.sale.status || "Unknown"}
        />
        {receipt.customer ? (
          <ReceiptRow
            label="Customer"
            value={
              receipt.customer.full_name ||
              receipt.customer.customer_number
            }
          />
        ) : null}
        {receipt.cashier ? (
          <ReceiptRow
            label="Cashier"
            value={receipt.cashier.name || receipt.cashier.username || receipt.cashier.id}
          />
        ) : null}
        {receipt.till ? (
          <ReceiptRow
            label="Till"
            value={`${receipt.till.code} - ${receipt.till.name}`}
          />
        ) : null}
      </section>

      <section className="border-b py-3">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b text-left">
              <th className="py-1 font-medium">Item</th>
              <th className="py-1 text-right font-medium">Qty</th>
              <th className="py-1 text-right font-medium">Total</th>
            </tr>
          </thead>
          <tbody>
            {receipt.items.map((item) => (
              <tr key={item.id}>
                <td className="py-1 pr-2 align-top">
                  <div>{item.description}</div>
                  {item.sku ? (
                    <div className="text-muted-foreground">{item.sku}</div>
                  ) : null}
                  <div className="text-muted-foreground">
                    @ {displayMoney(item.unit_price, currency)}
                  </div>
                </td>
                <td className="py-1 text-right align-top">
                  {item.quantity}
                </td>
                <td className="py-1 text-right align-top">
                  {displayMoney(item.line_total, currency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="grid gap-1 border-b py-3 text-xs">
        <ReceiptRow
          label="Subtotal"
          value={displayMoney(receipt.totals.subtotal, currency)}
        />
        {receipt.totals.discount_amount !== "0.00" ? (
          <ReceiptRow
            label="Discount"
            value={displayMoney(receipt.totals.discount_amount, currency)}
          />
        ) : null}
        {receipt.totals.tax_amount !== "0.00" ? (
          <ReceiptRow
            label="Tax"
            value={displayMoney(receipt.totals.tax_amount, currency)}
          />
        ) : null}
        <ReceiptRow
          label="Total"
          value={displayMoney(receipt.totals.total_amount, currency)}
          strong
        />
        <ReceiptRow
          label="Paid"
          value={displayMoney(receipt.totals.paid_amount, currency)}
        />
        <ReceiptRow
          label="Balance"
          value={displayMoney(receipt.totals.balance_due, currency)}
        />
      </section>

      <section className="border-b py-3">
        <h2 className="mb-1 text-xs font-semibold">Payments</h2>
        <table className="w-full text-xs">
          <tbody>
            {receipt.payments.map((payment) => (
              <tr key={payment.id}>
                <td className="py-1">
                  {payment.payment_method?.name || "Payment"}
                  {payment.reference ? (
                    <div className="text-muted-foreground">
                      {payment.reference}
                    </div>
                  ) : null}
                </td>
                <td className="py-1 text-right">
                  {displayMoney(payment.amount, currency)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <footer className="pt-3 text-center text-xs text-muted-foreground">
        <p>Thank you</p>
      </footer>
    </article>
  );
}

function ReceiptRow({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: string;
  strong?: boolean;
}) {
  return (
    <div className="flex justify-between gap-3">
      <span className="text-muted-foreground">{label}</span>
      <span className={strong ? "font-semibold" : "font-medium"}>
        {value}
      </span>
    </div>
  );
}

export default SaleReceipt;
