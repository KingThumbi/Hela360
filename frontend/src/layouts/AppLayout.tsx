import { Outlet } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";

/**
 * ============================================================================
 * AppLayout
 * ============================================================================
 *
 * Root authenticated layout.
 *
 * Responsibilities
 * ----------------
 * • Render the enterprise AppShell
 * • Supply the router outlet
 *
 * This component intentionally contains almost no UI.
 * ============================================================================
 */

export function AppLayout() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

export default AppLayout;
