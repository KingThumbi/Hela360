import {
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

import {
  useQueryScope,
} from "@/hooks/useQueryScope";

import {
  QUERY_KEYS,
} from "@/lib/queryKeys";

import {
  productService,
} from "@/services/products";


interface ProductUnitLifecycleVariables {
  productId: string;
  productUnitId: string;
}


export function useRestoreProductUnit() {
  const queryClient = useQueryClient();

  const {
    tenantScope,
  } = useQueryScope();

  return useMutation({
    mutationFn: ({
      productId,
      productUnitId,
    }: ProductUnitLifecycleVariables) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to restore product units.",
        );
      }

      return productService.restoreProductUnit(
        productId,
        productUnitId,
      );
    },

    onSuccess: async (
      _productUnit,
      variables,
    ) => {
      if (!tenantScope) {
        return;
      }

      await queryClient.invalidateQueries({
        queryKey:
          QUERY_KEYS.products.units(
            tenantScope,
            variables.productId,
          ),
      });
    },
  });
}


export default useRestoreProductUnit;
