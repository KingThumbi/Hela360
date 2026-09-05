/**
 * ============================================================================
 * Hela360 Platform Authentication Service
 * ============================================================================
 *
 * API communication for Hela360 Office authentication.
 * ============================================================================
 */

import {
  platformApiClient,
} from "@/api/platformClient";

import {
  PLATFORM_AUTH_ENDPOINTS,
} from "@/api/platformAuthEndpoints";

import type {
  PlatformAuthenticatedSession,
  PlatformLoginRequest,
  PlatformLoginResponse,
  PlatformLoginResult,
  PlatformLogoutAllResponse,
  PlatformLogoutResponse,
  PlatformSessionResponse,
  PlatformUser,
} from "@/types/platformAuth";

function toUser(
  user: PlatformLoginResponse["user"],
): PlatformUser {
  return {
    id: user.id,
    email: user.email,
    username: user.username,
    firstName: user.first_name,
    lastName: user.last_name,
  };
}

function toAuthenticatedSession(
  response:
    | PlatformLoginResponse
    | PlatformSessionResponse,
): PlatformAuthenticatedSession {
  return {
    user: toUser(response.user),

    authorization: {
      roles: [
        ...response.authorization.roles,
      ],
      permissions: [
        ...response.authorization.permissions,
      ],
    },

    session: {
      id: response.session.id,
      expiresAt:
        response.session.expires_at ?? null,
    },
  };
}

export class PlatformAuthService {
  async login(
    payload: PlatformLoginRequest,
  ): Promise<PlatformLoginResult> {
    const response =
      await platformApiClient
        .post<PlatformLoginResponse>(
          PLATFORM_AUTH_ENDPOINTS.LOGIN,
          {
            username_or_email:
              payload.usernameOrEmail,

            password: payload.password,

            device_name:
              payload.deviceName,
          },
        );

    return {
      authenticatedSession:
        toAuthenticatedSession(
          response.data,
        ),

      accessToken:
        response.data.access_token,

      refreshToken:
        response.data.refresh_token,
    };
  }

  async getCurrentSession():
    Promise<PlatformAuthenticatedSession> {
    const response =
      await platformApiClient
        .get<PlatformSessionResponse>(
          PLATFORM_AUTH_ENDPOINTS.SESSION,
        );

    return toAuthenticatedSession(
      response.data,
    );
  }

  async logout(
    refreshToken: string,
  ): Promise<PlatformLogoutResponse> {
    const response =
      await platformApiClient
        .post<PlatformLogoutResponse>(
          PLATFORM_AUTH_ENDPOINTS.LOGOUT,
          {
            refresh_token: refreshToken,
          },
        );

    return response.data;
  }

  async logoutAll():
    Promise<PlatformLogoutAllResponse> {
    const response =
      await platformApiClient
        .post<PlatformLogoutAllResponse>(
          PLATFORM_AUTH_ENDPOINTS.LOGOUT_ALL,
        );

    return response.data;
  }
}

export const platformAuthService =
  new PlatformAuthService();

export default platformAuthService;
