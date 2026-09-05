/**
 * ============================================================================
 * Hela360 Platform Authentication Types
 * ============================================================================
 *
 * Authentication contracts for Hela360 Office.
 *
 * Platform identities are intentionally independent of tenant identities.
 * No tenant or branch scope belongs in this domain.
 * ============================================================================
 */

export interface PlatformUser {
  id: string;
  email: string;
  username: string;
  firstName: string;
  lastName: string | null;
}

export interface PlatformAuthorization {
  roles: string[];
  permissions: string[];
}

export interface PlatformSession {
  id: string;
  expiresAt: string | null;
}

export interface PlatformAuthenticatedSession {
  user: PlatformUser;
  authorization: PlatformAuthorization;
  session: PlatformSession;
}

export interface PlatformLoginRequest {
  usernameOrEmail: string;
  password: string;
  deviceName?: string;
}

export interface PlatformLoginResponse {
  success: true;

  access_token: string;
  refresh_token: string;
  token_type: string;

  user: {
    id: string;
    email: string;
    username: string;
    first_name: string;
    last_name: string | null;
  };

  authorization: {
    roles: string[];
    permissions: string[];
  };

  session: {
    id: string;
    expires_at?: string | null;
  };
}

export interface PlatformRefreshResponse {
  success: true;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PlatformSessionResponse {
  success: true;

  user: {
    id: string;
    email: string;
    username: string;
    first_name: string;
    last_name: string | null;
  };

  authorization: {
    roles: string[];
    permissions: string[];
  };

  session: {
    id: string;
    expires_at?: string | null;
  };
}

export interface PlatformLogoutResponse {
  success: true;
  session_id: string;
}

export interface PlatformLogoutAllResponse {
  success: true;
}

export interface PlatformLoginResult {
  authenticatedSession:
    PlatformAuthenticatedSession;

  accessToken: string;
  refreshToken: string;
}
