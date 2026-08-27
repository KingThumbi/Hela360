import { useLocation } from "react-router-dom";

import { navigation } from "@/navigation";

export interface Breadcrumb {
  label: string;
  href: string;
  current: boolean;
}

/**
 * ============================================================================
 * useBreadcrumbs
 * ============================================================================
 *
 * Builds enterprise breadcrumbs from the centralized navigation registry.
 *
 * This hook intentionally derives breadcrumb labels from navigation instead of
 * maintaining a second route map.
 *
 * Future enhancements:
 *
 * • Dynamic entity names
 * • Route handles
 * • React Router loader support
 * • Tenant-aware breadcrumbs
 * ============================================================================
 */

export function useBreadcrumbs(): Breadcrumb[] {
  const { pathname } = useLocation();

  const items = navigation.flatMap((section) => section.items);

  const match = items.find((item) => {
    return (
      pathname === item.href ||
      pathname.startsWith(`${item.href}/`)
    );
  });

  const breadcrumbs: Breadcrumb[] = [
    {
      label: "Home",
      href: "/dashboard",
      current: pathname === "/dashboard",
    },
  ];

  if (!match || match.href === "/dashboard") {
    return breadcrumbs;
  }

  const section = navigation.find((section) =>
    section.items.some((item) => item.id === match.id),
  );

  if (
    section &&
    section.title.length > 0 &&
    section.title !== match.title
  ) {
    breadcrumbs.push({
      label: section.title,
      href: match.href,
      current: false,
    });
  }

  breadcrumbs.push({
    label: match.title,
    href: match.href,
    current: true,
  });

  return breadcrumbs;
}

export default useBreadcrumbs;