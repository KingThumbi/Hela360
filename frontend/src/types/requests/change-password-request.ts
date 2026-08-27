/**
 * Authenticated password-change request payload.
 */

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
