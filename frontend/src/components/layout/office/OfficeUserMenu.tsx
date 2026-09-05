import {
  LogOut,
} from "lucide-react";

import {
  useNavigate,
} from "react-router-dom";

import {
  Button,
} from "@/components/ui/button";

import {
  usePlatformLogout,
} from "@/hooks/queries/platform-auth";

import {
  OFFICE_PATHS,
} from "@/routes/officeRoutes";

import {
  usePlatformAuthStore,
} from "@/store/platformAuthStore";

export function OfficeUserMenu() {
  const navigate = useNavigate();

  const user =
    usePlatformAuthStore(
      (state) => state.user,
    );

  const logoutMutation =
    usePlatformLogout();

  if (!user) {
    return null;
  }

  const displayName = [
    user.firstName,
    user.lastName,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="flex items-center gap-3">
      <div className="hidden text-right sm:block">
        <div className="text-sm font-medium">
          {displayName || user.username}
        </div>

        <div className="text-xs text-muted-foreground">
          {user.email}
        </div>
      </div>

      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled={
          logoutMutation.isPending
        }
        onClick={() => {
          logoutMutation.mutate(
            undefined,
            {
              onSettled: () => {
                navigate(
                  OFFICE_PATHS.LOGIN,
                  {
                    replace: true,
                  },
                );
              },
            },
          );
        }}
        aria-label="Sign out of Hela360 Office"
      >
        <LogOut className="size-4" />
      </Button>
    </div>
  );
}

export default OfficeUserMenu;
