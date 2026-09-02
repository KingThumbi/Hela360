import { Outlet } from "react-router-dom";

import { OfficeShell } from "@/components/layout/office/OfficeShell";

/**
 * Root authenticated layout for Hela360 Office.
 */
export function OfficeAppLayout() {
  return (
    <OfficeShell>
      <Outlet />
    </OfficeShell>
  );
}

export default OfficeAppLayout;
