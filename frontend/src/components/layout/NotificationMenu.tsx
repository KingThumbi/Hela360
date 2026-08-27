import { Bell } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuHeader,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

import { useNotifications } from "@/hooks/useNotifications";

/**
 * ============================================================================
 * NotificationMenu
 * ============================================================================
 *
 * Enterprise notification center.
 *
 * Responsibilities
 * ----------------
 * • Display unread notification count
 * • Open the notification center
 * • Render recent notifications
 * • Provide quick navigation to notification targets
 *
 * This component intentionally contains no notification business logic.
 * All state is supplied by useNotifications().
 *
 * Future Integrations
 * -------------------
 * • Real-time WebSocket updates
 * • Push notifications
 * • Notification preferences
 * • Mark-as-read API
 * • Notification categories
 * • Infinite scrolling
 * • Notification search
 * ============================================================================
 */

export function NotificationMenu() {
  const {
    summary,
    isOpen,
    open,
    close,
    markAllAsRead,
  } = useNotifications();

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
          size="icon"
          aria-label="Notifications"
          className="relative"
        >
          <Bell className="h-5 w-5" />

          {summary.unread > 0 && (
            <Badge
              variant="destructive"
              className="
                absolute
                -right-1
                -top-1
                flex
                h-5
                min-w-5
                items-center
                justify-center
                rounded-full
                px-1
                text-[10px]
              "
            >
              {summary.unread > 99
                ? "99+"
                : summary.unread}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        className="w-96"
      >
        <DropdownMenuHeader className="flex items-center justify-between">
          <DropdownMenuLabel>
            Notifications
          </DropdownMenuLabel>

          {summary.unread > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={markAllAsRead}
            >
              Mark all as read
            </Button>
          )}
        </DropdownMenuHeader>

        <DropdownMenuSeparator />

        {summary.items.length === 0 ? (
          <div
            className="
              flex
              flex-col
              items-center
              justify-center
              py-10
              text-center
            "
          >
            <Bell className="mb-3 h-8 w-8 text-muted-foreground" />

            <p className="text-sm font-medium">
              You're all caught up.
            </p>

            <p className="mt-1 text-xs text-muted-foreground">
              No new notifications.
            </p>
          </div>
        ) : (
          <>
            {summary.items.map((notification) => (
              <DropdownMenuItem
                key={notification.id}
                className="
                  flex
                  cursor-pointer
                  flex-col
                  items-start
                  gap-1
                  py-3
                "
                onSelect={() =>
                  notification.onSelect?.()
                }
              >
                <div className="flex w-full items-start justify-between gap-3">
                  <span className="font-medium">
                    {notification.title}
                  </span>

                  {!notification.read && (
                    <span
                      className="
                        mt-1
                        h-2
                        w-2
                        rounded-full
                        bg-primary
                      "
                    />
                  )}
                </div>

                <p
                  className="
                    line-clamp-2
                    text-sm
                    text-muted-foreground
                  "
                >
                  {notification.message}
                </p>

                {notification.timestamp && (
                  <span
                    className="
                      text-xs
                      text-muted-foreground
                    "
                  >
                    {notification.timestamp}
                  </span>
                )}
              </DropdownMenuItem>
            ))}

            <DropdownMenuSeparator />

            <DropdownMenuItem
              className="justify-center font-medium"
            >
              View all notifications
            </DropdownMenuItem>
          </>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export default NotificationMenu;
