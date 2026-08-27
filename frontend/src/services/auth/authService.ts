/**
 * ============================================================================
 * Hela360 Enterprise Authentication Service
 * ============================================================================
 *
 * Service responsible for all authentication-related API communication.
 *
 * Responsibilities
 * ----------------
 * • Login
 * • Logout
 * • Refresh access tokens
 * • Retrieve authenticated user
 * • Forgot password
 * • Reset password
 * • Change password
 * • Session validation
 *
 * This service should be the only layer communicating with authentication
 * endpoints.
 *
 * ============================================================================
 */

import apiClient from "@/api/client";
import { API_ENDPOINTS } from "@/api/endpoints";

import type {
  ChangePasswordRequest,
  ForgotPasswordRequest,
  LoginRequest,
  RefreshTokenRequest,
  ResetPasswordRequest,
} from "@/types/requests";

import type {
  CurrentSessionResponse,
  LoginResponse,
  RefreshTokenResponse,
} from "@/types/responses";

import type { ApiResponse } from "@/types/api";
import type {
  AuthenticatedSession,
  Branch,
  Identity,
  LoginResult,
  SessionRole,
} from "@/types/auth";

/* ============================================================================
 * Authentication Service
 * ============================================================================
 */

export class AuthService {
  /* ==========================================================================
   * Authentication
   * ==========================================================================
   */

  /**
   * Authenticate a user.
   */
  async login(
    payload: LoginRequest,
  ): Promise<LoginResult> {
    const response = await apiClient.post<LoginResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      payload,
    );

    return this.toLoginResult(response.data);
  }

  /**
   * Logout the current user.
   *
   * The backend may revoke refresh tokens and invalidate sessions.
   */
  async logout(): Promise<ApiResponse<void>> {
    const response = await apiClient.post<ApiResponse<void>>(
      API_ENDPOINTS.AUTH.LOGOUT,
    );

    return response.data;
  }

  /**
   * Refresh an expired access token.
   */
  async refreshToken(
    payload: RefreshTokenRequest,
  ): Promise<RefreshTokenResponse> {
    const response =
      await apiClient.post<RefreshTokenResponse>(
        API_ENDPOINTS.AUTH.REFRESH,
        payload,
      );

    return response.data;
  }

  /**
   * Retrieve the current authenticated session.
   */
  async getCurrentSession(): Promise<AuthenticatedSession> {
    const response =
      await apiClient.get<CurrentSessionResponse>(
        API_ENDPOINTS.AUTH.SESSION,
      );

    return this.toAuthenticatedSession(
      response.data,
    );
  }

  /**
   * Backward-compatible current-user projection.
   */
  async getCurrentUser(): Promise<Identity> {
    const session =
      await this.getCurrentSession();

    return session.identity;
  }

  /**
   * Backward-compatible alias for older authentication consumers.
   */
  async me(): Promise<Identity> {
    return this.getCurrentUser();
  }

  /* ==========================================================================
   * Password Recovery
   * ==========================================================================
   */

  /**
   * Request a password reset.
   */
  async forgotPassword(
    payload: ForgotPasswordRequest,
  ): Promise<ApiResponse<void>> {
    const response =
      await apiClient.post<ApiResponse<void>>(
        API_ENDPOINTS.AUTH.FORGOT_PASSWORD,
        payload,
      );

    return response.data;
  }

  /**
   * Reset a forgotten password.
   */
  async resetPassword(
    payload: ResetPasswordRequest,
  ): Promise<ApiResponse<void>> {
    const response =
      await apiClient.post<ApiResponse<void>>(
        API_ENDPOINTS.AUTH.RESET_PASSWORD,
        payload,
      );

    return response.data;
  }

  /**
   * Change the current user's password.
   */
  async changePassword(
    payload: ChangePasswordRequest,
  ): Promise<ApiResponse<void>> {
    const response =
      await apiClient.post<ApiResponse<void>>(
        API_ENDPOINTS.AUTH.CHANGE_PASSWORD,
        payload,
      );

    return response.data;
  }

  /* ==========================================================================
   * Session
   * ==========================================================================
   */

  /**
   * Validate the current authenticated session.
   */
  async validateSession(): Promise<boolean> {
    try {
      await this.getCurrentSession();

      return true;
    } catch {
      return false;
    }
  }

  private toLoginResult(
    response: LoginResponse,
  ): LoginResult {
    return {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      accessExpiresIn: response.access_expires_in,
      refreshExpiresIn: response.refresh_expires_in,
      tokenType: response.token_type,
    };
  }

  private toAuthenticatedSession(
    response: CurrentSessionResponse,
  ): AuthenticatedSession {
    const { session } = response;

    const roles: SessionRole[] =
      session.roles.map((role) => ({
        id: role.id,
        name: role.name,
        code: role.code,
      }));

    const branches: Branch[] =
      session.branches.map((branch) => ({
        id: branch.id,
        tenantId: branch.tenant_id,
        name: branch.name,
        code: branch.code,
        isActive: branch.is_active,
      }));

    return {
      identity: {
        id: session.user.id,
        username: session.user.username,
        firstName: session.user.first_name,
        lastName: session.user.last_name,
        email: session.user.email,
        isActive: session.user.is_active,
        isLocked: session.user.is_locked,
        isOwner: session.user.is_owner,
        tenantId: session.tenant.id,
        tenantName: session.tenant.name,
      },
      branches,
      roles,
      permissions: [...session.permissions],
      defaultBranchId: session.default_branch_id,
    };
  }
}

/* ============================================================================
 * Singleton
 * ============================================================================
 */

export const authService = new AuthService();

export default authService;
