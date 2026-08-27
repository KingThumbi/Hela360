/**
 * ============================================================================
 * Hela360 Administration Services
 * ============================================================================
 *
 * Central export point for all administration services.
 *
 * Exports:
 * • Users
 * • Roles
 * • Permissions
 * • Branches
 * • Tenants
 *
 * ============================================================================
 */

/* ============================================================================
 * User Service
 * ============================================================================
 */

export {
  UserService,
  userService,
} from "./userService";

export type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
} from "./userService";

/* ============================================================================
 * Role Service
 * ============================================================================
 */

export {
  RoleService,
  roleService,
} from "./roleService";

export type {
  Role,
  CreateRoleRequest,
  UpdateRoleRequest,
  RolePermission,
  RoleUser,
} from "./roleService";

/* ============================================================================
 * Permission Service
 * ============================================================================
 */

export {
  PermissionService,
  permissionService,
} from "./permissionService";

export type {
  Permission,
} from "./permissionService";

/* ============================================================================
 * Branch Service
 * ============================================================================
 */

export {
  BranchService,
  branchService,
} from "./branchService";

export type {
  Branch,
  CreateBranchRequest,
  UpdateBranchRequest,
  BranchUser,
} from "./branchService";

/* ============================================================================
 * Tenant Service
 * ============================================================================
 */

export {
  TenantService,
  tenantService,
} from "./tenantService";

export type {
  Tenant,
  CreateTenantRequest,
  UpdateTenantRequest,
  TenantUser,
} from "./tenantService";
