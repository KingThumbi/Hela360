/**
 * ============================================================================
 * Hela360 Enterprise Login Page
 * ============================================================================
 *
 * Authentication entry point for the application.
 *
 * Responsibilities
 * ----------------
 * • Compose the login experience
 * • Display branding
 * • Arrange authentication components
 * • Remain free of business logic
 *
 * Business Logic
 * --------------
 * Authentication is delegated to LoginForm.
 *
 * Future Enhancements
 * -------------------
 * • Multi-factor authentication (MFA)
 * • Single Sign-On (SSO)
 * • Passwordless authentication
 * • Organization selection
 * • Language selection
 * • Security announcements
 * • Maintenance notifications
 * *
 * ============================================================================
 */

import { Card } from "@/components/ui/card";

import {
  LoginFooter,
  LoginForm,
  LoginHeader,
  LoginIllustration,
} from "./components";

/* ============================================================================
 * Component
 * ============================================================================
 */

export function LoginPage() {
  return (
    <main className="min-h-screen bg-muted/30">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* ------------------------------------------------------------------
         * Left Side
         * ------------------------------------------------------------------ */}

        <section className="hidden bg-primary lg:flex lg:items-center lg:justify-center">
          <LoginIllustration />
        </section>

        {/* ------------------------------------------------------------------
         * Right Side
         * ------------------------------------------------------------------ */}

        <section className="flex items-center justify-center p-8">
          <div className="w-full max-w-md space-y-8">
            <LoginHeader />

            <Card className="p-8">
              <LoginForm />
            </Card>

            <LoginFooter />
          </div>
        </section>
      </div>
    </main>
  );
}

export default LoginPage;
