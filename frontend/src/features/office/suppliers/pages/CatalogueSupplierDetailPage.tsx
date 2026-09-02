import {
  ArrowLeft,
} from "lucide-react";

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
  buttonVariants,
} from "@/components/ui/button";

import {
  useOfficeCatalogueSupplier,
} from "@/hooks/queries/office";

import {
  OFFICE_PATHS,
} from "@/routes/officeRoutes";

import type {
  OfficeCatalogueSupplierDetail,
} from "@/types/officeSupplier";

import {
  CatalogueSupplierMappingsTable,
} from "../components/CatalogueSupplierMappingsTable";


function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "Catalogue Supplier could not be loaded.";
}


function dateLabel(
  value: string | null,
): string {
  if (!value) {
    return "Not available";
  }

  return new Date(
    `${value}T00:00:00`,
  ).toLocaleDateString();
}


export function CatalogueSupplierDetailPage() {
  const {
    supplierId,
  } = useParams();

  const supplierQuery =
    useOfficeCatalogueSupplier(
      supplierId,
    );

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Catalogue Supplier
          </PageTitle>

          <PageDescription>
            Inspect supplier catalogue coverage,
            mapped Master Items and procurement
            evidence across Hela360.
          </PageDescription>
        </div>

        <PageActions>
          <Link
            to={
              OFFICE_PATHS
                .SUPPLIER_INTELLIGENCE
                .CATALOGUE_SUPPLIERS
            }
            className={buttonVariants({
              variant: "outline",
            })}
          >
            <ArrowLeft />
            Catalogue Suppliers
          </Link>
        </PageActions>
      </PageHeader>

      <PageContent>
        {!supplierId ? (
          <PageSection>
            <EmptyState
              title="Catalogue Supplier not selected"
              description="Open a Catalogue Supplier to inspect it."
            />
          </PageSection>
        ) : supplierQuery.isLoading ? (
          <PageSection>
            <LoadingState
              title="Loading Catalogue Supplier"
            />
          </PageSection>
        ) : supplierQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Catalogue Supplier unavailable"
              description={errorMessage(
                supplierQuery.error,
              )}
            />
          </PageSection>
        ) : supplierQuery.data ? (
          <CatalogueSupplierDetail
            supplier={supplierQuery.data}
          />
        ) : null}
      </PageContent>
    </Page>
  );
}


function CatalogueSupplierDetail({
  supplier,
}: {
  supplier: OfficeCatalogueSupplierDetail;
}) {
  return (
    <>
      <PageSection>
        <div className="grid gap-4 lg:grid-cols-4">
          <DetailBlock
            label="Supplier"
            value={supplier.name}
          />

          <DetailBlock
            label="Country"
            value={
              supplier.country ??
              "Not specified"
            }
          />

          <DetailBlock
            label="Lifecycle"
            value={
              supplier.is_active
                ? "Active"
                : "Inactive"
            }
          />

          <DetailBlock
            label="Procurement Status"
            value={
              supplier.procurement_comparable
                ? "Comparable"
                : "Evidence only"
            }
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <MetricBlock
            label="Mapped Items"
            value={supplier.mapping_count}
          />

          <MetricBlock
            label="Observations"
            value={
              supplier.price_observation_count
            }
          />

          <MetricBlock
            label="Comparable"
            value={
              supplier
                .comparable_observation_count
            }
          />

          <MetricBlock
            label="Evidence Only"
            value={
              supplier
                .non_comparable_observation_count
            }
          />

          <DetailBlock
            label="Latest Effective"
            value={dateLabel(
              supplier.latest_effective_date,
            )}
          />
        </div>
      </PageSection>

      <PageSection>
        <div className="mb-4">
          <h2 className="text-lg font-semibold">
            Mapped Master Items
          </h2>

          <p className="text-sm text-muted-foreground">
            Supplier listing identities and their
            latest valid procurement-comparable
            evidence.
          </p>
        </div>

        {supplier.mappings.length > 0 ? (
          <CatalogueSupplierMappingsTable
            mappings={supplier.mappings}
          />
        ) : (
          <EmptyState
            title="No mapped Master Items"
            description="This Catalogue Supplier has no Master Item mappings."
          />
        )}
      </PageSection>
    </>
  );
}


function DetailBlock({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>

      <p className="mt-2 font-medium">
        {value}
      </p>
    </div>
  );
}


function MetricBlock({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-lg border p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold">
        {value.toLocaleString()}
      </p>
    </div>
  );
}


export default CatalogueSupplierDetailPage;
