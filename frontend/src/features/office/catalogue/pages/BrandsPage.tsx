import {
  BadgeCheck,
  RefreshCw,
} from "lucide-react";

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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import {
  useOfficeCatalogueBrands,
} from "@/hooks/queries/office";

import type {
  OfficeCatalogueBrandSummary,
} from "@/types/officeCatalogue";


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
    : "Catalogue brands could not be loaded.";
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


export function BrandsPage() {
  const brandsQuery =
    useOfficeCatalogueBrands();

  const summary =
    brandsQuery.data;

  const brands =
    summary?.brands ?? [];

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Brands
          </PageTitle>

          <PageDescription>
            Review brand names currently referenced
            by the Hela360 Master Catalogue.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              brandsQuery.refetch()
            }
            disabled={
              brandsQuery.isFetching
            }
          >
            <RefreshCw
              className={
                brandsQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        {brandsQuery.isLoading ? (
          <PageSection>
            <LoadingState
              title="Loading catalogue brands"
              description="Building the current Master Catalogue brand distribution."
            />
          </PageSection>
        ) : brandsQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Brands unavailable"
              description={errorMessage(
                brandsQuery.error,
              )}
            />
          </PageSection>
        ) : summary ? (
          <>
            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Brand coverage
                </h2>

                <p className="text-sm text-muted-foreground">
                  Brand coverage is derived from
                  Master Item metadata and does not
                  represent tenant Brand records.
                </p>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <SummaryCard
                  label="Master Items"
                  value={summary.total_items}
                  description="Total platform catalogue identities."
                />

                <SummaryCard
                  label="Branded"
                  value={summary.branded_items}
                  description={`${coveragePercent(
                    summary.branded_items,
                    summary.total_items,
                  )}% of the Master Catalogue.`}
                />

                <SummaryCard
                  label="Unbranded"
                  value={summary.unbranded_items}
                  description="Items without recorded brand metadata."
                />

                <SummaryCard
                  label="Brand Names"
                  value={summary.brand_count}
                  description="Distinct brand strings currently in use."
                />
              </div>
            </PageSection>

            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Brand distribution
                </h2>

                <p className="text-sm text-muted-foreground">
                  Observational view of brand usage,
                  review state, and lifecycle across
                  the Master Catalogue.
                </p>
              </div>

              {brands.length === 0 ? (
                <div className="mt-4">
                  <EmptyState
                    icon={<BadgeCheck />}
                    title="No brands recorded"
                    description="No Master Items currently contain brand metadata."
                  />
                </div>
              ) : (
                <Card className="mt-4">
                  <CardContent className="px-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>
                            Brand
                          </TableHead>

                          <TableHead className="text-right">
                            Items
                          </TableHead>

                          <TableHead className="text-right">
                            Approved
                          </TableHead>

                          <TableHead className="text-right">
                            Draft
                          </TableHead>

                          <TableHead className="text-right">
                            Active
                          </TableHead>

                          <TableHead className="text-right">
                            Inactive
                          </TableHead>
                        </TableRow>
                      </TableHeader>

                      <TableBody>
                        {brands.map(
                          (
                            brand: OfficeCatalogueBrandSummary,
                          ) => (
                            <TableRow
                              key={brand.name}
                            >
                              <TableCell>
                                <div className="min-w-56">
                                  <p className="font-medium">
                                    {brand.name}
                                  </p>
                                </div>
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  brand.item_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  brand.approved_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  brand.draft_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  brand.active_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  brand.inactive_count,
                                )}
                              </TableCell>
                            </TableRow>
                          ),
                        )}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}
            </PageSection>
          </>
        ) : null}
      </PageContent>
    </Page>
  );
}


export default BrandsPage;
