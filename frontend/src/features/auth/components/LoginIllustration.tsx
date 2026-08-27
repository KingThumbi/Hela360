/**
 * Login page brand panel.
 */

import { APP_NAME } from "@/constants";

export function LoginIllustration() {
  return (
    <div className="max-w-md space-y-4 px-10 text-primary-foreground">
      <p className="text-sm font-medium opacity-80">
        {APP_NAME}
      </p>

      <h2 className="text-4xl font-semibold tracking-normal">
        Authentication entry point for the application.
      </h2>
    </div>
  );
}
