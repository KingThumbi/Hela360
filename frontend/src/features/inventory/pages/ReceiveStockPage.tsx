import {
  ArrowLeft,
  PackagePlus,
  Plus,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";
import {
  useMemo,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Link,
  useNavigate,
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
  useCreateGoodsReceipt,
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
import type {
  Product,
} from "@/types/entities";
import type {
  CreateGoodsReceiptRequest,
} from "@/types/requests";

const PAGE_SIZE = 10;

interface ReceiptLine {
  id: string;
  product: Product;
  quantity: string;
  unit_cost: string;
  batch_number: string;
  manufacture_date: string;
  expiry_date: string;
  supplier_batch_reference: string;
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

function requestSnapshot(
  payload: Omit<CreateGoodsReceiptRequest, "idempotency_key">,
): string {
  return JSON.stringify(payload);
}

function buildRequestBase({
  warehouseId,
  supplierId,
  supplierReference,
  receivedAt,
  notes,
  lines,
}: {
  warehouseId: string;
  supplierId: string;
  supplierReference: string;
  receivedAt: string;
  notes: string;
  lines: ReceiptLine[];
}): Omit<CreateGoodsReceiptRequest, "idempotency_key"> {
  return {
    warehouse_id: warehouseId,
    ...(supplierId ? { supplier_id: supplierId } : {}),
    ...(supplierReference.trim()
      ? { supplier_reference: supplierReference.trim() }
      : {}),
    ...(receivedAt ? { received_at: new Date(receivedAt).toISOString() } : {}),
    ...(notes.trim() ? { notes: notes.trim() } : {}),
    items: lines.map((line) => ({
      product_id: line.product.id,
      quantity: line.quantity,
      unit_cost: line.unit_cost,
      ...(line.batch_number.trim()
        ? { batch_number: line.batch_number.trim() }
        : {}),
      ...(line.manufacture_date
        ? { manufacture_date: line.manufacture_date }
        : {}),
      ...(line.expiry_date ? { expiry_date: line.expiry_date } : {}),
      ...(line.supplier_batch_reference.trim()
        ? {
            supplier_batch_reference:
              line.supplier_batch_reference.trim(),
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
    receivedAt,
    setReceivedAt,
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
    submittedSnapshot,
    setSubmittedSnapshot,
  ] = useState<string | null>(null);

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
  const createReceipt = useCreateGoodsReceipt();

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
        quantity: "1",
        unit_cost: selectedProduct.cost_price ?? "0.00",
        batch_number: "",
        manufacture_date: "",
        expiry_date: "",
        supplier_batch_reference: "",
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
    setReceivedAt("");
    setNotes("");
    setLines([]);
    setProductSearch("");
    setProductSearchInput("");
    setSelectedProductId("");
    setIdempotencyKey(createIdempotencyKey());
    setSubmittedSnapshot(null);
  };

  const submitReceipt = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!warehouseId) {
      toast.error("Select a warehouse.");
      return;
    }

    const validationError = validateLines(lines);
    if (validationError) {
      toast.error(validationError);
      return;
    }

    const requestBase = buildRequestBase({
      warehouseId,
      supplierId,
      supplierReference,
      receivedAt,
      notes,
      lines,
    });
    const snapshot = requestSnapshot(requestBase);
    const nextKey =
      submittedSnapshot && submittedSnapshot !== snapshot
        ? createIdempotencyKey()
        : idempotencyKey;

    if (nextKey !== idempotencyKey) {
      setIdempotencyKey(nextKey);
    }
    setSubmittedSnapshot(snapshot);

    createReceipt.mutate(
      {
        ...requestBase,
        idempotency_key: nextKey,
      },
      {
        onSuccess: (receipt) => {
          toast.success("Goods receipt created.");
          resetForAnotherReceipt();
          navigate(PATHS.INVENTORY.receipt(receipt.id));
        },
        onError: (error) => {
          const message = errorMessage(error);
          toast.error(message);
          if (message.toLowerCase().includes("idempotency_key")) {
            setIdempotencyKey(createIdempotencyKey());
            setSubmittedSnapshot(null);
          }
        },
      },
    );
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

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Receive Stock</PageTitle>
          <PageDescription>
            Receive physical stock into a branch warehouse with batch, expiry, and cost details.
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

              <Field label="Received date">
                <Input
                  type="datetime-local"
                  value={receivedAt}
                  onChange={(event) => setReceivedAt(event.target.value)}
                />
              </Field>
            </div>

            <Field label="Notes">
              <Textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Operational receipt notes"
              />
            </Field>
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

                <NativeSelect
                  value={selectedProductId}
                  onChange={setSelectedProductId}
                  placeholder={
                    productsQuery.isLoading
                      ? "Loading products"
                      : "Select inventory product"
                  }
                  options={eligibleProducts.map((product) => ({
                    value: product.id,
                    label: productLabel(product),
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
              <ReceiptLinesTable
                lines={lines}
                onUpdate={updateLine}
                onRemove={removeLine}
              />
            )}
          </PageSection>

          <PageSection>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="text-sm text-muted-foreground">
                {lines.length} receipt line{lines.length === 1 ? "" : "s"}
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  onClick={resetForAnotherReceipt}
                  disabled={createReceipt.isPending}
                >
                  Clear
                </Button>
                <Button
                  type="submit"
                  disabled={
                    createReceipt.isPending ||
                    warehouses.length === 0 ||
                    lines.length === 0
                  }
                >
                  <RefreshCw
                    className={
                      createReceipt.isPending ? "animate-spin" : undefined
                    }
                  />
                  Receive Stock
                </Button>
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
          <TableHead>Quantity</TableHead>
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
                  value={line.quantity}
                  onChange={(event) =>
                    onUpdate(line.id, {
                      quantity: event.target.value,
                    })
                  }
                  className="w-28"
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
