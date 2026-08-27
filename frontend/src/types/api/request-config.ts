/**
 * Canonical transport request configuration contracts.
 */

export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE";

export interface RequestConfig {
  signal?: AbortSignal;
  headers?: Record<string, string>;
  params?: Record<
    string,
    string | number | boolean | undefined | null
  >;
}

export type EntityId = string;
