import {
  Library,
  RefreshCw,
  Search,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import {
  toast,
} from "sonner";

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

import {
  Button,
} from "@/components/ui/button";

import {
  Input,
} from "@/components/ui/input";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  useAdoptCatalogueItem,
  useCatalogueItems,
} from "@/hooks/queries/catalogue";

import {
  useProduct,
} from "@/hooks/queries/products";

import {
  useAuthorization,
} from "@/hooks/useAuthorization";

import {
  AppError,
} from "@/lib/errors";

import type {
  CatalogueItem,
} from "@/types/entities";

import type {
  AdoptCatalogueItemRequest,
  CatalogueAdoptionStatus,
} from "@/types/requests";

import {
  ProductDetailDialog,
} from "../../components/ProductDetailDialog";

import {
  AdoptCatalogueItemDialog,
} from "../components/AdoptCatalogueItemDialog";

import {
  CatalogueItemsTable,
} from "../components/CatalogueItemsTable";


const DEFAULT_PAGE_SIZE = 25;

type AdoptionFilter =
  CatalogueAdoptionStatus;


function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "We couldn't load the Master Catalogue.";
}


export function MasterCataloguePage() {
  const authorization =
    useAuthorization();

  const canCreate =
    authorization.can(
      "products.create",
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
    adoptionStatus,
    setAdoptionStatus,
  ] = useState<AdoptionFilter>("all");

  const [
    adoptionItem,
    setAdoptionItem,
  ] = useState<CatalogueItem | null>(
    null,
  );

  const [
    viewedProductId,
    setViewedProductId,
  ] = useState("");

  const [
    productDialogOpen,
    setProductDialogOpen,
  ] = useState(false);


  const params = useMemo(
    () => ({
      page,

      per_page: DEFAULT_PAGE_SIZE,

      search:
        submittedSearch.trim().length > 0
          ? submittedSearch.trim()
          : undefined,

      adoption_status:
        adoptionStatus,
    }),
    [
      adoptionStatus,
      page,
      submittedSearch,
    ],
  );


  const catalogueQuery =
    useCatalogueItems(params);

  const adoptMutation =
    useAdoptCatalogueItem();

  const productQuery =
    useProduct(
      viewedProductId,
      {
        enabled:
          productDialogOpen &&
          viewedProductId.length > 0,
      },
    );


  const items =
    catalogueQuery.data?.items ?? [];

  const pagination =
    catalogueQuery.data?.pagination;


  const handleSearchSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setPage(1);

    setSubmittedSearch(
      searchInput.trim(),
    );
  };


  const handleViewProduct = (
    item: CatalogueItem,
  ) => {
    const productId =
      item.adoption.product_id;

    if (!productId) {
      toast.error(
        "The linked Product could not be identified.",
      );

      return;
    }

    setViewedProductId(productId);

    setProductDialogOpen(true);
  };


  const handleAdoptionSubmit = (
    payload: AdoptCatalogueItemRequest,
  ) => {
    if (!adoptionItem) {
      return;
    }

    adoptMutation.mutate(
      {
        masterItemId:
          adoptionItem.id,

        data: payload,
      },
      {
        onSuccess: (product) => {
          toast.success(
            "Product added to your catalogue.",
          );

          setAdoptionItem(null);

          setViewedProductId(
            product.id,
          );

          setProductDialogOpen(true);
        },

        onError: (error) => {
          if (
            error instanceof AppError &&
            error.code ===
              "master_item_already_adopted"
          ) {
            toast.info(
              "This item is already in your Product catalogue.",
            );

            setAdoptionItem(null);

            void catalogueQuery.refetch();

            return;
          }

          toast.error(
            errorMessage(error),
          );
        },
      },
    );
  };


  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Master Catalogue
          </PageTitle>

          <PageDescription>
            Browse approved Hela360 catalogue
            items and add them to your
            Product catalogue.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              catalogueQuery.refetch()
            }
            disabled={
              catalogueQuery.isFetching
            }
          >
            <RefreshCw
              className={
                catalogueQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageToolbar>
          <form
            onSubmit={handleSearchSubmit}
            className="flex flex-1 gap-2"
          >
            <div className="relative flex-1">
              <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />

              <Input
                value={searchInput}
                onChange={(event) =>
                  setSearchInput(
                    event.target.value,
                  )
                }
                placeholder="Search catalogue items"
                className="pl-9"
              />
            </div>

            <Button type="submit">
              Search
            </Button>
          </form>

          <Select
            value={adoptionStatus}
            onValueChange={(value) => {
              setPage(1);

              setAdoptionStatus(
                value as AdoptionFilter,
              );
            }}
          >
            <SelectTrigger className="w-[190px]">
              <SelectValue />
            </SelectTrigger>

            <SelectContent>
              <SelectItem value="all">
                All items
              </SelectItem>

              <SelectItem value="available">
                Available
              </SelectItem>

              <SelectItem value="adopted">
                Already added
              </SelectItem>
            </SelectContent>
          </Select>
        </PageToolbar>

        <PageSection>
          {catalogueQuery.isLoading &&
          items.length === 0 ? (
            <LoadingState
              title="Loading catalogue"
              description="Getting approved catalogue items ready."
            />
          ) : catalogueQuery.isError ? (
            <ErrorState
              title="Unable to load catalogue"
              description={errorMessage(
                catalogueQuery.error,
              )}
              onRetry={() =>
                catalogueQuery.refetch()
              }
            />
          ) : items.length === 0 ? (
            <EmptyState
              icon={<Library />}
              title="No catalogue items found"
              description={
                submittedSearch
                  ? "No catalogue items match your search."
                  : "No approved catalogue items match the current filter."
              }
            />
          ) : (
            <div className="space-y-4">
              <CatalogueItemsTable
                items={items}
                canCreate={canCreate}
                onAdopt={
                  setAdoptionItem
                }
                onViewProduct={
                  handleViewProduct
                }
              />

              {pagination ? (
                <div className="flex items-center justify-between border-t pt-4">
                  <div className="text-sm text-muted-foreground">
                    Page {pagination.page} of{" "}
                    {pagination.pages || 1} ·{" "}
                    {pagination.total} items
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={
                        !pagination.has_prev ||
                        catalogueQuery.isFetching
                      }
                      onClick={() =>
                        setPage((current) =>
                          Math.max(
                            1,
                            current - 1,
                          ),
                        )
                      }
                    >
                      Previous
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      disabled={
                        !pagination.has_next ||
                        catalogueQuery.isFetching
                      }
                      onClick={() =>
                        setPage(
                          (current) =>
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

      <AdoptCatalogueItemDialog
        key={adoptionItem?.id ?? "closed"}
        open={Boolean(adoptionItem)}
        item={adoptionItem}
        isPending={
          adoptMutation.isPending
        }
        onOpenChange={(open) => {
          if (
            !open &&
            !adoptMutation.isPending
          ) {
            setAdoptionItem(null);
          }
        }}
        onSubmit={
          handleAdoptionSubmit
        }
      />

      <ProductDetailDialog
        open={productDialogOpen}
        product={
          productQuery.data ?? null
        }
        onOpenChange={(open) => {
          setProductDialogOpen(open);

          if (!open) {
            setViewedProductId("");
          }
        }}
      />
    </Page>
  );
}


export default MasterCataloguePage;
