import {
  RefreshCw,
  Search,
  Truck,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

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
  useOfficeCatalogueSuppliers,
} from "@/hooks/queries/office";

import {
  CatalogueSuppliersTable,
} from "../components/CatalogueSuppliersTable";


const DEFAULT_PAGE_SIZE = 25;


type ActiveFilter =
  | "all"
  | "active"
  | "inactive";


function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "We couldn't load catalogue suppliers.";
}


export function CatalogueSuppliersPage() {
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
    activeFilter,
    setActiveFilter,
  ] = useState<ActiveFilter>("all");


  const params = useMemo(
    () => ({
      page,

      per_page:
        DEFAULT_PAGE_SIZE,

      search:
        submittedSearch.trim().length > 0
          ? submittedSearch.trim()
          : undefined,

      is_active:
        activeFilter === "active"
          ? true
          : activeFilter === "inactive"
            ? false
            : undefined,
    }),
    [
      activeFilter,
      page,
      submittedSearch,
    ],
  );


  const suppliersQuery =
    useOfficeCatalogueSuppliers(
      params,
    );


  const suppliers =
    suppliersQuery.data?.items ?? [];

  const pagination =
    suppliersQuery.data?.pagination;


  const handleSearchSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setPage(1);

    setSubmittedSearch(
      searchInput.trim(),
    );
  };


  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Catalogue Suppliers
          </PageTitle>

          <PageDescription>
            Inspect platform-owned supplier
            catalogue coverage and commercial
            price evidence across the Hela360
            Master Catalogue.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              suppliersQuery.refetch()
            }
            disabled={
              suppliersQuery.isFetching
            }
          >
            <RefreshCw
              className={
                suppliersQuery.isFetching
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
            className="flex min-w-64 flex-1 gap-2"
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
                placeholder="Search catalogue suppliers"
                className="pl-9"
              />
            </div>

            <Button type="submit">
              Search
            </Button>
          </form>

          <Select
            value={activeFilter}
            onValueChange={(value) => {
              setPage(1);

              setActiveFilter(
                value as ActiveFilter,
              );
            }}
          >
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>

            <SelectContent>
              <SelectItem value="all">
                All lifecycle
              </SelectItem>

              <SelectItem value="active">
                Active
              </SelectItem>

              <SelectItem value="inactive">
                Inactive
              </SelectItem>
            </SelectContent>
          </Select>
        </PageToolbar>

        <PageSection>
          {suppliersQuery.isLoading &&
          suppliers.length === 0 ? (
            <LoadingState
              title="Loading Catalogue Suppliers"
              description="Preparing supplier catalogue coverage and evidence metrics."
            />
          ) : suppliersQuery.isError ? (
            <ErrorState
              title="Unable to load Catalogue Suppliers"
              description={errorMessage(
                suppliersQuery.error,
              )}
              onRetry={() =>
                suppliersQuery.refetch()
              }
            />
          ) : suppliers.length === 0 ? (
            <EmptyState
              icon={<Truck />}
              title="No Catalogue Suppliers found"
              description={
                submittedSearch
                  ? "No Catalogue Suppliers match your search."
                  : "No Catalogue Suppliers match the current lifecycle filter."
              }
            />
          ) : (
            <div className="space-y-4">
              <CatalogueSuppliersTable
                suppliers={suppliers}
              />

              {pagination ? (
                <div className="flex items-center justify-between border-t pt-4">
                  <div className="text-sm text-muted-foreground">
                    Page {pagination.page} of{" "}
                    {pagination.pages || 1} ·{" "}
                    {pagination.total} suppliers
                  </div>

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={
                        !pagination.has_prev ||
                        suppliersQuery.isFetching
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
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={
                        !pagination.has_next ||
                        suppliersQuery.isFetching
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
    </Page>
  );
}


export default CatalogueSuppliersPage;
