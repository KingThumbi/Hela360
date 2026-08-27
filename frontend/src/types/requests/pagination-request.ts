/**
 * Canonical outbound pagination query contract.
 */

export interface PaginationRequest {
  page?: number;
  per_page?: number;
  search?: string;
  q?: string;
}
