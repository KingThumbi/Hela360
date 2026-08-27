import type {
  BranchQueryScope,
  TenantQueryScope,
} from "@/types/domains/query-scope";

export type QueryKeySegment =
  | string
  | number
  | boolean
  | null
  | undefined
  | readonly QueryKeySegment[]
  | { readonly [key: string]: QueryKeySegment };

function normalizeScopeId(value: string, label: string): string {
  const normalized = value.trim();

  if (normalized.length === 0) {
    throw new Error(`${label} is required for scoped query keys.`);
  }

  return normalized;
}

export function normalizeTenantQueryScope(
  scope: TenantQueryScope,
): TenantQueryScope {
  return Object.freeze({
    tenantId: normalizeScopeId(scope.tenantId, "tenantId"),
  });
}

export function normalizeBranchQueryScope(
  scope: BranchQueryScope,
): BranchQueryScope {
  return Object.freeze({
    tenantId: normalizeScopeId(scope.tenantId, "tenantId"),
    branchId: normalizeScopeId(scope.branchId, "branchId"),
  });
}

export function createTenantQueryKey(
  scope: TenantQueryScope,
  domain: string,
  ...segments: readonly QueryKeySegment[]
) {
  const normalizedScope = normalizeTenantQueryScope(scope);

  return [
    "tenant",
    normalizedScope.tenantId,
    normalizeScopeId(domain, "domain"),
    ...segments,
  ] as const;
}

export function createBranchQueryKey(
  scope: BranchQueryScope,
  domain: string,
  ...segments: readonly QueryKeySegment[]
) {
  const normalizedScope = normalizeBranchQueryScope(scope);

  return [
    "tenant",
    normalizedScope.tenantId,
    "branch",
    normalizedScope.branchId,
    normalizeScopeId(domain, "domain"),
    ...segments,
  ] as const;
}

export function createPlatformQueryKey(
  domain: string,
  ...segments: readonly QueryKeySegment[]
) {
  return ["platform", normalizeScopeId(domain, "domain"), ...segments] as const;
}

export function createIdentityQueryKey(
  ...segments: readonly QueryKeySegment[]
) {
  return ["identity", ...segments] as const;
}
