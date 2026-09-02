import {
  ClipboardCheck,
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

const REVIEW_STATUS = "draft";


type ActiveFilter =
  | "all"
  | "active"
  | "inactive";


function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "The catalogue review queue could not be loaded.";
}


export function ReviewQueuePage() {
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

      review_status:
        REVIEW_STATUS,

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


  const reviewQueueQuery =
    useOfficeMasterItems(
      params,
    );


  const items =
    reviewQueueQuery.data?.items ?? [];

  const pagination =
    reviewQueueQuery.data?.pagination;


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
            Review Queue
          </PageTitle>

          <PageDescription>
            Review draft Master Items awaiting
            human catalogue governance before
            approval.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              reviewQueueQuery.refetch()
            }
            disabled={
              reviewQueueQuery.isFetching
            }
          >
            <RefreshCw
              className={
                reviewQueueQuery.isFetching
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
                placeholder="Search pending Master Items"
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
          {reviewQueueQuery.isLoading &&
          items.length === 0 ? (
            <LoadingState
              title="Loading Review Queue"
              description="Checking for draft Master Items awaiting governance."
            />
          ) : reviewQueueQuery.isError ? (
            <ErrorState
              title="Unable to load Review Queue"
              description={errorMessage(
                reviewQueueQuery.error,
              )}
              onRetry={() =>
                reviewQueueQuery.refetch()
              }
            />
          ) : items.length === 0 ? (
            <EmptyState
              icon={<ClipboardCheck />}
              title={
                submittedSearch
                  ? "No pending items match your search"
                  : "Review Queue is clear"
              }
              description={
                submittedSearch
                  ? "No draft Master Items match the current search and lifecycle filter."
                  : "There are currently no draft Master Items awaiting catalogue governance."
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
                    {pagination.total} pending items
                  </div>

                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={
                        !pagination.has_prev ||
                        reviewQueueQuery.isFetching
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
                        reviewQueueQuery.isFetching
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


export default ReviewQueuePage;
