/**
 * ============================================================================
 * Hela360 Authentication Types
 * ============================================================================
 *
 * Shared authentication and identity models used throughout the frontend.
 *
 * The Identity interface mirrors the backend AuthorizationContext and serves
 * as the canonical representation of the authenticated user.
 * ============================================================================
 */

/**
 * Authenticated user identity.
 *
 * This mirrors the backend AuthorizationContext.
 */
export interface Identity {
  /**
   * User
   */
  id: string;

  username: string | null;

  firstName: string;

  lastName: string | null;

  email: string | null;

  avatarUrl?: string;

  /**
   * Account
   */
  isActive: boolean;

  isLocked: boolean;

  isOwner: boolean;

  /**
   * Tenant
   */
  tenantId: string;

  tenantName: string;

  /**
   * Authorization data is retained as inert session data until the
   * Authorization Context migration owns frontend permission decisions.
   */

}

/**
 * Tenant summary.
 */
export interface Tenant {
  id: string;

  name: string;
}

/**
 * Branch summary.
 */
export interface Branch {
  id: string;

  tenantId: string;

  name: string;

  code: string;

  isActive: boolean;
}

/**
 * Authenticated session role summary.
 */
export interface SessionRole {
  id: string;

  name: string;

  code: string;
}

/**
 * Backend-owned permission code.
 *
 * Permission codes are dynamic strings returned in the authenticated session.
 * The frontend consumes them as effective permissions and does not maintain a
 * closed permission union.
 */
export type PermissionCode = string;

/**
 * Frontend application session produced by authService.
 */
export interface AuthenticatedSession {
  identity: Identity;

  branches: Branch[];

  roles: SessionRole[];

  permissions: PermissionCode[];

  defaultBranchId: string | null;
}

/**
 * Frontend login result produced by the authentication service.
 *
 * The backend login response currently returns tokens only. Identity remains
 * optional until a confirmed current-user source is wired into the auth flow.
 */
export interface LoginResult {
  accessToken: string;

  refreshToken: string;

  accessExpiresIn: number;

  refreshExpiresIn: number;

  tokenType: string;

  identity?: Identity;
}

export type {
  LoginRequest,
  RefreshTokenRequest,
} from "./requests";

export type {
  LoginResponse,
  RefreshTokenResponse,
} from "./responses";
