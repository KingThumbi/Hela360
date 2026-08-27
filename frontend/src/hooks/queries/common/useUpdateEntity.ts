/**
 * ============================================================================
 * Hela360 Enterprise Update Entity Mutation
 * ============================================================================
 *
 * Generic mutation hook for updating existing entities.
 *
 * Responsibilities
 * ----------------
 * • Standardize update mutations
 * • Eliminate duplicated mutation logic
 * • Support cache invalidation
 * • Preserve full TanStack Query flexibility
 * • Support optimistic updates
 *
 * This hook powers every update operation throughout Hela360.
 *
 * Example
 * -------
 *
 * const updateProduct = useUpdateEntity(
 *   ({ id, data }) => productService.update(id, data),
 *   invalidateProducts,
 * );
 *
 * ============================================================================
 */

import {
  useMutation,
  useQueryClient,
  type DefaultError,
  type UseMutationOptions,
  type UseMutationResult,
} from "@tanstack/react-query";

import { createMutationOptions } from "@/lib/queryFactory";

import type { InvalidateCallback } from "./useCreateEntity";

/* ============================================================================
 * Types
 * ============================================================================
 */

export interface UpdateEntityPayload<TUpdate> {
  /**
   * Entity identifier.
   */
  id: string | number;

  /**
   * Updated entity data.
   */
  data: TUpdate;
}

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Generic update mutation.
 */
export function useUpdateEntity<
  TResult,
  TUpdate,
  TOnMutateResult = unknown,
>(
  mutationFn: (
    payload: UpdateEntityPayload<TUpdate>,
  ) => Promise<TResult>,

  invalidate?: InvalidateCallback,

  options?: Omit<
    UseMutationOptions<
      TResult,
      DefaultError,
      UpdateEntityPayload<TUpdate>,
      TOnMutateResult
    >,
    "mutationFn"
  >,
): UseMutationResult<
  TResult,
  DefaultError,
  UpdateEntityPayload<TUpdate>,
  TOnMutateResult
> {
  const queryClient = useQueryClient();

  return useMutation(
    createMutationOptions<
      TResult,
      UpdateEntityPayload<TUpdate>,
      TOnMutateResult
    >(
      mutationFn,
      {
        ...options,

        onSuccess: async (
          data,
          variables,
          onMutateResult,
          context,
        ) => {
          if (invalidate) {
            await invalidate(queryClient);
          }

          await options?.onSuccess?.(
            data,
            variables,
            onMutateResult,
            context,
          );
        },
      },
    ),
  );
}

export default useUpdateEntity;
