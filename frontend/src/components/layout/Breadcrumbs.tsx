import { Fragment } from "react";
import { Link } from "react-router-dom";
import { ChevronRight, Home } from "lucide-react";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

import { useBreadcrumbs } from "@/hooks/useBreadcrumbs";

/**
 * ============================================================================
 * Breadcrumbs
 * ============================================================================
 *
 * Enterprise application breadcrumb navigation.
 *
 * Responsibilities
 * ----------------
 * • Display the current navigation hierarchy
 * • Provide navigation back to parent pages
 * • Reflect the active route
 * • Delegate breadcrumb generation to useBreadcrumbs()
 *
 * This component intentionally contains no routing or navigation logic.
 * All breadcrumb resolution is performed by useBreadcrumbs().
 *
 * Future Integrations
 * -------------------
 * • Route metadata
 * • Dynamic entity names
 * • Product names
 * • Customer names
 * • Invoice numbers
 * • Purchase order numbers
 * • Unsaved state indicators
 * • Multi-tenant route context
 * ============================================================================
 */

export function Breadcrumbs() {
  const breadcrumbs = useBreadcrumbs();

  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {breadcrumbs.map((breadcrumb, index) => {
          const isLast =
            index === breadcrumbs.length - 1;

          return (
            <Fragment key={breadcrumb.href}>
              <BreadcrumbItem>
                {isLast ? (
                  <BreadcrumbPage className="flex items-center gap-2">
                    {index === 0 && (
                      <Home className="h-4 w-4" />
                    )}

                    {breadcrumb.label}
                  </BreadcrumbPage>
                ) : (
                  <BreadcrumbLink
                    render={
                      <Link
                        to={breadcrumb.href}
                        className="flex items-center gap-2"
                      >
                        {index === 0 && (
                          <Home className="h-4 w-4" />
                        )}

                        {breadcrumb.label}
                      </Link>
                    }
                  />
                )}
              </BreadcrumbItem>

              {!isLast && (
                <BreadcrumbSeparator>
                  <ChevronRight className="h-4 w-4" />
                </BreadcrumbSeparator>
              )}
            </Fragment>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}

export default Breadcrumbs;
