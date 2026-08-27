import {
  ChevronDown,
  LogOut,
  Settings,
  Shield,
  User,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { useUserMenu } from "@/hooks/useUserMenu";

/**
 * ============================================================================
 * UserMenu
 * ============================================================================
 *
 * Enterprise authenticated user menu.
 *
 * Responsibilities
 * ----------------
 * • Display the authenticated user's identity
 * • Display tenant and branch context
 * • Provide access to account pages
 * • Provide access to security settings
 * • Provide logout entry point
 *
 * This component intentionally contains no authentication or authorization
 * logic. All state is supplied by useUserMenu().
 *
 * Future Integrations
 * -------------------
 * • User profile
 * • Avatar service
 * • User preferences
 * • MFA management
 * • Session management
 * • Login history
 * • Device management
 * • Keyboard shortcuts
 * • Activity log
 * • Impersonation (Platform Admin)
 * ============================================================================
 */

export function UserMenu() {
  const {
    identity,
    roles,
    isAuthenticated,
    isOpen,
    open,
    close,
    logout,
  } = useUserMenu();

  if (!isAuthenticated || !identity) {
    return null;
  }

  const displayName = [
    identity.firstName,
    identity.lastName,
  ]
    .filter(Boolean)
    .join(" ");

  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <DropdownMenu
      open={isOpen}
      onOpenChange={(value) =>
        value ? open() : close()
      }
    >
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="
            h-auto
            gap-3
            px-2
            py-1.5
          "
        >
          <Avatar className="h-9 w-9">
            <AvatarImage
              src={identity.avatarUrl}
              alt={displayName}
            />

            <AvatarFallback>
              {initials}
            </AvatarFallback>
          </Avatar>

          <div
            className="
              hidden
              min-w-0
              flex-1
              text-left
              lg:block
            "
          >
            <div className="truncate text-sm font-semibold">
              {displayName}
            </div>

            <div className="truncate text-xs text-muted-foreground">
              {identity.email}
            </div>
          </div>

          <ChevronDown
            className="
              hidden
              h-4
              w-4
              text-muted-foreground
              lg:block
            "
          />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        className="w-80"
      >
        <DropdownMenuLabel className="font-normal">
          <div className="flex items-start gap-3">
            <Avatar className="h-10 w-10">
              <AvatarImage
                src={identity.avatarUrl}
                alt={displayName}
              />

              <AvatarFallback>
                {initials}
              </AvatarFallback>
            </Avatar>

            <div className="min-w-0 flex-1 space-y-1">
              <p className="truncate text-sm font-semibold">
                {displayName}
              </p>

              <p className="truncate text-xs text-muted-foreground">
                {identity.username
                  ? `@${identity.username}`
                  : "User"}
              </p>

              <p className="truncate text-xs text-muted-foreground">
                {identity.email}
              </p>
            </div>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <div className="space-y-2 px-2 py-2 text-xs">
          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Tenant
            </span>

            <span className="font-medium">
              {identity.tenantName}
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Branch
            </span>

            <span className="font-medium">
              Not selected
            </span>
          </div>

          <div className="flex justify-between">
            <span className="text-muted-foreground">
              Roles
            </span>

            <span className="truncate text-right font-medium">
              {roles.map((role) => role.name).join(", ") || "No role assigned"}
            </span>
          </div>
        </div>

        <DropdownMenuSeparator />

        <DropdownMenuGroup>
          <DropdownMenuItem>
            <User className="mr-2 h-4 w-4" />
            My Profile
          </DropdownMenuItem>

          <DropdownMenuItem>
            <Settings className="mr-2 h-4 w-4" />
            Preferences
          </DropdownMenuItem>

          <DropdownMenuItem>
            <Shield className="mr-2 h-4 w-4" />
            Security
          </DropdownMenuItem>
        </DropdownMenuGroup>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          variant="destructive"
          onClick={logout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Sign Out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default UserMenu;
