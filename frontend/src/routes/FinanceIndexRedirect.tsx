import { Navigate } from "react-router-dom";

import { useAuthorization } from "@/hooks/useAuthorization";
import { ROUTE_PERMISSION_REQUIREMENTS } from "@/routes/permissions";
import { PATHS } from "@/routes/routes";

export function FinanceIndexRedirect() {
  const authorization = useAuthorization();

  const target = authorization.can(
    ROUTE_PERMISSION_REQUIREMENTS[
      PATHS.FINANCE.CHART_OF_ACCOUNTS
    ].permission,
  )
    ? PATHS.FINANCE.CHART_OF_ACCOUNTS
    : PATHS.FINANCE.JOURNALS;

  return <Navigate to={target} replace />;
}
