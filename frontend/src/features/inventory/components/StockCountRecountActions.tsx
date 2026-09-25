import {
  CheckSquare2,
  FileSpreadsheet,
  Printer,
  RotateCcw,
  Search,
  Square,
  X,
} from "lucide-react";
import {
  useMemo,
  useRef,
  useState,
} from "react";
import { useReactToPrint } from "react-to-print";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type {
  StockCount,
  StockCountItem,
} from "@/types/entities";

interface StockCountRecountActionsProps {
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

  return Number.isFinite(parsed)
    ? parsed.toLocaleString(
        undefined,
        {
          maximumFractionDigits: 4,
        },
      )
    : value;
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

function sortedItems(
  items: StockCountItem[],
): StockCountItem[] {
  return [...items].sort(
    (a, b) =>
      a.line_number -
      b.line_number,
  );
}

async function exportRecountExcel(
  count: StockCount,
  items: StockCountItem[],
): Promise<void> {
  const XLSX = await import("xlsx");

  const showExpected =
    count.count_mode === "visible";

  const metadata: Array<
    [string, string]
  > = [
    ["Document", "Physical Recount Sheet"],
    ["Source Count", count.count_number],
    [
      "Warehouse",
      `${count.warehouse.code} - ${count.warehouse.name}`,
    ],
    [
      "Count Mode",
      count.count_mode === "blind"
        ? "Blind"
        : "Visible",
    ],
    [
      "Source Snapshot",
      dateTimeLabel(count.snapshot_at),
    ],
    [
      "Generated",
      new Date().toLocaleString(),
    ],
    [
      "Selected Lines",
      String(items.length),
    ],
  ];

  const headers = [
    "Original Line",
    "SKU",
    "Product",
    "Batch",
    "Expiry",
    "Counting UOM",
    ...(showExpected
      ? ["Expected Qty"]
      : []),
    "Recount Qty",
    "Notes",
  ];

  const rows = sortedItems(items)
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
    { wch: 13 },
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
    "Recount Sheet",
  );

  XLSX.writeFile(
    workbook,
    `${safeFilename(
      count.count_number,
    )}-recount-sheet.xlsx`,
    {
      compression: true,
    },
  );
}

export function StockCountRecountActions({
  count,
}: StockCountRecountActionsProps) {
  const [
    open,
    setOpen,
  ] = useState(false);

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    selectedIds,
    setSelectedIds,
  ] = useState<Set<string>>(
    () => new Set(),
  );

  const printRef =
    useRef<HTMLDivElement>(null);

  const printRecountSheet =
    useReactToPrint({
      contentRef: printRef,
      documentTitle:
        `${count.count_number}-recount-sheet`,
    });

  const showExpected =
    count.count_mode === "visible";

  const filteredItems =
    useMemo(() => {
      const query =
        search.trim().toLowerCase();

      const items =
        sortedItems(count.items);

      if (!query) {
        return items;
      }

      return items.filter(
        (item) => {
          const haystack = [
            String(item.line_number),
            item.product.internal_sku,
            item.product.name,
            batchLabel(item),
          ]
            .join(" ")
            .toLowerCase();

          return haystack.includes(query);
        },
      );
    }, [
      count.items,
      search,
    ]);

  const selectedItems =
    useMemo(
      () =>
        sortedItems(
          count.items.filter(
            (item) =>
              selectedIds.has(
                item.id,
              ),
          ),
        ),
      [
        count.items,
        selectedIds,
      ],
    );

  const allFilteredSelected =
    filteredItems.length > 0 &&
    filteredItems.every(
      (item) =>
        selectedIds.has(item.id),
    );

  const toggleItem = (
    itemId: string,
  ) => {
    setSelectedIds(
      (current) => {
        const next =
          new Set(current);

        if (next.has(itemId)) {
          next.delete(itemId);
        } else {
          next.add(itemId);
        }

        return next;
      },
    );
  };

  const toggleVisible = () => {
    setSelectedIds(
      (current) => {
        const next =
          new Set(current);

        if (allFilteredSelected) {
          for (
            const item
            of filteredItems
          ) {
            next.delete(item.id);
          }
        } else {
          for (
            const item
            of filteredItems
          ) {
            next.add(item.id);
          }
        }

        return next;
      },
    );
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  return (
    <>
      <Button
        type="button"
        variant="outline"
        onClick={() => setOpen(true)}
      >
        <RotateCcw />
        Recount Sheet
      </Button>

      {open ? (
        <div
          className={
            "fixed inset-0 z-50 flex " +
            "items-center justify-center " +
            "bg-black/60 p-4"
          }
          role="dialog"
          aria-modal="true"
          aria-labelledby={
            "stock-count-recount-title"
          }
        >
          <div
            className={
              "flex max-h-[88vh] w-full " +
              "max-w-4xl flex-col overflow-hidden " +
              "rounded-xl border bg-background shadow-xl"
            }
          >
            <div
              className={
                "flex items-start justify-between " +
                "gap-4 border-b p-5"
              }
            >
              <div>
                <h2
                  id={
                    "stock-count-recount-title"
                  }
                  className="text-lg font-semibold"
                >
                  Prepare Recount Sheet
                </h2>

                <p
                  className={
                    "mt-1 text-sm " +
                    "text-muted-foreground"
                  }
                >
                  Select only the stock lines
                  requiring physical verification.
                  No inventory quantities are
                  changed.
                </p>
              </div>

              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() =>
                  setOpen(false)
                }
                aria-label={
                  "Close recount selector"
                }
              >
                <X />
              </Button>
            </div>

            <div
              className={
                "flex flex-wrap items-center " +
                "gap-2 border-b p-4"
              }
            >
              <div
                className={
                  "relative min-w-[260px] flex-1"
                }
              >
                <Search
                  className={
                    "absolute left-3 top-1/2 " +
                    "size-4 -translate-y-1/2 " +
                    "text-muted-foreground"
                  }
                />

                <Input
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value,
                    )
                  }
                  placeholder={
                    "Search product, SKU, batch, or line"
                  }
                  className="pl-9"
                />
              </div>

              <Button
                type="button"
                variant="outline"
                onClick={toggleVisible}
                disabled={
                  filteredItems.length === 0
                }
              >
                {allFilteredSelected ? (
                  <Square />
                ) : (
                  <CheckSquare2 />
                )}

                {allFilteredSelected
                  ? "Unselect Visible"
                  : "Select Visible"}
              </Button>

              <Button
                type="button"
                variant="ghost"
                onClick={clearSelection}
                disabled={
                  selectedIds.size === 0
                }
              >
                Clear
              </Button>
            </div>

            <div
              className={
                "flex items-center justify-between " +
                "border-b px-4 py-3 text-sm"
              }
            >
              <div>
                <span className="font-medium">
                  {selectedIds.size}
                </span>{" "}
                selected
              </div>

              <div
                className={
                  "text-muted-foreground"
                }
              >
                {filteredItems.length}{" "}
                visible of{" "}
                {count.items.length} lines
              </div>
            </div>

            <div className="overflow-y-auto">
              {filteredItems.length ? (
                <div className="divide-y">
                  {filteredItems.map(
                    (item) => {
                      const selected =
                        selectedIds.has(
                          item.id,
                        );

                      return (
                        <label
                          key={item.id}
                          className={
                            "flex cursor-pointer " +
                            "items-start gap-3 px-4 py-3 " +
                            "hover:bg-muted/40"
                          }
                        >
                          <input
                            type="checkbox"
                            checked={selected}
                            onChange={() =>
                              toggleItem(
                                item.id,
                              )
                            }
                            className="mt-1 size-4"
                          />

                          <div
                            className={
                              "min-w-0 flex-1"
                            }
                          >
                            <div
                              className={
                                "flex flex-wrap items-center " +
                                "gap-x-3 gap-y-1"
                              }
                            >
                              <span
                                className={
                                  "font-medium"
                                }
                              >
                                Line{" "}
                                {item.line_number}
                              </span>

                              <span
                                className={
                                  "text-xs " +
                                  "text-muted-foreground"
                                }
                              >
                                {
                                  item.product
                                    .internal_sku
                                }
                              </span>
                            </div>

                            <div className="mt-1">
                              {
                                item.product
                                  .name
                              }
                            </div>

                            <div
                              className={
                                "mt-1 flex flex-wrap " +
                                "gap-x-4 gap-y-1 text-xs " +
                                "text-muted-foreground"
                              }
                            >
                              <span>
                                Batch:{" "}
                                {batchLabel(
                                  item,
                                )}
                              </span>

                              <span>
                                Expiry:{" "}
                                {expiryLabel(
                                  item,
                                )}
                              </span>

                              <span>
                                UOM:{" "}
                                {unitLabel(
                                  item,
                                )}
                              </span>
                            </div>
                          </div>
                        </label>
                      );
                    },
                  )}
                </div>
              ) : (
                <div
                  className={
                    "p-8 text-center text-sm " +
                    "text-muted-foreground"
                  }
                >
                  No Stock Count lines match
                  this search.
                </div>
              )}
            </div>

            <div
              className={
                "flex flex-wrap items-center " +
                "justify-between gap-3 border-t p-4"
              }
            >
              <div
                className={
                  "text-sm text-muted-foreground"
                }
              >
                {count.count_mode === "blind"
                  ? (
                      "Blind-count protection: " +
                      "expected quantities and variances " +
                      "will not appear."
                    )
                  : (
                      "Visible count: expected quantity " +
                      "will appear on the recount sheet."
                    )}
              </div>

              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() =>
                    printRecountSheet()
                  }
                  disabled={
                    selectedItems.length === 0
                  }
                >
                  <Printer />
                  Print Recount
                </Button>

                <Button
                  type="button"
                  onClick={() => {
                    void exportRecountExcel(
                      count,
                      selectedItems,
                    );
                  }}
                  disabled={
                    selectedItems.length === 0
                  }
                >
                  <FileSpreadsheet />
                  Export Recount Excel
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div
        className={
          "fixed left-[-20000px] top-0 " +
          "w-[190mm] bg-white text-black"
        }
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

                .hela360-recount-sheet {
                  font-family:
                    Arial,
                    Helvetica,
                    sans-serif;
                  color: #111827;
                  font-size: 9pt;
                }

                .hela360-recount-sheet table {
                  width: 100%;
                  border-collapse: collapse;
                }

                .hela360-recount-sheet thead {
                  display: table-header-group;
                }

                .hela360-recount-sheet tr {
                  break-inside: avoid;
                  page-break-inside: avoid;
                }

                .hela360-recount-sheet th,
                .hela360-recount-sheet td {
                  border: 1px solid #9ca3af;
                  padding: 5px 6px;
                  vertical-align: top;
                }

                .hela360-recount-sheet th {
                  background: #f3f4f6 !important;
                  font-weight: 700;
                  text-align: left;
                }

                .hela360-recount-sheet .physical-cell {
                  height: 28px;
                  min-width: 22mm;
                }

                .hela360-recount-sheet .notes-cell {
                  min-width: 28mm;
                }
              }
            `}
          </style>

          <section className="hela360-recount-sheet">
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
                    Physical Recount Sheet
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
                    Source:{" "}
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
                <strong>
                  Warehouse:
                </strong>{" "}
                {count.warehouse.code} -{" "}
                {count.warehouse.name}
              </div>

              <div>
                <strong>
                  Selected lines:
                </strong>{" "}
                {selectedItems.length}
              </div>

              <div>
                <strong>Mode:</strong>{" "}
                {count.count_mode === "blind"
                  ? "Blind recount"
                  : "Visible recount"}
              </div>

              <div>
                <strong>
                  Source snapshot:
                </strong>{" "}
                {dateTimeLabel(
                  count.snapshot_at,
                )}
              </div>
            </div>

            {count.count_mode === "blind" ? (
              <div
                style={{
                  marginBottom: "10px",
                  padding: "6px 8px",
                  border:
                    "1px solid #9ca3af",
                  background: "#f9fafb",
                  fontSize: "8.5pt",
                }}
              >
                Blind recount sheet —
                system expected quantities
                and variances are intentionally
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
                  <th>
                    Original Line
                  </th>
                  <th>SKU</th>
                  <th>Product</th>
                  <th>Batch</th>
                  <th>Expiry</th>
                  <th>UOM</th>

                  {showExpected ? (
                    <th>Expected</th>
                  ) : null}

                  <th>Recount Qty</th>
                  <th>Notes</th>
                </tr>
              </thead>

              <tbody>
                {selectedItems.map(
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
                        {
                          item.product
                            .name
                        }
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
              Recount working sheet generated
              from Hela360 Stock Count{" "}
              {count.count_number}. This
              document does not modify
              inventory or post adjustments.
            </footer>
          </section>
        </div>
      </div>
    </>
  );
}
