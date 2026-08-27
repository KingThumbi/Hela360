import type {
  NavigationItem,
  NavigationSection,
} from "@/types/navigation";
import type { PermissionCode } from "@/types/auth";


export type NavigationPermissionChecker = (
  permission: PermissionCode,
) => boolean;


/**
 * Flattens all navigation items, including nested children,
 * into a single array.
 */
export function flattenNavigation(
  sections: NavigationSection[],
): NavigationItem[] {
  return sections.flatMap(
    (section) => flattenItems(section.items),
  );
}


function flattenItems(
  items: NavigationItem[],
): NavigationItem[] {
  return items.flatMap(
    (item) =>
      item.children
        ? [
            item,
            ...flattenItems(item.children),
          ]
        : [item],
  );
}


/**
 * Finds a navigation item by its unique identifier.
 */
export function findNavigationItemById(
  sections: NavigationSection[],
  id: string,
): NavigationItem | undefined {
  return flattenNavigation(sections).find(
    (item) => item.id === id,
  );
}


/**
 * Finds a navigation item by its route.
 */
export function findNavigationItemByPath(
  sections: NavigationSection[],
  path: string,
): NavigationItem | undefined {
  return flattenNavigation(sections).find(
    (item) => item.href === path,
  );
}


/**
 * Returns true when a path matches a navigation item's route.
 *
 * Exact matches are preferred. Nested routes are also considered active.
 */
export function isNavigationItemActive(
  item: NavigationItem,
  currentPath: string,
): boolean {
  if (!item.href) {
    return false;
  }

  if (item.href === "/") {
    return currentPath === "/";
  }

  return (
    currentPath === item.href ||
    currentPath.startsWith(`${item.href}/`)
  );
}


/**
 * Returns the section containing a route.
 */
export function findNavigationSection(
  sections: NavigationSection[],
  path: string,
): NavigationSection | undefined {
  return sections.find(
    (section) =>
      flattenItems(section.items).some(
        (item) =>
          isNavigationItemActive(
            item,
            path,
          ),
      ),
  );
}


/**
 * Returns all navigation items that require a permission.
 */
export function getProtectedNavigationItems(
  sections: NavigationSection[],
): NavigationItem[] {
  return flattenNavigation(sections).filter(
    (item) =>
      item.permission !== undefined,
  );
}


/**
 * Filters one navigation section through the caller's canonical
 * authorization decision.
 *
 * This helper does not interpret permissions itself. The caller owns
 * authorization semantics such as owner authority, role permissions,
 * direct grants, future entitlement checks, and other policy decisions.
 */
export function filterNavigationSection(
  section: NavigationSection,
  can: NavigationPermissionChecker,
): NavigationSection {
  return {
    ...section,
    items: filterItems(
      section.items,
      can,
    ),
  };
}


/**
 * Filters grouped navigation through the caller's canonical
 * authorization decision.
 */
export function filterNavigation(
  sections: NavigationSection[],
  can: NavigationPermissionChecker,
): NavigationSection[] {
  return sections
    .map(
      (section) =>
        filterNavigationSection(
          section,
          can,
        ),
    )
    .filter(
      (section) =>
        section.items.length > 0,
    );
}


/**
 * Compatibility alias for the pre-boundary public name.
 *
 * The second argument is now an authorization predicate rather than
 * a raw permission collection.
 */
export function filterNavigationByPermissions(
  sections: NavigationSection[],
  can: NavigationPermissionChecker,
): NavigationSection[] {
  return filterNavigation(
    sections,
    can,
  );
}


function filterItems(
  items: NavigationItem[],
  can: NavigationPermissionChecker,
): NavigationItem[] {
  return items.flatMap((item) => {
    const children = item.children
      ? filterItems(
          item.children,
          can,
        )
      : undefined;

    const hasRequiredPermission =
      !item.permission ||
      can(item.permission);

    const hasAnyRequiredPermission =
      !item.anyOfPermissions ||
      item.anyOfPermissions.length === 0 ||
      item.anyOfPermissions.some(
        (permission) => can(permission),
      );

    const allowed =
      hasRequiredPermission &&
      hasAnyRequiredPermission;

    if (
      !allowed &&
      (!children ||
        children.length === 0)
    ) {
      return [];
    }

    return [
      {
        ...item,
        children,
      },
    ];
  });
}


/**
 * Generates breadcrumb items from the current route.
 *
 * This is intentionally lightweight for now. Dynamic route breadcrumbs
 * can be added later without changing the authorization boundary.
 */
export function buildBreadcrumbs(
  sections: NavigationSection[],
  currentPath: string,
): NavigationItem[] {
  const item = findNavigationItemByPath(
    sections,
    currentPath,
  );

  return item ? [item] : [];
}
