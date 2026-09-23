export const administrationQueryKeys = {
  root: ["tenant-administration"] as const,

  users: () =>
    [
      ...administrationQueryKeys.root,
      "users",
    ] as const,

  user: (userId: string) =>
    [
      ...administrationQueryKeys.users(),
      userId,
    ] as const,

  userRoles: (userId: string) =>
    [
      ...administrationQueryKeys.user(userId),
      "roles",
    ] as const,

  userPermissions: (userId: string) =>
    [
      ...administrationQueryKeys.user(userId),
      "effective-permissions",
    ] as const,

  userPermissionManagement: (userId: string) =>
    [
      ...administrationQueryKeys.user(userId),
      "permissions",
    ] as const,

  roles: () =>
    [
      ...administrationQueryKeys.root,
      "roles",
    ] as const,
} as const;
