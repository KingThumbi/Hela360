import type { PermissionCode } from "@/types/auth";

export type PermissionCollection =
  | ReadonlySet<PermissionCode>
  | readonly PermissionCode[];

function toPermissionSet(
  permissions: PermissionCollection,
): ReadonlySet<PermissionCode> {
  return permissions instanceof Set
    ? permissions
    : new Set(permissions);
}

export function can(
  permissions: PermissionCollection,
  permission: PermissionCode,
): boolean {
  return toPermissionSet(permissions).has(permission);
}

export function cannot(
  permissions: PermissionCollection,
  permission: PermissionCode,
): boolean {
  return !can(permissions, permission);
}

export function canAny(
  permissions: PermissionCollection,
  requiredPermissions: readonly PermissionCode[],
): boolean {
  if (requiredPermissions.length === 0) {
    return false;
  }

  const permissionSet = toPermissionSet(permissions);

  return requiredPermissions.some((permission) =>
    permissionSet.has(permission),
  );
}

export function canAll(
  permissions: PermissionCollection,
  requiredPermissions: readonly PermissionCode[],
): boolean {
  if (requiredPermissions.length === 0) {
    return false;
  }

  const permissionSet = toPermissionSet(permissions);

  return requiredPermissions.every((permission) =>
    permissionSet.has(permission),
  );
}

