import {
  Eye,
  EyeOff,
  ShieldCheck,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  useForm,
} from "react-hook-form";

import {
  Navigate,
  useNavigate,
} from "react-router-dom";

import {
  Button,
} from "@/components/ui/button";

import {
  Card,
} from "@/components/ui/card";

import {
  Input,
} from "@/components/ui/input";

import {
  Label,
} from "@/components/ui/label";

import {
  usePlatformLogin,
} from "@/hooks/queries/platform-auth";

import {
  OFFICE_PATHS,
} from "@/routes/officeRoutes";

import {
  usePlatformAuthStore,
} from "@/store/platformAuthStore";

interface OfficeLoginFormValues {
  usernameOrEmail: string;
  password: string;
}

export function OfficeLoginPage() {
  const navigate = useNavigate();

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const isAuthenticated =
    usePlatformAuthStore(
      (state) => state.isAuthenticated,
    );

  const isInitializing =
    usePlatformAuthStore(
      (state) => state.isInitializing,
    );

  const loginMutation =
    usePlatformLogin();

  const {
    formState: {
      errors,
    },
    handleSubmit,
    register,
  } = useForm<OfficeLoginFormValues>({
    defaultValues: {
      usernameOrEmail: "",
      password: "",
    },
  });

  if (
    !isInitializing &&
    isAuthenticated
  ) {
    return (
      <Navigate
        to={OFFICE_PATHS.DASHBOARD}
        replace
      />
    );
  }

  const onSubmit = (
    values: OfficeLoginFormValues,
  ) => {
    loginMutation.mutate(
      {
        usernameOrEmail:
          values.usernameOrEmail.trim(),

        password:
          values.password,

        deviceName:
          "Hela360 Office Web",
      },
      {
        onSuccess: () => {
          navigate(
            OFFICE_PATHS.DASHBOARD,
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
    <main className="flex min-h-screen items-center justify-center bg-muted/30 p-6">
      <div className="w-full max-w-md space-y-8">
        <div className="space-y-3 text-center">
          <div className="mx-auto flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <ShieldCheck className="size-6" />
          </div>

          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Hela360 Office
            </h1>

            <p className="mt-1 text-sm text-muted-foreground">
              Platform administration
            </p>
          </div>
        </div>

        <Card className="p-8">
          <form
            className="space-y-5"
            onSubmit={handleSubmit(onSubmit)}
          >
            <div className="space-y-2">
              <Label htmlFor="office-username">
                Username or email
              </Label>

              <Input
                id="office-username"
                autoComplete="username"
                aria-invalid={
                  errors.usernameOrEmail
                    ? true
                    : undefined
                }
                {...register(
                  "usernameOrEmail",
                  {
                    required:
                      "Username or email is required.",
                  },
                )}
              />

              {errors.usernameOrEmail ? (
                <p className="text-sm text-destructive">
                  {
                    errors
                      .usernameOrEmail
                      .message
                  }
                </p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="office-password">
                Password
              </Label>

              <div className="relative">
                <Input
                  id="office-password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  autoComplete="current-password"
                  className="pr-10"
                  aria-invalid={
                    errors.password
                      ? true
                      : undefined
                  }
                  {...register(
                    "password",
                    {
                      required:
                        "Password is required.",
                    },
                  )}
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(
                      (current) => !current,
                    )
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground transition-colors hover:text-foreground"
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  aria-pressed={
                    showPassword
                  }
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

            {errorMessage ? (
              <p className="text-sm text-destructive">
                {errorMessage}
              </p>
            ) : null}

            <Button
              type="submit"
              className="w-full"
              disabled={
                loginMutation.isPending
              }
            >
              {
                loginMutation.isPending
                  ? "Signing in..."
                  : "Sign in to Hela360 Office"
              }
            </Button>
          </form>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          Authorized Hela360 platform personnel only.
        </p>
      </div>
    </main>
  );
}

export default OfficeLoginPage;
