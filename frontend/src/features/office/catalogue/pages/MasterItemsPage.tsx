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
  useOfficeMasterItems,
} from "@/hooks/queries/office";

import {
  MasterItemsTable,
} from "../components/MasterItemsTable";


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
    : "We couldn't load the Hela360 Master Catalogue.";
}


export function MasterItemsPage() {
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
    reviewStatus,
    setReviewStatus,
  ] = useState("all");

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

      review_status:
        reviewStatus !== "all"
          ? reviewStatus
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
      reviewStatus,
      submittedSearch,
    ],
  );


  const masterItemsQuery =
    useOfficeMasterItems(params);


  const items =
    masterItemsQuery.data?.items ?? [];

  const pagination =
    masterItemsQuery.data?.pagination;


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
            Master Items
          </PageTitle>

          <PageDescription>
            Govern the platform-owned Hela360
            Master Catalogue and its canonical
            item identities.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              masterItemsQuery.refetch()
            }
            disabled={
              masterItemsQuery.isFetching
            }
          >
            <RefreshCw
              className={
                masterItemsQuery.isFetching
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
                placeholder="Search master items"
                className="pl-9"
              />
            </div>

            <Button type="submit">
              Search
            </Button>
          </form>

          <Select
            value={reviewStatus}
            onValueChange={(value) => {
              setPage(1);
              setReviewStatus(
                value ?? "all",
              );
            }}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>

            <SelectContent>
              <SelectItem value="all">
                All review states
              </SelectItem>

              <SelectItem value="draft">
                Draft
              </SelectItem>

              <SelectItem value="approved">
                Approved
              </SelectItem>
            </SelectContent>
          </Select>

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
          {masterItemsQuery.isLoading &&
          items.length === 0 ? (
            <LoadingState
              title="Loading Master Items"
              description="Getting platform catalogue records ready."
            />
          ) : masterItemsQuery.isError ? (
            <ErrorState
              title="Unable to load Master Items"
              description={errorMessage(
                masterItemsQuery.error,
              )}
              onRetry={() =>
                masterItemsQuery.refetch()
              }
            />
          ) : items.length === 0 ? (
            <EmptyState
              icon={<Library />}
              title="No Master Items found"
              description={
                submittedSearch
                  ? "No Master Items match your search."
                  : "No Master Items match the current governance filters."
              }
            />
          ) : (
            <div className="space-y-4">
              <MasterItemsTable
                items={items}
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
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={
                        !pagination.has_prev ||
                        masterItemsQuery.isFetching
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
                        masterItemsQuery.isFetching
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


export default MasterItemsPage;
