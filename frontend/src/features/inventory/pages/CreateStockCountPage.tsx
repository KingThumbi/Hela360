import {
  ArrowLeft,
  ClipboardList,
  Plus,
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
  useCreateStockCount,
} from "@/hooks/queries/inventory";
import {
  useProducts,
} from "@/hooks/queries/products";
import {
  useWarehouses,
} from "@/hooks/queries/warehouses";
import { useQueryScope } from "@/hooks/useQueryScope";
import { createClientId } from "@/lib/clientId";
import { PATHS } from "@/routes/routes";
import type {
  Product,
  StockCountMode,
} from "@/types/entities";
import type {
  CreateStockCountRequest,
} from "@/types/requests";

const PRODUCT_PAGE_SIZE = 10;

type CountScope = "full" | "selected";

function createIdempotencyKey(): string {
  return `stock-count-${createClientId()}`;
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
  payload: Omit<CreateStockCountRequest, "idempotency_key">,
): string {
  return JSON.stringify(payload);
}

export function CreateStockCountPage() {
  const navigate = useNavigate();
  const {
    isBranchScopeReady,
  } = useQueryScope();
  const [
    warehouseId,
    setWarehouseId,
  ] = useState("");
  const [
    scope,
    setScope,
  ] = useState<CountScope>("full");
  const [
    countMode,
    setCountMode,
  ] = useState<StockCountMode>("blind");
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
    selectedProducts,
    setSelectedProducts,
  ] = useState<Product[]>([]);
  const [
    idempotencyKey,
    setIdempotencyKey,
  ] = useState(createIdempotencyKey);
  const [
    submittedSnapshot,
    setSubmittedSnapshot,
  ] = useState<string | null>(null);

  const warehousesQuery = useWarehouses();
  const productsQuery = useProducts({
    page: 1,
    per_page: PRODUCT_PAGE_SIZE,
    search: productSearch || undefined,
    is_active: true,
  }, {
    enabled: scope === "selected",
  });
  const createStockCount = useCreateStockCount();

  const warehouses = useMemo(
    () => (warehousesQuery.data ?? []).filter((warehouse) => warehouse.is_active),
    [warehousesQuery.data],
  );
  const eligibleProducts = (productsQuery.data?.items ?? []).filter(
    (product) => product.is_active && product.track_inventory,
  );
  const selectedProduct = eligibleProducts.find(
    (product) => product.id === selectedProductId,
  );

  const addSelectedProduct = () => {
    if (!selectedProduct) {
      return;
    }
    if (selectedProducts.some((product) => product.id === selectedProduct.id)) {
      toast.error("Product is already selected.");
      return;
    }
    setSelectedProducts((current) => [
      ...current,
      selectedProduct,
    ]);
    setSelectedProductId("");
  };

  const removeProduct = (productId: string) => {
    setSelectedProducts((current) =>
      current.filter((product) => product.id !== productId),
    );
  };

  const submitCount = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!warehouseId) {
      toast.error("Select a Warehouse.");
      return;
    }

    if (scope === "selected" && selectedProducts.length === 0) {
      toast.error("Select at least one inventory-tracked Product.");
      return;
    }

    const requestBase: Omit<CreateStockCountRequest, "idempotency_key"> = {
      warehouse_id: warehouseId,
      count_mode: countMode,
      ...(scope === "selected"
        ? {
            product_ids: selectedProducts.map((product) => product.id),
          }
        : {}),
      ...(notes.trim() ? { notes: notes.trim() } : {}),
    };
    const snapshot = requestSnapshot(requestBase);
    const nextKey =
      submittedSnapshot && submittedSnapshot !== snapshot
        ? createIdempotencyKey()
        : idempotencyKey;

    if (nextKey !== idempotencyKey) {
      setIdempotencyKey(nextKey);
    }
    setSubmittedSnapshot(snapshot);

    createStockCount.mutate(
      {
        ...requestBase,
        idempotency_key: nextKey,
      },
      {
        onSuccess: (count) => {
          toast.success("Stock Count created.");
          navigate(PATHS.INVENTORY.stockCount(count.id));
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
            <PageTitle>New Stock Count</PageTitle>
            <PageDescription>
              Select an active branch before creating a Stock Count.
            </PageDescription>
          </div>
        </PageHeader>
        <PageContent>
          <PageSection>
            <EmptyState
              title="Branch required"
              description="Stock Count creation is branch-scoped."
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
          <PageTitle>New Stock Count</PageTitle>
          <PageDescription>
            Create a Warehouse stock snapshot for physical counting.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={PATHS.INVENTORY.STOCK_COUNTS}
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Stock Counts
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        <form
          className="space-y-4"
          onSubmit={submitCount}
        >
          <PageSection>
            <div className="grid gap-4 lg:grid-cols-2">
              <Field label="Warehouse">
                {warehousesQuery.isLoading ? (
                  <LoadingState title="Loading Warehouses" />
                ) : warehousesQuery.isError ? (
                  <ErrorState
                    title="Warehouses unavailable"
                    description={errorMessage(warehousesQuery.error)}
                  />
                ) : warehouses.length === 0 ? (
                  <ErrorState
                    title="No active Warehouses"
                    description="Configure an active branch Warehouse before creating a Stock Count."
                  />
                ) : (
                  <NativeSelect
                    value={warehouseId}
                    onChange={setWarehouseId}
                    placeholder="Select Warehouse"
                    options={warehouses.map((warehouse) => ({
                      value: warehouse.id,
                      label: `${warehouse.code} - ${warehouse.name}`,
                    }))}
                  />
                )}
              </Field>

              <Field label="Count scope">
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant={scope === "full" ? "default" : "outline"}
                    onClick={() => setScope("full")}
                  >
                    Full Warehouse
                  </Button>
                  <Button
                    type="button"
                    variant={scope === "selected" ? "default" : "outline"}
                    onClick={() => setScope("selected")}
                  >
                    Selected Products
                  </Button>
                </div>
              </Field>

              <Field label="Count mode">
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant={
                        countMode === "blind"
                          ? "default"
                          : "outline"
                      }
                      onClick={() => setCountMode("blind")}
                    >
                      Blind Count
                    </Button>
                    <Button
                      type="button"
                      variant={
                        countMode === "visible"
                          ? "default"
                          : "outline"
                      }
                      onClick={() => setCountMode("visible")}
                    >
                      Visible Count
                    </Button>
                  </div>

                  <p className="text-sm text-muted-foreground">
                    {countMode === "blind"
                      ? "Recommended for physical stock takes. System quantities and variances remain hidden until the count is completed."
                      : "System quantities remain visible while counting. Use for supervised verification or operational reconciliation."}
                  </p>
                </div>
              </Field>
            </div>

            <Field label="Notes">
              <Textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                placeholder="Optional count notes"
              />
            </Field>
          </PageSection>

          {scope === "selected" ? (
            <PageSection>
              <PageToolbar>
                <div className="grid w-full gap-3 lg:grid-cols-[minmax(240px,1fr)_minmax(260px,1fr)_auto]">
                  <div className="flex gap-2">
                    <Input
                      type="search"
                      value={productSearchInput}
                      onChange={(event) =>
                        setProductSearchInput(event.target.value)
                      }
                      placeholder="Search Product or SKU"
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
                        ? "Loading Products"
                        : "Select inventory Product"
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
              ) : selectedProducts.length === 0 ? (
                <EmptyState
                  icon={<ClipboardList className="h-12 w-12" />}
                  title="No Products selected"
                  description="Selected counts snapshot only the Products chosen before the count is created."
                />
              ) : (
                <SelectedProductsTable
                  products={selectedProducts}
                  onRemove={removeProduct}
                />
              )}
            </PageSection>
          ) : (
            <PageSection>
              <div className="rounded-md border bg-muted/20 p-4 text-sm text-muted-foreground">
                Full Warehouse counts snapshot all current countable stock lines in the selected Warehouse.
              </div>
            </PageSection>
          )}

          <div className="flex justify-end gap-2">
            <Link
              to={PATHS.INVENTORY.STOCK_COUNTS}
              className={buttonVariants({
                variant: "outline",
              })}
            >
              Cancel
            </Link>
            <Button
              type="submit"
              disabled={
                createStockCount.isPending ||
                !warehouseId ||
                warehouses.length === 0 ||
                (scope === "selected" && selectedProducts.length === 0)
              }
            >
              <ClipboardList />
              Start Count
            </Button>
          </div>
        </form>
      </PageContent>
    </Page>
  );
}

function SelectedProductsTable({
  products,
  onRemove,
}: {
  products: Product[];
  onRemove: (productId: string) => void;
}) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Product</TableHead>
          <TableHead>SKU</TableHead>
          <TableHead>Tracking</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {products.map((product) => (
          <TableRow key={product.id}>
            <TableCell>
              <div className="font-medium">
                {product.name}
              </div>
              {product.generic_name ? (
                <div className="text-xs text-muted-foreground">
                  {product.generic_name}
                </div>
              ) : null}
            </TableCell>
            <TableCell>{product.internal_sku}</TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {product.track_batches ? (
                  <Badge variant="outline">Batch</Badge>
                ) : null}
                {product.track_expiry ? (
                  <Badge variant="outline">Expiry</Badge>
                ) : null}
                {!product.track_batches && !product.track_expiry ? (
                  <Badge variant="secondary">Product</Badge>
                ) : null}
              </div>
            </TableCell>
            <TableCell className="text-right">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => onRemove(product.id)}
              >
                <Trash2 />
                Remove
              </Button>
            </TableCell>
          </TableRow>
        ))}
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

export default CreateStockCountPage;
