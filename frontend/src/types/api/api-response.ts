/**
 * Canonical generic API response contracts.
 */

export interface ApiResponse<T> {
  data: T;
  ok?: boolean;
  message?: string;
}

export interface ListResponse<T> {
  items: T[];
  count?: number;
  ok?: boolean;
}

export interface MutationResponse<T> {
  data: T;
  message?: string;
  ok?: boolean;
}

export interface HealthResponse {
  ok: boolean;
  service: string;
  status: string;
}

export interface EmptyResponse {
  success: true;
}
