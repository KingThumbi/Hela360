import { ShieldAlert } from "lucide-react";

import { ErrorState } from "@/components/page";

export function AccessDeniedPage() {
  return (
    <ErrorState
      title="Access denied"
      description="You do not have permission to view this area."
      icon={<ShieldAlert className="h-12 w-12" />}
    />
  );
}

export default AccessDeniedPage;

