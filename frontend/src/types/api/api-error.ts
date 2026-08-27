/**
 * Canonical transport error contracts.
 */

export interface ValidationError {
  field: string;
  message: string;
}

export interface ApiError {
  code: string;
  message: string;
  status?: number;
  validationErrors?: ValidationError[];
  details?: unknown;
}
