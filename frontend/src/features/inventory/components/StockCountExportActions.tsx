import {
  FileSpreadsheet,
  Printer,
} from "lucide-react";
import {
  useRef,
} from "react";
import { useReactToPrint } from "react-to-print";
import { Button } from "@/components/ui/button";
import {
  StockCountRecountActions,
} from "@/features/inventory/components/StockCountRecountActions";
import type {
  StockCount,
  StockCountItem,
} from "@/types/entities";

interface StockCountExportActionsProps {
  count: StockCount;
}

function dateTimeLabel(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return new Date(value).toLocaleString();
}

function dateLabel(
  value: string | null,
): string {
  if (!value) {
    return "—";
  }

  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString();
}

function quantityLabel(
  value: string | null | undefined,
): string {
  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }

  const parsed = Number(value);

  if (!Number.isFinite(parsed)) {
    return value;
  }

  return parsed.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 4,
    },
  );
}

function batchLabel(
  item: StockCountItem,
): string {
  return (
    item.batch?.batch_number ??
    item.observed_batch_number ??
    "—"
  );
}

function expiryLabel(
  item: StockCountItem,
): string {
  return dateLabel(
    item.batch?.expiry_date ??
      item.observed_expiry_date,
  );
}

function unitLabel(
  item: StockCountItem,
): string {
  return (
    item.counted_unit_name ??
    item.counted_unit_code ??
    "Base quantity"
  );
}

function safeFilename(
  value: string,
): string {
  return value.replace(
    /[^a-zA-Z0-9._-]+/g,
    "-",
  );
}

async function exportStockCountExcel(
  count: StockCount,
): Promise<void> {
  const XLSX = await import("xlsx");

  const showExpected =
    count.count_mode === "visible";

  const metadata: Array<
    [string, string]
  > = [
    ["Document", "Physical Stock Count Sheet"],
    ["Count Number", count.count_number],
    [
      "Warehouse",
      `${count.warehouse.code} - ${count.warehouse.name}`,
    ],
    [
      "Scope",
      count.scope_type === "full"
        ? "Full warehouse"
        : "Selected products",
    ],
    [
      "Count Mode",
      count.count_mode === "blind"
        ? "Blind"
        : "Visible",
    ],
    [
      "Snapshot",
      dateTimeLabel(count.snapshot_at),
    ],
    [
      "Started",
      dateTimeLabel(count.started_at),
    ],
    [
      "Generated",
      new Date().toLocaleString(),
    ],
  ];

  const headers = [
    "Line",
    "SKU",
    "Product",
    "Batch",
    "Expiry",
    "Counting UOM",
    ...(showExpected
      ? ["Expected Qty"]
      : []),
    "Physical Qty",
    "Notes",
  ];

  const rows = [...count.items]
    .sort(
      (a, b) =>
        a.line_number -
        b.line_number,
    )
    .map((item) => [
      item.line_number,
      item.product.internal_sku,
      item.product.name,
      batchLabel(item),
      expiryLabel(item),
      unitLabel(item),
      ...(showExpected
        ? [
            quantityLabel(
              item.expected_quantity,
            ),
          ]
        : []),
      "",
      "",
    ]);

  const worksheet =
    XLSX.utils.aoa_to_sheet([
      ...metadata,
      [],
      [
        "Counter",
        "",
        "Signature",
        "",
        "Date",
        "",
      ],
      [],
      headers,
      ...rows,
    ]);

  worksheet["!cols"] = [
    { wch: 8 },
    { wch: 18 },
    { wch: 42 },
    { wch: 18 },
    { wch: 14 },
    { wch: 18 },
    ...(showExpected
      ? [{ wch: 15 }]
      : []),
    { wch: 16 },
    { wch: 30 },
  ];

  const workbook =
    XLSX.utils.book_new();

  XLSX.utils.book_append_sheet(
    workbook,
    worksheet,
    "Count Sheet",
  );

  XLSX.writeFile(
    workbook,
    `${safeFilename(
      count.count_number,
    )}-count-sheet.xlsx`,
    {
      compression: true,
    },
  );
}

export function StockCountExportActions({
  count,
}: StockCountExportActionsProps) {
  const printRef =
    useRef<HTMLDivElement>(null);

  const printCountSheet =
    useReactToPrint({
      contentRef: printRef,
      documentTitle:
        `${count.count_number}-count-sheet`,
    });

  const showExpected =
    count.count_mode === "visible";

  const sortedItems =
    [...count.items].sort(
      (a, b) =>
        a.line_number -
        b.line_number,
    );

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={() => printCountSheet()}
      >
        <Printer />
        Print Count Sheet
      </Button>

      <Button
        type="button"
        variant="outline"
        onClick={() => {
          void exportStockCountExcel(count);
        }}
      >
        <FileSpreadsheet />
        Export Excel
      </Button>

      <StockCountRecountActions
        count={count}
      />

      <div
        className="fixed left-[-20000px] top-0 w-[190mm] bg-white text-black"
        aria-hidden="true"
      >
        <div
          ref={printRef}
          className="bg-white p-0 text-black"
        >
          <style>
            {`
              @page {
                size: A4 portrait;
                margin: 10mm;
              }

              @media print {
                html,
                body {
                  background: white !important;
                }

                .hela360-count-sheet {
                  font-family:
                    Arial,
                    Helvetica,
                    sans-serif;
                  color: #111827;
                  font-size: 9pt;
                }

                .hela360-count-sheet table {
                  width: 100%;
                  border-collapse: collapse;
                }

                .hela360-count-sheet thead {
                  display: table-header-group;
                }

                .hela360-count-sheet tr {
                  break-inside: avoid;
                  page-break-inside: avoid;
                }

                .hela360-count-sheet th,
                .hela360-count-sheet td {
                  border: 1px solid #9ca3af;
                  padding: 5px 6px;
                  vertical-align: top;
                }

                .hela360-count-sheet th {
                  background: #f3f4f6 !important;
                  font-weight: 700;
                  text-align: left;
                }

                .hela360-count-sheet .physical-cell {
                  height: 26px;
                  min-width: 22mm;
                }

                .hela360-count-sheet .notes-cell {
                  min-width: 28mm;
                }
              }
            `}
          </style>

          <section className="hela360-count-sheet">
            <header
              style={{
                marginBottom: "12px",
                borderBottom:
                  "2px solid #111827",
                paddingBottom: "8px",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent:
                    "space-between",
                  gap: "16px",
                }}
              >
                <div>
                  <div
                    style={{
                      fontSize: "18pt",
                      fontWeight: 700,
                    }}
                  >
                    Hela360
                  </div>

                  <div
                    style={{
                      marginTop: "2px",
                      fontSize: "11pt",
                      fontWeight: 700,
                    }}
                  >
                    Physical Stock Count Sheet
                  </div>
                </div>

                <div
                  style={{
                    textAlign: "right",
                  }}
                >
                  <div
                    style={{
                      fontWeight: 700,
                    }}
                  >
                    {count.count_number}
                  </div>

                  <div>
                    Generated{" "}
                    {new Date().toLocaleString()}
                  </div>
                </div>
              </div>
            </header>

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "1fr 1fr",
                gap: "6px 24px",
                marginBottom: "12px",
              }}
            >
              <div>
                <strong>Warehouse:</strong>{" "}
                {count.warehouse.code} -{" "}
                {count.warehouse.name}
              </div>

              <div>
                <strong>Scope:</strong>{" "}
                {count.scope_type === "full"
                  ? "Full warehouse"
                  : "Selected products"}
              </div>

              <div>
                <strong>Mode:</strong>{" "}
                {count.count_mode === "blind"
                  ? "Blind count"
                  : "Visible count"}
              </div>

              <div>
                <strong>Snapshot:</strong>{" "}
                {dateTimeLabel(
                  count.snapshot_at,
                )}
              </div>

              <div>
                <strong>Started:</strong>{" "}
                {dateTimeLabel(
                  count.started_at,
                )}
              </div>

              <div>
                <strong>Lines:</strong>{" "}
                {count.items.length}
              </div>
            </div>

            {count.count_mode === "blind" ? (
              <div
                style={{
                  marginBottom: "10px",
                  padding: "6px 8px",
                  border: "1px solid #9ca3af",
                  background: "#f9fafb",
                  fontSize: "8.5pt",
                }}
              >
                Blind count sheet — system
                expected quantities and
                variances are intentionally
                omitted.
              </div>
            ) : null}

            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "1fr 1fr 1fr",
                gap: "12px",
                marginBottom: "12px",
              }}
            >
              <div>
                Counter: __________________
              </div>

              <div>
                Signature: ________________
              </div>

              <div>
                Date: _____________________
              </div>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Line</th>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Batch</th>
                  <th>Expiry</th>
                  <th>UOM</th>

                  {showExpected ? (
                    <th>Expected</th>
                  ) : null}

                  <th>Physical Qty</th>
                  <th>Notes</th>
                </tr>
              </thead>

              <tbody>
                {sortedItems.map(
                  (item) => (
                    <tr key={item.id}>
                      <td>
                        {item.line_number}
                      </td>

                      <td>
                        {
                          item.product
                            .internal_sku
                        }
                      </td>

                      <td>
                        {item.product.name}
                      </td>

                      <td>
                        {batchLabel(item)}
                      </td>

                      <td>
                        {expiryLabel(item)}
                      </td>

                      <td>
                        {unitLabel(item)}
                      </td>

                      {showExpected ? (
                        <td>
                          {quantityLabel(
                            item.expected_quantity,
                          )}
                        </td>
                      ) : null}

                      <td className="physical-cell">
                        &nbsp;
                      </td>

                      <td className="notes-cell">
                        &nbsp;
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>

            <footer
              style={{
                marginTop: "10px",
                borderTop:
                  "1px solid #9ca3af",
                paddingTop: "6px",
                fontSize: "8pt",
              }}
            >
              Generated from Hela360 Stock
              Count {count.count_number}.
              This working sheet does not
              modify inventory or post stock
              adjustments.
            </footer>
          </section>
        </div>
      </div>
    </>
  );
}
