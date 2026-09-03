import {
  Layers3,
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
  Badge,
} from "@/components/ui/badge";

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
  useOfficeCatalogueCategories,
} from "@/hooks/queries/office";

import type {
  OfficeCatalogueCategorySummary,
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
    : "Catalogue categories could not be loaded.";
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


function SubcategoryBadges({
  category,
}: {
  category: OfficeCatalogueCategorySummary;
}) {
  if (category.subcategories.length === 0) {
    return (
      <span className="text-sm text-muted-foreground">
        None recorded
      </span>
    );
  }

  return (
    <div className="flex max-w-xl flex-wrap gap-2">
      {category.subcategories.map(
        (subcategory) => (
          <Badge
            key={subcategory.name}
            variant="outline"
          >
            {subcategory.name}
            {" · "}
            {formatCount(
              subcategory.item_count,
            )}
          </Badge>
        ),
      )}
    </div>
  );
}


export function CategoriesPage() {
  const categoriesQuery =
    useOfficeCatalogueCategories();

  const summary =
    categoriesQuery.data;

  const categories =
    summary?.categories ?? [];

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Categories
          </PageTitle>

          <PageDescription>
            Review the category and subcategory
            structure currently derived from the
            Hela360 Master Catalogue.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            variant="outline"
            onClick={() =>
              categoriesQuery.refetch()
            }
            disabled={
              categoriesQuery.isFetching
            }
          >
            <RefreshCw
              className={
                categoriesQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />

            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        {categoriesQuery.isLoading ? (
          <PageSection>
            <LoadingState
              title="Loading catalogue categories"
              description="Building the current Master Catalogue category distribution."
            />
          </PageSection>
        ) : categoriesQuery.isError ? (
          <PageSection>
            <ErrorState
              title="Categories unavailable"
              description={errorMessage(
                categoriesQuery.error,
              )}
            />
          </PageSection>
        ) : summary ? (
          <>
            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Catalogue coverage
                </h2>

                <p className="text-sm text-muted-foreground">
                  Category coverage is derived from
                  Master Item metadata and does not
                  represent tenant ProductCategory records.
                </p>
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                <SummaryCard
                  label="Master Items"
                  value={summary.total_items}
                  description="Total platform catalogue identities."
                />

                <SummaryCard
                  label="Categorized"
                  value={summary.categorized_items}
                  description={`${coveragePercent(
                    summary.categorized_items,
                    summary.total_items,
                  )}% of the Master Catalogue.`}
                />

                <SummaryCard
                  label="Uncategorized"
                  value={summary.uncategorized_items}
                  description="Items awaiting category enrichment."
                />

                <SummaryCard
                  label="Categories"
                  value={summary.category_count}
                  description="Distinct category names currently in use."
                />
              </div>
            </PageSection>

            <PageSection>
              <div className="space-y-1">
                <h2 className="text-base font-semibold">
                  Category distribution
                </h2>

                <p className="text-sm text-muted-foreground">
                  Governance view of category usage,
                  review state, lifecycle, and
                  subcategory distribution.
                </p>
              </div>

              {categories.length === 0 ? (
                <div className="mt-4">
                  <EmptyState
                    icon={<Layers3 />}
                    title="No categories recorded"
                    description="No Master Items currently contain category metadata."
                  />
                </div>
              ) : (
                <Card className="mt-4">
                  <CardContent className="px-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>
                            Category
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

                          <TableHead>
                            Subcategories
                          </TableHead>
                        </TableRow>
                      </TableHeader>

                      <TableBody>
                        {categories.map(
                          (category) => (
                            <TableRow
                              key={category.name}
                            >
                              <TableCell>
                                <div className="min-w-48">
                                  <p className="font-medium">
                                    {category.name}
                                  </p>
                                </div>
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  category.item_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  category.approved_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  category.draft_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  category.active_count,
                                )}
                              </TableCell>

                              <TableCell className="text-right tabular-nums">
                                {formatCount(
                                  category.inactive_count,
                                )}
                              </TableCell>

                              <TableCell>
                                <SubcategoryBadges
                                  category={category}
                                />
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


export default CategoriesPage;
