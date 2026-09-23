import {
  BadgeCheck,
  Building2,
  Crown,
  Mail,
  KeyRound,
  RefreshCw,
  Search,
  Shield,
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";

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
  PageToolbar,
} from "@/components/page";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  EditUserRolesDialog,
} from "@/features/administration/components/EditUserRolesDialog";
import {
  ManageUserPermissionsDialog,
} from "@/features/administration/components/ManageUserPermissionsDialog";
import {
  useAdministrationUser,
  useAdministrationUserPermissions,
  useAdministrationUserRoles,
  useAdministrationUsers,
} from "@/hooks/queries/administration";
import {
  useAuthorization,
} from "@/hooks/useAuthorization";

import type {
  AdministrationPermission,
  AdministrationUser,
} from "@/features/administration/api/tenantAdministrationApi";

function userDisplayName(
  user: AdministrationUser,
): string {
  const fullName = [
    user.first_name,
    user.last_name,
  ]
    .filter(Boolean)
    .join(" ")
    .trim();

  return fullName || user.username;
}

function userInitials(
  user: AdministrationUser,
): string {
  const first =
    user.first_name?.trim().charAt(0) ?? "";
  const last =
    user.last_name?.trim().charAt(0) ?? "";

  const initials = `${first}${last}`.toUpperCase();

  return initials || user.username
    .slice(0, 2)
    .toUpperCase();
}

function permissionModule(
  permission: AdministrationPermission,
): string {
  if (
    permission.module_code &&
    permission.module_code.trim()
  ) {
    return permission.module_code;
  }

  const [prefix] = permission.code.split(".");
  return prefix || "other";
}

export function AdministrationUsersPage() {
  const authorization = useAuthorization();
  const canManageUsers =
    authorization.can("users.manage");

  const usersQuery =
    useAdministrationUsers();

  const [search, setSearch] = useState("");
  const [
    selectedUserId,
    setSelectedUserId,
  ] = useState<string | null>(null);
  const [
    editRolesOpen,
    setEditRolesOpen,
  ] = useState(false);
  const [
    managePermissionsOpen,
    setManagePermissionsOpen,
  ] = useState(false);

  const users = usersQuery.data ?? [];

  const filteredUsers = useMemo(() => {
    const query = search
      .trim()
      .toLowerCase();

    if (!query) {
      return users;
    }

    return users.filter((user) => {
      const haystack = [
        user.first_name,
        user.last_name,
        user.username,
        user.email,
        user.phone,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      return haystack.includes(query);
    });
  }, [users, search]);

  const effectiveSelectedUserId =
    selectedUserId ??
    filteredUsers[0]?.id ??
    null;

  const userQuery =
    useAdministrationUser(
      effectiveSelectedUserId,
    );

  const rolesQuery =
    useAdministrationUserRoles(
      effectiveSelectedUserId,
    );

  const permissionsQuery =
    useAdministrationUserPermissions(
      effectiveSelectedUserId,
    );

  const selectedUser =
    userQuery.data ??
    users.find(
      (user) =>
        user.id === effectiveSelectedUserId,
    );

  const roles = rolesQuery.data ?? [];
  const permissions =
    permissionsQuery.data ?? [];

  const permissionGroups = useMemo(() => {
    const groups = new Map<
      string,
      AdministrationPermission[]
    >();

    for (const permission of permissions) {
      const module = permissionModule(permission);

      const current =
        groups.get(module) ?? [];

      current.push(permission);
      groups.set(module, current);
    }

    return Array.from(groups.entries())
      .sort(([a], [b]) =>
        a.localeCompare(b),
      )
      .map(([module, items]) => ({
        module,
        items: [...items].sort((a, b) =>
          a.code.localeCompare(b.code),
        ),
      }));
  }, [permissions]);

  const refreshAll = async () => {
    await Promise.all([
      usersQuery.refetch(),
      userQuery.refetch(),
      rolesQuery.refetch(),
      permissionsQuery.refetch(),
    ]);
  };

  return (
    <Page>
      <PageHeader>
        <div>
          <PageTitle>
            Staff & access
          </PageTitle>
          <PageDescription>
            Manage tenant staff identities, inspect
            effective access, and assign operational
            roles.
          </PageDescription>
        </div>

        <PageActions>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              void refreshAll();
            }}
            disabled={usersQuery.isFetching}
          >
            <RefreshCw
              className={
                usersQuery.isFetching
                  ? "animate-spin"
                  : undefined
              }
            />
            Refresh
          </Button>
        </PageActions>
      </PageHeader>

      <PageContent>
        <PageToolbar>
          <div className="relative w-full">
            <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

            <Input
              type="search"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search staff by name, username, email or phone"
              className="pl-9"
            />
          </div>
        </PageToolbar>

        <PageSection>
          {usersQuery.isLoading &&
          users.length === 0 ? (
            <LoadingState
              title="Loading staff"
              description="Retrieving tenant staff and access records."
            />
          ) : usersQuery.isError ? (
            <ErrorState
              title="Unable to load staff"
              description={
                usersQuery.error.message ||
                "Tenant staff records could not be loaded."
              }
              onRetry={() =>
                usersQuery.refetch()
              }
            />
          ) : filteredUsers.length === 0 ? (
            <EmptyState
              icon={
                <Users className="h-12 w-12" />
              }
              title={
                search.trim()
                  ? "No staff match your search"
                  : "No staff records"
              }
              description={
                search.trim()
                  ? "Try a different name, username, email or phone."
                  : "Staff creation will appear here once that administration capability is enabled."
              }
            />
          ) : (
            <div className="grid gap-5 xl:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.6fr)]">
              <div className="overflow-hidden rounded-xl border bg-background">
                <div className="border-b px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h2 className="font-semibold">
                        Tenant staff
                      </h2>
                      <p className="text-xs text-muted-foreground">
                        {filteredUsers.length}{" "}
                        {filteredUsers.length === 1
                          ? "person"
                          : "people"}
                      </p>
                    </div>

                    <Badge variant="outline">
                      <Building2 className="mr-1 size-3" />
                      Tenant scoped
                    </Badge>
                  </div>
                </div>

                <div className="max-h-[68vh] overflow-y-auto p-2">
                  {filteredUsers.map((user) => {
                    const selected =
                      user.id ===
                      effectiveSelectedUserId;

                    return (
                      <button
                        key={user.id}
                        type="button"
                        onClick={() =>
                          setSelectedUserId(user.id)
                        }
                        className={[
                          "mb-1 flex w-full items-center gap-3 rounded-lg border border-transparent px-3 py-3 text-left transition-colors",
                          selected
                            ? "border-primary/20 bg-primary/5"
                            : "hover:bg-muted/50",
                        ].join(" ")}
                      >
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-semibold">
                          {userInitials(user)}
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="truncate font-medium">
                              {userDisplayName(user)}
                            </span>

                            {user.is_owner ? (
                              <Crown className="size-3.5 shrink-0 text-muted-foreground" />
                            ) : null}
                          </div>

                          <p className="truncate text-xs text-muted-foreground">
                            @{user.username}
                          </p>
                        </div>

                        <span
                          className={[
                            "size-2.5 rounded-full",
                            user.is_active
                              ? "bg-emerald-500"
                              : "bg-muted-foreground/40",
                          ].join(" ")}
                          aria-label={
                            user.is_active
                              ? "Active"
                              : "Inactive"
                          }
                        />
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="min-w-0 rounded-xl border bg-background">
                {!selectedUser ? (
                  <div className="flex min-h-[420px] items-center justify-center p-8 text-center">
                    <div>
                      <UserRound className="mx-auto mb-3 size-10 text-muted-foreground" />
                      <h2 className="font-semibold">
                        Select a staff member
                      </h2>
                      <p className="mt-1 text-sm text-muted-foreground">
                        Choose a user to inspect identity,
                        roles, and effective permissions.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="border-b p-5">
                      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                        <div className="flex items-start gap-4">
                          <div className="flex size-14 shrink-0 items-center justify-center rounded-2xl bg-muted text-lg font-semibold">
                            {userInitials(
                              selectedUser,
                            )}
                          </div>

                          <div>
                            <div className="flex flex-wrap items-center gap-2">
                              <h2 className="text-lg font-semibold">
                                {userDisplayName(
                                  selectedUser,
                                )}
                              </h2>

                              {selectedUser.is_owner ? (
                                <Badge variant="secondary">
                                  <Crown className="mr-1 size-3" />
                                  Tenant owner
                                </Badge>
                              ) : null}

                              <Badge
                                variant={
                                  selectedUser.is_active
                                    ? "default"
                                    : "outline"
                                }
                              >
                                {selectedUser.is_active
                                  ? "Active"
                                  : "Inactive"}
                              </Badge>
                            </div>

                            <p className="mt-1 text-sm text-muted-foreground">
                              @{selectedUser.username}
                            </p>
                          </div>
                        </div>

                        {canManageUsers ? (
                          <Button
                            type="button"
                            onClick={() =>
                              setEditRolesOpen(true)
                            }
                          >
                            <Shield className="size-4" />
                            Edit roles
                          </Button>
                        ) : null}

                        {canManageUsers ? (
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() =>
                              setManagePermissionsOpen(true)
                            }
                          >
                            <KeyRound className="size-4" />
                            Manage permissions
                          </Button>
                        ) : null}
                      </div>
                    </div>

                    <div className="grid gap-5 p-5 lg:grid-cols-2">
                      <section className="space-y-3">
                        <div>
                          <h3 className="font-semibold">
                            Identity
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            Tenant staff account details.
                          </p>
                        </div>

                        <div className="space-y-3 rounded-lg border p-4 text-sm">
                          <div className="flex items-start gap-3">
                            <UserRound className="mt-0.5 size-4 text-muted-foreground" />
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Username
                              </p>
                              <p className="font-medium">
                                {selectedUser.username}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-start gap-3">
                            <Mail className="mt-0.5 size-4 text-muted-foreground" />
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Email
                              </p>
                              <p className="font-medium">
                                {selectedUser.email ||
                                  "Not provided"}
                              </p>
                            </div>
                          </div>

                          <div className="flex items-start gap-3">
                            <Building2 className="mt-0.5 size-4 text-muted-foreground" />
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Branch access
                              </p>
                              <p className="font-medium">
                                {selectedUser.branch_id
                                  ? selectedUser.branch_id
                                  : "No primary branch assigned"}
                              </p>
                            </div>
                          </div>
                        </div>
                      </section>

                      <section className="space-y-3">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <h3 className="font-semibold">
                              Assigned roles
                            </h3>
                            <p className="text-sm text-muted-foreground">
                              Direct tenant role membership.
                            </p>
                          </div>

                          <Badge variant="outline">
                            {roles.length}
                          </Badge>
                        </div>

                        <div className="min-h-28 rounded-lg border p-4">
                          {rolesQuery.isLoading ? (
                            <p className="text-sm text-muted-foreground">
                              Loading roles…
                            </p>
                          ) : roles.length === 0 ? (
                            <p className="text-sm text-muted-foreground">
                              No roles assigned.
                            </p>
                          ) : (
                            <div className="flex flex-wrap gap-2">
                              {roles.map((role) => (
                                <Badge
                                  key={role.id}
                                  variant={
                                    role.is_system
                                      ? "secondary"
                                      : "outline"
                                  }
                                >
                                  {role.is_system ? (
                                    <ShieldCheck className="mr-1 size-3" />
                                  ) : null}
                                  {role.name}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                      </section>
                    </div>

                    <div className="border-t p-5">
                      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                        <div>
                          <h3 className="font-semibold">
                            Effective permissions
                          </h3>
                          <p className="text-sm text-muted-foreground">
                            Calculated from role permissions
                            plus explicit user overrides,
                            with denies taking precedence.
                          </p>
                        </div>

                        <Badge variant="outline">
                          <BadgeCheck className="mr-1 size-3" />
                          {permissions.length} effective
                        </Badge>
                      </div>

                      {permissionsQuery.isLoading ? (
                        <div className="rounded-lg border p-4 text-sm text-muted-foreground">
                          Calculating effective access…
                        </div>
                      ) : permissionsQuery.isError ? (
                        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-sm">
                          Effective permissions could
                          not be loaded.
                        </div>
                      ) : permissions.length === 0 ? (
                        <div className="rounded-lg border p-4 text-sm text-muted-foreground">
                          This user currently has no
                          effective permissions.
                        </div>
                      ) : (
                        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                          {permissionGroups.map(
                            (group) => (
                              <div
                                key={group.module}
                                className="rounded-lg border p-4"
                              >
                                <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                                  {group.module}
                                </p>

                                <div className="space-y-2">
                                  {group.items.map(
                                    (permission) => (
                                      <div
                                        key={
                                          permission.id
                                        }
                                        className="rounded-md bg-muted/50 px-2.5 py-2"
                                      >
                                        <p className="text-sm font-medium">
                                          {
                                            permission.code
                                          }
                                        </p>

                                        {permission.description ? (
                                          <p className="mt-0.5 text-xs text-muted-foreground">
                                            {
                                              permission.description
                                            }
                                          </p>
                                        ) : null}
                                      </div>
                                    ),
                                  )}
                                </div>
                              </div>
                            ),
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </PageSection>
      </PageContent>

      <EditUserRolesDialog
        open={editRolesOpen}
        userId={effectiveSelectedUserId}
        userName={
          selectedUser
            ? userDisplayName(selectedUser)
            : "this staff member"
        }
        onOpenChange={setEditRolesOpen}
      />

      <ManageUserPermissionsDialog
        open={managePermissionsOpen}
        userId={effectiveSelectedUserId}
        userName={
          selectedUser
            ? userDisplayName(selectedUser)
            : "Staff member"
        }
        onOpenChange={
          setManagePermissionsOpen
        }
      />
    </Page>
  );
}

export default AdministrationUsersPage;
