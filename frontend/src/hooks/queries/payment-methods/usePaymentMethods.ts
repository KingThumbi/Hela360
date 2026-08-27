/**
 * ============================================================================
 * Hela360 Payment Methods Query
 * ============================================================================
 *
 * Retrieves active tenant Payment Method reference data for POS checkout.
 *
 * ============================================================================
 */

import {
  useQuery,
} from "@tanstack/react-query";

import { useQueryScope } from "@/hooks/useQueryScope";
import {
  QUERY_KEYS,
} from "@/lib/queryKeys";
import {
  paymentMethodService,
} from "@/services/payment-methods";
import type { PaymentMethod } from "@/types/entities";

export function usePaymentMethods() {
  const {
    tenantScope,
    isTenantScopeReady,
  } = useQueryScope();

  return useQuery<PaymentMethod[]>({
    queryKey: tenantScope
      ? QUERY_KEYS.paymentMethods.list(
          tenantScope,
        )
      : QUERY_KEYS.paymentMethods.disabled(
          "list",
        ),

    queryFn: () =>
      paymentMethodService.listPaymentMethods(),

    enabled: isTenantScopeReady,
  });
}

export default usePaymentMethods;
