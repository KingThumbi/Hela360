import { useMemo } from "react";

import { useShellStore } from "@/store/shellStore";

/**
 * ============================================================================
 * useNotifications
 * ============================================================================
 *
 * Enterprise notification hook.
 *
 * Responsibilities
 * ----------------
 * • Manage notification panel visibility
 * • Expose notification count
 * • Prepare for React Query integration
 *
 * Future integrations:
 *
 * • Notification REST API
 * • WebSockets
 * • Server-Sent Events (SSE)
 * • Push Notifications
 * • Approval Engine alerts
 * • Inventory alerts
 * • Low stock alerts
 * • Purchase approval requests
 * ============================================================================
 */

export interface NotificationItem {
  id: string;

  title: string;

  message: string;

  createdAt: Date;

  read: boolean;

  href?: string;

  onSelect?: () => void;
}

export interface NotificationSummary {
  unread: number;
  items: Array<
    NotificationItem & {
      timestamp?: string;
    }
  >;
}

export interface UseNotificationsResult {
  notifications: NotificationItem[];

  unreadCount: number;

  summary: NotificationSummary;

  isOpen: boolean;

  open: () => void;

  close: () => void;

  toggle: () => void;

  markAsRead: (id: string) => void;

  markAllAsRead: () => void;
}

export function useNotifications(): UseNotificationsResult {
  const isOpen = useShellStore(
    (state) => state.notificationsOpen,
  );

  const open = useShellStore(
    (state) => state.openNotifications,
  );

  const close = useShellStore(
    (state) => state.closeNotifications,
  );

  const toggle = useShellStore(
    (state) => state.toggleNotifications,
  );

  /**
   * Placeholder.
   *
   * This will later come from React Query
   * and the Notifications API.
   */
  const notifications = useMemo<NotificationItem[]>(() => {
    return [];
  }, []);

  const unreadCount = useMemo(
    () =>
      notifications.filter(
        (notification) => !notification.read,
      ).length,
    [notifications],
  );

  const summary = useMemo<NotificationSummary>(
    () => ({
      unread: unreadCount,
      items: notifications.map((notification) => ({
        ...notification,
        timestamp:
          notification.createdAt.toLocaleString(),
      })),
    }),
    [
      notifications,
      unreadCount,
    ],
  );

  const markAsRead = (_id: string) => {
    /**
     * Future implementation:
     *
     * mutation.markAsRead()
     */
  };

  const markAllAsRead = () => {
    /**
     * Future implementation:
     *
     * mutation.markAllAsRead()
     */
  };

  return {
    notifications,

    unreadCount,

    summary,

    isOpen,

    open,

    close,

    toggle,

    markAsRead,

    markAllAsRead,
  };
}

export default useNotifications;
