import {
  KeyRound,
  Search,
  ShieldCheck,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import type {
  AdministrationManagedPermission,
} from "@/features/administration/api/tenantAdministrationApi";

import {
  useAdministrationUserPermissionManagement,
  useSetAdministrationUserPermission,
} from "@/hooks/queries/administration";

interface ManageUserPermissionsDialogProps {
  open: boolean;
  userId: string | null;
  userName: string;
  onOpenChange: (open: boolean) => void;
}

type DesiredEffect =
  | "inherit"
  | "allow"
  | "deny";

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Unable to update staff permission.";
}

function sourceLabel(
  permission: AdministrationManagedPermission,
): string {
  switch (permission.source) {
    case "role":
      return "Inherited from role";
    case "direct_allow":
      return "Direct allow";
    case "direct_deny":
      return "Direct deny";
    case "implied":
      return "Implied access";
    default:
      return "Not granted";
  }
}

function moduleLabel(module: string): string {
  return module
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

export function ManageUserPermissionsDialog({
  open,
  userId,
  userName,
  onOpenChange,
}: ManageUserPermissionsDialogProps) {
  const permissionsQuery =
    useAdministrationUserPermissionManagement(
      open ? userId : null,
    );

  const setPermission =
    useSetAdministrationUserPermission();

  const [search, setSearch] = useState("");
  const [reason, setReason] = useState("");

  const permissions =
    permissionsQuery.data ?? [];

  const groups = useMemo(() => {
    const query = search
      .trim()
      .toLowerCase();

    const filtered = permissions.filter(
      (permission) => {
        if (!query) {
          return true;
        }

        return [
          permission.code,
          permission.name,
          permission.description,
          permission.module,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase()
          .includes(query);
      },
    );

    const grouped = new Map<
      string,
      AdministrationManagedPermission[]
    >();

    for (const permission of filtered) {
      const module =
        permission.module?.trim() ||
        permission.code.split(".")[0] ||
        "other";

      const current =
        grouped.get(module) ?? [];

      current.push(permission);
      grouped.set(module, current);
    }

    return Array.from(grouped.entries())
      .sort(([a], [b]) =>
        a.localeCompare(b),
      )
      .map(([module, items]) => ({
        module,
        items: [...items].sort((a, b) =>
          a.code.localeCompare(b.code),
        ),
      }));
  }, [permissions, search]);

  const changePermission = (
    permission: AdministrationManagedPermission,
    effect: DesiredEffect,
  ) => {
    if (!userId) {
      return;
    }

    const currentEffect =
      permission.override_effect ??
      "inherit";

    if (currentEffect === effect) {
      return;
    }

    setPermission.mutate(
      {
        userId,
        permissionCode: permission.code,
        payload: {
          effect,
          reason:
            reason.trim().length > 0
              ? reason.trim()
              : undefined,
        },
      },
      {
        onSuccess: (result) => {
          if (result.changed) {
            toast.success(
              `Permission updated: ${permission.code}`,
            );
          } else {
            toast.success(
              "No permission change was required.",
            );
          }
        },
        onError: (error) => {
          toast.error(
            errorMessage(error),
          );
        },
      },
    );
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!nextOpen) {
          setSearch("");
          setReason("");
        }

        onOpenChange(nextOpen);
      }}
    >
      <DialogContent className="max-h-[92vh] overflow-hidden sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <KeyRound className="size-5" />
            Manage permissions
          </DialogTitle>

          <DialogDescription>
            Apply individual access exceptions for{" "}
            <span className="font-medium text-foreground">
              {userName}
            </span>
            . Roles remain the primary access model.
            Direct deny overrides inherited access.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 overflow-hidden">
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(240px,0.65fr)]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />

              <Input
                type="search"
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value,
                  )
                }
                placeholder="Search permissions or modules"
                className="pl-9"
              />
            </div>

            <Input
              value={reason}
              onChange={(event) =>
                setReason(
                  event.target.value,
                )
              }
              placeholder="Optional audit reason"
            />
          </div>

          <div className="flex flex-wrap gap-2 rounded-lg border bg-muted/20 p-3 text-xs text-muted-foreground">
            <span>
              <strong className="text-foreground">
                Inherited
              </strong>{" "}
              removes a direct override.
            </span>

            <span>•</span>

            <span>
              <strong className="text-foreground">
                Allow
              </strong>{" "}
              grants this user an exception.
            </span>

            <span>•</span>

            <span>
              <strong className="text-foreground">
                Deny
              </strong>{" "}
              overrides role-derived access.
            </span>
          </div>

          <div className="max-h-[62vh] overflow-y-auto pr-1">
            {permissionsQuery.isLoading ? (
              <div className="rounded-lg border bg-muted/20 p-8 text-center text-sm text-muted-foreground">
                Loading permission catalogue…
              </div>
            ) : permissionsQuery.isError ? (
              <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-5 text-sm">
                <p className="font-medium">
                  Unable to load permissions.
                </p>

                <p className="mt-1 text-muted-foreground">
                  {permissionsQuery.error.message}
                </p>

                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => {
                    void permissionsQuery.refetch();
                  }}
                >
                  Retry
                </Button>
              </div>
            ) : groups.length === 0 ? (
              <div className="rounded-lg border bg-muted/20 p-8 text-center text-sm text-muted-foreground">
                No permissions match this search.
              </div>
            ) : (
              <div className="space-y-5">
                {groups.map(
                  ({ module, items }) => (
                    <section
                      key={module}
                      className="space-y-2"
                    >
                      <div className="flex items-center justify-between gap-3 px-1">
                        <h3 className="text-sm font-semibold">
                          {moduleLabel(module)}
                        </h3>

                        <Badge variant="outline">
                          {items.length}{" "}
                          {items.length === 1
                            ? "capability"
                            : "capabilities"}
                        </Badge>
                      </div>

                      <div className="overflow-hidden rounded-xl border">
                        {items.map(
                          (
                            permission,
                            index,
                          ) => {
                            const selectedEffect =
                              permission.override_effect ??
                              "inherit";

                            return (
                              <div
                                key={
                                  permission.id
                                }
                                className={[
                                  "grid gap-4 p-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center",
                                  index > 0
                                    ? "border-t"
                                    : "",
                                ].join(" ")}
                              >
                                <div className="min-w-0">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="font-medium">
                                      {permission.name ||
                                        permission.code}
                                    </span>

                                    <Badge
                                      variant={
                                        permission.effective
                                          ? "secondary"
                                          : "outline"
                                      }
                                    >
                                      {permission.effective
                                        ? "Effective"
                                        : "Not effective"}
                                    </Badge>

                                    {permission.role_inherited ? (
                                      <Badge variant="outline">
                                        <ShieldCheck className="mr-1 size-3" />
                                        Role
                                      </Badge>
                                    ) : null}
                                  </div>

                                  <p className="mt-1 font-mono text-xs text-muted-foreground">
                                    {
                                      permission.code
                                    }
                                  </p>

                                  {permission.description ? (
                                    <p className="mt-2 text-sm text-muted-foreground">
                                      {
                                        permission.description
                                      }
                                    </p>
                                  ) : null}

                                  <p className="mt-2 text-xs text-muted-foreground">
                                    Current source:{" "}
                                    <span className="font-medium text-foreground">
                                      {sourceLabel(
                                        permission,
                                      )}
                                    </span>
                                  </p>
                                </div>

                                <div className="grid grid-cols-3 gap-1 rounded-lg border bg-muted/20 p-1">
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant={
                                      selectedEffect ===
                                      "inherit"
                                        ? "secondary"
                                        : "ghost"
                                    }
                                    disabled={
                                      setPermission.isPending
                                    }
                                    onClick={() =>
                                      changePermission(
                                        permission,
                                        "inherit",
                                      )
                                    }
                                  >
                                    Inherited
                                  </Button>

                                  <Button
                                    type="button"
                                    size="sm"
                                    variant={
                                      selectedEffect ===
                                      "allow"
                                        ? "secondary"
                                        : "ghost"
                                    }
                                    disabled={
                                      setPermission.isPending
                                    }
                                    onClick={() =>
                                      changePermission(
                                        permission,
                                        "allow",
                                      )
                                    }
                                  >
                                    Allow
                                  </Button>

                                  <Button
                                    type="button"
                                    size="sm"
                                    variant={
                                      selectedEffect ===
                                      "deny"
                                        ? "destructive"
                                        : "ghost"
                                    }
                                    disabled={
                                      setPermission.isPending
                                    }
                                    onClick={() =>
                                      changePermission(
                                        permission,
                                        "deny",
                                      )
                                    }
                                  >
                                    Deny
                                  </Button>
                                </div>
                              </div>
                            );
                          },
                        )}
                      </div>
                    </section>
                  ),
                )}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default ManageUserPermissionsDialog;
