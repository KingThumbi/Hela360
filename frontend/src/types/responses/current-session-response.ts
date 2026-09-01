/**
 * Current authenticated session response envelope.
 *
 * Mirrors GET /api/auth/session exactly. Backend field names remain
 * snake_case in transport DTOs.
 */

export interface CurrentSessionUserResponse {
  id: string;
  email: string | null;
  username: string | null;
  first_name: string;
  last_name: string | null;
  is_active: boolean;
  is_locked: boolean;
  is_owner: boolean;
  is_platform_admin: boolean;
}

export interface CurrentSessionTenantResponse {
  id: string;
  name: string;
  status: string;
  is_active: boolean;
}

export interface CurrentSessionRoleResponse {
  id: string;
  name: string;
  code: string;
}

export interface CurrentSessionBranchResponse {
  id: string;
  tenant_id: string;
  name: string;
  code: string;
  is_active: boolean;
}

export interface CurrentSession {
  user: CurrentSessionUserResponse;
  tenant: CurrentSessionTenantResponse;
  roles: CurrentSessionRoleResponse[];
  permissions: string[];
  branches: CurrentSessionBranchResponse[];
  default_branch_id: string | null;
}

export interface CurrentSessionResponse {
  session: CurrentSession;
}
