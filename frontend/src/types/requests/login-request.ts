/**
 * Login request payload accepted by the authentication API.
 *
 * Tenant identity is resolved server-side from the public workspace
 * identifier. Internal tenant UUIDs are not supplied by the login client.
 */
export interface LoginRequest {
  workspace: string;
  email: string;
  password: string;
  branch_id?: string | null;
  remember_me?: boolean;
  device_name?: string | null;
}