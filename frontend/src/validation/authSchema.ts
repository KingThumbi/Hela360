/**
 * ============================================================================
 * Hela360 Enterprise Authentication Validation
 * ============================================================================
 *
 * Zod schemas for authentication and account security.
 *
 * Responsibilities
 * ----------------
 * • Login validation
 * • Password validation
 * • Password reset validation
 * • Forgot password validation
 * • Change password validation
 * • Type inference
 *
 * Every authentication form should use these schemas via
 * React Hook Form's Zod resolver.
 *
 * ============================================================================
 */

import { z } from "zod";

/* ============================================================================
 * Constants
 * ============================================================================
 */

const PASSWORD_MIN_LENGTH = 8;

const PASSWORD_MAX_LENGTH = 128;

/* ============================================================================
 * Common Fields
 * ============================================================================
 */

/**
 * Username or email.
 */
export const usernameSchema = z
  .string()
  .trim()
  .min(1, "Username or email is required.")
  .max(255, "Username is too long.");

/**
 * Email.
 */
export const emailSchema = z
  .email("Enter a valid email address.")
  .max(255, "Email is too long.");

/**
 * Enterprise password policy.
 *
 * Current policy:
 * • Minimum 8 characters
 * • Maximum 128 characters
 *
 * Complexity rules can be strengthened later without
 * changing consuming forms.
 */
export const passwordSchema = z
  .string()
  .min(
    PASSWORD_MIN_LENGTH,
    `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`,
  )
  .max(
    PASSWORD_MAX_LENGTH,
    `Password must not exceed ${PASSWORD_MAX_LENGTH} characters.`,
  );

/**
 * Public tenant workspace identifier.
 *
 * Workspace identifiers are normalized by the backend, but the frontend
 * performs basic validation to provide immediate feedback to the user.
 */
export const workspaceSchema = z
  .string()
  .trim()
  .min(1, "Workspace is required.")
  .max(80, "Workspace must not exceed 80 characters.");

/* ============================================================================
 * Login
 * ============================================================================
 */

export const loginSchema = z.object({
  workspace: workspaceSchema,

  username: usernameSchema,

  password: passwordSchema,

  rememberMe: z.boolean(),
});

/* ============================================================================
 * Forgot Password
 * ============================================================================
 */

export const forgotPasswordSchema = z.object({
  email: emailSchema,
});

/* ============================================================================
 * Reset Password
 * ============================================================================
 */

export const resetPasswordSchema = z
  .object({
    token: z
      .string()
      .trim()
      .min(1, "Reset token is required."),

    password: passwordSchema,

    confirmPassword: z.string(),
  })
  .refine(
    (data) => data.password === data.confirmPassword,
    {
      path: ["confirmPassword"],
      message: "Passwords do not match.",
    },
  );

/* ============================================================================
 * Change Password
 * ============================================================================
 */

export const changePasswordSchema = z
  .object({
    currentPassword: z
      .string()
      .min(1, "Current password is required."),

    newPassword: passwordSchema,

    confirmPassword: z.string(),
  })
  .refine(
    (data) => data.newPassword === data.confirmPassword,
    {
      path: ["confirmPassword"],
      message: "Passwords do not match.",
    },
  );

/* ============================================================================
 * Types
 * ============================================================================
 */

export type LoginFormValues = z.infer<
  typeof loginSchema
>;

export type ForgotPasswordFormValues = z.infer<
  typeof forgotPasswordSchema
>;

export type ResetPasswordFormValues = z.infer<
  typeof resetPasswordSchema
>;

export type ChangePasswordFormValues = z.infer<
  typeof changePasswordSchema
>;