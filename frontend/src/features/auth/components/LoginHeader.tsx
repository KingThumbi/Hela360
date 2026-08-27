/**
 * Login page branding header.
 */

import { APP_NAME } from "@/constants";

export function LoginHeader() {
  return (
    <header className="space-y-2 text-center">
      <p className="text-sm font-medium text-primary">
        {APP_NAME}
      </p>

      <h1 className="text-2xl font-semibold tracking-normal text-foreground">
        Enterprise Login Page
      </h1>
    </header>
  );
}
