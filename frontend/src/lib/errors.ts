/**
 * ============================================================================
 * Hela360 Enterprise Error Framework
 * ============================================================================
 *
 * Centralized application error hierarchy.
 *
 * Every error exposed to the UI should derive from AppError.
 *
 * Responsibilities
 * ----------------
 * • Normalize API errors
 * • Standardize error handling
 * • Preserve HTTP status codes
 * • Preserve backend error codes
 * • Support retry logic
 * • Support toast notifications
 * • Support logging
 *
 * The API client is responsible for converting transport-specific
 * errors (Axios, Fetch, etc.) into these application errors.
 * ============================================================================
 */

import type {
  AxiosError,
} from "axios";

import {
  ERROR_CODES,
} from "@/types/enums";

import type {
  ApiError,
} from "@/types/api";

import type {
  ErrorCode,
} from "@/types/enums";

/**
 * ============================================================================
 * Error Codes
 * ============================================================================
 */

export {
  ERROR_CODES,
};

export type {
  ErrorCode,
};

export type ErrorCategory =
  | "network"
  | "transport"
  | "business"
  | "validation"
  | "system";

interface BackendErrorEnvelope {
  error?: string | {
    code?: string;
    message?: string;
    details?: unknown;
    validationErrors?: ApiError["validationErrors"];
  };
  code?: string;
  message?: string;
  details?: unknown;
  validationErrors?: ApiError["validationErrors"];
}
/**
 * ============================================================================
 * Base Application Error
 * ============================================================================
 */

export class AppError extends Error {
  readonly code: ErrorCode | string;

  readonly category: ErrorCategory;

  readonly status?: number;

  readonly details?: unknown;

  readonly validationErrors?: ApiError["validationErrors"];

  readonly retryable: boolean;

  constructor(
    error: ApiError,
    category: ErrorCategory = "system",
    retryable = false,
  ) {
    super(error.message);

    this.name = this.constructor.name;

    this.code = error.code;

    this.status = error.status;

    this.details = error.details;

    this.validationErrors = error.validationErrors;

    this.category = category;

    this.retryable = retryable;

    Object.setPrototypeOf(this, new.target.prototype);
  }

  static fromAxios(
    error: AxiosError<unknown>,
  ): AppError {
    return createAppError(
      normalizeAxiosError(error),
    );
  }
}

/**
 * ============================================================================
 * Authentication
 * ============================================================================
 */

export class AuthenticationError extends AppError {}

export class AuthorizationError extends AppError {}

export class ForbiddenError extends AppError {}

/**
 * ============================================================================
 * Validation
 * ============================================================================
 */

export class ValidationError extends AppError {}

/**
 * ============================================================================
 * Infrastructure
 * ============================================================================
 */

export class NetworkError extends AppError {}

export class TimeoutError extends AppError {}

export class ServerError extends AppError {}

/**
 * ============================================================================
 * Domain
 * ============================================================================
 */

export class NotFoundError extends AppError {}

export class ConflictError extends AppError {}

export class TenantError extends AppError {}

export class BranchError extends AppError {}

/**
 * ============================================================================
 * Factory
 * ============================================================================
 *
 * Converts a normalized ApiError into a typed AppError.
 */

export function createAppError(
  error: ApiError,
): AppError {
  switch (error.code) {
    case ERROR_CODES.NETWORK:
      return new NetworkError(
        error,
        "network",
        true,
      );

    case ERROR_CODES.TIMEOUT:
      return new TimeoutError(
        error,
        "network",
        true,
      );

    case ERROR_CODES.AUTHENTICATION:
      return new AuthenticationError(
        error,
        "transport",
        false,
      );

    case ERROR_CODES.AUTHORIZATION:
      return new AuthorizationError(
        error,
        "transport",
        false,
      );

    case ERROR_CODES.FORBIDDEN:
      return new ForbiddenError(
        error,
        "transport",
        false,
      );

    case ERROR_CODES.VALIDATION:
      return new ValidationError(
        error,
        "validation",
        false,
      );

    case ERROR_CODES.NOT_FOUND:
      return new NotFoundError(
        error,
        "transport",
        false,
      );

    case ERROR_CODES.CONFLICT:
      return new ConflictError(
        error,
        "business",
        false,
      );

    case ERROR_CODES.SERVER:
      return new ServerError(
        error,
        "transport",
        true,
      );

    case ERROR_CODES.TENANT:
      return new TenantError(
        error,
        "business",
        false,
      );

    case ERROR_CODES.BRANCH:
      return new BranchError(
        error,
        "business",
        false,
      );

    default:
      return new AppError(error);
  }
}

function normalizeAxiosError(
  error: AxiosError<unknown>,
): ApiError {
  if (error.code === "ECONNABORTED") {
    return {
      code: ERROR_CODES.TIMEOUT,
      message: "Unable to reach the server. Please try again.",
      status: error.response?.status,
      details: error.response?.data,
    };
  }

  if (!error.response) {
    return {
      code: ERROR_CODES.NETWORK,
      message: "Unable to reach the server. Please try again.",
      details: error.message,
    };
  }

  const status = error.response.status;
  const payload =
    readBackendErrorEnvelope(
      error.response.data,
    );

  return {
    code:
      payload.code ??
      codeFromStatus(status),
    message:
      payload.message ??
      messageFromStatus(status),
    status,
    details:
      payload.details ??
      error.response.data,
    validationErrors:
      payload.validationErrors,
  };
}

function readBackendErrorEnvelope(
  data: unknown,
): BackendErrorEnvelope {
  if (
    typeof data !== "object" ||
    data === null
  ) {
    return {};
  }

  const envelope =
    data as BackendErrorEnvelope;

  if (
    typeof envelope.error === "object" &&
    envelope.error !== null
  ) {
    return {
      code:
        envelope.error.code ??
        envelope.code,
      message:
        envelope.error.message ??
        envelope.message,
      details:
        envelope.error.details ??
        envelope.details,
      validationErrors:
        envelope.error.validationErrors ??
        envelope.validationErrors,
    };
  }

  if (typeof envelope.error === "string") {
    return {
      code: envelope.code,
      message: envelope.error,
      details: envelope.details,
      validationErrors:
        envelope.validationErrors,
    };
  }

  return envelope;
}

function codeFromStatus(
  status: number,
): ErrorCode {
  if (status === 401) {
    return ERROR_CODES.AUTHENTICATION;
  }

  if (status === 403) {
    return ERROR_CODES.FORBIDDEN;
  }

  if (status === 404) {
    return ERROR_CODES.NOT_FOUND;
  }

  if (status === 409) {
    return ERROR_CODES.CONFLICT;
  }

  if (status === 400 || status === 422) {
    return ERROR_CODES.VALIDATION;
  }

  if (status >= 500) {
    return ERROR_CODES.SERVER;
  }

  return ERROR_CODES.UNKNOWN;
}

function messageFromStatus(
  status: number,
): string {
  if (status === 401) {
    return "Your session has expired. Please sign in again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "The requested resource was not found.";
  }

  if (status === 409) {
    return "The request conflicts with the current state.";
  }

  if (status === 400 || status === 422) {
    return "Please check the submitted information.";
  }

  if (status >= 500) {
    return "The server could not complete the request. Please try again.";
  }

  return "An unexpected error occurred.";
}
