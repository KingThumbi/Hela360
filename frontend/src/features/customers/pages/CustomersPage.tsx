import {
  Plus,
  RefreshCw,
  Search,
  Users,
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
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthorization } from "@/hooks/useAuthorization";
import {
  useCreateCustomer,
  useCustomers,
} from "@/hooks/queries/customers";
import type { CreateCustomerRequest } from "@/types/requests";

import { CustomerDetailDialog } from "../components/CustomerDetailDialog";
import { CustomerFormDialog } from "../components/CustomerFormDialog";
import { CustomersTable } from "../components/CustomersTable";

const PAGE_SIZE = 25;

function getErrorMessage(
  error: unknown,
): string | null {
  return error instanceof Error
    ? error.message
    : null;
}

export function CustomersPage() {
  const authorization = useAuthorization();

  const canCreate = authorization.can(
    "customers.create",
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
    createOpen,
    setCreateOpen,
  ] = useState(false);
  const [
    detailCustomerId,
    setDetailCustomerId,
  ] = useState<string | null>(null);

  const params = useMemo(
    () => ({
      page,
      per_page: PAGE_SIZE,
      search:
        submittedSearch.trim().length > 0
          ? submittedSearch.trim()
          : undefined,
    }),
    [
      page,
      submittedSearch,
    ],
  );

  const customersQuery = useCustomers(params);
  const createCustomer = useCreateCustomer();

  const customers =
    customersQuery.data?.items ?? [];
  const pagination =
    customersQuery.data?.pagination;

  const handleSearchSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setPage(1);
    setSubmittedSearch(searchInput);
  };

  const handleCreate = (
    payload: CreateCustomerRequest,
  ) => {
    createCustomer.mutate(payload, {
      onSuccess: (customer) => {
        toast.success("Customer created.");
        setCreateOpen(false);
        setDetailCustomerId(customer.id);
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  };

  const isInitialLoading =
    customersQuery.isLoading &&
    customers.length === 0;
  const isSearchEmpty =
    submittedSearch.trim().length > 0 &&
    customers.length === 0;

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Customers</PageTitle>
          <PageDescription>
            Manage tenant customer master records for
            sales, account lookup, and pharmacy service
            continuity.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            type="button"
            variant="outline"
            onClick={() => customersQuery.refetch()}
            disabled={customersQuery.isFetching}
          >
            <RefreshCw
              className={
                customersQuery.isFetching
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
              Create Customer
            </Button>
          ) : null}
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageToolbar>
          <form
            className="flex w-full flex-col gap-2 sm:flex-row sm:items-center"
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
                placeholder="Search customers"
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
        </PageToolbar>

        <PageSection>
          {isInitialLoading ? (
            <LoadingState
              title="Loading customers"
              description="Retrieving tenant customer records."
            />
          ) : customersQuery.isError ? (
            <ErrorState
              title="Unable to load customers"
              description={
                getErrorMessage(
                  customersQuery.error,
                ) ??
                "Customer records could not be loaded."
              }
              onRetry={() =>
                customersQuery.refetch()
              }
            />
          ) : customers.length === 0 ? (
            <EmptyState
              icon={<Users className="h-12 w-12" />}
              title={
                isSearchEmpty
                  ? "No customers match your search"
                  : "No customers yet"
              }
              description={
                isSearchEmpty
                  ? "Try a different name, phone, email, customer number, or ID number."
                  : "Create the first customer record for this tenant."
              }
              actionLabel={
                !isSearchEmpty && canCreate
                  ? "Create Customer"
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
                <CustomersTable
                  customers={customers}
                  onView={(customer) =>
                    setDetailCustomerId(
                      customer.id,
                    )
                  }
                />
              </div>

              {pagination ? (
                <div className="flex flex-col gap-3 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
                  <span>
                    Page {pagination.page} of{" "}
                    {pagination.pages || 1} ·{" "}
                    {pagination.total} customers
                  </span>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      disabled={
                        !pagination.has_prev ||
                        customersQuery.isFetching
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
                        customersQuery.isFetching
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

      <CustomerFormDialog
        open={createOpen}
        isSubmitting={createCustomer.isPending}
        errorMessage={getErrorMessage(
          createCustomer.error,
        )}
        onOpenChange={setCreateOpen}
        onCreate={handleCreate}
      />

      <CustomerDetailDialog
        open={detailCustomerId !== null}
        customerId={detailCustomerId}
        onOpenChange={(open) => {
          if (!open) {
            setDetailCustomerId(null);
          }
        }}
      />
    </Page>
  );
}

export default CustomersPage;
