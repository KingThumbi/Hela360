import {
  Barcode,
  Package,
  Plus,
  RefreshCw,
  Search,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthorization } from "@/hooks/useAuthorization";
import {
  useArchiveProduct,
  useCreateProduct,
  useDeleteProduct,
  useProductByCode,
  useProducts,
  useRestoreProduct,
  useUpdateProduct,
} from "@/hooks/queries/products";
import type { Product } from "@/types/entities";
import type {
  CreateProductRequest,
  UpdateProductRequest,
} from "@/types/requests";

import { ProductDeleteDialog } from "../components/ProductDeleteDialog";
import { ProductDetailDialog } from "../components/ProductDetailDialog";
import { ProductEditDialog } from "../components/ProductEditDialog";
import { ProductFormDialog } from "../components/ProductFormDialog";
import { ProductLifecycleDialog } from "../components/ProductLifecycleDialog";
import { ProductsTable } from "../components/ProductsTable";

const PAGE_SIZE = 25;

type ProductLifecycleFilter =
  | "active"
  | "archived"
  | "all";

function getErrorMessage(
  error: unknown,
): string | null {
  return error instanceof Error
    ? error.message
    : null;
}

export function ProductsPage() {
  const authorization = useAuthorization();

  const canCreate = authorization.can(
    "products.create",
  );

  const canEdit = authorization.can(
    "products.edit",
  );

  const canDelete = authorization.can(
    "products.delete",
  );

  const [
    page,
    setPage,
  ] = useState(1);
  const [
    searchInput,
    setSearchInput,
  ] = useState("");
  const [
    submittedSearch,
    setSubmittedSearch,
  ] = useState("");
  const [
    codeInput,
    setCodeInput,
  ] = useState("");
  const [
    submittedCode,
    setSubmittedCode,
  ] = useState("");
  const [
    createOpen,
    setCreateOpen,
  ] = useState(false);
  const [
    detailProduct,
    setDetailProduct,
  ] = useState<Product | null>(null);

  const [
    editProduct,
    setEditProduct,
  ] = useState<Product | null>(null);

  const [
    lifecycleProduct,
    setLifecycleProduct,
  ] = useState<Product | null>(null);

  const [
    deleteProductTarget,
    setDeleteProductTarget,
  ] = useState<Product | null>(null);

  const [
    lifecycleFilter,
    setLifecycleFilter,
  ] = useState<ProductLifecycleFilter>(
    "active",
  );

  const params = useMemo(
    () => ({
      page,
      per_page: PAGE_SIZE,
      search:
        submittedSearch.trim().length > 0
          ? submittedSearch.trim()
          : undefined,
      is_active:
        lifecycleFilter === "all"
          ? undefined
          : lifecycleFilter === "active",
    }),
    [
      lifecycleFilter,
      page,
      submittedSearch,
    ],
  );

  const productsQuery = useProducts(params);
  const createProduct = useCreateProduct();
  const updateProduct = useUpdateProduct();
  const archiveProduct = useArchiveProduct();
  const restoreProduct = useRestoreProduct();
  const deleteProductMutation = useDeleteProduct();

  const byCodeQuery = useProductByCode(
    submittedCode,
    {
      enabled: submittedCode.trim().length > 0,
    },
  );

  const products =
    productsQuery.data?.items ?? [];
  const pagination =
    productsQuery.data?.pagination;

  const handleSearchSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setPage(1);
    setSubmittedSearch(searchInput);
  };

  const handleCodeSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setSubmittedCode(codeInput.trim());
  };

  const handleCreate = (
    payload: CreateProductRequest,
  ) => {
    createProduct.mutate(payload, {
      onSuccess: (product) => {
        toast.success("Product created.");
        setCreateOpen(false);
        setDetailProduct(product);
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  };

  const handleUpdate = (
    id: string,
    payload: UpdateProductRequest,
  ) => {
    updateProduct.mutate(
      {
        id,
        data: payload,
      },
      {
        onSuccess: (product) => {
          toast.success("Product updated.");
          setEditProduct(null);
          setDetailProduct(product);
        },
        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  const handleLifecycleConfirm = () => {
    if (!lifecycleProduct) {
      return;
    }

    const product = lifecycleProduct;
    const mutation = product.is_active
      ? archiveProduct
      : restoreProduct;

    mutation.mutate(product.id, {
      onSuccess: () => {
        toast.success(
          product.is_active
            ? "Product archived."
            : "Product restored.",
        );
        setLifecycleProduct(null);
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  };

  const handleDeleteConfirm = () => {
    if (!deleteProductTarget) {
      return;
    }

    deleteProductMutation.mutate(
      deleteProductTarget.id,
      {
        onSuccess: () => {
          toast.success(
            "Product permanently deleted.",
          );

          setDeleteProductTarget(null);
        },

        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  const lifecycleMutationPending =
    archiveProduct.isPending ||
    restoreProduct.isPending;

  const isInitialLoading =
    productsQuery.isLoading &&
    products.length === 0;
  const isSearchEmpty =
    submittedSearch.trim().length > 0 &&
    products.length === 0;

  const emptyTitle =
    isSearchEmpty
      ? "No products match your search"
      : lifecycleFilter === "archived"
        ? "No archived products"
        : lifecycleFilter === "active"
          ? "No active products"
          : "No products yet";

  const emptyDescription =
    isSearchEmpty
      ? "Try a different product name, SKU, generic name, or supplier SKU."
      : lifecycleFilter === "archived"
        ? "Products you archive will appear here."
        : lifecycleFilter === "active"
          ? "Create a product or restore one from the archived list."
          : "Add your first product to get started.";

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Products</PageTitle>
          <PageDescription>
            Manage your products, prices, stock settings and product information.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            type="button"
            variant="outline"
            onClick={() => productsQuery.refetch()}
            disabled={productsQuery.isFetching}
          >
            <RefreshCw
              className={
                productsQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />
            Refresh
          </Button>

          {canCreate ? (
            <Button
              type="button"
              onClick={() => setCreateOpen(true)}
            >
              <Plus />
              Create Product
            </Button>
          ) : null}
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageToolbar>
          <div className="grid w-full gap-3 lg:grid-cols-[1fr_0.8fr]">
            <form
              className="flex flex-col gap-2 sm:flex-row sm:items-center"
              onSubmit={handleSearchSubmit}
            >
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  type="search"
                  value={searchInput}
                  onChange={(event) =>
                    setSearchInput(
                      event.target.value,
                    )
                  }
                  placeholder="Search products"
                  className="pl-8"
                />
              </div>
              <Button type="submit">
                Search
              </Button>
              {submittedSearch ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setSearchInput("");
                    setSubmittedSearch("");
                    setPage(1);
                  }}
                >
                  Clear
                </Button>
              ) : null}
            </form>

            <form
              className="flex flex-col gap-2 sm:flex-row sm:items-center"
              onSubmit={handleCodeSubmit}
            >
              <div className="relative flex-1">
                <Barcode className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={codeInput}
                  onChange={(event) =>
                    setCodeInput(
                      event.target.value,
                    )
                  }
                  placeholder="Lookup code"
                  className="pl-8"
                />
              </div>
              <Button type="submit">
                Lookup
              </Button>
            </form>
          </div>
        </PageToolbar>

        {submittedCode ? (
          <PageSection>
            <div className="rounded-lg border bg-background p-4">
              {byCodeQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">
                  Looking up product code...
                </p>
              ) : byCodeQuery.isError ? (
                <p className="text-sm text-destructive">
                  {getErrorMessage(
                    byCodeQuery.error,
                  ) ??
                    "No product was found for that code."}
                </p>
              ) : byCodeQuery.data ? (
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium">
                      {byCodeQuery.data.name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {
                        byCodeQuery.data
                          .internal_sku
                      }{" "}
                      ·{" "}
                      {
                        byCodeQuery.data
                          .product_type
                      }
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">
                      Code Match
                    </Badge>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() =>
                        setDetailProduct(
                          byCodeQuery.data,
                        )
                      }
                    >
                      View
                    </Button>
                  </div>
                </div>
              ) : null}
            </div>
          </PageSection>
        ) : null}

        <PageSection>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <span className="mr-1 text-sm font-medium">
              Catalogue
            </span>

            {(
              [
                ["active", "Active"],
                ["archived", "Archived"],
                ["all", "All"],
              ] as const
            ).map(([value, label]) => (
              <Button
                key={value}
                type="button"
                size="sm"
                variant={
                  lifecycleFilter === value
                    ? "default"
                    : "outline"
                }
                onClick={() => {
                  setLifecycleFilter(value);
                  setPage(1);
                }}
              >
                {label}
              </Button>
            ))}
          </div>

          {isInitialLoading ? (
            <LoadingState
              title="Loading products"
              description="Getting your products ready."
            />
          ) : productsQuery.isError ? (
            <ErrorState
              title="Unable to load products"
              description={
                getErrorMessage(
                  productsQuery.error,
                ) ??
                "We couldn't load your products. Please try again."
              }
              onRetry={() =>
                productsQuery.refetch()
              }
            />
          ) : products.length === 0 ? (
            <EmptyState
              icon={
                <Package className="h-12 w-12" />
              }
              title={emptyTitle}
              description={emptyDescription}
              actionLabel={
                !isSearchEmpty && canCreate
                  ? "Create Product"
                  : undefined
              }
              onAction={
                !isSearchEmpty && canCreate
                  ? () => setCreateOpen(true)
                  : undefined
              }
            />
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg border bg-background">
                <ProductsTable
                  products={products}
                  canEdit={canEdit}
                  canDelete={canDelete}
                  onView={setDetailProduct}
                  onEdit={setEditProduct}
                  onLifecycle={
                    setLifecycleProduct
                  }
                  onDelete={
                    setDeleteProductTarget
                  }
                />
              </div>

              {pagination ? (
                <div className="flex flex-col gap-3 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
                  <span>
                    Page {pagination.page} of{" "}
                    {pagination.pages || 1} ·{" "}
                    {pagination.total} products
                  </span>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      disabled={
                        !pagination.has_prev ||
                        productsQuery.isFetching
                      }
                      onClick={() =>
                        setPage((current) =>
                          Math.max(
                            current - 1,
                            1,
                          ),
                        )
                      }
                    >
                      Previous
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      disabled={
                        !pagination.has_next ||
                        productsQuery.isFetching
                      }
                      onClick={() =>
                        setPage((current) =>
                          current + 1,
                        )
                      }
                    >
                      Next
                    </Button>
                  </div>
                </div>
              ) : null}
            </div>
          )}
        </PageSection>
      </PageContent>

      <ProductFormDialog
        open={createOpen}
        isSubmitting={createProduct.isPending}
        errorMessage={getErrorMessage(
          createProduct.error,
        )}
        onOpenChange={setCreateOpen}
        onCreate={handleCreate}
      />

      <ProductEditDialog
        open={editProduct !== null}
        product={editProduct}
        isSubmitting={updateProduct.isPending}
        errorMessage={getErrorMessage(
          updateProduct.error,
        )}
        onOpenChange={(open) => {
          if (!open) {
            setEditProduct(null);
          }
        }}
        onSubmit={handleUpdate}
      />

      <ProductLifecycleDialog
        product={lifecycleProduct}
        isPending={lifecycleMutationPending}
        onOpenChange={(open) => {
          if (
            !open &&
            !lifecycleMutationPending
          ) {
            setLifecycleProduct(null);
          }
        }}
        onConfirm={handleLifecycleConfirm}
      />

      <ProductDeleteDialog
        product={deleteProductTarget}
        isPending={deleteProductMutation.isPending}
        errorMessage={getErrorMessage(
          deleteProductMutation.error,
        )}
        onOpenChange={(open) => {
          if (
            !open &&
            !deleteProductMutation.isPending
          ) {
            setDeleteProductTarget(null);
          }
        }}
        onConfirm={handleDeleteConfirm}
      />

      <ProductDetailDialog
        open={detailProduct !== null}
        product={detailProduct}
        onOpenChange={(open) => {
          if (!open) {
            setDetailProduct(null);
          }
        }}
      />
    </Page>
  );
}

export default ProductsPage;
