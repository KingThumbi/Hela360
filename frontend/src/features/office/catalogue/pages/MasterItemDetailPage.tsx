import {
  ArrowLeft,
} from "lucide-react";

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
  Badge,
} from "@/components/ui/badge";

import {
  buttonVariants,
} from "@/components/ui/button";

import {
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
