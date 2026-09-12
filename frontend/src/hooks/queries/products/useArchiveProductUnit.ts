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


export function useArchiveProductUnit() {
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
          "Tenant scope is required to archive product units.",
        );
      }

      return productService.archiveProductUnit(
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


export default useArchiveProductUnit;
