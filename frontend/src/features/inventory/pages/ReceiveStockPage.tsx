import { SearchableSelect } from "@/components/forms/SearchableSelect"
import {
  ArrowLeft,
  PackagePlus,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Link,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { toast } from "sonner";

import {
  EmptyState,
  ErrorState,
  LoadingState,
  Page,
  PageActions,
  PageContent,
  PageDescription,
  PageHeader,
  PageSection,
  PageTitle,
  PageToolbar,
} from "@/components/page";
import { Badge } from "@/components/ui/badge";
import {
  Button,
  buttonVariants,
} from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import {
  useBeginGoodsReceiptReceiving,
  useCompleteGoodsReceiptReceiving,
  useCreateGoodsReceiptDraft,
  useGoodsReceipt,
  useUpdateGoodsReceipt,
} from "@/hooks/queries/inventory";
import {
  useProducts,
} from "@/hooks/queries/products";
import {
  useSuppliers,
} from "@/hooks/queries/suppliers";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import { useQueryScope } from "@/hooks/useQueryScope";
import { createClientId } from "@/lib/clientId";
import { PATHS } from "@/routes/routes";
import { productService } from "@/services/products";
import type {
  GoodsReceipt,
  GoodsReceiptStatus,
  Product,
} from "@/types/entities";
import type {
  CreateGoodsReceiptDraftRequest,
  UpdateGoodsReceiptRequest,
} from "@/types/requests";

const PAGE_SIZE = 10;

interface ReceiptLine {
  id: string;
  product: Product;

  product_unit_id: string;

  quantity: string;
  invoiced_quantity: string;
  received_quantity: string;
  accepted_quantity: string;
  rejected_quantity: string;
  bonus_quantity: string;

  unit_cost: string;

  batch_number: string;
  manufacture_date: string;
  expiry_date: string;
  supplier_batch_reference: string;

  supplier_item_code: string;
  supplier_description: string;

  supplier_unit_price: string;
  discount_percent: string;
  discount_amount: string;
  tax_rate: string;
  tax_amount: string;
  net_unit_cost: string;
  line_total: string;

  discrepancy_status: string;
  discrepancy_reason: string;
}

function createDraftId(): string {
  return createClientId();
}

function createIdempotencyKey(): string {
  return `goods-receipt-${createClientId()}`;
}

function numericValue(value: string): number {
  return Number(value);
}

function productRequiresBatch(product: Product): boolean {
  return product.track_batches || product.track_expiry;
}

function productLabel(product: Product): string {
  return `${product.internal_sku} - ${product.name}`;
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Something went wrong.";
}

function buildDraftRequest({
  warehouseId,
  supplierId,
  supplierReference,
  notes,
}: {
  warehouseId: string;
  supplierId: string;
  supplierReference: string;
  notes: string;
}): Omit<CreateGoodsReceiptDraftRequest, "idempotency_key"> {
  return {
    warehouse_id: warehouseId,
    ...(supplierId ? { supplier_id: supplierId } : {}),
    ...(supplierReference.trim()
      ? { supplier_reference: supplierReference.trim() }
      : {}),
    ...(notes.trim() ? { notes: notes.trim() } : {}),
  };
}

function buildUpdateRequest({
  warehouseId,
  supplierId,
  supplierReference,
  supplierInvoiceNumber,
  supplierInvoiceDate,
  paymentTerms,
  invoiceCurrency,
  supplierSubtotal,
  supplierDiscountTotal,
  supplierTaxTotal,
  supplierInvoiceTotal,
  notes,
  lines,
}: {
  warehouseId: string;
  supplierId: string;
  supplierReference: string;
  supplierInvoiceNumber: string;
  supplierInvoiceDate: string;
  paymentTerms: string;
  invoiceCurrency: string;
  supplierSubtotal: string;
  supplierDiscountTotal: string;
  supplierTaxTotal: string;
  supplierInvoiceTotal: string;
  notes: string;
  lines: ReceiptLine[];
}): UpdateGoodsReceiptRequest {
  return {
    warehouse_id: warehouseId,

    ...(supplierId
      ? { supplier_id: supplierId }
      : {}),
    ...(supplierReference.trim()
      ? { supplier_reference: supplierReference.trim() }
      : {}),

    ...(supplierInvoiceNumber.trim()
      ? {
          supplier_invoice_number:
            supplierInvoiceNumber.trim(),
        }
      : {}),
    ...(supplierInvoiceDate
      ? {
          supplier_invoice_date:
            supplierInvoiceDate,
        }
      : {}),
    ...(paymentTerms.trim()
      ? { payment_terms: paymentTerms.trim() }
      : {}),

    invoice_currency:
      invoiceCurrency.trim().toUpperCase() || "KES",

    ...(supplierSubtotal.trim()
      ? { supplier_subtotal: supplierSubtotal.trim() }
      : {}),
    ...(supplierDiscountTotal.trim()
      ? {
          supplier_discount_total:
            supplierDiscountTotal.trim(),
        }
      : {}),
    ...(supplierTaxTotal.trim()
      ? { supplier_tax_total: supplierTaxTotal.trim() }
      : {}),
    ...(supplierInvoiceTotal.trim()
      ? {
          supplier_invoice_total:
            supplierInvoiceTotal.trim(),
        }
      : {}),

    ...(notes.trim()
      ? { notes: notes.trim() }
      : {}),

    items: lines.map((line) => ({
      product_id: line.product.id,

      ...(line.product_unit_id
        ? {
            product_unit_id:
              line.product_unit_id,
          }
        : {}),

      quantity: line.quantity,

      ...(line.invoiced_quantity
        ? {
            invoiced_quantity:
              line.invoiced_quantity,
          }
        : {}),
      ...(line.received_quantity
        ? {
            received_quantity:
              line.received_quantity,
          }
        : {}),
      ...(line.accepted_quantity
        ? {
            accepted_quantity:
              line.accepted_quantity,
          }
        : {}),
      ...(line.rejected_quantity
        ? {
            rejected_quantity:
              line.rejected_quantity,
          }
        : {}),
      ...(line.bonus_quantity
        ? {
            bonus_quantity:
              line.bonus_quantity,
          }
        : {}),

      unit_cost: line.unit_cost,

      ...(line.batch_number.trim()
        ? {
            batch_number:
              line.batch_number.trim(),
          }
        : {}),
      ...(line.manufacture_date
        ? {
            manufacture_date:
              line.manufacture_date,
          }
        : {}),
      ...(line.expiry_date
        ? {
            expiry_date:
              line.expiry_date,
          }
        : {}),
      ...(line.supplier_batch_reference.trim()
        ? {
            supplier_batch_reference:
              line.supplier_batch_reference.trim(),
          }
        : {}),

      ...(line.supplier_item_code.trim()
        ? {
            supplier_item_code:
              line.supplier_item_code.trim(),
          }
        : {}),
      ...(line.supplier_description.trim()
        ? {
            supplier_description:
              line.supplier_description.trim(),
          }
        : {}),

      ...(line.supplier_unit_price
        ? {
            supplier_unit_price:
              line.supplier_unit_price,
          }
        : {}),
      ...(line.discount_percent
        ? {
            discount_percent:
              line.discount_percent,
          }
        : {}),
      ...(line.discount_amount
        ? {
            discount_amount:
              line.discount_amount,
          }
        : {}),
      ...(line.tax_rate
        ? {
            tax_rate:
              line.tax_rate,
          }
        : {}),
      ...(line.tax_amount
        ? {
            tax_amount:
              line.tax_amount,
          }
        : {}),
      ...(line.net_unit_cost
        ? {
            net_unit_cost:
              line.net_unit_cost,
          }
        : {}),
      ...(line.line_total
        ? {
            line_total:
              line.line_total,
          }
        : {}),

      ...(line.discrepancy_status.trim()
        ? {
            discrepancy_status:
              line.discrepancy_status.trim(),
          }
        : {}),
      ...(line.discrepancy_reason.trim()
        ? {
            discrepancy_reason:
              line.discrepancy_reason.trim(),
          }
        : {}),
    })),
  };
}

function validateLines(lines: ReceiptLine[]): string | null {
  if (lines.length === 0) {
    return "Add at least one product.";
  }

  const seen = new Set<string>();
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  for (const line of lines) {
    const quantity = numericValue(line.quantity);
    const unitCost = numericValue(line.unit_cost);

    if (!Number.isFinite(quantity) || quantity <= 0) {
      return `${line.product.name}: quantity must be greater than zero.`;
    }

    if (!Number.isFinite(unitCost) || unitCost < 0) {
      return `${line.product.name}: unit cost must be non-negative.`;
    }

    const requiresBatch = productRequiresBatch(line.product);
    const batchNumber = line.batch_number.trim();

    if (requiresBatch && !batchNumber) {
      return `${line.product.name}: batch number is required.`;
    }

    if (!requiresBatch && (batchNumber || line.expiry_date || line.manufacture_date)) {
      return `${line.product.name}: batch fields are not available for this product.`;
    }

    if (line.product.track_expiry && !line.expiry_date) {
      return `${line.product.name}: expiry date is required.`;
    }

    if (line.expiry_date) {
      const expiry = new Date(`${line.expiry_date}T00:00:00`);
      if (expiry < today) {
        return `${line.product.name}: expired stock cannot be received.`;
      }
    }

    const duplicateKey = `${line.product.id}::${batchNumber}`;
    if (seen.has(duplicateKey)) {
      return "Duplicate product and batch lines are not allowed.";
    }
    seen.add(duplicateKey);
  }

  return null;
}

export function ReceiveStockPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const resumeReceiptId =
    searchParams.get("receipt")?.trim() || undefined;
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    supplierId,
    setSupplierId,
  ] = useState("");
  const [
    supplierSearchInput,
    setSupplierSearchInput,
  ] = useState("");
  const [
    supplierSearch,
    setSupplierSearch,
  ] = useState("");
  const [
    supplierReference,
    setSupplierReference,
  ] = useState("");

  const [
    supplierInvoiceNumber,
    setSupplierInvoiceNumber,
  ] = useState("");
  const [
    supplierInvoiceDate,
    setSupplierInvoiceDate,
  ] = useState("");
  const [
    paymentTerms,
    setPaymentTerms,
  ] = useState("");
  const [
    invoiceCurrency,
    setInvoiceCurrency,
  ] = useState("KES");

  const [
    supplierSubtotal,
    setSupplierSubtotal,
  ] = useState("");
  const [
    supplierDiscountTotal,
    setSupplierDiscountTotal,
  ] = useState("");
  const [
    supplierTaxTotal,
    setSupplierTaxTotal,
  ] = useState("");
  const [
    supplierInvoiceTotal,
    setSupplierInvoiceTotal,
  ] = useState("");

  const [
    notes,
    setNotes,
  ] = useState("");
  const [
    productSearchInput,
    setProductSearchInput,
  ] = useState("");
  const [
    productSearch,
    setProductSearch,
  ] = useState("");
  const [
    selectedProductId,
    setSelectedProductId,
  ] = useState("");
  const [
    lines,
    setLines,
  ] = useState<ReceiptLine[]>([]);
  const [
    idempotencyKey,
    setIdempotencyKey,
  ] = useState(createIdempotencyKey);
  const [
    receiptId,
    setReceiptId,
  ] = useState<string | null>(null);
  const [
    receiptStatus,
    setReceiptStatus,
  ] = useState<GoodsReceiptStatus | null>(null);
  const [
    resumeHydrationError,
    setResumeHydrationError,
  ] = useState<string | null>(null);
  const [
    isHydratingResume,
    setIsHydratingResume,
  ] = useState(false);

  const hydratedReceiptIdRef = useRef<string | null>(null);

  const resumeReceiptQuery = useGoodsReceipt(resumeReceiptId);
  const warehousesQuery = useWarehouses();
  const suppliersQuery = useSuppliers({
    page: 1,
    per_page: PAGE_SIZE,
    search: supplierSearch || undefined,
  });
  const productsQuery = useProducts({
    page: 1,
    per_page: PAGE_SIZE,
    search: productSearch || undefined,
    is_active: true,
  });
  const createDraft = useCreateGoodsReceiptDraft();
  const updateReceipt = useUpdateGoodsReceipt();
  const beginReceiving = useBeginGoodsReceiptReceiving();
  const completeReceiving = useCompleteGoodsReceiptReceiving();

  const isWorking =
    createDraft.isPending ||
    updateReceipt.isPending ||
    beginReceiving.isPending ||
    completeReceiving.isPending;

  useEffect(() => {
    const receipt = resumeReceiptQuery.data;

    if (!resumeReceiptId || !receipt) {
      return;
    }

    if (hydratedReceiptIdRef.current === receipt.id) {
      return;
    }

    let cancelled = false;

    const hydrateReceipt = async () => {
      if (
        receipt.status !== "draft" &&
        receipt.status !== "receiving"
      ) {
        toast.error(
          "Only draft or receiving Goods Receipts can be resumed.",
        );

        navigate(
          PATHS.INVENTORY.receipt(receipt.id),
          { replace: true },
        );
        return;
      }

      setIsHydratingResume(true);
      setResumeHydrationError(null);

      try {
        const productIds = [
          ...new Set(
            receipt.items.map((item) => item.product.id),
          ),
        ];

        const fullProducts = await Promise.all(
          productIds.map((productId) =>
            productService.getProduct(productId),
          ),
        );

        if (cancelled) {
          return;
        }

        const productsById = new Map(
          fullProducts.map((product) => [
            product.id,
            product,
          ]),
        );

        const hydratedLines: ReceiptLine[] =
          receipt.items.map((item) => {
            const product = productsById.get(
              item.product.id,
            );

            if (!product) {
              throw new Error(
                `Unable to hydrate product ${item.product.name}.`,
              );
            }

            return {
              id: item.id,
              product,

              product_unit_id:
                item.product_unit_id ?? "",

              quantity: item.quantity,
              invoiced_quantity:
                item.invoiced_quantity ?? "",
              received_quantity:
                item.received_quantity ?? "",
              accepted_quantity:
                item.accepted_quantity ?? "",
              rejected_quantity:
                item.rejected_quantity ?? "",
              bonus_quantity:
                item.bonus_quantity ?? "",

              unit_cost: item.unit_cost,

              batch_number:
                item.batch_number ?? "",
              manufacture_date:
                item.manufacture_date ?? "",
              expiry_date:
                item.expiry_date ?? "",
              supplier_batch_reference:
                item.supplier_batch_reference ?? "",

              supplier_item_code:
                item.supplier_item_code ?? "",
              supplier_description:
                item.supplier_description ?? "",

              supplier_unit_price:
                item.supplier_unit_price ?? "",
              discount_percent:
                item.discount_percent ?? "",
              discount_amount:
                item.discount_amount ?? "",
              tax_rate:
                item.tax_rate ?? "",
              tax_amount:
                item.tax_amount ?? "",
              net_unit_cost:
                item.net_unit_cost ?? "",
              line_total:
                item.line_total ?? "",

              discrepancy_status:
                item.discrepancy_status ?? "",
              discrepancy_reason:
                item.discrepancy_reason ?? "",
            };
          });

        setWarehouseId(receipt.warehouse.id);
        setSupplierId(receipt.supplier?.id ?? "");
        setSupplierReference(
          receipt.supplier_reference ?? "",
        );

        setSupplierInvoiceNumber(
          receipt.supplier_invoice_number ?? "",
        );
        setSupplierInvoiceDate(
          receipt.supplier_invoice_date ?? "",
        );
        setPaymentTerms(
          receipt.payment_terms ?? "",
        );
        setInvoiceCurrency(
          receipt.invoice_currency ?? "KES",
        );

        setSupplierSubtotal(
          receipt.supplier_subtotal ?? "",
        );
        setSupplierDiscountTotal(
          receipt.supplier_discount_total ?? "",
        );
        setSupplierTaxTotal(
          receipt.supplier_tax_total ?? "",
        );
        setSupplierInvoiceTotal(
          receipt.supplier_invoice_total ?? "",
        );

        setNotes(receipt.notes ?? "");
        setLines(hydratedLines);
        setReceiptId(receipt.id);
        setReceiptStatus(receipt.status);

        if (receipt.supplier) {
          setSupplierSearchInput(receipt.supplier.name);
          setSupplierSearch(receipt.supplier.name);
        }

        hydratedReceiptIdRef.current = receipt.id;
      } catch (error) {
        if (!cancelled) {
          setResumeHydrationError(
            errorMessage(error),
          );
        }
      } finally {
        if (!cancelled) {
          setIsHydratingResume(false);
        }
      }
    };

    void hydrateReceipt();

    return () => {
      cancelled = true;
    };
  }, [
    navigate,
    resumeReceiptId,
    resumeReceiptQuery.data,
  ]);

  const warehouses = useMemo(
    () => (warehousesQuery.data ?? []).filter((warehouse) => warehouse.is_active),
    [warehousesQuery.data],
  );
  const suppliers = (suppliersQuery.data?.items ?? []).filter(
    (supplier) => supplier.is_active,
  );
  const products = productsQuery.data?.items ?? [];
  const eligibleProducts = products.filter(
    (product) => product.is_active && product.track_inventory,
  );
  const selectedProduct = eligibleProducts.find(
    (product) => product.id === selectedProductId,
  );

  const addSelectedProduct = () => {
    if (!selectedProduct) {
      return;
    }

    setLines((current) => [
      ...current,
      {
        id: createDraftId(),
        product: selectedProduct,

        product_unit_id: "",

        quantity: "1",
        invoiced_quantity: "",
        received_quantity: "",
        accepted_quantity: "",
        rejected_quantity: "",
        bonus_quantity: "",

        unit_cost:
          selectedProduct.cost_price ?? "0.00",

        batch_number: "",
        manufacture_date: "",
        expiry_date: "",
        supplier_batch_reference: "",

        supplier_item_code: "",
        supplier_description: "",

        supplier_unit_price: "",
        discount_percent: "",
        discount_amount: "",
        tax_rate: "",
        tax_amount: "",
        net_unit_cost: "",
        line_total: "",

        discrepancy_status: "",
        discrepancy_reason: "",
      },
    ]);
    setSelectedProductId("");
  };

  const updateLine = (
    lineId: string,
    updates: Partial<Omit<ReceiptLine, "id" | "product">>,
  ) => {
    setLines((current) =>
      current.map((line) =>
        line.id === lineId
          ? {
              ...line,
              ...updates,
            }
          : line,
      ),
    );
  };

  const removeLine = (lineId: string) => {
    setLines((current) => current.filter((line) => line.id !== lineId));
  };

  const resetForAnotherReceipt = () => {
    setSupplierId("");
    setSupplierReference("");

    setSupplierInvoiceNumber("");
    setSupplierInvoiceDate("");
    setPaymentTerms("");
    setInvoiceCurrency("KES");

    setSupplierSubtotal("");
    setSupplierDiscountTotal("");
    setSupplierTaxTotal("");
    setSupplierInvoiceTotal("");

    setNotes("");
    setLines([]);
    setProductSearch("");
    setProductSearchInput("");
    setSelectedProductId("");
    setIdempotencyKey(createIdempotencyKey());
    setReceiptId(null);
    setReceiptStatus(null);
  };

  const syncReceiptState = (receipt: GoodsReceipt) => {
    setReceiptId(receipt.id);
    setReceiptStatus(receipt.status);
  };

  const persistEditableReceipt = async (): Promise<GoodsReceipt> => {
    if (!warehouseId) {
      throw new Error("Select a warehouse.");
    }

    const updatePayload = buildUpdateRequest({
      warehouseId,
      supplierId,
      supplierReference,

      supplierInvoiceNumber,
      supplierInvoiceDate,
      paymentTerms,
      invoiceCurrency,

      supplierSubtotal,
      supplierDiscountTotal,
      supplierTaxTotal,
      supplierInvoiceTotal,

      notes,
      lines,
    });

    if (!receiptId) {
      const draft = await createDraft.mutateAsync({
        ...buildDraftRequest({
          warehouseId,
          supplierId,
          supplierReference,
          notes,
        }),
        idempotency_key: idempotencyKey,
      });

      syncReceiptState(draft);

      // Draft creation intentionally has no line collection.
      // Persist the full editable aggregate immediately afterward.
      const saved = await updateReceipt.mutateAsync({
        receiptId: draft.id,
        payload: updatePayload,
      });

      syncReceiptState(saved);
      return saved;
    }

    const saved = await updateReceipt.mutateAsync({
      receiptId,
      payload: updatePayload,
    });

    syncReceiptState(saved);
    return saved;
  };

  const submitReceipt = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    try {
      const receipt = await persistEditableReceipt();

      toast.success(
        receipt.status === "receiving"
          ? "Receiving work saved."
          : "Goods receipt draft saved.",
      );
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  const handleBeginReceiving = async () => {
    try {
      const saved = await persistEditableReceipt();

      if (saved.status === "receiving") {
        toast.success("Goods receipt is already receiving.");
        return;
      }

      if (saved.status !== "draft") {
        toast.error(
          `Cannot begin receiving from ${saved.status}.`,
        );
        return;
      }

      const receiving =
        await beginReceiving.mutateAsync(saved.id);

      syncReceiptState(receiving);
      toast.success("Receiving started.");
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  const handleCompleteReceiving = async () => {
    if (receiptStatus !== "receiving") {
      toast.error("Begin receiving before completing the receipt.");
      return;
    }

    const validationError = validateLines(lines);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    try {
      const saved = await persistEditableReceipt();

      const received =
        await completeReceiving.mutateAsync(saved.id);

      syncReceiptState(received);
      toast.success("Goods receipt receiving completed.");

      navigate(
        PATHS.INVENTORY.receipt(received.id),
      );
    } catch (error) {
      toast.error(errorMessage(error));
    }
  };

  if (!isBranchScopeReady) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>Receive Stock</PageTitle>
            <PageDescription>
              Select an active branch before receiving stock.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <EmptyState
              title="Branch required"
              description="Receiving stock is branch-scoped."
            />
          </PageSection>
        </PageContent>
      </Page>
    );
  }

  if (
    resumeReceiptId &&
    (
      resumeReceiptQuery.isLoading ||
      isHydratingResume
    )
  ) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>Resume Receiving</PageTitle>
            <PageDescription>
              Loading the persisted Goods Receipt and product evidence.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <LoadingState title="Loading Goods Receipt" />
          </PageSection>
        </PageContent>
      </Page>
    );
  }

  if (
    resumeReceiptId &&
    (
      resumeReceiptQuery.isError ||
      resumeHydrationError
    )
  ) {
    return (
      <Page>
        <PageHeader>
          <div>
            <PageTitle>Resume Receiving</PageTitle>
            <PageDescription>
              The Goods Receipt could not be restored.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <ErrorState
              title="Unable to resume Goods Receipt"
              description={
                resumeHydrationError ??
                errorMessage(resumeReceiptQuery.error)
              }
            />
          </PageSection>
        </PageContent>
      </Page>
    );
  }

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            {receiptId ? "Resume Receiving" : "Receive Stock"}
          </PageTitle>
          <PageDescription>
            {receiptId
              ? "Continue the saved Goods Receipt receiving workflow."
              : "Receive physical stock into a branch warehouse with batch, expiry, and cost details."}
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.ROOT}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Inventory
          </Link>
          <Link
            to={PATHS.INVENTORY.RECEIPTS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            Receiving History
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        <form
          className="space-y-4"
          onSubmit={submitReceipt}
        >
          <PageSection>
            <div className="grid gap-4 lg:grid-cols-2">
              <Field label="Warehouse">
                {warehousesQuery.isLoading ? (
                  <LoadingState title="Loading warehouses" />
                ) : warehouses.length === 0 ? (
                  <ErrorState
                    title="No active warehouses"
                    description="Configure an active branch warehouse before receiving stock."
                  />
                ) : (
                  <NativeSelect
                    value={warehouseId}
                    onChange={setWarehouseId}
                    placeholder="Select warehouse"
                    options={warehouses.map((warehouse) => ({
                      value: warehouse.id,
                      label: `${warehouse.code} - ${warehouse.name}`,
                    }))}
                  />
                )}
              </Field>

              <Field label="Supplier">
                <div className="space-y-2">
                  <div
                    className="flex gap-2"
                  >
                    <Input
                      type="search"
                      value={supplierSearchInput}
                      onChange={(event) =>
                        setSupplierSearchInput(event.target.value)
                      }
                      placeholder="Search suppliers"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        setSupplierSearch(supplierSearchInput.trim())
                      }
                    >
                      <Search />
                      Search
                    </Button>
                  </div>
                  <NativeSelect
                    value={supplierId}
                    onChange={setSupplierId}
                    placeholder="No supplier / other source"
                    options={suppliers.map((supplier) => ({
                      value: supplier.id,
                      label: `${supplier.supplier_code} - ${supplier.name}`,
                    }))}
                  />
                </div>
              </Field>

              <Field label="Supplier reference">
                <Input
                  value={supplierReference}
                  onChange={(event) =>
                    setSupplierReference(event.target.value)
                  }
                  placeholder="Delivery note / invoice reference"
                />
              </Field>

              <Field label="Supplier invoice no.">
                <Input
                  value={supplierInvoiceNumber}
                  onChange={(event) =>
                    setSupplierInvoiceNumber(event.target.value)
                  }
                  placeholder="Supplier invoice number"
                />
              </Field>

              <Field label="Supplier invoice date">
                <Input
                  type="date"
                  value={supplierInvoiceDate}
                  onChange={(event) =>
                    setSupplierInvoiceDate(event.target.value)
                  }
                />
              </Field>

              <Field label="Payment terms">
                <Input
                  value={paymentTerms}
                  onChange={(event) =>
                    setPaymentTerms(event.target.value)
                  }
                  placeholder="e.g. Cash, 30 days"
                />
              </Field>

              <Field label="Invoice currency">
                <Input
                  value={invoiceCurrency}
                  onChange={(event) =>
                    setInvoiceCurrency(
                      event.target.value.toUpperCase(),
                    )
                  }
                  maxLength={3}
                  placeholder="KES"
                />
              </Field>

            </div>

            <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <Field label="Supplier subtotal">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={supplierSubtotal}
                  onChange={(event) =>
                    setSupplierSubtotal(event.target.value)
                  }
                  placeholder="0.00"
                />
              </Field>

              <Field label="Supplier discount">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={supplierDiscountTotal}
                  onChange={(event) =>
                    setSupplierDiscountTotal(event.target.value)
                  }
                  placeholder="0.00"
                />
              </Field>

              <Field label="Supplier tax">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={supplierTaxTotal}
                  onChange={(event) =>
                    setSupplierTaxTotal(event.target.value)
                  }
                  placeholder="0.00"
                />
              </Field>

              <Field label="Supplier invoice total">
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={supplierInvoiceTotal}
                  onChange={(event) =>
                    setSupplierInvoiceTotal(event.target.value)
                  }
                  placeholder="0.00"
                />
              </Field>
            </div>

            <div className="mt-4">
              <Field label="Notes">
                <Textarea
                  value={notes}
                  onChange={(event) =>
                    setNotes(event.target.value)
                  }
                  placeholder="Operational receipt notes"
                />
              </Field>
            </div>
          </PageSection>

          <PageSection>
            <PageToolbar>
              <div className="grid w-full gap-3 lg:grid-cols-[minmax(240px,1fr)_minmax(260px,1fr)_auto]">
                <div
                  className="flex gap-2"
                >
                  <Input
                    type="search"
                    value={productSearchInput}
                    onChange={(event) =>
                      setProductSearchInput(event.target.value)
                    }
                    placeholder="Search product or SKU"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      setProductSearch(productSearchInput.trim());
                      setSelectedProductId("");
                    }}
                  >
                    <Search />
                    Search
                  </Button>
                </div>

                <SearchableSelect
                  value={selectedProductId}
                  onValueChange={setSelectedProductId}
                  placeholder={
                    productsQuery.isLoading
                      ? "Loading products"
                      : "Select inventory product"
                  }
                  searchPlaceholder="Search product or SKU..."
                  emptyText="No inventory product found."
                  disabled={productsQuery.isLoading}
                  options={eligibleProducts.map((product) => ({
                    value: product.id,
                    label: productLabel(product),
                    keywords: [
                      product.name,
                      product.internal_sku,
                    ]
                      .filter(Boolean)
                      .join(" "),
                  }))}
                />

                <Button
                  type="button"
                  onClick={addSelectedProduct}
                  disabled={!selectedProduct}
                >
                  <Plus />
                  Add Product
                </Button>
              </div>
            </PageToolbar>

            {productsQuery.isError ? (
              <ErrorState
                title="Products unavailable"
                description={errorMessage(productsQuery.error)}
              />
            ) : lines.length === 0 ? (
              <EmptyState
                icon={<PackagePlus className="h-12 w-12" />}
                title="No products added"
                description="Search for inventory-tracked products and add receipt lines."
              />
            ) : (
              <div className="space-y-3">
                <div className="rounded-md border bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                  Invoice, physical, accepted, rejected, and bonus
                  quantities are receiving evidence. Stock Qty is the
                  quantity that will be converted to the product base
                  unit and posted to inventory after approval.
                </div>

                <div className="overflow-x-auto">
                  <ReceiptLinesTable
                    lines={lines}
                    onUpdate={updateLine}
                    onRemove={removeLine}
                  />
                </div>
              </div>
            )}
          </PageSection>

          <PageSection>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  {lines.length} receipt line{lines.length === 1 ? "" : "s"}
                </span>

                {receiptStatus ? (
                  <Badge variant="outline">
                    {receiptStatus.replace("_", " ")}
                  </Badge>
                ) : (
                  <Badge variant="outline">
                    Not saved
                  </Badge>
                )}
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={resetForAnotherReceipt}
                  disabled={isWorking || Boolean(receiptId)}
                >
                  Clear
                </Button>
                <Button
                  type="submit"
                  variant="outline"
                  disabled={
                    isWorking ||
                    warehouses.length === 0 ||
                    !warehouseId
                  }
                >
                  <RefreshCw
                    className={
                      isWorking ? "animate-spin" : undefined
                    }
                  />
                  {receiptId
                    ? "Save"
                    : "Save Draft"}
                </Button>

                {receiptStatus === null ||
                receiptStatus === "draft" ? (
                  <Button
                    type="button"
                    onClick={handleBeginReceiving}
                    disabled={
                      isWorking ||
                      warehouses.length === 0 ||
                      !warehouseId
                    }
                  >
                    <PackagePlus />
                    Begin Receiving
                  </Button>
                ) : null}

                {receiptStatus === "receiving" ? (
                  <Button
                    type="button"
                    onClick={handleCompleteReceiving}
                    disabled={
                      isWorking ||
                      lines.length === 0
                    }
                  >
                    <PackagePlus />
                    Complete Receiving
                  </Button>
                ) : null}
              </div>
            </div>
          </PageSection>
        </form>
      </PageContent>
    </Page>
  );
}

function ReceiptLinesTable({
  lines,
  onUpdate,
  onRemove,
}: {
  lines: ReceiptLine[];
  onUpdate: (
    lineId: string,
    updates: Partial<Omit<ReceiptLine, "id" | "product">>,
  ) => void;
  onRemove: (lineId: string) => void;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>Invoice Qty</TableHead>
          <TableHead>Physical Qty</TableHead>
          <TableHead>Accepted</TableHead>
          <TableHead>Rejected</TableHead>
          <TableHead>Bonus</TableHead>
          <TableHead>Stock Qty</TableHead>
          <TableHead>Unit Cost</TableHead>
          <TableHead>Batch</TableHead>
          <TableHead>Manufacture</TableHead>
          <TableHead>Expiry</TableHead>
          <TableHead>Supplier Batch</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {lines.map((line) => {
          const requiresBatch = productRequiresBatch(line.product);
          return (
            <TableRow key={line.id}>
              <TableCell className="min-w-[220px] whitespace-normal">
                <div className="font-medium">{line.product.name}</div>
                <div className="text-xs text-muted-foreground">
                  {line.product.internal_sku}
                </div>
                <div className="mt-1 flex flex-wrap gap-1">
                  {line.product.track_batches ? (
                    <Badge variant="outline">Batch</Badge>
                  ) : null}
                  {line.product.track_expiry ? (
                    <Badge variant="outline">Expiry</Badge>
                  ) : null}
                </div>
              </TableCell>
              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={line.invoiced_quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      invoiced_quantity:
                        event.target.value,
                    })
                  }
                  className="w-24"
                  aria-label={`Invoice quantity for ${line.product.name}`}
                />
              </TableCell>

              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={line.received_quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      received_quantity:
                        event.target.value,
                    })
                  }
                  className="w-24"
                  aria-label={`Physical quantity for ${line.product.name}`}
                />
              </TableCell>

              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={line.accepted_quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      accepted_quantity:
                        event.target.value,
                    })
                  }
                  className="w-24"
                  aria-label={`Accepted quantity for ${line.product.name}`}
                />
              </TableCell>

              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={line.rejected_quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      rejected_quantity:
                        event.target.value,
                    })
                  }
                  className="w-24"
                  aria-label={`Rejected quantity for ${line.product.name}`}
                />
              </TableCell>

              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={line.bonus_quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      bonus_quantity:
                        event.target.value,
                    })
                  }
                  className="w-24"
                  aria-label={`Bonus quantity for ${line.product.name}`}
                />
              </TableCell>

              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.0001"
                  value={line.quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      quantity: event.target.value,
                    })
                  }
                  className="w-24"
                  aria-label={`Stock quantity for ${line.product.name}`}
                />
              </TableCell>
              <TableCell>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={line.unit_cost}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      unit_cost: event.target.value,
                    })
                  }
                  className="w-28"
                />
              </TableCell>
              <TableCell>
                <Input
                  value={line.batch_number}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      batch_number: event.target.value,
                    })
                  }
                  disabled={!requiresBatch}
                  className="w-36"
                />
              </TableCell>
              <TableCell>
                <Input
                  type="date"
                  value={line.manufacture_date}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      manufacture_date: event.target.value,
                    })
                  }
                  disabled={!requiresBatch}
                  className="w-36"
                />
              </TableCell>
              <TableCell>
                <Input
                  type="date"
                  value={line.expiry_date}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      expiry_date: event.target.value,
                    })
                  }
                  disabled={!requiresBatch}
                  className="w-36"
                />
              </TableCell>
              <TableCell>
                <Input
                  value={line.supplier_batch_reference}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      supplier_batch_reference: event.target.value,
                    })
                  }
                  disabled={!requiresBatch}
                  className="w-40"
                />
              </TableCell>
              <TableCell className="text-right">
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  onClick={() => onRemove(line.id)}
                  aria-label={`Remove ${line.product.name}`}
                >
                  <Trash2 />
                </Button>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function NativeSelect({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  options: Array<{
    value: string;
    label: string;
  }>;
  placeholder: string;
}) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
    >
      <option value="">
        {placeholder}
      </option>
      {options.map((option) => (
        <option
          key={option.value}
          value={option.value}
        >
          {option.label}
        </option>
      ))}
    </select>
  );
}

export default ReceiveStockPage;
