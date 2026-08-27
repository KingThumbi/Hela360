/**
 * ============================================================================
 * Hela360 Enterprise Login Form
 * ============================================================================
 *
 * Owns login form state, validation, submission, loading state and error
 * presentation for the authentication entry point.
 *
 * ============================================================================
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin } from "@/hooks/queries/auth";
import { PATHS } from "@/routes/routes";
import type { LoginRequest } from "@/types/requests";
import {
  loginSchema,
  type LoginFormValues,
} from "@/validation/authSchema";

/* ============================================================================
 * Component
 * ============================================================================
 */

export function LoginForm() {
  const navigate = useNavigate();

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const loginMutation = useLogin();

  const {
    formState: { errors },
    handleSubmit,
    register,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      workspace: "",
      username: "",
      password: "",
      rememberMe: false,
    },
  });

  const onSubmit = (
    values: LoginFormValues,
  ) => {
    const payload: LoginRequest = {
      workspace: values.workspace.trim(),
      email: values.username.trim(),
      password: values.password,
      branch_id: null,
      remember_me: values.rememberMe,
      device_name: null,
    };

    loginMutation.mutate(
      payload,
      {
        onSuccess: () => {
          navigate(
            PATHS.DASHBOARD,
            {
              replace: true,
            },
          );
        },
      },
    );
  };

  const errorMessage =
    loginMutation.error instanceof Error
      ? loginMutation.error.message
      : null;

  return (
    <form
      className="space-y-5"
      onSubmit={handleSubmit(onSubmit)}
    >
      {/* ---------------------------------------------------------------
       * Workspace
       * --------------------------------------------------------------- */}
      <div className="space-y-2">
        <Label htmlFor="workspace">
          Workspace
        </Label>

        <Input
          id="workspace"
          autoComplete="organization"
          placeholder="e.g. dimples"
          aria-invalid={
            errors.workspace
              ? true
              : undefined
          }
          {...register("workspace")}
        />

        {errors.workspace ? (
          <p className="text-sm text-destructive">
            {errors.workspace.message}
          </p>
        ) : null}
      </div>

      {/* ---------------------------------------------------------------
       * Username / Email
       * --------------------------------------------------------------- */}
      <div className="space-y-2">
        <Label htmlFor="username">
          Username or email
        </Label>

        <Input
          id="username"
          autoComplete="username"
          aria-invalid={
            errors.username
              ? true
              : undefined
          }
          {...register("username")}
        />

        {errors.username ? (
          <p className="text-sm text-destructive">
            {errors.username.message}
          </p>
        ) : null}
      </div>

      {/* ---------------------------------------------------------------
       * Password
       * --------------------------------------------------------------- */}
      <div className="space-y-2">
        <Label htmlFor="password">
          Password
        </Label>

        <div className="relative">
          <Input
            id="password"
            type={
              showPassword
                ? "text"
                : "password"
            }
            autoComplete="current-password"
            aria-invalid={
              errors.password
                ? true
                : undefined
            }
            className="pr-10"
            {...register("password")}
          />

          <button
            type="button"
            onClick={() =>
              setShowPassword(
                (current) => !current,
              )
            }
            className="
              absolute
              right-3
              top-1/2
              -translate-y-1/2
              text-muted-foreground
              transition-colors
              hover:text-foreground
            "
            aria-label={
              showPassword
                ? "Hide password"
                : "Show password"
            }
            aria-pressed={showPassword}
          >
            {showPassword ? (
              <EyeOff className="size-4" />
            ) : (
              <Eye className="size-4" />
            )}
          </button>
        </div>

        {errors.password ? (
          <p className="text-sm text-destructive">
            {errors.password.message}
          </p>
        ) : null}
      </div>

      {/* ---------------------------------------------------------------
       * Remember Me
       * --------------------------------------------------------------- */}
      <label
        htmlFor="rememberMe"
        className="
          flex
          items-center
          gap-2
          text-sm
          text-muted-foreground
        "
      >
        <input
          id="rememberMe"
          type="checkbox"
          className="size-4 rounded border-input"
          {...register("rememberMe")}
        />

        Remember me
      </label>

      {/* ---------------------------------------------------------------
       * Authentication Error
       * --------------------------------------------------------------- */}
      {errorMessage ? (
        <p className="text-sm text-destructive">
          {errorMessage}
        </p>
      ) : null}

      {/* ---------------------------------------------------------------
       * Submit
       * --------------------------------------------------------------- */}
      <Button
        type="submit"
        className="w-full"
        disabled={loginMutation.isPending}
      >
        {loginMutation.isPending
          ? "Signing in..."
          : "Sign in"}
      </Button>
    </form>
  );
}

export default LoginForm;