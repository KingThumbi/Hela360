import {
  Plus,
  RefreshCw,
  Search,
  Truck,
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
  useCreateSupplier,
  useDeleteSupplier,
  useReactivateSupplier,
  useSuppliers,
  useUpdateSupplier,
} from "@/hooks/queries/suppliers";
import type { Supplier } from "@/types/entities";
import type {
  CreateSupplierRequest,
  UpdateSupplierRequest,
} from "@/types/requests";

import { SupplierDetailDialog } from "../components/SupplierDetailDialog";
import { SupplierFormDialog } from "../components/SupplierFormDialog";
import { SupplierLifecycleDialog } from "../components/SupplierLifecycleDialog";
import { SuppliersTable } from "../components/SuppliersTable";

const PAGE_SIZE = 25;

type FormDialogState =
  | {
      mode: "create";
      supplier: null;
    }
  | {
      mode: "edit";
      supplier: Supplier;
    }
  | null;

function getErrorMessage(
  error: unknown,
): string | null {
  return error instanceof Error
    ? error.message
    : null;
}

export function SuppliersPage() {
  const authorization = useAuthorization();

  const canCreate = authorization.can(
    "suppliers.create",
  );
  const canUpdate = authorization.can(
    "suppliers.update",
  );
  const canManageLifecycle = authorization.can(
    "suppliers.deactivate",
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
    formDialog,
    setFormDialog,
  ] = useState<FormDialogState>(null);
  const [
    detailSupplier,
    setDetailSupplier,
  ] = useState<Supplier | null>(null);
  const [
    lifecycleSupplier,
    setLifecycleSupplier,
  ] = useState<Supplier | null>(null);

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

  const suppliersQuery = useSuppliers(params);
  const createSupplier = useCreateSupplier();
  const updateSupplier = useUpdateSupplier();
  const deactivateSupplier = useDeleteSupplier();
  const reactivateSupplier =
    useReactivateSupplier();

  const suppliers =
    suppliersQuery.data?.items ?? [];
  const pagination =
    suppliersQuery.data?.pagination;

  const mutationError =
    getErrorMessage(createSupplier.error) ??
    getErrorMessage(updateSupplier.error);

  const lifecyclePending =
    deactivateSupplier.isPending ||
    reactivateSupplier.isPending;

  const handleSearchSubmit = (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setPage(1);
    setSubmittedSearch(searchInput);
  };

  const handleCreate = (
    payload: CreateSupplierRequest,
  ) => {
    createSupplier.mutate(payload, {
      onSuccess: () => {
        toast.success("Supplier created.");
        setFormDialog(null);
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  };

  const handleUpdate = (
    supplierId: string,
    payload: UpdateSupplierRequest,
  ) => {
    updateSupplier.mutate(
      {
        id: supplierId,
        data: payload,
      },
      {
        onSuccess: () => {
          toast.success("Supplier updated.");
          setFormDialog(null);
        },
        onError: (error) => {
          toast.error(error.message);
        },
      },
    );
  };

  const handleLifecycleConfirm = () => {
    if (!lifecycleSupplier) {
      return;
    }

    const mutation = lifecycleSupplier.is_active
      ? deactivateSupplier
      : reactivateSupplier;

    mutation.mutate(lifecycleSupplier.id, {
      onSuccess: () => {
        toast.success(
          lifecycleSupplier.is_active
            ? "Supplier deactivated."
            : "Supplier reactivated.",
        );
        setLifecycleSupplier(null);
      },
      onError: (error) => {
        toast.error(error.message);
      },
    });
  };

  const isInitialLoading =
    suppliersQuery.isLoading && suppliers.length === 0;
  const isSearchEmpty =
    submittedSearch.trim().length > 0 &&
    suppliers.length === 0;

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>Suppliers</PageTitle>
          <PageDescription>
            Manage tenant-wide supplier master records
            for purchasing and replenishment operations.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            type="button"
            variant="outline"
            onClick={() => suppliersQuery.refetch()}
            disabled={suppliersQuery.isFetching}
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

          {canCreate ? (
            <Button
              type="button"
              onClick={() =>
                setFormDialog({
                  mode: "create",
                  supplier: null,
                })
              }
            >
              <Plus />
              Create Supplier
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
                placeholder="Search suppliers"
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
              title="Loading suppliers"
              description="Retrieving tenant supplier records."
            />
          ) : suppliersQuery.isError ? (
            <ErrorState
              title="Unable to load suppliers"
              description={
                getErrorMessage(
                  suppliersQuery.error,
                ) ??
                "Supplier records could not be loaded."
              }
              onRetry={() =>
                suppliersQuery.refetch()
              }
            />
          ) : suppliers.length === 0 ? (
            <EmptyState
              icon={<Truck className="h-12 w-12" />}
              title={
                isSearchEmpty
                  ? "No suppliers match your search"
                  : "No suppliers yet"
              }
              description={
                isSearchEmpty
                  ? "Try a different supplier name, code, contact, phone, or email."
                  : "Create the first supplier record for this tenant."
              }
              actionLabel={
                !isSearchEmpty && canCreate
                  ? "Create Supplier"
                  : undefined
              }
              onAction={
                !isSearchEmpty && canCreate
                  ? () =>
                      setFormDialog({
                        mode: "create",
                        supplier: null,
                      })
                  : undefined
              }
            />
          ) : (
            <div className="space-y-4">
              <div className="rounded-lg border bg-background">
                <SuppliersTable
                  suppliers={suppliers}
                  canUpdate={canUpdate}
                  canManageLifecycle={
                    canManageLifecycle
                  }
                  onView={setDetailSupplier}
                  onEdit={(supplier) =>
                    setFormDialog({
                      mode: "edit",
                      supplier,
                    })
                  }
                  onLifecycle={
                    setLifecycleSupplier
                  }
                />
              </div>

              {pagination ? (
                <div className="flex flex-col gap-3 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
                  <span>
                    Page {pagination.page} of{" "}
                    {pagination.pages || 1} ·{" "}
                    {pagination.total} suppliers
                  </span>
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      disabled={
                        !pagination.has_prev ||
                        suppliersQuery.isFetching
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

      <SupplierFormDialog
        open={formDialog !== null}
        mode={formDialog?.mode ?? "create"}
        supplier={formDialog?.supplier ?? null}
        isSubmitting={
          createSupplier.isPending ||
          updateSupplier.isPending
        }
        errorMessage={mutationError}
        onOpenChange={(open) => {
          if (!open) {
            setFormDialog(null);
          }
        }}
        onCreate={handleCreate}
        onUpdate={handleUpdate}
      />

      <SupplierDetailDialog
        open={detailSupplier !== null}
        supplier={detailSupplier}
        onOpenChange={(open) => {
          if (!open) {
            setDetailSupplier(null);
          }
        }}
      />

      <SupplierLifecycleDialog
        supplier={lifecycleSupplier}
        isPending={lifecyclePending}
        onOpenChange={(open) => {
          if (!open) {
            setLifecycleSupplier(null);
          }
        }}
        onConfirm={handleLifecycleConfirm}
      />
    </Page>
  );
}

export default SuppliersPage;
