/**
 * ============================================================================
 * Hela360 Enterprise Delete Entity Mutation
 * ============================================================================
 *
 * Generic mutation hook for deleting entities.
 *
 * Responsibilities
 * ----------------
 * • Standardize delete mutations
 * • Eliminate duplicated mutation logic
 * • Support cache invalidation
 * • Preserve full TanStack Query flexibility
 * • Support optimistic deletion
 *
 * This hook powers every delete operation throughout Hela360.
 *
 * Example
 * -------
 *
 * const deleteProduct = useDeleteEntity(
 *   (id) => productService.delete(id),
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

export type EntityId = string | number;

/* ============================================================================
 * Hook
 * ============================================================================
 */

/**
 * Generic delete mutation.
 */
export function useDeleteEntity<
  TResult = void,
  TOnMutateResult = unknown,
>(
  mutationFn: (
    id: EntityId,
  ) => Promise<TResult>,

  invalidate?: InvalidateCallback,

  options?: Omit<
    UseMutationOptions<
      TResult,
      DefaultError,
      EntityId,
      TOnMutateResult
    >,
    "mutationFn"
  >,
): UseMutationResult<
  TResult,
  DefaultError,
  EntityId,
  TOnMutateResult
> {
  const queryClient = useQueryClient();

  return useMutation(
    createMutationOptions<
      TResult,
      EntityId,
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
            await invalidate(
              queryClient,
            );
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

export default useDeleteEntity;
