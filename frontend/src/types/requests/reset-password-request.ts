/**
 * Reset-password request payload.
 */

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}
