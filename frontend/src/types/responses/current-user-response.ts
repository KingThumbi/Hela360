/**
 * Current authenticated user response projection.
 */

export interface CurrentUserResponse {
  id: string;
  email: string;
  username: string | null;
  first_name: string;
  last_name: string;
  tenant_id: string;
  branch_id: string | null;
  role: string | null;
  permissions: string[];
  is_owner: boolean;
  is_active: boolean;
}
