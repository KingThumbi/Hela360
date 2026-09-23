import {
  ShieldCheck,
  ShieldPlus,
} from "lucide-react";
import {
  useEffect,
  useMemo,
  useState,
} from "react";
import { toast } from "sonner";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  useAdministrationRoles,
  useAdministrationUserRoles,
  useReplaceAdministrationUserRoles,
} from "@/hooks/queries/administration";

interface EditUserRolesDialogProps {
  open: boolean;
  userId: string | null;
  userName: string;
  onOpenChange: (open: boolean) => void;
}

function errorMessage(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "Unable to update staff roles.";
}

export function EditUserRolesDialog({
  open,
  userId,
  userName,
  onOpenChange,
}: EditUserRolesDialogProps) {
  const rolesQuery = useAdministrationRoles();
  const userRolesQuery =
    useAdministrationUserRoles(userId);

  const replaceRoles =
    useReplaceAdministrationUserRoles();

  const [selectedRoleIds, setSelectedRoleIds] =
    useState<string[]>([]);
  const [reason, setReason] = useState("");

  const currentRoleIds = useMemo(
    () =>
      (userRolesQuery.data ?? []).map(
        (role) => role.id,
      ),
    [userRolesQuery.data],
  );

  useEffect(() => {
    if (!open) {
      return;
    }

    setSelectedRoleIds(currentRoleIds);
    setReason("");
  }, [
    open,
    userId,
    currentRoleIds,
  ]);

  const roles = rolesQuery.data ?? [];

  const toggleRole = (roleId: string) => {
    setSelectedRoleIds((current) =>
      current.includes(roleId)
        ? current.filter((id) => id !== roleId)
        : [...current, roleId],
    );
  };

  const save = () => {
    if (!userId) {
      return;
    }

    replaceRoles.mutate(
      {
        userId,
        payload: {
          role_ids: selectedRoleIds,
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
              "Staff roles updated successfully.",
            );
          } else {
            toast.success(
              "No role changes were required.",
            );
          }

          onOpenChange(false);
        },
        onError: (error) => {
          toast.error(errorMessage(error));
        },
      },
    );
  };

  const loading =
    rolesQuery.isLoading ||
    userRolesQuery.isLoading;

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldPlus className="size-5" />
            Edit staff roles
          </DialogTitle>

          <DialogDescription>
            Manage tenant roles assigned to{" "}
            <span className="font-medium text-foreground">
              {userName}
            </span>
            . Effective permissions are recalculated
            immediately after a role change.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="rounded-lg border bg-muted/30 p-6 text-sm text-muted-foreground">
            Loading available roles…
          </div>
        ) : rolesQuery.isError ||
          userRolesQuery.isError ? (
          <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-sm">
            Unable to load role assignments.
          </div>
        ) : (
          <div className="space-y-3">
            {roles.map((role) => {
              const checked =
                selectedRoleIds.includes(role.id);

              return (
                <label
                  key={role.id}
                  className={[
                    "flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors",
                    checked
                      ? "border-primary/40 bg-primary/5"
                      : "hover:bg-muted/40",
                  ].join(" ")}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() =>
                      toggleRole(role.id)
                    }
                    className="mt-1 size-4 rounded border-border"
                  />

                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">
                        {role.name}
                      </span>

                      {role.is_system ? (
                        <Badge variant="secondary">
                          <ShieldCheck className="mr-1 size-3" />
                          System role
                        </Badge>
                      ) : (
                        <Badge variant="outline">
                          Tenant role
                        </Badge>
                      )}
                    </div>

                    <p className="mt-1 text-sm text-muted-foreground">
                      {role.description ||
                        "No role description has been provided."}
                    </p>

                    {role.is_system ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Protected role. The backend applies
                        owner-level safeguards to system-role
                        assignment and removal.
                      </p>
                    ) : null}
                  </div>
                </label>
              );
            })}
          </div>
        )}

        <div className="space-y-2">
          <label
            htmlFor="role-change-reason"
            className="text-sm font-medium"
          >
            Reason for change
          </label>

          <Input
            id="role-change-reason"
            value={reason}
            onChange={(event) =>
              setReason(event.target.value)
            }
            placeholder="Optional audit note"
          />

          <p className="text-xs text-muted-foreground">
            This reason is retained with role assignment
            provenance and audit history.
          </p>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() =>
              onOpenChange(false)
            }
            disabled={replaceRoles.isPending}
          >
            Cancel
          </Button>

          <Button
            type="button"
            onClick={save}
            disabled={
              !userId ||
              loading ||
              rolesQuery.isError ||
              userRolesQuery.isError ||
              replaceRoles.isPending
            }
          >
            {replaceRoles.isPending
              ? "Saving…"
              : "Save roles"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default EditUserRolesDialog;
