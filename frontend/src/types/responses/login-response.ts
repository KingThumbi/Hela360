/**
 * Login response returned by the authentication API.
 */

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  access_expires_in: number;
  refresh_expires_in: number;
  token_type: string;
}
