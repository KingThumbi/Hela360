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

import type {
  UpdateProductUnitRequest,
} from "@/types/requests";


interface UpdateProductUnitVariables {
  productId: string;
  productUnitId: string;
  data: UpdateProductUnitRequest;
}


export function useUpdateProductUnit() {
  const queryClient = useQueryClient();

  const {
    tenantScope,
  } = useQueryScope();

  return useMutation({
    mutationFn: ({
      productId,
      productUnitId,
      data,
    }: UpdateProductUnitVariables) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to update product units.",
        );
      }

      return productService.updateProductUnit(
        productId,
        productUnitId,
        data,
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


export default useUpdateProductUnit;
