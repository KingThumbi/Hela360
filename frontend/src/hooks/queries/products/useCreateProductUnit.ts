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
  CreateProductUnitRequest,
} from "@/types/requests";


interface CreateProductUnitVariables {
  productId: string;
  data: CreateProductUnitRequest;
}


export function useCreateProductUnit() {
  const queryClient = useQueryClient();

  const {
    tenantScope,
  } = useQueryScope();

  return useMutation({
    mutationFn: ({
      productId,
      data,
    }: CreateProductUnitVariables) => {
      if (!tenantScope) {
        throw new Error(
          "Tenant scope is required to create product units.",
        );
      }

      return productService.createProductUnit(
        productId,
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


export default useCreateProductUnit;
