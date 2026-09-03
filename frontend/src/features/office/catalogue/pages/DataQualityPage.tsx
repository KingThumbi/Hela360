import {
  RefreshCw,
} from "lucide-react";

import {
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
  Button,
} from "@/components/ui/button";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  useOfficeCatalogueDataQuality,
} from "@/hooks/queries/office";


function formatCount(
  value: number,
): string {
  return new Intl.NumberFormat().format(
    value,
  );
}


function coveragePercent(
  value: number,
  total: number,
): number {
  if (total <= 0) {
    return 0;
  }

  return Math.round(
    (value / total) * 100,
  );
}


function errorMessage(
  error: unknown,
): string {
  return error instanceof Error
    ? error.message
    : "Catalogue data quality could not be loaded.";
}


function SummaryCard({
  label,
  value,
  description,
}: {
  label: string;
  value: number;
  description: string;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {label}
        </CardTitle>

        <CardDescription>
          {description}
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="text-3xl font-semibold tracking-tight">
          {formatCount(value)}
        </div>
      </CardContent>
    </Card>
  );
}


function CoverageRow({
  label,
  populated,
  missing,
  total,
}: {
  label: string;
  populated: number;
  missing: number;
  total: number;
}) {
  const percent =
    coveragePercent(
      populated,
      total,
    );

  return (
    <div className="space-y-2 border-b py-4 last:border-b-0">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium">
            {label}
          </p>

          <p className="text-sm text-muted-foreground">
            {formatCount(populated)} populated ·{" "}
            {formatCount(missing)} outstanding
          </p>
        </div>

        <div className="text-sm font-medium">
          {percent}%
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-foreground transition-[width]"
          style={{
            width: `${percent}%`,
          }}
        />
      </div>
    </div>
  );
}


function ProvenanceRow({
  label,
  count,
  total,
  description,
}: {
  label: string;
  count: number;
  total: number;
  description: string;
}) {
  const percent =
    coveragePercent(
      count,
      total,
    );

  return (
    <div className="space-y-2 border-b py-4 last:border-b-0">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-medium">
            {label}
          </p>

          <p className="text-sm text-muted-foreground">
            {description}
          </p>
        </div>

        <div className="text-right">
          <p className="font-medium">
            {formatCount(count)}
          </p>

          <p className="text-xs text-muted-foreground">
            {percent}% of catalogue
          </p>
        </div>
      </div>

      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-foreground transition-[width]"
          style={{
            width: `${percent}%`,
          }}
        />
      </div>
    </div>
  );
}


export function DataQualityPage() {
  const dataQualityQuery =
    useOfficeCatalogueDataQuality();

  const summary =
    dataQualityQuery.data;

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Data Quality
          </PageTitle>

          <PageDescription>
            Review objective catalogue completeness,
            enrichment, provenance, and governance
            observations.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              dataQualityQuery.refetch()
            }
            disabled={
              dataQualityQuery.isFetching
            }
          >
            <RefreshCw
              className={
                dataQualityQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        {dataQualityQuery.isLoading ? (
          <PageSection>
            <LoadingState
              title="Loading catalogue data quality"
            />
          </PageSection>
        ) : dataQualityQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Data quality unavailable"
              description={errorMessage(
                dataQualityQuery.error,
              )}
            />
          </PageSection>
        ) : summary ? (
          <>
            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Catalogue baseline
                </h2>

                <p className="text-sm text-muted-foreground">
                  Current platform catalogue governance
                  and lifecycle totals.
                </p>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                <SummaryCard
                  label="Master Items"
                  value={summary.catalogue.total}
                  description="Total platform catalogue identities."
                />

                <SummaryCard
                  label="Approved"
                  value={summary.catalogue.approved}
                  description="Governed catalogue identities."
                />

                <SummaryCard
                  label="Draft"
                  value={summary.catalogue.draft}
                  description="Awaiting catalogue review."
                />

                <SummaryCard
                  label="Active"
                  value={summary.catalogue.active}
                  description="Active Master Items."
                />

                <SummaryCard
                  label="Inactive"
                  value={summary.catalogue.inactive}
                  description="Retained but inactive identities."
                />
              </div>
            </PageSection>

            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Enrichment coverage
                </h2>

                <p className="text-sm text-muted-foreground">
                  Optional metadata coverage. Outstanding
                  values represent enrichment opportunities,
                  not invalid catalogue records.
                </p>
              </div>

              <Card className="mt-4">
                <CardContent>
                  <CoverageRow
                    label="Category"
                    populated={
                      summary.enrichment.categorized
                    }
                    missing={
                      summary.enrichment.uncategorized
                    }
                    total={summary.catalogue.total}
                  />

                  <CoverageRow
                    label="Item class"
                    populated={
                      summary.enrichment.classified
                    }
                    missing={
                      summary.enrichment.unclassified
                    }
                    total={summary.catalogue.total}
                  />

                  <CoverageRow
                    label="Dosage form"
                    populated={
                      summary.enrichment
                        .dosage_form_populated
                    }
                    missing={
                      summary.enrichment
                        .dosage_form_missing
                    }
                    total={summary.catalogue.total}
                  />

                  <CoverageRow
                    label="Complete pack definition"
                    populated={
                      summary.enrichment
                        .complete_pack_definition
                    }
                    missing={
                      summary.enrichment
                        .incomplete_pack_definition
                    }
                    total={summary.catalogue.total}
                  />

                  <CoverageRow
                    label="Generic name"
                    populated={
                      summary.enrichment
                        .generic_name_populated
                    }
                    missing={
                      summary.enrichment
                        .generic_name_missing
                    }
                    total={summary.catalogue.total}
                  />

                  <CoverageRow
                    label="Manufacturer"
                    populated={
                      summary.enrichment
                        .manufacturer_populated
                    }
                    missing={
                      summary.enrichment
                        .manufacturer_missing
                    }
                    total={summary.catalogue.total}
                  />
                </CardContent>
              </Card>
            </PageSection>

            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Supplier provenance
                </h2>

                <p className="text-sm text-muted-foreground">
                  Coverage of supplier mapping and commercial
                  source evidence across the Master Catalogue.
                </p>
              </div>

              <Card className="mt-4">
                <CardContent>
                  <ProvenanceRow
                    label="Supplier mapping"
                    count={
                      summary.provenance
                        .with_supplier_mapping
                    }
                    total={summary.catalogue.total}
                    description="Master Items linked to at least one catalogue supplier listing."
                  />

                  <ProvenanceRow
                    label="Price evidence"
                    count={
                      summary.provenance
                        .with_price_evidence
                    }
                    total={summary.catalogue.total}
                    description="Master Items with recorded supplier price observations."
                  />

                  <ProvenanceRow
                    label="Comparable procurement evidence"
                    count={
                      summary.provenance
                        .with_comparable_evidence
                    }
                    total={summary.catalogue.total}
                    description="Master Items with supplier observations explicitly marked procurement-comparable."
                  />

                  <ProvenanceRow
                    label="Dated comparable evidence"
                    count={
                      summary.provenance
                        .with_dated_comparable_evidence
                    }
                    total={summary.catalogue.total}
                    description="Master Items with dated procurement-comparable supplier evidence."
                  />
                </CardContent>
              </Card>
            </PageSection>
          </>
        ) : null}
      </PageContent>
    </Page>
  );
}


export default DataQualityPage;
