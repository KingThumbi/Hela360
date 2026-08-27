import {
  useMemo,
  useState,
} from "react";

import { useAuthStore } from "@/store/authStore";

export interface TenantContext {
  id: string;
  name: string;
}

export interface UseTenantResult {
  tenant?: TenantContext;
  tenants: TenantContext[];
  canSwitchTenant: boolean;
  isOpen: boolean;
  open: () => void;
  close: () => void;
  setTenant: (tenantId: string) => void;
}

export function useTenant(): UseTenantResult {
  const [isOpen, setIsOpen] = useState(false);

  const identity = useAuthStore(
    (state) => state.identity,
  );

  const tenant = useMemo<TenantContext | undefined>(() => {
    if (!identity?.tenantId) {
      return undefined;
    }

    return {
      id: identity.tenantId,
      name: identity.tenantName,
    };
  }, [
    identity?.tenantId,
    identity?.tenantName,
  ]);

  const tenants = useMemo<TenantContext[]>(
    () => (tenant ? [tenant] : []),
    [tenant],
  );

  return {
    tenant,
    tenants,
    canSwitchTenant: false,
    isOpen,
    open: () => setIsOpen(true),
    close: () => setIsOpen(false),
    setTenant: () => undefined,
  };
}

export default useTenant;
