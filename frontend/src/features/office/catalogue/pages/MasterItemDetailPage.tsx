import {
  ArrowLeft,
  CheckCircle2,
} from "lucide-react";

import {
  useState,
} from "react";

import type {
  ReactNode,
} from "react";

import {
  Link,
  useParams,
} from "react-router-dom";

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
} from "@/components/page";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

import {
  Badge,
} from "@/components/ui/badge";

import {
  Button,
  buttonVariants,
} from "@/components/ui/button";

import {
  useApproveOfficeMasterItem,
  useOfficeMasterItem,
  useOfficeMasterItemSupplierEvidence,
} from "@/hooks/queries/office";

import {
  OFFICE_PATHS,
} from "@/routes/officeRoutes";

import type {
  OfficeMasterItem,
} from "@/types/officeCatalogue";

import {
  MasterItemSupplierEvidence,
} from "../components/MasterItemSupplierEvidence";


function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "Master Item could not be loaded.";
}


function displayValue(
  value: string | null,
  fallback = "Not specified",
): string {
  return value?.trim() || fallback;
}


function booleanLabel(
  value: boolean | null,
): string {
  if (value === null) {
    return "Not specified";
  }

  return value
    ? "Yes"
    : "No";
}


function packDescription(
  item: OfficeMasterItem,
): string {
  const quantity =
    item.pack_quantity?.trim();

  const unit =
    item.pack_unit?.trim();

  const type =
    item.pack_type?.trim();

  const base =
    [quantity, unit]
      .filter(Boolean)
      .join(" ");

  return [base, type]
    .filter(Boolean)
    .join(" · ") || "Not specified";
}


function statusLabel(
  value: string,
): string {
  return value
    .replace(/[_-]+/g, " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


export function MasterItemDetailPage() {
  const {
    masterItemId,
  } = useParams();

  const [
    approvalOpen,
    setApprovalOpen,
  ] = useState(false);

  const approveMasterItem =
    useApproveOfficeMasterItem();

  const masterItemQuery =
    useOfficeMasterItem(
      masterItemId,
    );


  const supplierEvidenceQuery =
    useOfficeMasterItemSupplierEvidence(
      masterItemId,
    );

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Master Item
          </PageTitle>

          <PageDescription>
            Inspect the canonical platform-owned
            catalogue identity and governance state.
          </PageDescription>
        </div>

        <PageActions>
          {masterItemQuery.data?.review_status
            === "draft" ? (
            <Button
              type="button"
              onClick={() =>
                setApprovalOpen(true)
              }
            >
              <CheckCircle2 />
              Approve
            </Button>
          ) : null}

          <Link
            to={
              OFFICE_PATHS.CATALOGUE.MASTER_ITEMS
            }
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Master Items
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        {!masterItemId ? (
          <PageSection>
            <EmptyState
              title="Master Item not selected"
              description="Open a Master Item from the catalogue to inspect it."
            />
          </PageSection>
        ) : masterItemQuery.isLoading ? (
          <PageSection>
            <LoadingState
              title="Loading Master Item"
            />
          </PageSection>
        ) : masterItemQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Master Item unavailable"
              description={errorMessage(
                masterItemQuery.error,
              )}
            />
          </PageSection>
        ) : masterItemQuery.data ? (
          <MasterItemDetail
            item={masterItemQuery.data}
            supplierEvidenceQuery={
              supplierEvidenceQuery
            }
          />
        ) : null}
      </PageContent>

      <AlertDialog
        open={approvalOpen}
        onOpenChange={(open) => {
          setApprovalOpen(open);

          if (!open) {
            approveMasterItem.reset();
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              Approve this Master Item?
            </AlertDialogTitle>

            <AlertDialogDescription>
              Approval confirms this canonical catalogue
              identity and makes it available for tenant
              catalogue consumption and adoption.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {approveMasterItem.isError ? (
            <div className="text-sm text-destructive">
              {errorMessage(
                approveMasterItem.error,
              )}
            </div>
          ) : null}

          <AlertDialogFooter>
            <AlertDialogCancel
              disabled={
                approveMasterItem.isPending
              }
            >
              Cancel
            </AlertDialogCancel>

            <AlertDialogAction
              type="button"
              disabled={
                approveMasterItem.isPending ||
                !masterItemId
              }
              onClick={() => {
                if (!masterItemId) {
                  return;
                }

                approveMasterItem.mutate(
                  masterItemId,
                  {
                    onSuccess: () => {
                      setApprovalOpen(false);
                    },
                  },
                );
              }}
            >
              {approveMasterItem.isPending
                ? "Approving..."
                : "Approve Master Item"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Page>
  );
}


type SupplierEvidenceQuery =
  ReturnType<
    typeof useOfficeMasterItemSupplierEvidence
  >;


function MasterItemDetail({
  item,
  supplierEvidenceQuery,
}: {
  item: OfficeMasterItem;
  supplierEvidenceQuery: SupplierEvidenceQuery;
}) {
  return (
    <>
      <PageSection>
        <div className="grid gap-4 lg:grid-cols-4">
          <DetailBlock
            label="Master Code"
            value={item.master_code}
          />

          <DetailBlock
            label="Canonical Name"
            value={item.canonical_name}
          />

          <DetailBlock
            label="Review Status"
            value={
              <Badge variant="outline">
                {statusLabel(
                  item.review_status,
                )}
              </Badge>
            }
          />

          <DetailBlock
            label="Lifecycle"
            value={
              <Badge
                variant={
                  item.is_active
                    ? "secondary"
                    : "outline"
                }
              >
                {item.is_active
                  ? "Active"
                  : "Inactive"}
              </Badge>
            }
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-4 lg:grid-cols-4">
          <DetailBlock
            label="Brand"
            value={displayValue(
              item.brand_name,
            )}
          />

          <DetailBlock
            label="Generic Name"
            value={displayValue(
              item.generic_name,
            )}
          />

          <DetailBlock
            label="Strength"
            value={displayValue(
              item.strength,
            )}
          />

          <DetailBlock
            label="Dosage Form"
            value={displayValue(
              item.dosage_form,
            )}
          />

          <DetailBlock
            label="Item Class"
            value={displayValue(
              item.item_class,
            )}
          />

          <DetailBlock
            label="Category"
            value={displayValue(
              item.category_name,
              "Uncategorized",
            )}
          />

          <DetailBlock
            label="Subcategory"
            value={displayValue(
              item.subcategory_name,
            )}
          />

          <DetailBlock
            label="Pack"
            value={packDescription(item)}
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-4 lg:grid-cols-4">
          <DetailBlock
            label="Manufacturer"
            value={displayValue(
              item.manufacturer,
            )}
          />

          <DetailBlock
            label="Country of Origin"
            value={displayValue(
              item.country_of_origin,
            )}
          />

          <DetailBlock
            label="Tax Classification"
            value={displayValue(
              item.tax_classification,
            )}
          />

          <DetailBlock
            label="Cold Chain"
            value={booleanLabel(
              item.cold_chain,
            )}
          />

          <DetailBlock
            label="Restricted Item"
            value={booleanLabel(
              item.restricted_item,
            )}
          />

          <DetailBlock
            label="Prescription Required"
            value={booleanLabel(
              item.requires_prescription,
            )}
          />
        </div>
      </PageSection>


      <PageSection>
        <div className="space-y-1">
          <h2 className="text-base font-semibold">
            Supplier Intelligence
          </h2>

          <p className="text-sm text-muted-foreground">
            Review supplier catalogue mappings, procurement-comparable
            prices, source evidence, and price history for this Master Item.
          </p>
        </div>

        <div className="mt-4">
          {supplierEvidenceQuery.isLoading ? (
            <LoadingState
              title="Loading supplier evidence"
            />
          ) : supplierEvidenceQuery.isError ? (
            <ErrorState
              title="Supplier evidence unavailable"
              description={errorMessage(
                supplierEvidenceQuery.error,
              )}
            />
          ) : supplierEvidenceQuery.data &&
            supplierEvidenceQuery.data.mapping_count > 0 ? (
            <MasterItemSupplierEvidence
              evidence={
                supplierEvidenceQuery.data
              }
            />
          ) : (
            <EmptyState
              title="No supplier evidence"
              description="No supplier catalogue mappings or price evidence are currently linked to this Master Item."
            />
          )}
        </div>
      </PageSection>
    </>
  );
}


function DetailBlock({
  label,
  value,
}: {
  label: string;
  value: ReactNode;
}) {
  return (
    <div className="space-y-1 rounded-md border p-3">
      <div className="text-xs uppercase text-muted-foreground">
        {label}
      </div>

      <div className="text-sm font-medium">
        {value}
      </div>
    </div>
  );
}


export default MasterItemDetailPage;
