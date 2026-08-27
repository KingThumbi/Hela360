/**
 * ============================================================================
 * useInitializeShell
 * ============================================================================
 *
 * Initializes the enterprise application shell.
 *
 * Responsibilities
 * ----------------
 * • Restore persisted shell preferences
 * • Restore sidebar state
 * • Restore selected branch
 * • Prepare future shell initialization
 *
 * This hook should be called exactly once during application startup by the
 * ShellProvider. Components should never invoke this hook directly.
 *
 * Future Responsibilities
 * -----------------------
 * • Restore tenant context
 * • Restore workspace state
 * • Restore recent pages
 * • Register keyboard shortcuts
 * • Initialize command palette
 * • Restore notification preferences
 * • Restore UI density
 * • Restore language preferences
 * * ============================================================================
 */

import { useEffect } from "react";

import { storage } from "@/lib/storage";
import { useShellStore } from "@/store/shellStore";

/**
 * ============================================================================
 * Shell Initializer
 * ============================================================================
 */

export function useInitializeShell(): void {
  const collapseSidebar = useShellStore(
    (state) => state.collapseSidebar,
  );

  const expandSidebar = useShellStore(
    (state) => state.expandSidebar,
  );

  const setSelectedBranch = useShellStore(
    (state) => state.setSelectedBranch,
  );

  useEffect(() => {
    /**
     * ------------------------------------------------------------------------
     * Restore Sidebar Preference
     * ------------------------------------------------------------------------
     */

    if (storage.isSidebarCollapsed()) {
      collapseSidebar();
    } else {
      expandSidebar();
    }

    /**
     * ------------------------------------------------------------------------
     * Restore Branch Context
     * ------------------------------------------------------------------------
     */

    const branchId = storage.getBranchId();

    if (branchId) {
      setSelectedBranch(branchId);
    }

    /**
     * ------------------------------------------------------------------------
     * Future Initialization
     * ------------------------------------------------------------------------
     *
     * Enterprise shell services will be restored here as they are introduced.
     *
     * Planned:
     *
     * • Tenant context
     * • Workspace state
     * • Recent workspaces
     * • Command palette state
     * • Notification preferences
     * • Keyboard shortcuts
     * • Feature flags
     * • Localization
     * • Accessibility preferences
     */
  }, [
    collapseSidebar,
    expandSidebar,
    setSelectedBranch,
  ]);
}

export default useInitializeShell;